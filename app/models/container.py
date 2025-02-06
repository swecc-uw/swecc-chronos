from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Union
from datetime import datetime
from enum import Enum

class ContainerMetadata(BaseModel):
    """container identification and configuration data"""
    short_id: str = Field(..., description="First 12 characters of container ID")
    name: str = Field(..., description="Container name")
    image: str = Field(..., description="Image name and tag")
    created_at: datetime = Field(..., description="Container creation timestamp")
    labels: Dict[str, str] = Field(default_factory=dict, description="Container labels")

    command: Optional[Union[str, List[str]]] = Field(None, description="Command running in container")
    ports: Dict[str, List[Dict[str, str]]] = Field(
        default_factory=dict,
        description="Exposed and mapped ports"
    )

    @property
    def command_string(self) -> Optional[str]:
        """Convert command to string representation regardless of input type"""
        if isinstance(self.command, str):
            return self.command
        elif isinstance(self.command, list):
            return ' '.join(self.command)
        return None

class NetworkStats(BaseModel):
    """network interface statistics"""
    rx_bytes: int = Field(..., description="Received bytes")
    tx_bytes: int = Field(..., description="Transmitted bytes")
    rx_packets: int = Field(..., description="Received packets")
    tx_packets: int = Field(..., description="Transmitted packets")
    rx_errors: int = Field(0, description="Receive errors")
    tx_errors: int = Field(0, description="Transmit errors")
    rx_dropped: int = Field(0, description="Received packets dropped")
    tx_dropped: int = Field(0, description="Transmitted packets dropped")

class DiskStats(BaseModel):
    """block device I/O statistics"""
    read_bytes: int = Field(0, description="Total bytes read")
    write_bytes: int = Field(0, description="Total bytes written")
    reads: int = Field(0, description="Total read operations")
    writes: int = Field(0, description="Total write operations")
    io_service_bytes_recursive: Optional[List[Dict]] = Field(
        None,
        description="Detailed I/O statistics per block device"
    )

    @classmethod
    def create_empty(cls) -> 'DiskStats':
        """Create an empty DiskStats object with zero values"""
        return cls(
            read_bytes=0,
            write_bytes=0,
            reads=0,
            writes=0,
            io_service_bytes_recursive=[]
        )

class MemoryStats(BaseModel):
    """memory usage statistics"""
    usage_bytes: int = Field(..., description="Current memory usage in bytes")
    limit_bytes: int = Field(..., description="Memory limit in bytes")
    percent: float = Field(..., description="Memory usage percentage")

    # optional detailed memory stats
    stats: Optional[Dict] = Field(None, description="Detailed memory statistics")
    cache: Optional[int] = Field(None, description="Page cache memory")
    rss: Optional[int] = Field(None, description="Anonymous and swap cache")
    swap: Optional[int] = Field(0, description="Swap usage")

class CpuStats(BaseModel):
    """CPU usage statistics"""
    percent: float = Field(..., description="CPU usage percentage")
    system_cpu_usage: int = Field(..., description="Host's total CPU usage")
    online_cpus: int = Field(..., description="Number of CPU cores available")

    # optional detailed CPU stats
    usage_in_usermode: Optional[int] = Field(None, description="Time spent in user mode")
    usage_in_kernelmode: Optional[int] = Field(None, description="Time spent in kernel mode")
    cpu_usage: Optional[Dict] = Field(None, description="Detailed CPU usage statistics")

class ContainerHealth(BaseModel):
    """container health and status information"""
    status: str = Field(..., description="Container status (running, stopped, etc.)")
    health_status: Optional[str] = Field(None, description="Health check status if configured")
    restarts: int = Field(0, description="Number of container restarts")
    exit_code: Optional[int] = Field(None, description="Last exit code if stopped")
    started_at: Optional[datetime] = Field(None, description="Last start timestamp")
    finished_at: Optional[datetime] = Field(None, description="Last stop timestamp")

class ContainerStats(BaseModel):
    """all container statistics"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Statistics timestamp")
    metadata: ContainerMetadata
    health: ContainerHealth
    cpu: CpuStats
    memory: MemoryStats
    network: Dict[str, NetworkStats] = Field(
        default_factory=dict,
        description="Stats per network interface"
    )
    disk: DiskStats

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DockerActionType(str, Enum):
    # general actions (more that one that have this type)
    DESTROY = "destroy"
    # container actions
    ATTACH = "attach"
    COMMIT = "commit"
    COPY = "copy"
    CREATE = "create"
    DETACH = "detach"
    DIE = "die"
    EXEC_CREATE = "exec_create"
    EXEC_DETACH = "exec_detach"
    EXEC_DIE = "exec_die"
    EXEC_START = "exec_start"
    EXPORT = "export"
    HEALTH_STATUS = "health_status"
    KILL = "kill"
    OOM = "oom"
    PAUSE = "pause"
    RENAME = "rename"
    RESIZE = "resize"
    RESTART = "restart"
    START = "start"
    STOP = "stop"
    TOP = "top"
    UNPAUSE = "unpause"
    UPDATE = "update"

    # network actions
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    REMOVE = "remove"

    #image actions
    DELETE = "delete"
    IMPORT = "import"
    LOAD = "load"
    PULL = "pull"
    PUSH = "push"
    SAVE = "save"
    TAG = "tag"
    UNTAG = "untag"

class DockerEventType(str, Enum):
    CONTAINER = "container"
    NETWORK = "network"
    VOLUME = "volume"
    IMAGE = "image"
    PLUGIN = "plugin"

class DockerEvent(BaseModel):
    id: str = Field(..., description="Event ID")
    action: DockerActionType
    time: datetime = Field(..., description="Event timestamp")
    name: str = Field(..., description="Target name")
    type: DockerEventType

    def to_dynamo_item(self) -> dict:
        """Convert to a format suitable for DynamoDB."""
        return {
            "event_type#container_name": f"{self.type.value}#{self.name}",  # Partition Key
            "timestamp": int(self.time.timestamp()),  # Sort Key
            "id": self.id,
            "action": self.action.value,  # Convert Enum to string
        }
    
    @classmethod
    def from_dynamo_item(cls, item: dict) -> 'DockerEvent':
        """Convert a DynamoDB item back to a DockerEvent."""
        event_type, container_name = item["event_type#container_name"].split("#")
        return cls(
            id=item["id"],
            action=DockerActionType(item["action"]),
            time=datetime.fromtimestamp(float(item["timestamp"])),
            name=container_name,
            type=DockerEventType(event_type)
        )

def convert_raw_event_to_docker_event(raw_event: Dict) -> DockerEvent:
    """Convert raw event data to DockerEvent"""
    event_type = raw_event.get('Type', '')
    event_action = raw_event.get('Action', '')
    event_time = datetime.fromtimestamp(raw_event.get('time', 0))
    event_id = raw_event.get('id', '')

    target_name = raw_event.get('Actor', {}).get('Attributes', {}).get('name', '')
    
    return DockerEvent(
        id=event_id,
        action=event_action,
        time=event_time,
        name=target_name,
        type=DockerEventType(event_type)
    )

class DynamoHealthMetric(BaseModel):
    # dynamodb type system is a pain
    """Compact & compatible DynamoDB health metric data"""
    container_name: str = Field(..., description="Container name")
    timestamp: str = Field(..., description="Metric timestamp")
    memory_usage_bytes: int = Field(..., description="Memory usage in bytes")
    memory_limit_bytes: int = Field(..., description="Memory limit in bytes")
    memory_percent: int = Field(..., description="Memory usage percentage")
    system_cpu_usage: int = Field(..., description="Host's total CPU usage")
    online_cpus: int = Field(..., description="Number of CPU cores available")
    status: str = Field(..., description="Container status")
    health_status: Optional[str] = Field(None, description="Health check status")
    nw_rx_bytes: int = Field(..., description="Received bytes")
    nw_tx_bytes: int = Field(..., description="Transmitted bytes")
    nw_rx_packets: int = Field(..., description="Received packets")
    nw_tx_packets: int = Field(..., description="Transmitted packets")
    nw_rx_errors: int = Field(..., description="Receive errors")
    nw_tx_errors: int = Field(..., description="Transmit errors")
    nw_rx_dropped: int = Field(..., description="Received packets dropped")
    nw_tx_dropped: int = Field(..., description="Transmitted packets dropped")
    disk_read_bytes: int = Field(..., description="Total bytes read")
    disk_write_bytes: int = Field(..., description="Total bytes written")
    disk_reads: int = Field(..., description="Total read operations")
    disk_writes: int = Field(..., description="Total write operations")
    restarts: int = Field(..., description="Number of container restarts")
    exit_code: Optional[int] = Field(None, description="Last exit code")
    started_at: Optional[str] = Field(None, description="Last start timestamp")
    finished_at: Optional[str] = Field(None, description="Last stop timestamp")


def convert_health_metric_to_dynamo(metric: ContainerStats) -> DynamoHealthMetric:
    """Convert ContainerStats to DynamoHealthMetric"""
    first_network_key = next(iter(metric.network))
    return DynamoHealthMetric(
        container_name=metric.metadata.name,
        timestamp=metric.timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
        memory_usage_bytes=metric.memory.usage_bytes,
        memory_limit_bytes=metric.memory.limit_bytes,
        memory_percent=int(metric.memory.percent),
        system_cpu_usage=metric.cpu.system_cpu_usage,
        online_cpus=metric.cpu.online_cpus,
        status=metric.health.status,
        health_status=metric.health.health_status,
        nw_rx_bytes=metric.network[first_network_key].rx_bytes,
        nw_tx_bytes=metric.network[first_network_key].tx_bytes,
        nw_rx_packets=metric.network[first_network_key].rx_packets,
        nw_tx_packets=metric.network[first_network_key].tx_packets,
        nw_rx_errors=metric.network[first_network_key].rx_errors,
        nw_tx_errors=metric.network[first_network_key].tx_errors,
        nw_rx_dropped=metric.network[first_network_key].rx_dropped,
        nw_tx_dropped=metric.network[first_network_key].tx_dropped,
        disk_read_bytes=metric.disk.read_bytes,
        disk_write_bytes=metric.disk.write_bytes,
        disk_reads=metric.disk.reads,
        disk_writes=metric.disk.writes,
        restarts=metric.health.restarts,
        exit_code=metric.health.exit_code,
        started_at=metric.health.started_at.strftime('%Y-%m-%dT%H:%M:%S') if metric.health.started_at else None,
        finished_at=metric.health.finished_at.strftime('%Y-%m-%dT%H:%M:%S') if metric.health.finished_at else None
    )

class JobItem(BaseModel):
    id: str = Field(..., description="Job ID")