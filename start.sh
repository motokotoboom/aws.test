#!/bin/sh

while [ ! -f /tmp/date.txt ]
do
  sleep 2
  echo "."
done

cd /mnt/aws.test
sudo screen /mnt/aws.test/deploy.py -chttp
sleep 1