# from ast import main
from time import sleep
from json import dumps
from json import load
from kafka import KafkaProducer
import csv

# A producer class defiend to perform the functionalities of Kafka Producer
class Producer():
    # Initialize the producer with Kafka Producer using port
    def __init__(self):
        # super().__init__()
        self.producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            # value_serializer=lambda x: dumps(x).encode('utf-8')
        )
    # Function which gets the scrapped data in json and deploys it on the topic for consumer to receive
    def SendData(self):
        # with open('../../Data_Generator/jsons/2021/2021-11-20/Scrapped.json') as json_file:
        #     data = load(json_file)
        #     self.producer.send('topic_test1', value=data)
        #     sleep(1)
        #     # print(type(data))
        #     # print(data)
        #     # print(data["Header"])
        topic_name = 'topic_test1'
        file_path = 'islamabad.csv'

        # Open the file and read the contents
        with open(file_path, newline='') as file:
            reader = csv.reader(file)
            # Converting the file as list of lists
            # We're also encoding the CSV data as UTF-8 strings to ensure that non-ASCII characters are handled properly.
            file_content = '\n'.join([','.join(row) for row in reader]).encode('utf-8')

        # Send the file as a message to the Kafka topic
        print(file_content)
        self.producer.send(topic_name, file_content)
# Main function which creates the producer object and calss the function to send data
def main():
    prod_obj = Producer()
    prod_obj.SendData()

if __name__ == "__main__":
    main()