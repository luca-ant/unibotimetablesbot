#!/bin/bash


RP=$(realpath $0)
CURRENT_DIR=$(dirname $RP)
VENV_ACT="$CURRENT_DIR/venv/bin/activate"


#default option
OPTION='install'


if [ $# == 1 ]
then
	OPTION="$1"
fi


if [ $OPTION == "run" ]
then
	source "$VENV_ACT"
	python3 "$CURRENT_DIR"/unibotimetablesbot/unibotimetablesbot.py

fi


if [ $OPTION == "install" ] 
then
	BOT_USER='unibotimetablesuser'
	
	UNI_BOT_TOKEN="YOUR_TOKEN_HERE"
	


	sudo adduser $BOT_USER
	sudo su $BOT_USER
	echo $HOME
	cd $HOME

	git clone https://github.com/luca-ant/unibotimetablesbot.git
	
	cd unibotimetalblesbot

	python3 -m venv "$CURRENT_DIR"/venv
	source "$CURRENT_DIR"/venv/bin/activate

	python3 -m pip install -r "$CURRENT_DIR/"requirements.txt
	deactivate




	sudo echo -e "[Unit]
Description=Unibo timetables bot
After=network.target
StartLimitIntervalSec=0
[Service]
Environment=UNI_BOT_TOKEN=$UNI_BOT_TOKEN
WorkingDirectory="$CURRENT_DIR"
Type=simple
Restart=always
RestartSec=1
User=$USER
ExecStart="$CURRENT_DIR/service.sh run"

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/unibotimetablesbot.service


fi
