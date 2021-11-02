# Dockerfile to build Python3.7 + Qt5
FROM python:3.7

RUN apt-get update && apt-get clean

RUN apt-get install -y python-serial \
	python-qt4 \	
	libgl1-mesa-dev && \	
	apt-get clean 

RUN rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash pyuser
WORKDIR /home/pyuser

COPY . .

RUN pip install -r requirements.txt

CMD [ "python", "demo.py"]