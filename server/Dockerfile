FROM python:latest

ADD server.py /server/
ADD config.py /server/
ADD requirements.txt /server/

ENV PYTHONUNBUFFERED=1

WORKDIR /server/

RUN pip3 install -r requirements.txt
