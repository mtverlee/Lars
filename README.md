# lars
Python script to record livestreams from Twitch.

## Requirements:
- Minimal, but are contained in the ```requirements.txt``` file.
- Uses [streamlink](https://github.com/streamlink/streamlink) to record streams.

## Installation:
- ```git clone https://github.com/mtverlee/lars```
- ```cd lars```
- ```./install.sh```
- Edit the ```config.ini``` file to include your desired channel names in the format ```name, name, name```.
- ```sudo systemctl start lars.service```

## Logs:
- Logs are written to the ```lars.log``` file in your install directory.