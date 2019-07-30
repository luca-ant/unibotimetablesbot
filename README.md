# unibotimetablesbot


A Telegram bot for Unibo lessons timetables in Bologna.

## Getting started

### Linux
Clonare il repository
```
git clone https://github.com/luca-ant/unibotimetablesbot.git
```
or
```
git clone git@github.com:luca-ant/unibotimetablesbot.git
```


* Install dependencies, create a virtual environment and install requirements modules
```
sudo apt install python3-setuptools
sudo apt install python3-pip
sudo apt install python3-venv

cd unibotimetablesbot
python3.7 -m venv venv
source venv/bin/activate

python3.7 -m pip install -r requirements.txt
```



* Create a file with a telegram bot token in a single line *(es: bot.tk)*
* Run the python script as:

`python3 unibotimetablesbot.py bot.tk`



**An instance of bot it's now running!** You can find it on Telegram searching `@unibotimetablesbot`
