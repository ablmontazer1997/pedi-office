#!/bin/bash
# Keep the bot-world status server alive; restarted by tmux socket "botworld".
cd /home/rade/projects/botworld
while true; do
    python3 server.py >> server.log 2>&1
    sleep 3
done
