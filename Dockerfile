# Get the bitnami spark image
FROM bitnami/spark:latest
USER root
# Install Python libraries 
COPY requirements.txt requirements.txt
ARG src="Distributed Parser/Alldata_refined.csv" 
COPY ${src} /opt/bitnami/spark/alldata_refined.csv 
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm
RUN [ "python", "-c", "import nltk; nltk.download('wordnet')" ]
RUN apt update -y
