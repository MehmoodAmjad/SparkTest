'''
This file is the main part of our system where the parser imports modules from other files.
It also contains the driver class that runs our information extraction module.
Spark uses this file to distribute workload over its workers
'''
# Importing modules for Temporal extraction 
from nltk.stem.wordnet import WordNetLemmatizer
import spacy
from fuzzywuzzy import fuzz
import re
import pandas as pd
import glob
import pathlib
import json
# from sutime import SUTime
from datetime import datetime
import datefinder
import numpy as np
import csv
import os
from pyspark.sql import *
from pyspark import *
# from timetag import TimeTag

'''
Timetag is a tag that is extracted from the NEWS documents. 
Each timetag contains the weight and the values of the tag itself.
'''

#The class for the timetag object
class TimeTag:
    def __init__(self, date, textType, appearence, count):
        # The date or the value of the tag itself
        self.date = date
        # The texttype which would be either the header, summary or details. Weight is based on this.
        self.textType = textType
        # Appearence is the position of the number of bytes from the start of the article where the tag first appears
        self.appearence = appearence
        # Count is the number of unique times the tag appears in the article
        self.count = count
        # The weight assigned to each tag. Weight specifies how much of a good focus time it is. The higher the weight, the better.
        self.weight = 0.0
        self.calculateWeight()

    # Function to calculate the weight of each tag, weights are multipled by the count of the tag and the inverted appeareance of the tag.
    # Inverted appearence means the sooner the tag appeared, the higher its value.
    def calculateWeight(self):
        # If tag was in the header, assign highest weight of 10
        if self.textType == "Header":
            self.weight = 10 * (1/self.appearence) * self.count
        # If tag was in the Summary, assign the weight of 5
        elif self.textType == "Summary":
            self.weight = 5 * (1/self.appearence) * self.count
        # If tag was in the Summary, assign the weight of 2
        elif self.textType == "Details":
            self.weight = 2 * (1/self.appearence) * self.count
    # To print the tag for logging purposes
    def __repr__(self):
        print({"date": self.date, "weight": self.weight, "count": self.count, "type": self.textType})



nlp = spacy.load('en_core_web_sm', disable=['ner', 'textcat'])

# Main parser class that handles all the information extraction
class parser():
    def __init__(self):
        self.index = {}

    # Function to clean the string
    def clean(self, doc):
        # Convert all alphabets to lower case
        doc = doc.lower()
        # Loading string in to nlp model 
        doc = nlp(doc)
        # Tokenizing the string

        tokens = [tokens.lower_ for tokens in doc]
        # Removing all stopping words from the string
        tokens = [tokens for tokens in doc if (tokens.is_stop == False)]
        # Removing all punctuation from the string
        tokens = [tokens for tokens in tokens if (tokens.is_punct == False)]
        # Changing all verbs to its base form (changing - > change , changed -> change etc)
        try:
            final_token = [WordNetLemmatizer().lemmatize(token.text)
                       for token in tokens]
        except:
            # If modules are not loaded properly 
            import nltk
            nltk.download('wordnet')
            nltk.download('omw-1.4')
            final_token = [WordNetLemmatizer().lemmatize(token.text)
                       for token in tokens]
        
        # Returning back the final string 
        return " ".join(final_token)

    
    # Converting string into sentences 
    def sentences(self, text):
        # split sentences and questions
        text = re.split('[.?]', text)
        clean_sent = []
        for sent in text:
            clean_sent.append(sent)
        return clean_sent

    # Load cities from data set provided by ECP Election commission of Pakistan
    def load_cities(self, file):
        # Loading dataset
        df = pd.read_csv(file)
        # Droping NULL rows
        df = df.dropna()
        # Extracting location col
        df = df["Locations"]
        # Converting Data frame to sorted list in lower case
        Data_of_region = df.values.tolist()
        Data_of_region = [each_city.lower() for each_city in Data_of_region]
        Data_of_region = list(dict.fromkeys(sorted(Data_of_region)))
        # Storing indexes of each alphabet starting index
        index = dict()
        # Helping variables to store indexes
        flag = False
        push = False
        current_alphabet = ""
        start = 0
        finish = 0
        # Creating index hash
        for i in range(len(Data_of_region)):
            if i != 0 and Data_of_region[i][0] != Data_of_region[i][0]:
                flag = True
                push = True
                finish = i-1
            if push == True:
                index[current_alphabet] = finish
            if flag == False:
                start = i
                current_alphabet = Data_of_region[i][0]
                index.__setitem__(current_alphabet, start)
        self.index = index
        self.Data_of_region = Data_of_region

    def createTags(self, tags):
        tagValues = []
        newTags = []
        for tag in tags:
            try: 
                tagValues.append(list(datefinder.find_dates(tag["value"]))[0])
                newTags.append(tag)
            except:
                pass
        tagValues, indices, counts = np.unique(tagValues, return_index=True, return_counts=True)
        newTags = [newTags[index] for index in indices]
        newtags = []
        for i in range(len(newTags)):
            newtags.append(TimeTag(tagValues[i], newTags[i]["textType"], newTags[i]["start"], counts[i]))
        return newtags

    # Function adds another element to the Timetags with the text type i.e header, summary or detail
    def addTextType(self, tags, textType):
        for tag in tags:
            tag["textType"] = textType
        return tags

    # FGet location from the extracted news 
    def Get_location(self, read_more, header):
        if len(self.index) <= 0:
            # Loading data set of ECP Election commission of Pakistan
            # file_path = os.getcwd() + "/alldata_refined.csv" 
            file_path = '/opt/bitnami/spark/alldata_refined.csv' 
            self.load_cities(file_path)
        # Clean header of news
        header = self.clean(header)
        # Split header
        header = header.split()
        # Generate sentences from the article  
        text = self.sentences(self.clean(read_more))
        # Dictionary to store the City counts from news
        cities = dict()
        for i in text:
            # For each sentence in the article load it in nlp model
            doc = nlp(i)
            # A skipper variable  
            jump = 0
            # Foe each word in the sentence 
            for token in range(len(doc)):
                try:
                    # If the word is already explored skip the iteration
                    if token < jump:
                        continue
                    jump = 0
                    # Check if the extracted word is a proper noun
                    if doc[token].pos_ == "PROPN":
                        flag = False
                        # Extracting the start and end index where the first alphabet of proper noun matches with the the location loaded
                        # From ECP data
                        end = self.index[doc[token].text.lower()[0]]
                        if end == self.index['a']:
                            start = 0
                        else:
                            start = chr(ord(doc[token].text.lower()[0])-1)
                            # print(self.index, start)
                            start = self.index[start]
                            start += 1
                        area_count = 0
                        previous = ""
                        # Check only those entries which first alphabet matches with the first alphabet of proper noun
                        for areas in range(start, end):
                            words = self.Data_of_region[areas].split()
                            subtoken = token
                            checker = []
                            # Check the match (not exact matching of the noun and the location)
                            if fuzz.ratio(doc[subtoken].text.lower(),words[0])>=95:
                                checker.append(words[0])
                                for iterator in range(len(words)-1):
                                    # If first token matches extract more data from sentence and compare it for full name of the location
                                    if subtoken + (iterator + 1 ) < len(doc):
                                        if fuzz.ratio(doc[subtoken + iterator+1 ].text.lower(),words[iterator+1])>=70:
                                            checker.append(words[iterator+1])
                                city = ' '.join(checker)
                                # If noun and the location matches (turn on the match flag)
                                if len(previous) < len(city): 
                                    area_count = len(checker)
                                    flag = True
                                    previous = city
                                else:
                                    city = previous
                        # Check if the extracted location has any match with the header
                        if flag:
                            match = False
                            word1 = ""
                            word2 = ""
                            if token != 0:
                                word1 = doc[token-1].text.lower()
                            # Storing the number of extra read we did from the text
                            # Thus we can skip those token in the next iteration 
                            jump = token + area_count
                            if jump + 1 < len(doc):
                                word2 = doc[jump+1].text.lower()
                            if word1 in header or word2 in header:
                                match = True
                            # If the sentence in which the location is found has any co relation with the header increase its weight 
                            if city in cities:
                                if match:
                                    cities[city] += 3
                                else:
                                    cities[city] += 1
                            else:
                                if match:
                                    cities.__setitem__(city, 3)
                                else:
                                    cities.__setitem__(city, 1)
                except:
                    continue
        # Extract the maximum count which will represent the focused locaiton of the news
        self.city = max(cities, key=cities.get, default="null")
        if self.city == 0:
            print(cities)
        # file_path = os.getcwd() + "/alldata_refined.csv"
        file_path = '/opt/bitnami/spark/alldata_refined.csv'
        df = pd.read_csv(file_path)
        # Droping NULL rows
        df = df.dropna()
        # Extracting location col
        # Only keeping locations that are actually present in our database
        df["Locations"] = df["Locations"].apply(lambda x: x.upper())
        # Check if the extracted location is present in our database
        if df[df["Locations"] == self.city.upper()].empty:
            if self.city != "null":
                flag = False
                cityList = sorted(((v,k) for k,v in cities.items()), reverse=True)
                for city in cityList:
                    if df[df["Locations"] == city[1].upper()].empty == False:
                        self.city = city[1]
                        flag = True
                        break
            
            if flag == False: 
                self.city = "null"
        self.cities = cities

    # Our main focus time extraction function. Takes in a dataframe of news article and returns the focus location in a dictionary
    def Get_Time(self, data, timeData):
        tags = []
        # Parse the header, summary and details individually
        headerParse = sutime.parse(data[1], reference_date=data[6])
        headerParse = self.addTextType(headerParse, "Header")
        
        summaryParse = sutime.parse(data[2], reference_date=data[6])
        summaryParse = self.addTextType(summaryParse, "Summary")
        #  Remove the publication date from the details so as to not interfere with our algorithm
        details = data[3]
        lines = details.split('\n')
        del lines[-2]
        details = '\n'.join(lines)
        detailsParse = sutime.parse(details, reference_date=data[6])
        detailsParse = self.addTextType(detailsParse, "Details")
        # Creat tags of all the elements and combine into one
        
        tags = headerParse + summaryParse + detailsParse
        try:
            # Assign weights to tags

            tags = self.createTags(tags)
            tags = sorted(tags, key=lambda x: x.weight, reverse=True)
            # Use the highest weighted tag as focusTime
            timeData["focusTime"] = tags[0].date.date().strftime('%Y-%m-%d')
        except:
            # If no tags found, assign creation date as focusTime
            timeData["focusTime"] = data[6]
        
        # Create the rest of the dictionary using the text and tags of each
        timeData["CreationDate"] = data[6]
        
        timeData["Header"] = dict()
        timeData["Header"]["Text"] = data[1]
        timeData["Header"]["Tags"] = headerParse
        
        timeData['Summary'] = dict()
        timeData['Summary']["Text"] = data[2]
        timeData['Summary']["Tags"] = summaryParse
        
        timeData['Details'] = dict()
        timeData['Details']["Text"] = details
        timeData['Details']["Tags"] = detailsParse

        timeData['Link'] = data[4]
        timeData['Category'] = data[5]
        return timeData

    # Main function which executes the get location to extract focus location
    def read(self, dataFrame):
        self.Get_location(dataFrame["Detail"], dataFrame["Header"])
        return self.city

    # The function which is applied on every element of the RDD in pySpark
    def informationExtractor(self, dataframe):
            results = dict()
            city = self.read(dataframe)
            results["focusLocation"] = city
            print("The Results from the parser:")
            print(results)
            return city


def main():
    # Instantiate parser object
    Parser = parser()
    # Find spark library to automatically find and start the Spark instance that is installed on the system, 
    # without having to manually specify the path to the Spark home directory
    # Create the spark session to connect to the Spark runtime
    spark = SparkSession.builder.appName("NAaaS").getOrCreate()
    filename = r'islamabad.csv'
    # Read our file which holds the NEWS
    df = pd.read_csv(filename, index_col=None, header=0, dtype="string")
    # Convert dataframe to RDD
    rows = df.to_dict('records')

    rdd = spark.sparkContext.parallelize(rows)
    # Run the information extractor function on each element of RDD
    result = rdd.map(Parser.informationExtractor)
    # Print final result
    print(result.collect())

    spark.stop()

main()
