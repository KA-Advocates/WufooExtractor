#!/bin/sh
cp *.service *.timer /etc/systemd/system/
systemctl enable *.timer
systemctl start *.timer