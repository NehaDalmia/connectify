import threading

from src.datastructures import (
    ThreadSafeLogQueue,
    ThreadSafeConsumerDict,
    ThreadSafeProducerSet,
)
from src.models import Log


class Topic:
    """
    A topic is a collection of log messages that are related to each other.
    """

    def __init__(self, name: str, partition_index: int):
        self._name = name
        self._partition_index = partition_index
        self._logs = ThreadSafeLogQueue()
        self._producers = ThreadSafeProducerSet()
        self._consumers = ThreadSafeConsumerDict()

    def get_length(self) -> int:
        """Return the length of the topic."""
        return len(self._logs)

    def get_log(self, index: int) -> Log:
        """Return the log at the given index."""
        return self._logs[index]

    def add_log(self, log: Log) -> int:
        """Add a log to the topic and return its index."""
        return self._logs.append(log)

    def add_producer(self, producer_id: str) -> None:
        """Add a producer to the topic."""
        self._producers.add(producer_id)

    def add_consumer(self, consumer_id: str, offset: int = 0) -> None:
        """Add a consumer to the topic with given offset."""
        self._consumers.add(consumer_id, offset)

    def check_producer(self, producer_id: str) -> bool:
        """Return whether the producer is in the topic."""
        return self._producers.contains(producer_id)

    def check_consumer(self, consumer_id: str) -> bool:
        """Return whether the consumer is in the topic."""
        return self._consumers.contains(consumer_id)

    def get_consumer_offset(self, consumer_id: str) -> int:
        """Return the consumer offset."""
        return self._consumers.get_offset(consumer_id)

    def get_and_increment_consumer_offset(
        self, consumer_id: str, threshold: int
    ) -> int:
        """Return the consumer offset and increment it by one."""
        return self._consumers.get_offset_and_increment(consumer_id, threshold)