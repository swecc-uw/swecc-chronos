import unittest
from datetime import datetime, timedelta
from app.models.container import DynamoHealthMetric
from app.services.data.prune_exited import PruneExitedAfterDays

class TestPruneExitedAfterDays(unittest.TestCase):

    def setUp(self):
        """Set up test data for pruning."""
        self.threshold_days = 14
        self.prune_strategy = PruneExitedAfterDays(time_threshold=self.threshold_days)

        now = datetime.now()
        old_timestamp = (now - timedelta(days=15)).isoformat()  # Older than threshold
        recent_timestamp = (now - timedelta(days=10)).isoformat()  # Within threshold

        junk = {
            "nw_rx_bytes": 100,
            "nw_tx_bytes": 200,
            "nw_rx_packets": 10,
            "nw_tx_packets": 20,
            "nw_rx_errors": 1,
            "nw_tx_errors": 2,
            "nw_rx_dropped": 0,
            "nw_tx_dropped": 1,
            "disk_read_bytes": 500,
            "disk_write_bytes": 1000,
            "disk_reads": 5,
            "disk_writes": 10,
            "restarts": 0,
            "memory_usage_bytes": 10000,
            "memory_limit_bytes": 20000,
            "memory_percent": 50,
            "system_cpu_usage": 30,
            "online_cpus": 4,
        }

        self.test_data = [
            DynamoHealthMetric(timestamp=old_timestamp, container_name="container_1", status="exited", started_at=None, finished_at=None, **junk),  # Should be pruned
            DynamoHealthMetric(timestamp=old_timestamp, container_name="container_2", status="running", started_at=old_timestamp, finished_at=None, **junk),  # Should NOT be pruned
            DynamoHealthMetric(timestamp=recent_timestamp, container_name="container_3", status="exited", started_at=None, finished_at=None, **junk),  # Should NOT be pruned
            DynamoHealthMetric(timestamp=old_timestamp, container_name="container_4", status="exited", started_at="2023-01-01T00:00:00", finished_at=None, **junk),  # Should NOT be pruned
        ]

    def test_compact(self):
        """Test that PruneExitedAfterDays correctly removes old exited containers with no start/finish time."""
        pruned_data = self.prune_strategy.compact(self.test_data)

        expected_containers = {"container_2", "container_3", "container_4"}
        result_containers = {entry.container_name for entry in pruned_data}

        self.assertSetEqual(result_containers, expected_containers, f"Expected {expected_containers}, got {result_containers}")

if __name__ == '__main__':
    unittest.main()
