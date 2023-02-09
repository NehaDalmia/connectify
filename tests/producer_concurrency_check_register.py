import requests
import random

MESSAGES = 100

# response = requests.post(
#     "http://172.19.0.1:8080/topics", json={"name": "test_topic_n"}
# )
# assert response.status_code == 200
# assert response.json()["status"] == "success"

counters = [[0 for _ in range(10)] for _ in range(10)]

def prod(i):
    k = 107 # vary for different topic name
    response = requests.post(
        "http://172.19.0.1:8080/producer/register",
        json={"topic": f"test_topic_r{k}"},
    )
    if response.status_code != 200:
        print(response.json()["message"])
    assert response.status_code == 200
    producer_id = response.json()["producer_id"]
    list1 = [0,1]
    for cnt in range(MESSAGES):
        response = requests.post(
            "http://172.19.0.1:8080/producer/produce",
            json={
                "producer_id": producer_id,
                "topic": f"test_topic_r{k}",
                "message": f"{i} {cnt}",
                "partition_number": random.choice(list1),
            },
        )

        if response.status_code != 200 : 
            print(response.json()["message"])
    print(f"Producer {i} done")



import threading

threads = []
for i in range(10):
    threads.append(threading.Thread(target=prod, args=(i,)))
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()