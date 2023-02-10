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
    k = 69 # vary for different topic name
    response = requests.post(
        "http://172.19.0.1:8080/topics", json={"name": f"test_topic_r{k}","number_of_partitions":5}
    )
    if response.status_code != 200:
        print(response.json()["message"])
    else : 
        print(f"producer {i} created topic")
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



import threading

threads = []
for i in range(10):
    threads.append(threading.Thread(target=prod, args=(i,)))
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()