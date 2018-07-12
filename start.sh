#!/bin/sh

while [ ! -f /tmp/date.txt ]
do
  sleep 2
  echo "."
done

nohup /mnt/aws.test/deploy.py -chttp&
cd /mnt/aws.test
currCommit = `git git rev-parse HEAD`
sudo git pull
nextCommit = `git git rev-parse HEAD`
if [ "$currCommit" !="$nextCommit" $ ]; then
  echo "restarting http service"
  sudo killall -9 deploy.py
  sudo nohup /mnt/aws.test/deploy.py -chttp&
fi
