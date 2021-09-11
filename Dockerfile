FROM yashk7/tortoolkitbase

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p .config/qBittorrent
RUN cp qBittorrent.conf .config/qBittorrent/qBittorrent.conf

RUN chmod 777 alive.sh
RUN chmod 777 start.sh

#RUN useradd -ms /bin/bash  myuser
#USER myuser

CMD ./start.sh
