# unibotimetablesbot


A Telegram bot for Unibo lessons timetables in Bologna.

## Getting started

* Clone repository
```
git clone https://github.com/luca-ant/unibotimetablesbot.git
```
or
```
git clone git@github.com:luca-ant/unibotimetablesbot.git
```


* Install dependencies, create a virtual environment and install requirements modules
```
sudo apt install python3.7-setuptools
sudo apt install python3.7-pip
sudo apt install python3.7-venv
```
or
```
sudo pacman -S python-pip
python-virtualenv
```

```
cd unibotimetablesbot
python3.7 -m venv venv
source venv/bin/activate

python3.7 -m pip install -r requirements.txt
```


* Set BOT_TOKEN environment variable with bot's token

```
export BOT_TOKEN=YOUR_TOKEN_HERE
```
* Run the python script as:

```
python3.7 unibotimetablesbot.py
```


**An instance of bot it's now running!** You can find it on Telegram searching `@unibotimetablesbot`
