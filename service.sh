#!/bin/bash


RP=$(realpath $0)
CURRENT_DIR=$(dirname $RP)
VENV_ACT="$CURRENT_DIR/venv/bin/activate"



OPTION=""


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

	
	

	python3 -m venv "$CURRENT_DIR"/venv
	source "$CURRENT_DIR"/venv/bin/activate

	python3 -m pip install -r "$CURRENT_DIR/"requirements.txt
	deactivate


	BOT_USER=$(whoami)
	UNI_BOT_TOKEN="YOUR_TOKEN_HERE"

	
	echo -e "[Unit]
Description=Unibo timetables bot
After=network.target
StartLimitIntervalSec=0
[Service]
Environment=UNI_BOT_TOKEN=$UNI_BOT_TOKEN
WorkingDirectory="$CURRENT_DIR"
Type=simple
Restart=always
RestartSec=1
User=$BOT_USER
ExecStart="$CURRENT_DIR/service.sh run"

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/unibotimetablesbot.service


fi
