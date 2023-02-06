# Get the bitnami spark image
FROM bitnami/spark:latest

# Deploy as root user
USER root
# Install Python libraries 
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
RUN python -m spacy download en_core_web_sm
RUN [ "python", "-c", "import nltk; nltk.download('wordnet')" ]