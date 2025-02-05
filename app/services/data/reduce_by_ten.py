from collections import defaultdict
from datetime import datetime
from typing import List
import statistics

from app.models.container import DynamoHealthMetric
from app.services.data.data_compact import DataCompactStrategy


class ReduceByTenForEachContainer(DataCompactStrategy):
    def compact(self, data: List[DynamoHealthMetric]) -> List[DynamoHealthMetric]:
        """Reduce the dataset by a factor of 10, grouped by container."""
        if not data:
            return []

        # Convert timestamps to datetime objects
        for entry in data:
            entry.timestamp = datetime.fromisoformat(entry.timestamp)

        # Group data by container
        container_groups = defaultdict(list[DynamoHealthMetric])
        for entry in data:
            container_groups[entry.container_name].append(entry)

        compacted_data: List[DynamoHealthMetric] = []

        for _, container_data in container_groups.items():
            # Sort data by timestamp
            container_data.sort(key=lambda x: x.timestamp)

            earliest = container_data[0].timestamp
            latest = container_data[-1].timestamp
            interval = (latest - earliest) / 10

            bins = defaultdict(list)
            for entry in container_data:
                bin_index = min(9, int((entry.timestamp - earliest) / interval))
                bins[bin_index].append(entry)

            for bin_index in range(10):
                period_data: List[DynamoHealthMetric] = bins[bin_index]
                if not period_data:
                    continue

                # Accumulate values
                accumulated = {
                    "nw_rx_bytes": sum(e.nw_rx_bytes for e in period_data),
                    "nw_tx_bytes": sum(e.nw_tx_bytes for e in period_data),
                    "nw_rx_packets": sum(e.nw_rx_packets for e in period_data),
                    "nw_tx_packets": sum(e.nw_tx_packets for e in period_data),
                    "nw_rx_errors": sum(e.nw_rx_errors for e in period_data),
                    "nw_tx_errors": sum(e.nw_tx_errors for e in period_data),
                    "nw_rx_dropped": sum(e.nw_rx_dropped for e in period_data),
                    "nw_tx_dropped": sum(e.nw_tx_dropped for e in period_data),
                    "disk_read_bytes": sum(e.disk_read_bytes for e in period_data),
                    "disk_write_bytes": sum(e.disk_write_bytes for e in period_data),
                    "disk_reads": sum(e.disk_reads for e in period_data),
                    "disk_writes": sum(e.disk_writes for e in period_data),
                    "restarts": sum(e.restarts for e in period_data),
                }

                # Average values
                averaged = {
                    "memory_usage_bytes": int(statistics.mean(e.memory_usage_bytes for e in period_data)),
                    "memory_limit_bytes": int(statistics.mean(e.memory_limit_bytes for e in period_data)),
                    "memory_percent": int(statistics.mean(e.memory_percent for e in period_data)),
                    "system_cpu_usage": int(statistics.mean(e.system_cpu_usage for e in period_data)),
                    "online_cpus": int(statistics.mean(e.online_cpus for e in period_data)),
                }

                # Create a new compacted entry
                representative_entry = period_data[0]  # Use the first entry for non-aggregated fields
                compacted_entry = DynamoHealthMetric(
                    timestamp=representative_entry.timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
                    container_name=representative_entry.container_name,
                    status=representative_entry.status,
                    **accumulated,
                    **averaged
                )

                compacted_data.append(compacted_entry)

        return compacted_data
