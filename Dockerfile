FROM ubuntu:18.04

WORKDIR /torapp

RUN apt -qq update

ENV TZ Asia/Kolkata
ENV DEBIAN_FRONTEND noninteractive

RUN apt -qq install -y curl git gnupg2 wget \
    apt-transport-https \
    python3.8 python3-pip \
    coreutils aria2 jq pv \
    ffmpeg mediainfo unzip redis-server

RUN curl https://rclone.org/install.sh | bash

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

CMD ./alive.sh & gunicorn tortoolkit:start_server --bind 0.0.0.0:$PORT --worker-class aiohttp.GunicornWebWorker & python3 -m tortoolkit
