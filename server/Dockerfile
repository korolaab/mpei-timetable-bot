FROM python:latest

ADD server.py /server/
ADD models.py /server/
ADD config.py /server/
ADD requirements.txt /server/

ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Moscow

WORKDIR /server/

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN pip3 install -r requirements.txt
