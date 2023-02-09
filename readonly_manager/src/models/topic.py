import threading
from typing import List

class Topic:
    def __init__(self, topic_name: str, partition_count: int):
        self._topic_name = topic_name
        self._consumers: List[str] = []
        self._partition_count = partition_count

    def get_topic_name(self) -> str:
        """Return the name of the topic."""
        return self._topic_name
    
    def get_consumers(self) -> List[str]:
        """Return a list of registered consumers."""
        return self._consumers

    def contains(self, consumer_id: str) -> bool:
        """Check if the consumer is registered."""
        return consumer_id in self._consumers

    def add_consumer(self, consumer_id: str) -> None:
        """Add a consumer to the list of registered consumers."""
        self._consumers.append(consumer_id)
    
    def get_partition_count(self) -> int:
        """Return the number of partitions in the topic."""
        return self._partition_count
