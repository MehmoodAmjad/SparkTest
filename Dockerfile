# Get the bitnami spark image
FROM bitnami/spark:latest

# Install Python libraries 
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm
RUN [ "python", "-c", "import nltk; nltk.download('wordnet')" ]
RUN apt update -y
COPY /opt/bitnami/spark/alldata_refined.csv "Distributed Parser/Alldata_refined.csv"
