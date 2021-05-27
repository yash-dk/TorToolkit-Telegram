FROM ubuntu:20.04

WORKDIR /torapp

RUN chmod -R 777 /torapp

RUN apt -qq update

ENV TZ Asia/Kolkata
ENV DEBIAN_FRONTEND noninteractive

RUN apt -qq install -y curl git wget \
    python3 python3-pip \
    aria2 \
    ffmpeg mediainfo unzip p7zip-full p7zip-rar \
    libcrypto++-dev libssl-dev libc-ares-dev libcurl4-openssl-dev \
    libsqlite3-dev libsodium-dev

RUN curl -L https://github.com/jaskaranSM/megasdkrest/releases/download/v0.1/megasdkrest -o /usr/local/bin/megasdkrest && \
    chmod +x /usr/local/bin/megasdkrest

RUN curl https://rclone.org/install.sh | bash


RUN apt-get install -y software-properties-common
RUN apt-get -y update

RUN add-apt-repository -y ppa:qbittorrent-team/qbittorrent-stable
RUN apt install -y qbittorrent-nox

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod 777 alive.sh
RUN chmod 777 start.sh

#RUN useradd -ms /bin/bash  myuser
#USER myuser

CMD ./start.sh
