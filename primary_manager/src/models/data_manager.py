import threading
from typing import Dict, List, Any, Tuple
import uuid
import time
import requests

from src.models import Topic
from src import db
from src import TopicDB, BrokerDB, ProducerDB, PartitionDB, ConsumerDB

class DataManager:
    """
    Handles the meta-data checking and updates in the primary
    manager.
    """
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._topics: Dict[str, Topic] = {}
        self._brokers: Dict[str, int] = {}
        self._inactive_brokers : Dict[str,int] = {}


    def init_from_db(self) -> None:
        """Initialize the manager from the db."""
        topics = TopicDB.query.all()
        for topic in topics:
            self._topics[topic.name] = Topic(topic.name, topic.partitions)
            # get producers with topic_name=topic.name
            producers = ProducerDB.query.filter_by(topic_name=topic.name).all()
            for producer in producers:
                self._topics[topic.name].add_producer(producer.id)
            consumers = ConsumerDB.query.filter_by(topic_name=topic.name).all()
            for consumer in consumers:
                self._topics[topic.name].add_consumer(consumer.id)
    
        brokers = BrokerDB.query.all()
        for broker in brokers:
            if broker.status == 1:
                self._brokers[broker.name] = 0
            else :
                self._inactive_brokers[broker.name] = 0
            
        partitions = PartitionDB.query.order_by(PartitionDB.ind).all()
        for partition in partitions:
            self._topics[partition.topic_name].append_broker(partition.broker_host)
            if partition.broker_host in self._brokers:
                self._brokers[partition.broker_host]+=1
            else :
                self._inactive_brokers[partition.broker_host]+=1
        

    def _contains(self, topic_name: str) -> bool:
        """Return whether the master queue contains the given topic."""
        with self._lock:
            return topic_name in self._topics
    
    def add_topic_and_return(self, topic_name: str, num_partitions: int = 2) -> List[str]:
        broker_hosts = []
        # choosing [broker] with minimum number of partitions
        with self._lock:
            if topic_name in self._topics:
                raise Exception("Topic already exists.")
            self._topics[topic_name] = Topic(topic_name, num_partitions)
            for i in range(num_partitions) : 
                min_partition_broker = min(self._brokers, key=self._brokers.get)
                self._brokers[min_partition_broker]+=1
                broker_hosts.append(min_partition_broker)
                self._topics[topic_name].append_broker(broker_hosts[i])
            db.session.add(TopicDB(name=topic_name, partitions = num_partitions))
            db.session.commit()
            for index in range(num_partitions) : 
                db.session.add(PartitionDB(ind=index,topic_name = topic_name, broker_host = broker_hosts[index]))
                db.session.commit()
        return broker_hosts
        
    def add_producer(self, topic_name: str) -> List[str]:
        """Add a producer to the topic and return its id and #partitions"""
        producer_id = str(uuid.uuid4().hex)
        self._topics[topic_name].add_producer(producer_id)

        # add to db
        db.session.add(ProducerDB(id=producer_id, topic_name=topic_name))
        db.session.commit()

        return [producer_id, self._topics[topic_name].get_partition_count()]
    
    def add_consumer(self, topic_name: str) -> List[str]:
        """Add a consumer to the topic and return its id and #partitions"""
        if not self._contains(topic_name):
            raise Exception("Topic does not exist.")
        consumer_id = str(uuid.uuid4().hex)
        self._topics[topic_name].add_consumer(consumer_id)

        # add to db
        db.session.add(ConsumerDB(id=consumer_id, topic_name=topic_name))
        db.session.commit()

        return [consumer_id, self._topics[topic_name].get_partition_count()]
    
    def get_broker_host(self, topic_name: str, producer_id: str, partition_number : int = None) -> Tuple[str,int]:
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
    
    def get_broker_list_for_topic(self, topic_name:str) -> List[str]:
        return self._topics[topic_name].get_broker_list()
    
    def add_broker(self, broker_host) -> None: 
        with self._lock:
            if ( broker_host in self._brokers ) or ( broker_host in self._inactive_brokers ) : 
                raise Exception("Broker with hostname already exists.")
            self._brokers[broker_host] = 0
            db.session.add(BrokerDB(name = broker_host,status = 1))
            db.session.commit()
    
    def remove_broker(self, broker_host) -> None: 
        with self._lock:
            if ( broker_host not in self._brokers ) and ( broker_host not in self._inactive_brokers ) : 
                raise Exception("Broker with hostname not present.")
            if broker_host in self._brokers :
                self._brokers.pop(broker_host)
            else :
                self._inactive_brokers.pop(broker_host)
            BrokerDB.query.filter_by(name = broker_host).delete()
            db.session.commit()
    
    def activate_broker(self, broker_host) -> None: 
        with self._lock:
            if ( broker_host not in self._inactive_brokers ): 
                raise Exception("Broker with hostname not inactive.")
            self._brokers[broker_host] = self._inactive_brokers[broker_host]
            self._inactive_brokers.pop(broker_host)
            broker = BrokerDB.query.filter_by(name = broker_host).first()
            broker.status = 1
            db.session.commit()

    def deactivate_broker(self, broker_host) -> None: 
        with self._lock:
            if ( broker_host not in self._brokers ): 
                raise Exception("Broker with hostname not active.")
            self._inactive_brokers[broker_host] = self._brokers[broker_host]
            self._brokers.pop(broker_host)
            broker = BrokerDB.query.filter_by(name = broker_host).first()
            broker.status = 0
            db.session.commit()

        

        
       
    
        

