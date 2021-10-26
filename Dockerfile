FROM ubuntu:18.04

RUN apt-get update \
    && apt-get install software-properties-common -y \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get install python3.9 -y \
    && apt-get install python3-pip -y \
    && apt-get install python3.9-distutils -y \
    && apt install libmagickwand-dev -y

RUN python3.9 -m pip install --upgrade setuptools pip distlib

WORKDIR /image-processor

COPY requirements.txt .

RUN python3.9 -m pip install -r requirements.txt

COPY . .

ENTRYPOINT ["sh", "-c", "python3.9 main.py"]