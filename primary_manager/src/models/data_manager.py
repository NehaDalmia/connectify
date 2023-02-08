import threading
from typing import Dict, List, Any
import uuid
import time
import requests

from src.models import Topic
from src import db
from src import TopicDB, BrokerDB, ProducerDB, PartitionDB

class DataManager:
    """
    Handles the meta-data checking and updates in the primary
    manager.
    """
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._topics: Dict[str, Topic] = {}
        self._brokers: Dict[str, int] = {}

    def init_from_db(self) -> None:
        """Initialize the manager from the db."""
        topics = TopicDB.query.all()
        for topic in topics:
            self._topics[topic.name] = Topic(topic.name, topic.partitions)
            # get producers with topic_name=topic.name
            producers = ProducerDB.query.filter_by(topic_name=topic.name).all()
            for producer in producers:
                self._topics[topic.name].add_producer(producer.id)
        brokers = BrokerDB.query.all()
        for broker in brokers:
            self._brokers[broker.name] = 0
            
        partitions = PartitionDB.query.order_by(PartitionDB.ind).all()
        for partition in partitions:
            self._topics[partition.topic_name].append_broker(partition.broker_host)
            self._brokers[partition.broker_host]+=1
        

    def _contains(self, topic_name: str) -> bool:
        """Return whether the master queue contains the given topic."""
        with self._lock:
            return topic_name in self._topics
    
    def check_and_get_chosen_brokers(self, topic_name: str, num_partitions: int = 2) -> List[str]:
        broker_hosts = []
        # choosing partition with minimum number of brokers
        with self._lock:
            if topic_name in self._topics:
                raise Exception("Topic already exists.")
            self._topics[topic_name] = Topic(topic_name, num_partitions)
            for i in range(num_partitions) : 
                min_partition_broker = min(self._brokers, key=self._brokers.get)
                self._brokers[min_partition_broker]+=1
                broker_hosts.append(min_partition_broker)
                self._topics[topic_name].append_broker(broker_hosts[i])
        return broker_hosts

    def add_topic(self, topic_name: str, broker_hosts: List[str], num_partitions: int = 2) -> None:
        """Add a topic to the master queue."""
        # add to db
        db.session.add(TopicDB(name=topic_name, partitions = num_partitions))
        db.session.commit()
        for index in range(num_partitions) : 
            db.session.add(PartitionDB(ind=index,topic_name = topic_name, broker_host = broker_hosts[index]))
            db.session.commit()

    def add_producer(self, topic_name: str) -> List[str]:
        """Add a producer to the topic and return its id."""
        if not self._contains(topic_name):
            try: 
                requests.post("http://primary:5000/topics",json = {"name":topic_name})
            except Exception as e:
                raise
        producer_id = str(uuid.uuid4().hex)
        self._topics[topic_name].add_producer(producer_id)

        # add to db
        db.session.add(ProducerDB(id=producer_id, topic_name=topic_name))
        db.session.commit()

        return [producer_id, self._topics[topic_name].get_partition_count()]
    
    def get_broker_host(self, topic_name: str, producer_id: str, partition_number : int = None) -> str:
        """Add a log to the topic if producer is registered with topic."""
        if not self._contains(topic_name):
            raise Exception("Topic does not exist.")
        if not self._topics[topic_name].check_producer(producer_id):
            raise Exception("Producer not registered with topic.")
        
        broker_index = partition_number
        if partition_number is None:
            return self._topics[topic_name].round_robin_return_and_update_partition_index(producer_id)
        else:
            if self._topics[topic_name].get_partition_count() <= partition_number :
                raise Exception("Invalid Partition Number.")
            return  self._topics[topic_name].update_partition_index(producer_id, partition_number)
        
       
    
        

