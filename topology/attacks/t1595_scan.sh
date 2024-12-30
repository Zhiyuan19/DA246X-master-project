#!/bin/bash

# T1595: Active Scanning Script (Network Discovery)
# This script performs active scanning to identify active hosts and services within the target network.
# T1595 refers to "Active Scanning" techniques used by adversaries to gather information about a target network.

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <target_ip>"
    exit 1
fi

TARGET="$1"
OUTPUT_FILE="/home/attacks/t1595_scan_results_$TARGET.txt"

# Run nmap scan with SYN scan, service version detection, and vulnerability script
nmap -Pn -n -p 0-9000 -T4 "$TARGET" -oN "$OUTPUT_FILE" --host-timeout 15s

# Display the saved results
if [ -f "$OUTPUT_FILE" ]; then
    echo "\n[+] Scan Results:"
    cat "$OUTPUT_FILE"
else
    echo "Error: Scan results file not found at $OUTPUT_FILE."
    exit 1
fi
