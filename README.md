# Connectify : DS-Assignment-2

## Setup 
--> Rajat

## Design
We implement a multi-broker distributed queue system which serves write and read requests from `producers` and `consumers` via a __client side library__. The queue manages `topics`, to which producers and consumers subscribe to. Upon a successful subscription, producers write logs to the queue which the registered consumers can read. All consumers have their own offset which maintains how many logs they have read from a given topic. In order to make our distributed queue scalable, each topic is broken into various`partitions`. These partitions are distributed accross various containers called `brokers`, each broker can have zero to many partitions of a given topic. The implementation of our design is discussed further in the following sections.

### Project Structure
The project consists of various components that interact with each other to serve a request initiated via the client side library. They are listed as follows : 

##### Write Manager/ Primary Manager 
- __Function__ : The primary manager handles all requests involving __adding new or additional data__ to the queue. It also keeps track of the metadata required to validate such requests. Redirection of requests to the appropriate broker depending on the partition number of the topic (or in a *round robin fashion*) is also performed here.  Whenever required, it __relays__ appropriate information to the read-only managers. It ensures the consistency of the metadata in times of failure through __Write Ahead Logging__. It also implements a __health check protocol__ to maintain the validity of brokers as well as clients. Any functions involving adding or removing of brokers are also performed via the primary manager. 
- **Associated Databases :** It updates and reads from the  Primary Database for keeping track of and updating the the metadata of the queue.
- **Requests Handled :** 
    - `POST` on `/topics`
    - `POST` on `/producer/register`
    - `POST` on `/consumer/register`
    - `POST` on `/producer/produce`
- **Code Structure :**
    - __src__ - the directory containing the primary application with the in-memory datastructures, models and API support
    - __datastructures__ - implementations for the various thread-safe datastructures used in the primary manager. For more details, check this [README](primary_manager/src/datastructures/README.md)
    - __models__ - implementations for various concepts of the queue such as  `Topic`, and `Data_Manager` abstracted using classes. For more details, check this [README](primary_manager/src/models/README.md)
    - __views.py__ - the file containing the HTTP API endpoints for interacting with the primary manager.
    - __json_validator.py__ - the file containing the validator for validating the request JSON body based on the provided schema
    - __db_models__ - the directory containing the database models for programmatically interacting with the database using `SQLAlchemy`

##### Read-Ony Managers 
- **Function** : The read-only managers serve requests concerned with __reading data__ from the queue. They also locally maintain any metadata required to validate such requests such as validating consumer ids. The integrity of this metadata is maintained via communication with the primary manager.
- **Associated Databases :** It reads from the Primary Database only upon startup, and never further interacts with it.
- **Requests Handled :**
    - `GET` on `/topics`
    - `GET` on `/consumer/consume`
    - `GET` on `/size`
    - `POST` on `/sync/topics`
    - `POST` on `/sync/consumer/register`
- **Code Structure :**
    - __src__ - the directory containing the primary application with the in-memory datastructures, models and API support
    - __datastructures__ - implementations for the various thread-safe datastructures used in the read-only manager. For more details, check this [README](readonly_manager/src/datastructures/README.md)
    - __models__ - implementations for various concepts of the queue such as  `Topic`,  `Readonly_Manager` and `Broker` abstracted using classes. For more details, check this [README](readonly_manager/src/models/README.md)
    - __views.py__ - the file containing the HTTP API endpoints for interacting with the read-only manager.
    - __json_validator.py__ - the file containing the validator for validating the request JSON body based on the provided schema
    - __db_models__ - the directory containing the database models for programmatically interacting with the database using `SQLAlchemy`

##### Brokers :
- **Function:** The brokers serve as the entity which interact with the queue data for writes as well as reads. Each broker handles zero to many partitions of a topic and any read/write request made to any of its partitions is forwarded to the broker after validity checks are performed at a higher level. The broker then simply performs the update or returns the data requested from it. 
- **Associated Databases :** Each broker has its corresponding Master Database which handles all the queue data of the various partitions present in it, along with some broker specific metadata such as offsets of various consumers for read requests. It does not handle requests concerning metadata updates or reads such as registering a producer or `GET`ting the list of topics.
- **Requests Handled :**
    - `GET` on `/consumer/consume`
    - `GET` on `/size`
    - `POST` on `/topics`
    - `POST` on `/producer/produce`
- **Code Structure :**
    - __src__ - the directory containing the primary application with the in-memory datastructures, models and API support
    - __datastructures__ - implementations for the various thread-safe datastructures used in the broker. For more details, check this [README](broker/src/datastructures/README.md)
    - __models__ - implementations for various concepts of the queue such as  `Topic`,  `Master_Queue` and `Log` abstracted using classes. For more details, check this [README](broker/src/models/README.md)
    - __views.py__ - the file containing the HTTP API endpoints for interacting with the broker.
    - __json_validator.py__ - the file containing the validator for validating the request JSON body based on the provided schema
    - __db_models__ - the directory containing the database models for programmatically interacting with the database using `SQLAlchemy`

##### Load Balancer and Reverse Proxy 

We use `nginx` as a top level load balancer and a reverse proxy. All requests are directed to the nginx container which in turn redirects them appropriately within the docker network we have created. It serves the following purposes : 
- Redirection of appropriate requests to the singular primary manager.
- Redirection of appropriate requests to one of the multiple read-only managers in a round robin manner. 
- Act as a reverse proxy for the read only managers. Since the read-only managers are created as replicas in the docker network, their IP Addresses are dynamically created everytime they are instantiated and are not visible to us. To be able to redirect requests to these dynamically generated IP-Addresses, nginx provides a reverse proxy from the server name of the read only managers (which is fixed at every instantiation) to their IPs. 

##### Master Slave Architecture

--> Nisarg


### Database Schemas

The various databases used and their schemas are discussed as follows. 

##### Primary Database
This database is used to store all the __metadata__ associated with our distributed and partitioned queue. It does not store any actual data contained in the queue. The database schema is as follows: 

###### Table `topic` - contains the names and partition indices of the topics present in this portion of the queue. 
- `name` - the primary key of the table, also the name of the topic. 
- `partitions` - the number of partitions of the topic.

###### Table `partitions` - contains the producer ids and the topics they have subscribed to
- `ind` - the index of this partition, along with `topic_name` is a unique identifier to a partition of a topic.
- `topic_name` - the name of the topic ,  along with `ind` is a unique identifier to a partition of a topic.
- `broker_host` - the service name of the broker this partition is present in.

###### Table `producers` - contains the producer ids and the topics they have subscribed to
- `id` - the primary key of the table, id of the producer
- `topic_name` - the name of the topic the producer has subscribed to

###### Table `consumers` - contains the consumer ids and the topics they have subscribed to
- `id` - the primary key of the table, id of the consumer
- `topic_name` - the name of the topic the consumer has subscribed to

###### Table `brokers` - contains the broker service names and their availability status
- `name` - the primary key of the table, service name of the broker
- `status` - stores whether the broker is alive or not

##### Master Database(s)
These databases store the __actual queue data__ and the associated metadata required for the handling of this data. It does not store unnecessary queue metadata. Each master database has an associated broker. The database schema is as follows: 

###### Table `topic` - contains the names and partition indices of the topics present in this portion of the queue.
- `name` - The name of the topic. 
- `partition_index` - the partition number of this topic. `name` and `partition_index` to`GET`her form a primary key which uniquely identifies a unqiue partition present within this broker.

###### Table `log` - contains the logs present in this portion of the queue
- `id` - the primary key of the table, also the unique identifier of the log along with the `topic_name`
- `topic_name` - the [foreign key](#table-topic---contains-the-names-of-the-topics-in-the-queue) to the `topic` table, the topic to which the log belongs, also the unique identifier of the log along with the `id` and  `partition_index`.
- `partition_index` -  the [foreign key](#table-topic---contains-the-names-of-the-topics-in-the-queue) to the `topic` table, the partition index of the topic to which the log belongs, also the unique identifier of the log along with the `id` ans `topic_name`
- `producer_id` - the [foreign key](#table-producer---contains-the-details-of-the-producers) to the `producer` table, the id of the producer who produced the log
- `message` - the message of the log
- `timestamp` - the timestamp of the log

###### Table `consumer` - contains the partition offsets of the consumers consuming any partition in this portion of the queue
- `id` - the primary key of the table, also the unique identifier of the consumer along with `topic_name` and `partition_index`
- `topic_name` - the [foreign key](#table-topic---contains-the-names-of-the-topics-in-the-queue) to the `topic` table, the topic to which the consumer belongs.  Also the unique identifier of the consumer along with `id` and `partition_index`
- `partition_index ` - the [foreign key](#table-topic---contains-the-names-of-the-topics-in-the-queue) to the `topic` table, the partition index of the topic to which the consumer belongs
- `offset` - the offset of the consumer for the given partition. Also the unique identifier of the consumer along with `topic_name` and `id`.

### Endpoints

The overall structure of our design looks as follows : 

<a href="https://ibb.co/4R4WH18"><img src="https://i.ibb.co/PG1xdDc/overall.png" alt="overall" border="0"></a>


##### Client Side Endpoints

These endpoints are for the calls made via our client side library.

- __GET on /topics__ : returns the list of topics. 
    - Contact a read-only manager via round robin
    - The read-only manager returns the list of topics from local memory

<a href="https://ibb.co/X3fGz5H"><img src="https://i.ibb.co/MGyJR1d/topics-`GET`.png" alt="topics-`GET`" border="0"></a>

- __POST on /topics__ : A new topic is created
    - Contact the primary manager
    - Primary manager performs the necessary checks, returns any error found.
    - The primary database is updated with this new data
    - Information of the new topic is sent to all read-only managers 

<a href="https://ibb.co/q1WTrQf"><img src="https://i.ibb.co/w6w5zmX/topics-`POST`.png" alt="topics-`POST`" border="0"></a>

- __POST on /producer/register__:  Producer registers to a topic
    - Contact the primary manager
    - Primary manager performs the necessary checks, returns any error found.
    - If the topic does not exist, primary manager sends a create topic request to itself
    - The primary database is updated.

<a href="https://ibb.co/HPx7qS6"><img src="https://i.ibb.co/B6rLBpb/producer-register.png" alt="producer-register" border="0"></a>

- __POST on /consumer/register__:  Consumer registers to a topic
    - Contact the primary manager
    - Primary manager performs the necessary checks, returns any error found.
    - The primary database is updated
    - Information of the newly registered consumer is forwarded to all read-only manager

<a href="https://ibb.co/KmDYr8M"><img src="https://i.ibb.co/g6dGRc5/register-consumer.png" alt="register-consumer" border="0"></a>

- __POST on /producer/produce__: Producer produces a log to a topic
    - Contact the primary manager
    - Primary manager performs the necessary checks, returns any error found.
    - If the partition index is not provided, primary manager chooses one in a   round robin fashion
    - The primary manager chooses the appropriate broker having the desired partition and forwards the request to it
    - Updates are made to the master database via the broker.

<a href="https://ibb.co/SXZc91b"><img src="https://i.ibb.co/RpJNVMf/producer-produce.png" alt="producer-produce" border="0"></a>

- __GET on /consumer/consume__:  Consumer reads a log from a topic
    - One of the read-only managers is contacted in a round robin fashion.
    - Read-only manager performs the necessary checks, returns any error found.
    - If the partition index is not provided, read-only manager chooses one in a round robin fashion.
    - The broker is contacted to `GET` the log for a chosen partition.
    - The broker contacts the slave database for the log data, and updates the offset in the master database.

    __Additional functionality__  : If a parition index is not provided, we have to choose one ourselves, however it is possible that the next partition in the round-robin does not have any logs to consume, but some other partition of the topic does have remaining logs. Hence, if a partition is chosen via round robin, the read-only manager constantly contacts partitions in brokers in a round robin fashion till it finds a partition which has some logs to consume. It then returns a log from this partition. If all logs in that topic have been consumed, an appropriate message is returned.

<a href="https://ibb.co/qCwkyyC"><img src="https://i.ibb.co/ScpRssc/consumer-consume.png" alt="consumer-consume" border="0"></a>
    
- __GET on /size__ when partition index is provided : Returns the number of log messages left to consume on a given partition index of a topic
    - One of the read-only managers is contacted in a round robin fashion.
    - It contacts the appropriate broker having the desired partition.
    - Broker returns the remaining logs in this partition for this consumer

- __GET on /size__ when partition index is not provided : Returns the number of log messages left to consume on a each partition of a topic
    - One of the read-only managers is contacted in a round robin fashion.
    - It contacts all the  brokers having some partition of the desired topic.
    - Each broker returns a dictionary of {partition_index : size}.
    - The read-only manager aggregates the responses of all the brokers and returns a list.

<a href="https://ibb.co/F59dyDr"><img src="https://i.ibb.co/LxMscZF/size.png" alt="size" border="0"></a>

##### Administrative Endpoints

- __POST on /admin/broker/add__ : Add a new broker to the network.
    - Contact the primary manager
    - Update the primary database
    - Relay information to readonly managers for sync

- __POST on /admin/broker/remove__ : Remove a broker from the network.
    - Contact the primary manager
    - Update the primary database
    - Relay information to readonly managers for sync

- __POST on /admin/broker/activate__ : Activate an inactive broker in the network.
    - Contact the primary manager
    - Update the primary database
    - Relay information to readonly managers for sync

- __POST on /admin/broker/deactivate__ : Activate an inactive broker in the network.
    - Contact the primary manager
    - Update the primary database
    - Relay information to readonly managers for sync

##### Synchronisation Endpoints

These endpoints serve the purpose of synchronisation between the primary manager and the read only manager. These requests are sent from the former to the latter.

- __POST on /sync/topics__ : On a succeddful topic creation request, the primary manager sends the newly added topic to the read-only managers which update this information in their local memory.

- __POST on /sync/consumer/register__ : On a succeddful consumer register request, the primary manager sends the newly registered consumer id and topic to the read-only managers which update this information in their local memory.

- __POST on /sync/broker/add__ : On a successful broker addition, reflect in readonly managers's broker dicts

- __POST on /sync/broker/remove__ : On a successful broker removal reflect in readonly managers's broker dicts

- __POST on /sync/broker/activate__ : On a successful broker activation reflect in readonly managers's broker dicts

- __POST on /sync/broker/deactivate__ : On a successful broker deactivation reflect in readonly managers's broker dicts



##### Healthcheck Endpoints
--> Nisarg 



### Client Side Library
--> Rajat


## Optimisations 


## Testing

##### Unit Testing
Test all the individual API endpoints using the `requests` library. Checked both the success paths as well as the error paths.

##### Concurrency Testing 

###### Producers and Consumers Concurrency Checks
Test the thread-safety of the in-memory datastructures using the `threading` library. Created 10 producer threads and 10 consumer threads which would be interacting with the queue simultaneously. Checked that the consumer threads are able to consume the logs in the order they were produced by the producer threads. Topic name is specified by the parameter `<id>`. Ensured ordering by logging messages of the format `<producer_id> <log_id>`. While consuming the `<log_id>` should be in increasing order for each `<producer_id>`. The number of messages to be produced can be set by the `MESSAGES` parameter in the test file. Implemented in `tests/concurrency_test.py`.

###### Producer Concurrency Checks
Test the concurrent working of various producer associated endpoints such as register producer and produce. Implemented via running 10 producer threads which are interacting with the queue simultaneously. Topic name is specified by the parameter `<id>`. Ensured ordering by logging messages of the format `<producer_id> <log_id>`. While consuming the `<log_id>` should be in increasing order for each `<producer_id>`. The number of messages to be produced can be set by the `MESSAGES` parameter in the test files . Implemented in `tests/producer_concurrency_tests.py`.

###### Consumer Concurrency Checks
Test the concurrent working of various consumer associated endpoints such as register consumer and size. Implemented via running 10 producer threads which are interacting with the queue simultaneously. Topic name is specified by the parameter `<id>`. Ensured by asserting success of the required operations.  Implemented in `tests/consumer_concurrency_tests.py`.

##### Recovery Testing
Test the recovery of the queue from a crash. Start a producer and a consumer. Kill the application. Start the application again. Check that the producer and consumer are able to interact with the queue as before. The producer should be able to produce logs and the consumer should be able to consume logs as long as the limit is not reached. Limit can be set by the `MESSAGES` parameter in the respective test files. This also tests the working of the producer and consumer in our client library as we it for creating the producer and consumer.

##### Client Side Library Testing
--> Nisarg as done in assign1 
##### Performance Testing
--> Nisarg as done in assign1