import requests
import aiohttp
from urllib.parse import urljoin
from typing import Dict, Tuple, List

from .routes import Routes
from .async_requests import AsyncRequests


class Consumer:
    """
    Consumer class to interact with the queue.

    address: str - the address of the broker
    port: int - the port of the broker
    protocol: str - the protocol to use (currently only http is supported)
    """

    def __init__(
        self, address: str, port: int, protocol: str = "http"
    ) -> None:
        self.broker = protocol + "://" + address + ":" + str(port)
        self.topics: Dict[str, str] = {}
        self.async_requestor = AsyncRequests()

    async def _register(
        self, session: aiohttp.client.ClientSession, topic_name: str
    ) -> Tuple[bool, str]:
        """
        Register a topic to consume from if not already registered.
        """
        if topic_name not in self.topics:
            try:
                url = urljoin(self.broker, Routes.register_consumer)
                json_data: Dict[str, str] = {"topic": topic_name}
                async with session.post(url, json=json_data) as response:
                    response_status = response.status
                    response_json = await response.json()
                    if response_status == 200:
                        consumer_id = response_json["consumer_id"]
                        self.topics[topic_name] = consumer_id
                        return True, "Topic registered."
                    elif response_status == 400:
                        return False, response_json["message"]
                    else:
                        return False, await response.text()
            except Exception as e:
                return False, str(e)
        return False, "Topic already registered."

    async def _consume(
        self, session: aiohttp.client.ClientSession, topic_name: str
    ) -> Tuple[bool, str]:
        """
        Consume a message from a topic.
        """
        if topic_name in self.topics:
            try:
                url = urljoin(self.broker, Routes.consume_message)
                json_data: Dict[str, str] = {
                    "topic": topic_name,
                    "consumer_id": self.topics[topic_name],
                }
                async with session.get(url, json=json_data) as response:
                    response_status = response.status
                    response_json = await response.json()
                    if response_status == 200:
                        status = response_json["status"]
                        return status == "success", response_json["message"]
                    elif response_status == 400:
                        return False, response_json["message"]
                    else:
                        return False, await response.text()
            except Exception as e:
                return False, str(e)
        return False, "Topic not registered."

    async def _get_queue_length(
        self, session: aiohttp.client.ClientSession, topic_name: str
    ) -> Tuple[bool, str]:
        """
        Get the length of a queue.
        """
        if topic_name in self.topics:
            try:
                url = urljoin(self.broker, Routes.size)
                json_data: Dict[str, str] = {
                    "topic": topic_name,
                    "consumer_id": self.topics[topic_name],
                }
                async with session.get(url, json=json_data) as response:
                    response_status = response.status
                    response_json = await response.json()
                    if response_status == 200:
                        return True, response_json["size"]
                    elif response_status == 400:
                        return False, response_json["message"]
                    else:
                        return False, await response.text()
            except Exception as e:
                return False, str(e)
        return False, "Topic not registered."

    def consume_multiple(
        self, topic_name: str, n: int
    ) -> List[Tuple[bool, str]]:
        """
        Consume multiple messages from a topic. 

        Params:
            topic_name - the name of the topic to consume from
            n - the number of messages to consume
        
        Returns:
            A list of tuples of (success, message).
            If `success` is True:
                `message` is the message retrieved from topic
            Otherwise, it is an error message.

        Note: This method does not guarantee that the messages are in order.
        To guarantee order, use `consume` method multiple times.
        """
        return self.async_requestor.run(
            self._consume, [{"topic_name": topic_name} for _ in range(n)]
        )

    def consume(self, topic_name: str) -> Tuple[bool, str]:
        """
        Consume a message from a topic. 

        Params:
            topic_name - the name of the topic to consume from
        
        Returns:
            Tuple of (success, message).
            If `success` is True:
                `message` is the message retrieved from topic
            Otherwise, it is an error message.
        """
        return self.consume_multiple(topic_name, 1)[0]

    def register(self, topic_name: str) -> Tuple[bool, str]:
        """
        Register a topic to consume from. 

        Params:
            topic_name - the name of the topic to register
        
        Returns:
            Tuple of (success, message).
        """
        return self.async_requestor.run(
            self._register, [{"topic_name": topic_name}]
        )[0]

    def get_queue_length(self, topic_name: str) -> Tuple[bool, str]:
        """
        Get the length of a queue. 

        Params:
            topic_name - the name of the topic to get the length of
        
        Returns:
            Tuple of (success, message).
            If `success` is True:
                `message` is the number of messages remaining to be cosumed from the queue 
            Otherwise, it is an error message.
        """
        return self.async_requestor.run(
            self._get_queue_length, [{"topic_name": topic_name}]
        )[0]

    def can_consume(self, topic_name: str) -> bool:
        """
        Check if a topic can be consumed from.

        Params:
            topic_name - the name of the topic to check

        Returns:
            True if there is at least one unconsumed message in the queue.
        """
        success, message = self.get_queue_length(topic_name)
        return success and int(message) > 0

    def close(self) -> None:
        """
        Close the session.
        """
        self.async_requestor.close()