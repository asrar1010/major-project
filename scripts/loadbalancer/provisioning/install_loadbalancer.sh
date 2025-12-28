#!/bin/bash
set -e

sudo apt update
sudo apt install -y nginx python3 python3-venv python3-full

sudo systemctl enable nginx
sudo systemctl start nginx

sudo rm /etc/nginx/sites-enabled/default

APP_DIR=/tmp/provisioning
cd $APP_DIR

# Create venv
python3 -m venv venv

# Install dependencies INSIDE venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# Run app using venv Python
sudo nohup venv/bin/python load_balancer.py \
  > output.log 2>&1 &

echo "Load Balancer running"
