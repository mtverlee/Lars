#!/bin/bash

echo "Uninstalling!"
systemctl stop lars.service
systemctl disable lars.service
systemctl daemon-reload
rm /etc/systemctl/system/lars.service
python3 -m pip uninstall -r requirements.txt
rm -rf "$PWD"
echo "Uninstalled."