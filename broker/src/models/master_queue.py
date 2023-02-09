import threading
from typing import Dict, List, Optional
import uuid
import time

from src.models import Topic, Log
from src import db
from src import TopicDB, ConsumerDB, ProducerDB, LogDB


class MasterQueue:
    """
    Master queue is a collection of all the topics.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._topics: Dict[str, Topic] = {}

    def init_from_db(self) -> None:
        """Initialize the master queue from the db."""
        topics = TopicDB.query.all()
        for topic in topics:
            self._topics[topic.name] = Topic(topic.name)
            # get consumers with topic_name=topic.name
            consumers = ConsumerDB.query.filter_by(topic_name=topic.name).all()
            for consumer in consumers:
                self._topics[topic.name].add_consumer(
                    consumer.id, consumer.offset
                )
            # get producers with topic_name=topic.name
            # producers = ProducerDB.query.filter_by(topic_name=topic.name).all()
            # for producer in producers:
            #     self._topics[topic.name].add_producer(producer.id)
            # get logs with topic_name=topic.name and ordered by their ids
            logs = (
                LogDB.query.filter_by(topic_name=topic.name)
                .order_by(LogDB.id)
                .all()
            )
            for log in logs:
                self._topics[topic.name].add_log(
                    Log(log.producer_id, log.message, log.timestamp)
                )

    def _contains(self, topic_name: str) -> bool:
        """Return whether the master queue contains the given topic."""
        with self._lock:
            return topic_name in self._topics

    def check_and_add_topic(self, topic_name: str) -> None:
        """Add a topic to the master queue."""
        with self._lock:
            self._topics[topic_name] = Topic(topic_name)

        # add to db
        db.session.add(TopicDB(name=topic_name))
        db.session.commit()

    def get_size(self, topic_name: str, consumer_id: str) -> int:
        """Return the number of log messages in the requested topic for
        this consumer."""
        if not self._contains(topic_name):
            raise Exception("Topic does not exist.")
        if not self._topics[topic_name].check_consumer(consumer_id):
            raise Exception("Consumer not registered with topic.")
        total_length = self._topics[topic_name].get_length()
        consumer_offset = self._topics[topic_name].get_consumer_offset(
            consumer_id
        )
        return total_length - consumer_offset

    def get_log(self, topic_name: str, consumer_id: str) -> Optional[Log]:
        """Return the log if consumer registered with topic and has a log
        available to pull."""
        if not self._contains(topic_name):
            raise Exception("Topic does not exist.")
        if not self._topics[topic_name].check_consumer(consumer_id):
            raise Exception("Consumer not registered with topic.")
        current_length = self._topics[topic_name].get_length()
        index_to_fetch = self._topics[
            topic_name
        ].get_and_increment_consumer_offset(consumer_id, current_length)
        if index_to_fetch == current_length:
            return None

        # db update with index_to_fetch + 1
        db.session.execute(
            f"""
            UPDATE consumer 
            SET "offset" = GREATEST("offset", {index_to_fetch + 1}) 
            where id = '{consumer_id}'
            """
        )
        db.session.commit()
        return self._topics[topic_name].get_log(index_to_fetch)

    def add_log(self, topic_name: str, producer_id: str, message: str) -> None:
        """Add a log to the topic"""
        timestamp = time.time()
        index = self._topics[topic_name].add_log(
            Log(producer_id, message, timestamp)
        )

        # add to db
        db.session.add(
            LogDB(
                id=index,
                topic_name=topic_name,
                producer_id=producer_id,
                message=message,
                timestamp=timestamp,
            )
        )
        db.session.commit()

    def get_topics(self) -> List[str]:
        """Return the topic names."""
        with self._lock:
            return list(self._topics.keys())

    def add_consumer(self, topic_name: str, consumer_id: str) -> None:
        """Add a consumer to the topic"""
        self._topics[topic_name].add_consumer(consumer_id)
        # add to db
        db.session.add(
            ConsumerDB(id=consumer_id, topic_name=topic_name, offset=0)
        )
        db.session.commit()