#!/bin/sh
sudo /usr/bin/pip3 install boto3 httpserver paramiko psutil
# while [ ! -f /tmp/date.txt ]
# do
#   sleep 2
#   echo "waiting for dependencies installed"
# done
cd /mnt/aws.test
sudo screen /mnt/aws.test/deploy -chttp
