#________________________________________________________________________________________________________________________
# Insatll Some Required Files and Tools for TTK
FROM yashk7/tortoolkitbase
#________________________________________________________________________________________________________________________
# Install TTK Python Requirements.
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
#________________________________________________________________________________________________________________________
# Copy the requirements and The Files downloaded from docker and put them to root/current working directory.
COPY . .
#________________________________________________________________________________________________________________________
# QBT CONFIG STUFF.
RUN mkdir -p .config/qBittorrent
RUN cp qBittorrent.conf .config/qBittorrent/qBittorrent.conf
#________________________________________________________________________________________________________________________
# Setting 777 permissions to a file or directory means that it will be readable, writable and executable by all users.
RUN chmod 777 alive.sh
RUN chmod 777 start.sh
#________________________________________________________________________________________________________________________
# Add A Linux/Unix User account.
RUN useradd -ms /bin/bash  myuser
USER myuser
#________________________________________________________________________________________________________________________
# All done Now Set the starting command for TTK bot.
CMD ./start.sh
#________________________________________________________________________________________________________________________


## BUILDING TTK FROM DOCKER DONE.