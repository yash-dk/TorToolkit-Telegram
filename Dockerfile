FROM python:3.8.5-slim-buster

WORKDIR /torapp

RUN chmod -R 777 /torapp

RUN apt -qq update

ENV TZ Asia/Kolkata
ENV DEBIAN_FRONTEND noninteractive

RUN apt -qq install -y curl git wget \
    aria2 \
    ffmpeg mediainfo unzip p7zip-full p7zip-rar

#RUN curl https://rclone.org/install.sh | bash


RUN apt-get install -y software-properties-common
RUN apt-get -y update

RUN add-apt-repository -y ppa:qbittorrent-team/qbittorrent-stable
RUN apt install -y qbittorrent-nox

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod 777 alive.sh

# run as non root user inorder to bind to the heroku web port 
RUN useradd -ms /bin/bash  myuser
USER myuser

CMD ./start.sh
