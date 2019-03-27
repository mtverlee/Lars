# lars
Python script to record livestreams from Twitch.

## Requirements:
- Minimal, but are contained in the ```requirements.txt``` file.
- Uses [streamlink](https://github.com/streamlink/streamlink) to record streams.

## Installation:
- ```git clone https://github.com/mtverlee/lars```
- ```cd lars```
- ```cp config.ini.example config.ini```
- ```./install.sh```
- Edit the ```config.ini``` file to include your desired channel names in the format ```name, name, name```.
- ```sudo systemctl start lars.service```

## Usage:
- Use ```systemctl start lars.service``` to start service.
- Use ```systemctl stop lars.service``` to stop service.
- Use ```systemctl restart lars.service``` to restart service.
- Use ```systemctl status lars.service``` to see status of service.
- lars can also be used without a service: ```python3 main.py```

## Logs:
- Logs are written to the ```lars.log``` file in your install directory.
