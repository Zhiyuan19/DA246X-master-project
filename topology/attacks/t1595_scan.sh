#!/bin/bash

# T1595: Active Scanning Script (Network Discovery)
# This script performs active scanning to identify active hosts and services within the target network.
# T1595 refers to "Active Scanning" techniques used by adversaries to gather information about a target network.

TARGET="100.0.0.40/24"
OUTPUT_FILE="t1595_scan_results.txt"

# Run nmap scan with SYN scan, service version detection, and vulnerability script
nmap -sS -sV -p- -T4 -v "$TARGET" -oN "$OUTPUT_FILE"

# Display the saved results
echo "\n[+] Scan Results:"
cat "$OUTPUT_FILE"
