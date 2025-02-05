import unittest
from datetime import datetime, timedelta
from app.models.container import DynamoHealthMetric
from app.services.data.reduce_by_ten import ReduceByTenForEachContainer


class TestReduceByTen(unittest.TestCase):
    def setUp(self):
        """Set up sample data for testing"""
        self.strategy = ReduceByTenForEachContainer()

        # Simulate two containers with data over a 10-minute period
        start_time = datetime(2024, 2, 5, 12, 0, 0)
        self.data = []

        for i in range(100):  # 100 entries split between two containers
            timestamp = start_time + timedelta(seconds=i * 10)
            container_name = "container_1" if i < 50 else "container_2"

            self.data.append(DynamoHealthMetric(
                timestamp=timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
                container_name=container_name,
                status="running",
                nw_rx_bytes=100 + i,
                nw_tx_bytes=200 + i,
                nw_rx_packets=10 + (i % 5),
                nw_tx_packets=20 + (i % 5),
                nw_rx_errors=1,
                nw_tx_errors=2,
                nw_rx_dropped=0,
                nw_tx_dropped=1,
                disk_read_bytes=500 + i,
                disk_write_bytes=1000 + i,
                disk_reads=5,
                disk_writes=10,
                restarts=0,
                memory_usage_bytes=10000 + (i * 10),
                memory_limit_bytes=20000,
                memory_percent=50,
                system_cpu_usage=30,
                online_cpus=4
            ))

    def test_compact_data(self):
        """Ensure ReduceByTen correctly reduces each container's data"""
        compacted_data = self.strategy.compact(self.data)

        # Check we have exactly 20 entries (10 per container)
        self.assertEqual(len(compacted_data), 20)

        # Verify each container has 10 bins
        container_1_compacted = [entry for entry in compacted_data if entry.container_name == "container_1"]
        container_2_compacted = [entry for entry in compacted_data if entry.container_name == "container_2"]
        self.assertEqual(len(container_1_compacted), 10)
        self.assertEqual(len(container_2_compacted), 10)

        # Check timestamps are valid ISO format
        for entry in compacted_data:
            self.assertTrue(isinstance(datetime.fromisoformat(entry.timestamp), datetime))

        # Verify values are aggregated correctly
        first_bin = container_1_compacted[0]
        self.assertGreater(first_bin.nw_rx_bytes, 100)  # Should be summed
        self.assertGreater(first_bin.memory_usage_bytes, 10000)  # Should be averaged

        print("✅ Test passed! Data correctly reduced per container.")


if __name__ == "__main__":
    unittest.main()
