sudo bash -c 'cat > /etc/systemd/system/radar-server.service << EOF
[Unit]
Description=Radar Application Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR/RaspberryPiRadarFullStackApplicationAndStepperController/server
ExecStart=/usr/bin/npm run server:start
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=\"NODE_ENV=production\"
Environment=\"PORT=3000\"

[Install]
WantedBy=multi-user.target
EOF
"

sudo systemctl daemon-reload
sudo systemctl restart radar-server