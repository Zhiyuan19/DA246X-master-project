#!/bin/bash

#docker build -t containernet_example:ubuntu1404 -f Dockerfile.ubuntu1404 .
#docker build -t containernet_example:ubuntu1604 -f Dockerfile.ubuntu1604 .
docker build --no-cache -t containernet:firewall -f Dockerfile.ubuntu2004 .

#docker build -t containernet_example:centos6 -f Dockerfile.centos6 .
#docker build -t containernet_example:centos7 -f Dockerfile.centos7 .
#docker build --no-cache -t containernet_example:dns -f Dockerfile.dns .
