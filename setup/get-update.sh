#!/bin/bash
# Update RadarProject repo and optionally rebuild and restart services

set -e

cd ~/RadarProject || { echo "RadarProject directory not found"; exit 1; }
echo "Building client..."
echo "Pulling latest code..."
PULL_OUTPUT=$(git pull)
echo "$PULL_OUTPUT"

if [[ "$PULL_OUTPUT" == *"Already up to date."* ]]; then
	echo "No updates found. Skipping build and restart."
	exit 0
fi

echo "Building client..."
cd ~/RadarProject/RadarApp-FullStack/client
npm install && npm run build
cd ~/RadarProject
echo "Restarting services..."
sudo systemctl restart radar-server radar-client
echo "Update, build, and restart complete."
echo "To view logs:"
echo "sudo journalctl -u radar-server -f"
echo "sudo journalctl -u radar-client -f"
