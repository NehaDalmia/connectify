import requests
import random
import time

MESSAGES = 10

# response = requests.post(
#     "http://172.19.0.1:8080/topics", json={"name": "test_topic_n"}
# )
# assert response.status_code == 200
# assert response.json()["status"] == "success"
consumer_ids = []
counters = [[0 for _ in range(10)] for _ in range(10)]
k = 99
def prod(i):
    
    response = requests.post(
        "http://172.19.0.1:8080/topics", json={"name": f"test_topic_r{k}","number_of_partitions":5}
    )
    if response.status_code != 200:
        print(response.json()["message"])
    else : 
        print(f"producer {i} created topic")

    response = requests.post(
        "http://172.19.0.1:8080/consumer/register",
        json={"topic": f"test_topic_r{k}"},
    )
    if response.status_code != 200:
        print(response.json()["message"])
    consumer_ids.append(response.json()["consumer_id"])
    
    # assert response.status_code == 200
    # assert response.json()["status"] == "success"
    response = requests.post(
        "http://172.19.0.1:8080/producer/register",
        json={"topic": f"test_topic_r{k}"},
    )
    if response.status_code != 200:
        print(response.json()["message"])
        # print(f"error at producer{i}")
    # assert response.status_code == 200
    producer_id = response.json()["producer_id"]
    list1 = [0,1,2,3,4]
    for cnt in range(MESSAGES):
        part_id = random.choice(list1)
        response = requests.post(
            "http://172.19.0.1:8080/producer/produce",
            json={
                "producer_id": producer_id,
                "topic": f"test_topic_r{k}",
                "message": f"{i} {cnt}",
                "partition_number":  part_id,
            },
        )
        print(f"produced at {part_id}")

        if response.status_code != 200 : 
            print(response.json()["message"])
    print(f"Producer {i} done")

def cons(i, cons_id):

    list1 = [0,1,2,3,4]
    for cnt in range(MESSAGES):
        part_id = random.choice(list1)
        response = requests.get(
            "http://172.19.0.1:8080/size",
            json={
                "consumer_id": f"{cons_id}",
                "topic": f"test_topic_r{k}",
                "partition_number": part_id
            },
        )
        size_before = response.json()["size"]
        if(size_before > 0):
            response = requests.get(
                "http://172.19.0.1:8080/consumer/consume",
                json={
                    "consumer_id": f"{cons_id}",
                    "topic": f"test_topic_r{k}",
                    "message": f"{i} {cnt}",
                    "partition_number": part_id
                },
            )
            response = requests.get(
                "http://172.19.0.1:8080/size",
                json={
                    "consumer_id": f"{cons_id}",
                    "topic": f"test_topic_r{k}",
                    "partition_number": part_id
                },
            )
            assert response.json()["size"] == size_before - 1

        # if response.json()["status"] == "failure" : 
        print(response.json())

        # print("consumed - %s" % ({response.json()["message"]}))
    print(f"Consumer {i} done")


import threading

threads = []
for i in range(10):
    threads.append(threading.Thread(target=prod, args=(i,)))
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

print("sleeping...")
time.sleep(30)

threadsc = []
for i in range(10):
    threadsc.append(threading.Thread(target=cons, args=(i,consumer_ids[i])))
for thread in threadsc:
    thread.start()
for thread in threadsc:
    thread.join()