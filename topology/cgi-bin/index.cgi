#!/bin/bash
echo "Content-Type:text/html "

echo ""

read -n $CONTENT_LENGTH data

echo "Connected Success"
echo "PASS DATA: $data"