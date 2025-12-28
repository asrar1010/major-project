#!/bin/bash
set -e

APP_DIR=/tmp/provisioning
CUSTOM_HOSTNAME="$1"
sudo hostnamectl set-hostname "$CUSTOM_HOSTNAME"

echo "📦 Installing NVM..."
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

# Load nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "📦 Installing Node.js 24..."
nvm install 24
nvm use 24

echo "✅ Node version:"
node -v
npm -v

echo "📁 Moving to app directory..."
cd $APP_DIR

echo "📦 Installing dependencies..."
npm install

echo "🚀 Starting application..."
nohup npm start > output.log 2>&1 &

echo "✅ App started successfully"
