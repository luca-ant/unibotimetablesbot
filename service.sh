#!/bin/bash


RP=$(realpath $0)
CURRENT_DIR=$(dirname $RP)
VENV_ACT="$CURRENT_DIR/venv/bin/activate"

UNI_BOT_TOKEN="YOUR_TOKEN_HERE"

if [ $1 == "run"  ]
then
	source "$VENV_ACT"
	python "$CURRENT_DIR"/unibotimetablesbot/unibotimetablesbot.py

fi





if [ $1 == "install" ] 
then
	if [[ $EUID -ne 0 ]]; 
	then
		echo "This script must be run as root" 1>&2
		exit 1
	fi



	python3 -m venv "$CURRENT_DIR"/venv
	source "$CURRENT_DIR"/venv/bin/activate

	python3 -m pip install -r requirements.txt
	deactivate




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
User=$USER
ExecStart="$CURRENT_DIR/service.sh run"

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/unibotimetablesbot.service

	sudo systemctl daemon-reload
	sudo systemctl enable unibotimetablesbot.service
	sudo systemctl start unibotimetablesbot.service

fi
