from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Union
from datetime import datetime

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