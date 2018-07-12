#!/bin/sh

while [ ! -f /tmp/date.txt ]
do
  sleep 2
  echo "."
done

sudo nohup ./deploy.py -chttp&
cd /mnt/aws.test
CURR=`git rev-parse HEAD`
sudo git pull
NEXT=`git rev-parse HEAD`
echo $CURR $NEXT
if [ "$CURR" != "$NEXT" ]; then
  echo "restarting http service"
  sudo killall -9 deploy.py
  sudo nohup ./deploy.py -chttp&
fi

