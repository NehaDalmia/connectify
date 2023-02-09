import threading
from typing import Dict, List
from datetime import datetime
import random

from src.models import Broker, Topic
from src import BrokerDB, TopicDB, PartitionDB, ConsumerDB

class ReadonlyManager:
    """
    Readonly manager keeps track of {topic_name, partition_number} -> broker_host
    mapping. It also stores the list of topics.
    """
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._broker_count = 0
        self._round_robin_turn_counter = 0
        self._round_robin_seed = random.seed(datetime.now().microsecond)
        self._brokers_by_topic_and_ptn: Dict[(str, int), Broker]
        self._topics: Dict[str, Topic]
        self._brokers: List[Broker]

    def init_from_db(self) -> None:
        """
        Initialize the readonly manager from the databases.
        """
        
        # Instantiate the list of brokers according to the count of brokers running
        self._broker_count = BrokerDB.query.count()
        # DD: We apply a round-robin policy on the assignment of brokers for serving read
        # requests. This way we balance load across brokers when consumer traffic is high
        self._round_robin_turn_counter = 0
        for i in range(self._broker_count):
            self._brokers[i] = Broker(i+1)
        
        # Initialize the round robin turns of the brokers in a random order
        # DD: Reduces the chance of several readonly managers running R.R. in the same order
        # thus helping in better load balancing
        order_of_brokers = random.shuffle(list(range(self._broker_count)))
        for i in range(self._broker_count):
            self._brokers[i].set_last_requested(order_of_brokers[i])

        topics = TopicDB.query.all()
        for topic in topics:
            # Populate the map of topic_name -> Topic
            self._topics[topic.name] = Topic(topic.name, topic.partitions)
            partitions = PartitionDB.query.filter_by(topic_name=topic.name).all()
            for partition in partitions:
                self._brokers_by_topic_and_ptn[(partition.topic_name,partition.ind)] = self._brokers[Broker(partition.broker_host).get_number()-1]
            # Populate the list of registered consumers for this topic
            consumers = ConsumerDB.query.filter_by(topic_name=topic.name).all()
            for consumer in consumers:
                self._topics[topic.name].add_consumer(consumer.id)

    def get_broker(self, topic_name: str, partition_number: int) -> Broker:
        """
        Given topic name and partition number, return the corresponding Broker object
        """
        return self._brokers_by_topic_and_ptn[(topic_name, partition_number)]

    def get_broker_host(self, topic_name: str, partition_number: int) -> str:
        """
        Given topic name and partition number, return the corresponding broker hostname 
        """
        return self._brokers_by_topic_and_ptn[(topic_name, partition_number)].get_name()

    def find_best_broker(self, topic_name: str) -> str:
        """
        Given topic name, find a broker handling that topic. Use round-robin policy
        to assign a broker. Return the corresponding broker hostname.
        """
        best_broker_number = -1
        with self._lock:
            min_turn = self._broker_count
            # Among the subset of brokers that contain partitions of the topic passed, find the one
            # that got it's turn the earliest, reassign 
            for partition_idx in range(self._topics[topic_name].get_partition_count()):
                broker_number = self.get_broker(topic_name, partition_idx).get_number()
                broker_last_turn = self._brokers[broker_number-1].get_last_requested()
                adjusted_turn = broker_last_turn - self._round_robin_turn_counter + self._broker_count
                if adjusted_turn < min_turn :
                    min_turn = adjusted_turn
                    best_broker_number = broker_number
            self._brokers[best_broker_number-1].set_last_requested(self._round_robin_turn_counter)
            self.round_robin_turn_counter_increment()
        
        return str(Broker(best_broker_number))

    def round_robin_turn_counter_increment(self) -> None:
        """
        Increment the round robin turn counter by 1 modulo number of brokers
        """
        self._round_robin_turn_counter = (self._round_robin_turn_counter + 1) % self._broker_count

    def get_topics(self) -> List[str]:
        """Return the topic names."""
        return list(self._topics.keys())
    
    def has_topic(self, topic_name: str) -> bool:
        """Check if topic exists."""
        return topic_name in self._topics.keys()

    def is_registered(self, consumer_id: str, topic_name: str) -> bool:
        """Check if consumer is registered to topic"""
        return self._topics[topic_name].contains()
    
    def assign_size_request(self, topic_name: str, consumer_id: str) -> str:
        """
        Handle an incoming size request. Perform sanity checks (is topic present, 
        is consumer registered to this topic). Return a broker to handle this request.
        """
        if not self.has_topic(topic_name):
            raise Exception("Topic does not exist.")
        if not self.is_registered(consumer_id, topic_name):
            raise Exception("Consumer not registered with topic.")
        
        return self.find_best_broker(topic_name)
    
    def assign_consume_request(self, topic_name: str, consumer_id: str, partition_number: int = None) -> str:
        """
        Handle an incoming consume request. Perform sanity checks (is topic present, 
        is consumer registered to this topic). Return a broker to handle this request.
        """
        if not self.has_topic(topic_name):
            raise Exception("Topic does not exist.")
        if not self.is_registered(consumer_id, topic_name):
            raise Exception("Consumer not registered with topic.")
        
        if partition_number is not None:
            return self.get_broker_host(topic_name, partition_number)
        else:
            return self.find_best_broker(topic_name)
            # (as we handle only one partition of a given topic in a given broker, not needed)
            # partition_number = self.find_best_partition(broker_host, topic_name)
