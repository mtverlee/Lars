#!/bin/bash

echo "Starting install!"
printf "\n"
echo "Making sure python3 is installed."
printf "\n"
apt update && apt install python3 python3-pip python3-setuptools python3-dev
printf "\n"
echo "Installing requirements."
printf "\n"
/usr/bin/python3 -m pip install -r requirements.txt
printf "\n"
echo "Editing service file."
printf "\n"
sed -i "s|WorkingDirectory=|WorkingDirectory=$PWD|g" $PWD/lars.service
sed -i "s|ExecStart=|ExecStart=/usr/bin/python3 $PWD/main.py|g" $PWD/lars.service
echo "Setting file save directories and editing config files."
echo "lars saves files it is currently recording in a different directory than the rest of the completed recordings."
cp config.ini.example config.ini
echo -n "Enter directory to write in-progress streams to (end with /): "
read in_progress
sed -i "s|in_progress_directory = |in_progress_directory = $in_progress|g" $PWD/config.ini
echo -n "Enter directoty to write saved files to (end with /): "
read saved
sed -i "s|save_directory = |save_directory = $saved|g" $PWD/config.ini
mkdir -p "$in_progress"
mkdir -p "$saved"
printf "\n"
echo "Verifying permissions."
sudo chmod -R 666 "$in_progress"
sudo chmod -R 666 "$saved"
printf "\n"
echo "Setting up services."
printf "\n"
apt install systemd
sudo cp lars.service /etc/systemd/system/
systemctl daemon-reload
sudo systemctl enable lars.service
printf "\n"
echo "Setting up Twitch API."
printf "\n"
echo -n "Enter Twitch Helix Client ID: "
read client_id
sed -i "s|user_id = |user_id = $client_id|g" $PWD/config.ini
printf "\n"
echo "Setting up Pushover notifications."
printf "\n"
echo "Do you want to set up Pushover notifications?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) echo -n "Enter your Pushover user key: "; read user_key; echo -n "Enter your Pushover app key: "; read app_key; sed -i "s|send_pushover_notifications = False|send_pushover_notifications = True|g" $PWD/config.ini; sed -i "s|pushover_user_key = |pushover_user_key = $user_key|g" $PWD/config.ini; sed -i "s|pushover_app_key = |pushover_app_key = $app_key|g" $PWD/config.ini; echo "Done."; break;;
        No ) echo "Done."; break;;
    esac
done
printf "\n"
echo "Edit the config.ini file to include your desired channel names in the format '<name>, <name>, <name>'."
printf "\n"
printf "Then, start the service using:\n\n sudo systemctl start lars.service"
printf "\n"
printf "\n"