# unibotimetablesbot


A Telegram bot for Unibo lessons timetables in Bologna.



## Getting started

* Install dependencies.
```
sudo apt install python3-setuptools
sudo apt install python3-pip
sudo apt install python3-venv
```
or
```
sudo pacman -S python-setuptools 
sudo pacman -S python-pip
sudo pacman -S python-virtualenv
```



## Deploy as systemd service


* Create a new user and add it to sudoers. Then switch to new user and navigate to its home directory.

```
sudo adduser unibotimetablesuser
sudo adduser unibotimetablesuser sudo
su unibotimetablesuser
cd
```

* Clone repository.
```
git clone https://github.com/luca-ant/unibotimetablesbot.git
cd unibotimetablesbot
```
or
```
git clone git@github.com:luca-ant/unibotimetablesbot.git
cd unibotimetablesbot
```

* Run service.sh with *install* argument.
```
chmod u+x service.sh
./service.sh install
```

* Check manually the file */etc/systemd/system/unibotimetablesbot.service*. Put the bot token where you see "YOUR_TOKEN_HERE".

* Start the service
```
sudo systemctl enable unibotimetablesbot.service
sudo systemctl start unibotimetablesbot.service

```

## Run manually

* Clone repository.
```
git clone https://github.com/luca-ant/unibotimetablesbot.git
```
or
```
git clone git@github.com:luca-ant/unibotimetablesbot.git
```


* Create a virtual environment and install requirements modules.
```
cd unibotimetablesbot
python3 -m venv venv
source venv/bin/activate

python3 -m pip install -r requirements.txt
```

* Set UNI_BOT_TOKEN environment variable with bot's token.

```
export UNI_BOT_TOKEN=YOUR_TOKEN_HERE
```
* Run the python script as:

```
python unibotimetablesbot/unibotimetablesbot.py
```

## Credits
* unibotimetablesbot was developed by Luca Antognetti
* Data provided by [UNIBO OpenData](https://dati.unibo.it/it/dataset)


**An instance of bot it's now running!** You can find it on Telegram searching `@unibotimetablesbot`
