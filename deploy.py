#!/usr/bin/env python3
import sys,getopt
import boto3
import time
import uuid
import logging
import os
from httpsrv import *
import paramiko



ACCESS_KEY = ""
SECRET_KEY = ""
REGION = 'eu-west-1'
id = 'test-'+str(uuid.uuid4()) 
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CEcc():

    res = None
    access_key = None
    secret_key = None
    region = 'eu-west-1'
    client = None
    ssm = None
    publicIp = None

    def __init__(self,access_key,secret_key,region):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
       

    def connect(self):
        logger.info('creating resource...')
        self.res = boto3.resource('ec2',
            aws_access_key_id  = self.access_key,
            aws_secret_access_key = self.secret_key,
            region_name = self.region)
        logger.info('done!')
        
        logger.info('creating client...')
        self.client = boto3.client('ec2',
            aws_access_key_id  = self.access_key,
            aws_secret_access_key = self.secret_key,
            region_name = self.region)

        self.ssm = boto3.client('ssm',
            aws_access_key_id  = self.access_key,
            aws_secret_access_key = self.secret_key,
            region_name = self.region)
        logger.info('done!')
        logger.info('creating key pair')
        keys = self.client.create_key_pair(KeyName=id)
   
        with open('/tmp/'+id+'.pem', 'w') as file:
            file.write(keys['KeyMaterial'])

        return self


    def createInstance(self,ami='ami-58d7e821',instanceType='t2.micro',minCount=1,maxCount=1,userData=''):
        logger.info('creating instance')
        instance_id = self.res.create_instances(
            ImageId=ami,
            MinCount=minCount,
            MaxCount=maxCount,
            UserData=userData,
            InstanceType=instanceType,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': id+'.instance'
                        },
                    ]
                },
            ],
            KeyName=id,
        )[0].instance_id
       
        logger.info ('instance created')
       
        logger.info ('waiting for instance is started:')
       
        state = None
        while state != 'running':
            desc = self.client.describe_instances(InstanceIds=[instance_id])
           
            state = desc['Reservations'][0]['Instances'][0]['State']['Name']
            logger.debug("%s status: %s",instance_id,state)
            if state!='running':
                time.sleep(5)

        
        logger.info ('Instance is running now!')
        self.publicIp=desc['Reservations'][0]['Instances'][0]['PublicIpAddress']

        return instance_id

    def setSecurityGroup(self,instance_id,group_id):
        print 
        instance = list(self.res.instances.filter(Filters=[{'Name': 'instance-id', 'Values': [instance_id]}]))[0]
        instance.modify_attribute(Groups=[group_id])  
        return 

    def createVolume(self,size=1,volumeType='standard',zone=''):
        logger.info ("creating volume: %dGb type:%s in zone:%s ",size,volumeType,zone)
        volume = self.res.create_volume(
            Size=size,
            AvailabilityZone=zone,
            VolumeType=volumeType,
            TagSpecifications=[
                {
                    'ResourceType': 'volume',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': id+'.'+str(size)+'G.'+volumeType+'.volume'
                        },
                    ]
                },
            ],
        )

        logger.info('waiting for volume avialability:')
        waiter = self.client.get_waiter('volume_available')
        waiter.wait(VolumeIds=[volume.volume_id])
        logger.info('Volume available!')

        return volume.volume_id

    def createSecurityGroup(self):
        logger.info('creating access group')
        sg = self.res.create_security_group(
             GroupName=id+'.sg',
             Description='allow inbound 80 and 22'
        )

        print (sg.id)
     
        # )
        self.client.authorize_security_group_ingress(GroupId=sg.id,
        
                    IpProtocol="tcp",
                    CidrIp="0.0.0.0/0",
                    FromPort=80,
                    ToPort=80,
           )
        self.client.authorize_security_group_ingress(GroupId=sg.id,
        
                    IpProtocol="tcp",
                    CidrIp="0.0.0.0/0",
                    FromPort=22,
                    ToPort=22,
           )

        logger.info('Access group  created')
        return sg.id

    def attachVolume(self,volume_id,instance_id,device='xvdb'):
        logger.info("Attaching volume %s to instance %s",volume_id,instance_id)
        volume =  list(self.res.volumes.filter(Filters=[{'Name': 'volume-id', 'Values': [volume_id]}]))[0]
        response = volume.attach_to_instance(
            InstanceId=instance_id,
            Device=device)

        waiter = self.client.get_waiter('volume_in_use')
        waiter.wait(VolumeIds=[volume.volume_id])
        logger.info("Attached!")

    def executeSsh(self,instance_id,command):
        desc = self.res.instances.filter(InstanceIds=[instance_id])
      
        logger.info("Getting pem file %s",'/tmp/'+id+'.pem')

        keys = paramiko.RSAKey.from_private_key_file('/tmp/'+id+'.pem')
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        logger.info("Connecting to %s",self.publicIp)
        client.connect(hostname=self.publicIp, username="ubuntu", pkey=keys)
        logger.info("Executing ssh command:%s",command)
        stdin, stdout, stderr = client.exec_command(command)
        logger.info(stdout.read())
        client.close()
        return stdout


    def getCurrentCommit(self):
        return os.system("cd /home/www/aws.test;git rev-parse HEAD")



    def runHttp(self):
        server = CustomHTTPServer(('0.0.0.0', 80))
        server.set_auth('demo', 'demo')
        server.serve_forever()
        

    def help(self):
        print('''Usage:
        ./deploy [--access-key <AWS_ACCESS_KEY>] [--secret-key <AWS_SECRET_KEY>] --command=[batch|http]
        ''')






if __name__ == "__main__":

    opts=[]
    args=[]
    command = None
    try:
      opts, args = getopt.getopt(sys.argv[1:],"ha:s:c:r",["help","access-key=","secret-key=","command=","region="])
    except getopt.GetoptError:
        help()
        sys.exit(2)
    repr(opts)

    for opt, arg in opts:
        print (opt,arg)
        if opt == '-h':
            help()
            sys.exit()
        elif opt in ("-a", "--access-key"):
            ACCESS_KEY = arg
        elif opt in ("-s", "--secret-key"):
            SECRET_KEY = arg
        elif opt in ("-c", "--command"):
            command = arg
        elif opt in ("-r", "--region"):
            REGION = arg      
    ec2 = CEcc(ACCESS_KEY,SECRET_KEY,REGION)
    if command == 'batch':
        
        ec2.connect()
        instance = ec2.createInstance(userData = "#!/bin/sh\napt update; apt install openssh-server libssl-dev libffi-dev python3-pip -y;  LC_ALL=C pip3 install boto3 httpserver paramiko psutil ")
        sg = ec2.createSecurityGroup()
        ec2.setSecurityGroup(instance,sg)
        volume = ec2.createVolume(zone='eu-west-1c')
        ec2.attachVolume(volume,instance)
        response = ec2.executeSsh(instance,"sudo mkfs -t ext4 /dev/xvdb;sudo mount -t auto /dev/xvdb /mnt;cd /mnt/;sudo git clone https://github.com/motokotoboom/aws.test.git; cd aws.test")
        logging.debug(response)
        response = ec2.executeSsh(instance,"sudo nohup /mnt/aws.test/deploy.py -chttp&")
        logging.debug(response)
    elif command == 'http':
        ec2.runHttp()
    else:
        ec2.help()
