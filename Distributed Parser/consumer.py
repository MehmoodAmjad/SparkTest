from kafka import KafkaConsumer
from json import loads
import os
# # Receives from producer after every 2 seconds
# consumer.poll(timeout_ms=2000)

# A consumer class defined to perform the functionalities of Kafka Cosumer
class Consumer():
    # Initialize the comsumer with the kafka consumer port and topic
    def __init__(self):
        self.consumer = KafkaConsumer(
            'topic_test1',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='my-group-id',
            value_deserializer=lambda x: loads(x.decode('utf-8'))
        )
    # Function to display the data received by the consumer
    def Receive(self):
        for message in consumer:
            # Get the message value (which is the file content)
            file_content = message.value

            # Parse the CSV data
            rows = file_content.decode('utf-8').split('\n')
            data = [row.split(',') for row in rows]

            # Save the CSV data to a local file
            with open('received_file.csv', 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(data)
        # for msg in self.consumer:
        #     os.system("sudo docker exec sparktest-spark-master-1 spark-submit --master spark://172.18.0.2:7077 parser.py")
# Main function which creates the consumer and calls the receive function
def main():
    cons_obj = Consumer()
    cons_obj.Receive()

if __name__ == "__main__":
    main()
