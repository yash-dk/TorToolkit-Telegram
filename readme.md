# TorToolkit Telegram
So basically Tortoolkit is aimed to be most versatile torrent leecher and Youtube-DL bot for telegram. This bot is highly customizeable and to customize this bot you dont need to restart the bot everytime. 
The bot gets started with minimum variables and others can be set as and when needed using the /settings

[![Deploy](https://telegra.ph/file/e7d224c45cf1d106a28fa.png)](https://telegra.ph/Heroku-TorToolkit-01-18)

According to me this platform provides resources which are enough for a genuine user and by default prevents Abuse:
Click to see video guide to see how to deploy. Web is not yet available but soon will be available on zeet.

[![Deploy](https://telegra.ph/file/a81a05cc874e8636ddb86.png)](https://youtu.be/WWi9JWDzXSw)


### Working Demo Group:- [Group Link](https://t.me/TorToolKit) 

#### As This is a first release of this project the installation is a bit lengthy but takes less than 10 mins.
#### ~~In subsequent releases i will try to make one click install~~
### For Heroku users New repo will come soon (This repo will not work on heroku)

## Installing
ExecVarsSample.py location:- tortoolkit / consts / ExecVarsSample.py

### Docker (Simplest)
You should install docker first :- [How to Install Docker](https://docs.docker.com/engine/install/)

Clone the repo and edit ExecVarsSample.py while editing `Change the API_HASH, API_ID, BOT_TOKEN, ALD_USR and BASE_URL_OF_BOT` and `Uncomment the below DB_URI and comment out the above DB_URI`.

After that execute these commands in root of the repo where tortoolkit folder is located.

    apt install docker-compose
    docker-compose up

If you edit a file like ExecVarsSample.py just run below commands

    docker-compose build web tortk
    docker-compose up

### [Demo video for direct clone and run](https://youtu.be/HYjG4-VfxXs)
### Direct Clone and Run
Run the following commands. (Following commands can be used to setup the vps from scratch)
   
    git clone https://github.com/yash-dk/TorToolkit-Telegram.git
    sudo apt update
    sudo apt install -y python3.8
    sudo apt install -y python3-venv
    python3 -m venv venv
    source venv/bin/activate
    cd TorToolkit-Telegram
    pip install -r requirements.txt
	sudo apt install -y postgresql postgresql-contrib
	apt -qq install -y curl git wget python3 python3-pip aria2 ffmpeg mediainfo unzip p7zip-full p7zip-rar
	curl https://rclone.org/install.sh | bash
	apt-get install -y software-properties-common
	apt-get -y update
	add-apt-repository -y ppa:qbittorrent-team/qbittorrent-stable
	apt install -y qbittorrent-nox

After that setup the database:-
Remember the 'your-pass' that you enter below

    sudo -u postgres bash
    createdb tortk
    psql
    ALTER USER postgres with password 'your-pass';
    exit
    exit
After that setup the Variables.
	Assuming that you are in the dir where you clonned the repo
	   
     cd TorToolkit-Telegram/tortoolkit/consts
	 nano ExecVarsSample.py

Change the API_HASH, API_ID, BOT_TOKEN, ALD_USR and BASE_URL_OF_BOT
Change DB_URI = "dbname=tortk user=postgres password=your-pass host=127.0.0.1 port=5432"
enter the password in the above string
After that run (You can use any port for the web interface here i am using 80)
Each time before starting the bot export the port Number

    export PORT=80

And finally run ./start.sh in clonned folder.

    chmod 777 start.sh
    ./start.sh

## Variables
`IS_VPS` = False
#### Compulsory Vars

`API_HASH` = Obtained from Telegram 

`API_ID` = Obtained from Telegram

`BOT_TOKEN` = Obtained from Botfather

`BASE_URL_OF_BOT` = Ip/domain of your bot like "http://myip/"

`ALD_USR` = It is a list of IDs of all the allowed groups and useres who can use this bot in private.

`DB_URI` = Postgres database URL.
#### Optional Vars
(IT IS RECOMMENDED TO SET THE OPTIONAL VARS FROM SETTINGS MENU, If not all vars atleast use settings menu for RCLONE that way is much easier.)

`EDIT_SLEEP_SECS` = Seconds to Sleep before edits. Recommended is 40.

`TG_UP_LIMIT` = Telegram Upload limit in bytes.

`FORCE_DOCUMENTS` = Should all the upload to telegram be made as documents or not.

`COMPLETED_STR` = Character used to denote completed progress. 

`REMAINING_STR` = Character used to denote remaining progress.

`RCLONE_BASE_DIR` = Rclone Base Directory to where stuff should be clonned. (cannot be configured from settings)

`LEECH_ENABLED` = Upload to telegram should be enabled or not.

`RCLONE_ENABLED` = Upload to rclone should be enabled or not.

`DEFAULT_TIMEOUT` = Default destination to choose if the user fails to choose upload destination in 60 seconds.

`RCLONE_CONFIG` = Rclone file path.

`DEF_RCLONE_DRIVE` = Default Rclone drive from the config file.

`MAX_YTPLAYLIST_SIZE` = Max size of a playlist that is allowed (Number of videos)

`MAX_TORRENT_SIZE` = Max torrent size in GBs

Rest Variables are not to changes 
## Commands

    leech - To Leech a torrent or download a direct link
    ytdl - Donwload YouTube Video
    pytdl - Download YouTube Playlist
    about - About the bot
    status - Status of all the downloads
    server - Get server status
    usettings - User Settings
    settings - Settings of the bot ⚠️ Admin Only
    pauseall - Pause all torrents⚠️ Admin Only
    resumeall - Resume all torrents⚠️ Admin Only
    purge - Delete all torrents ⚠️ Admin Only
    getlogs - Get the robot logs ⚠️ Admin Only

# Credits
[Yash-DK](https://github.com/yash-dk)
[Lonami](https://github.com/LonamiWebs/Telethon/) for awesome Telethon
[All the Libraries owner](https://github.com/yash-dk/TorToolkit-Telegram/blob/master/requirements.txt)

# REST README WILL BE COMPLETED SHORTLY
