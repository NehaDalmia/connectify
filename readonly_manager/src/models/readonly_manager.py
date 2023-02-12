import threading
from typing import Dict, List, Tuple
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
        # self._round_robin_turn_counter = 0
        # self._round_robin_seed = random.seed(datetime.now().microsecond)
        self._brokers_by_topic_and_ptn: Dict[(str, int), Broker] = {}
        self._topics: Dict[str, Topic] = {}
        self._brokers: List[Broker] = []

    def init_from_db(self) -> None:
        """
        Initialize the readonly manager from the databases.
        """
        
        # Instantiate the list of brokers according to the count of brokers running
        self._broker_count = BrokerDB.query.count()
        # DD: We apply a round-robin policy on the assignment of brokers for serving read
        # requests. This way we balance load across brokers when consumer traffic is high
        # self._round_robin_turn_counter = 0
        for i in range(self._broker_count):
            self._brokers.append(Broker(i+1))
        
        # # Initialize the round robin turns of the brokers in a random order
        # # DD: Reduces the chance of several readonly managers running R.R. in the same order
        # # thus helping in better load balancing
        # order_of_brokers = list(range(self._broker_count))
        # random.shuffle(order_of_brokers)
        # for i in range(self._broker_count):
        #     self._brokers[i].set_last_requested(order_of_brokers[i])

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

    def get_broker_host(self, topic_name: str, partition_number: int, consumer_id: str) -> str:
        """
        Given topic name and partition number, return the corresponding broker hostname 
        """
        return self._brokers_by_topic_and_ptn[(topic_name, partition_number)].get_name()

    def add_topic(self, topic_name : str, partition_count : int, broker_list : List[str]) -> None:
        with self._lock:
            self._topics[topic_name] = Topic(topic_name, partition_count)
            for partition_index in range(partition_count):
                self._brokers_by_topic_and_ptn[(topic_name,partition_index)] = Broker(broker_list[partition_index])
            
    
    # def find_best_broker(self, topic_name: str) -> str:
    #     """
    #     Given topic name, find a broker handling that topic. Use round-robin policy
    #     to assign a broker. Return the corresponding broker hostname.
    #     """
    #     best_broker_number = -1
    #     with self._lock:
    #         min_turn = self._broker_count
    #         # Among the subset of brokers that contain partitions of the topic passed, find the one
    #         # that got it's turn the earliest, reassign 
    #         for partition_idx in range(self._topics[topic_name].get_partition_count()):
    #             broker_number = self.get_broker(topic_name, partition_idx).get_number()
    #             broker_last_turn = self._brokers[broker_number-1].get_last_requested()
    #             adjusted_turn = (broker_last_turn - self._round_robin_turn_counter + self._broker_count) % self._broker_count
    #             if adjusted_turn < min_turn :
    #                 min_turn = adjusted_turn
    #                 best_broker_number = broker_number
    #         self._brokers[best_broker_number-1].set_last_requested(self._round_robin_turn_counter)
    #         self.round_robin_turn_counter_increment()
        
    #     return self._brokers[best_broker_number-1].get_name()

    def find_best_partition(self, topic_name: str, consumer_id: str) -> Tuple[int,str]:
        """
        Given topic name, find a broker handling that topic. Use round-robin policy
        to assign a broker. Return the corresponding broker hostname.
        """
        return self._topics[topic_name].get_and_increment_next_partition(consumer_id)

    # def round_robin_turn_counter_increment(self) -> None:
    #     """
    #     Increment the round robin turn counter by 1 modulo number of brokers
    #     """
    #     self._round_robin_turn_counter = (self._round_robin_turn_counter + 1) % self._broker_count

    def get_topics(self) -> List[str]:
        """Return the topic names."""
        return list(self._topics.keys())
    
    def has_topic(self, topic_name: str) -> bool:
        """Check if topic exists."""
        with self._lock:
            return topic_name in self._topics.keys()

    def get_broker_count(self) -> int:
        """Return the number of brokers."""
        return self._broker_count

    def get_partition_count(self, topic_name: str) -> int:
        """Return the number of partitions in a given topic."""
        with self._lock:
            return self._topics[topic_name].get_partition_count()
    
    def is_registered(self, consumer_id: str, topic_name: str) -> bool:
        """Check if consumer is registered to topic"""
        with self._lock:
            return self._topics[topic_name].contains(consumer_id)
    
    def is_request_valid(self, topic_name: str, consumer_id: str, partition_number: int = None) -> str:
        """
        Perform sanity checks (is topic present, is partition number valid, is consumer registered to this topic).
        """
        if not self.has_topic(topic_name):
            raise Exception("Topic does not exist.")
        if partition_number is not None:
            if partition_number >= self._topics[topic_name].get_partition_count() or partition_number < 0:
                raise Exception("Invalid partition number.")
        if not self.is_registered(consumer_id, topic_name):
            raise Exception("Consumer not registered with topic.")
    
    def add_consumer_to_topic(self,topic_name : str, consumer_id : str) -> None:
        with self._lock:
            self._topics[topic_name].add_consumer(consumer_id)
