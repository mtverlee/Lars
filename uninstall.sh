#!/bin/bash

echo "Uninstalling!"
systemctl daemon-reload
systemctl stop lars.service
systemctl disable lars.service
rm /etc/systemctl/system/lars.service
systemctl daemon-reload
python3 -m pip uninstall -r requirements.txt
echo "Uninstalled."