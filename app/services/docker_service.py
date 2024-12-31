import docker
from typing import List, Dict, Optional
from datetime import datetime
from app.models.container import (
    ContainerMetadata,
    ContainerHealth,
    ContainerStats,
    CpuStats,
    MemoryStats,
    DiskStats,
    NetworkStats,
)
import logging
from docker.errors import NotFound, APIError

logger = logging.getLogger(__name__)


class DockerService:
    def __init__(self):
        self.client = docker.from_env()

    def get_all_containers_live_status(self):
        try:
            containers = self.client.containers.list(all=True)
            return {
                container.name: container.status
                for container in containers
            }
        except Exception as e:
            logger.error(f"Failed to list containers: {str(e)}")
            return {}

    def get_container_metadata(self, container_name: str) -> Optional[ContainerMetadata]:
        try:
            container = self.client.containers.get(container_name)
            return self._get_container_metadata(container)
        except NotFound:
            logger.warning(f"Container {container_name} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting metadata for container {container_name}: {str(e)}")
            return None

    def _get_container_metadata(self, container) -> ContainerMetadata:
        try:
            container.reload()

            # ports
            ports = {}
            for container_port, host_configs in (
                container.attrs.get("NetworkSettings", {}).get("Ports", {}).items()
            ):
                if host_configs:
                    ports[container_port] = [
                        {
                            "HostIp": config.get("HostIp", ""),
                            "HostPort": config.get("HostPort", ""),
                        }
                        for config in host_configs
                        if isinstance(config, dict)
                    ]

            # command
            command = container.attrs.get("Config", {}).get("Cmd")
            if isinstance(command, list):
                command = [
                    str(cmd) for cmd in command
                ]

            return ContainerMetadata(
                short_id=container.short_id,
                name=container.name,
                image=(
                    container.image.tags[0]
                    if container.image.tags
                    else container.image.id[:12]
                ),
                created_at=datetime.fromisoformat(
                    container.attrs["Created"].replace("Z", "+00:00")
                ),
                labels=container.labels,
                command=command,  # can be string, list, or None
                ports=ports,
            )
        except Exception as e:
            logger.error(
                f"Error getting metadata for container {container.name}: {str(e)}"
            )
            # minimal valid metadata if fail
            return ContainerMetadata(
                short_id=container.short_id,
                name=container.name,
                image="unknown",
                created_at=datetime.utcnow(),  # fallback to current time
                labels={},
            )

    def _get_container_health(self, container) -> ContainerHealth:
        try:
            health_status = None
            if "Health" in container.attrs.get("State", {}):
                health_status = container.attrs["State"]["Health"]["Status"]

            state = container.attrs.get("State", {})

            return ContainerHealth(
                status=container.status,
                health_status=health_status,
                restarts=container.attrs.get("RestartCount", 0),
                exit_code=state.get("ExitCode"),
                started_at=(
                    datetime.fromisoformat(
                        state.get("StartedAt", "").replace("Z", "+00:00")
                    )
                    if state.get("StartedAt")
                    else None
                ),
                finished_at=(
                    datetime.fromisoformat(
                        state.get("FinishedAt", "").replace("Z", "+00:00")
                    )
                    if state.get("FinishedAt")
                    and state.get("FinishedAt") != "0001-01-01T00:00:00Z"
                    else None
                ),
            )
        except Exception as e:
            logger.error(
                f"Error getting health for container {container.name}: {str(e)}"
            )
            return ContainerHealth(status=container.status or "unknown", restarts=0)

    def _get_container_cpu_stats(self, stats_data: Dict) -> CpuStats:
        try:
            cpu_stats = stats_data.get("cpu_stats", {})
            precpu_stats = stats_data.get("precpu_stats", {})

            # CPU usage percentage
            cpu_delta = cpu_stats.get("cpu_usage", {}).get(
                "total_usage", 0
            ) - precpu_stats.get("cpu_usage", {}).get("total_usage", 0)

            system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get(
                "system_cpu_usage", 0
            )

            online_cpus = cpu_stats.get(
                "online_cpus",
                len(cpu_stats.get("cpu_usage", {}).get("percpu_usage", [1])),
            )

            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0

            return CpuStats(
                percent=round(cpu_percent, 2),
                system_cpu_usage=cpu_stats.get("system_cpu_usage", 0),
                online_cpus=online_cpus,
                usage_in_usermode=cpu_stats.get("cpu_usage", {}).get(
                    "usage_in_usermode"
                ),
                usage_in_kernelmode=cpu_stats.get("cpu_usage", {}).get(
                    "usage_in_kernelmode"
                ),
                cpu_usage=cpu_stats.get("cpu_usage"),
            )
        except Exception as e:
            logger.error(f"Error calculating CPU stats: {str(e)}")
            return CpuStats(percent=0.0, system_cpu_usage=0, online_cpus=1)

    def _get_container_memory_stats(self, stats_data: Dict) -> MemoryStats:
        try:
            memory_stats = stats_data.get("memory_stats", {})

            usage = memory_stats.get("usage", 0)
            limit = memory_stats.get("limit", 0)

            if limit == 0:
                limit = self._get_host_memory_limit()

            percent = (usage / limit) * 100.0 if limit > 0 else 0.0

            return MemoryStats(
                usage_bytes=usage,
                limit_bytes=limit,
                percent=round(percent, 2),
                stats=memory_stats.get("stats"),
                cache=memory_stats.get("stats", {}).get("cache"),
                rss=memory_stats.get("stats", {}).get("rss"),
                swap=memory_stats.get("stats", {}).get("swap", 0),
            )
        except Exception as e:
            logger.error(f"Error calculating memory stats: {str(e)}")
            return MemoryStats(
                usage_bytes=0, limit_bytes=self._get_host_memory_limit(), percent=0.0
            )

    def _get_container_disk_stats(self, stats_data: Dict) -> DiskStats:
        """Extract disk I/O statistics handling missing or invalid data."""
        try:
            blkio_stats = stats_data.get("blkio_stats", {})
            if not blkio_stats:
                return DiskStats.create_empty()

            # initialize counters
            read_bytes = 0
            write_bytes = 0
            reads = 0
            writes = 0

            # process recursive IO stats
            io_service_bytes = blkio_stats.get("io_service_bytes_recursive") or []
            io_serviced = blkio_stats.get("io_serviced_recursive") or []

            # Safely process IO bytes
            for stat in io_service_bytes:
                if isinstance(stat, dict):
                    op = stat.get("op", "")
                    value = stat.get("value", 0)
                    if op == "Read":
                        read_bytes += value
                    elif op == "Write":
                        write_bytes += value

            # process IO operations
            for stat in io_serviced:
                if isinstance(stat, dict):
                    op = stat.get("op", "")
                    value = stat.get("value", 0)
                    if op == "Read":
                        reads += value
                    elif op == "Write":
                        writes += value

            return DiskStats(
                read_bytes=read_bytes,
                write_bytes=write_bytes,
                reads=reads,
                writes=writes,
                io_service_bytes_recursive=(
                    io_service_bytes if io_service_bytes else None
                ),
            )
        except Exception as e:
            logger.error(f"Error calculating disk stats: {str(e)}")
            return DiskStats.create_empty()

    def _get_container_network_stats(self, stats_data: Dict) -> Dict[str, NetworkStats]:
        try:
            networks = stats_data.get("networks", {})
            network_stats = {}

            for interface, data in networks.items():
                network_stats[interface] = NetworkStats(
                    rx_bytes=data.get("rx_bytes", 0),
                    tx_bytes=data.get("tx_bytes", 0),
                    rx_packets=data.get("rx_packets", 0),
                    tx_packets=data.get("tx_packets", 0),
                    rx_errors=data.get("rx_errors", 0),
                    tx_errors=data.get("tx_errors", 0),
                    rx_dropped=data.get("rx_dropped", 0),
                    tx_dropped=data.get("tx_dropped", 0),
                )

            return network_stats or {
                "default": NetworkStats(
                    rx_bytes=0,
                    tx_bytes=0,
                    rx_packets=0,
                    tx_packets=0,
                    rx_errors=0,
                    tx_errors=0,
                    rx_dropped=0,
                    tx_dropped=0,
                )
            }
        except Exception as e:
            logger.error(f"Error calculating network stats: {str(e)}")
            return {
                "default": NetworkStats(
                    rx_bytes=0,
                    tx_bytes=0,
                    rx_packets=0,
                    tx_packets=0,
                    rx_errors=0,
                    tx_errors=0,
                    rx_dropped=0,
                    tx_dropped=0,
                )
            }

    def _get_host_memory_limit(self) -> int:
        try:
            info = self.client.info()
            return info.get("MemTotal", 0)
        except Exception:
            return 0

    def _get_container_stats(self, container) -> Optional[ContainerStats]:
        try:
            # get raw stats from Docker API
            stats_data = container.stats(stream=False)

            # build statistics with derived values
            return ContainerStats(
                metadata=self._get_container_metadata(container),
                health=self._get_container_health(container),
                cpu=self._get_container_cpu_stats(stats_data),
                memory=self._get_container_memory_stats(stats_data),
                network=self._get_container_network_stats(stats_data),
                disk=self._get_container_disk_stats(stats_data),
            )
        except NotFound:
            logger.warning(
                f"Container {container.name} not found, might have been removed"
            )
            return None
        except APIError as e:
            logger.error(f"Docker API error for container {container.name}: {str(e)}")
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error getting stats for container {container.name}: {str(e)}"
            )
            return None

    def poll_all_container_stats(self) -> List[ContainerStats]:
        stats = []
        try:
            containers = self.client.containers.list(all=True)
        except Exception as e:
            logger.error(f"Failed to list containers: {str(e)}")
            return []

        for container in containers:
            try:
                container_stats = self._get_container_stats(container)
                if container_stats:
                    stats.append(container_stats)
            except Exception as e:
                logger.error(
                    f"Error getting stats for container {container.name}: {str(e)}"
                )
                continue

        return stats
