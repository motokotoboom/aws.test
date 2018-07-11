#!/bin/sh
while [ ! -f /tmp/date.txt ]
do
  sleep 2
  echo "waiting for dependencies installed"
done
sudo screen ./mnt/aws.test/deploy -chttp
