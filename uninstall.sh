#!/bin/bash

echo "Uninstalling!"
systemctl stop lars.service
systemctl disable lars.service
systemctl daemon-reload
rm /etc/systemctl/system/lars.service
rm -rf "$PWD"
echo "Uninstalled."