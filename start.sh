#!/bin/sh

while [ ! -f /tmp/date.txt ]
do
  sleep 2
  echo "."
done
sudo /usr/bin/pip3 install boto3 httpserver paramiko psutil
cd /mnt/aws.test
sudo /mnt/aws.test/deploy -chttp
