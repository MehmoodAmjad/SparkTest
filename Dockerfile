# Get the bitnami spark image
FROM bitnami/spark:latest

# Deploy as root user
USER root
# Install Python libraries 
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
RUN python -m spacy download en_core_web_sm
RUN [ "python", "-c", "import nltk; nltk.download('wordnet')" ]
RUN apt update -y
RUN apt install maven -y
# RUN [ "python", "-c", "import importlib; import pathlib; print(pathlib.Path(importlib.util.find_spec('sutime').origin).parent / 'pom.xml')" ]
RUN mvn dependency:copy-dependencies -DoutputDirectory=./jars -f $(python -c 'import importlib; import pathlib; print(pathlib.Path(importlib.util.find_spec("sutime").origin).parent / "pom.xml")')
