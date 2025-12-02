#!/usr/bin/env python3
import boto3
import time

# Crear cliente EC2
ec2 = boto3.client('ec2', region_name='us-east-1')

# Crear VPC
vpc_response = ec2.create_vpc(
    CidrBlock='192.168.0.0/24',
    TagSpecifications=[
        {
            'ResourceType': 'vpc',
            'Tags': [{'Key': 'Name', 'Value': 'MyVpc'}]
        }
    ]
)
vpc_id = vpc_response['Vpc']['VpcId']
print(f"VPC creada con ID: {vpc_id}")

# Habilitar DNS en la VPC
ec2.modify_vpc_attribute(
    VpcId=vpc_id,
    EnableDnsHostnames={'Value': True}
)

# Crear subred
subnet_response = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='192.168.0.0/28',
    AvailabilityZone='us-east-1a',
    TagSpecifications=[
        {
            'ResourceType': 'subnet',
            'Tags': [{'Key': 'Name', 'Value': 'MiSubred1'}]
        }
    ]
)
subnet_id = subnet_response['Subnet']['SubnetId']
print(f"Subred creada con ID: {subnet_id}")

# Habilitar asignación automática de IP pública
ec2.modify_subnet_attribute(
    SubnetId=subnet_id,
    MapPublicIpOnLaunch={'Value': True}
)

# Crear Security Group
sg_response = ec2.create_security_group(
    GroupName='gs-mck',
    Description='My security group for port 22',
    VpcId=vpc_id
)
sg_id = sg_response['GroupId']
print(f"Security Group creado con ID: {sg_id}")

# Autorizar puerto 22
ec2.authorize_security_group_ingress(
    GroupId=sg_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }
        # {
        #     'IpProtocol': 'tcp',
        #     'FromPort': 80,
        #     'ToPort': 80,
        #     'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        # }
    ]
)

# Crear EC2
instance_response = ec2.run_instances(
    ImageId='ami-0360c520857e3138f',
    InstanceType='t3.micro',
    KeyName='vockey',
    SubnetId=subnet_id,
    SecurityGroupIds=[sg_id],
    MinCount=1,
    MaxCount=1,
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': 'miEc2'}]
        }
    ]
)
instance_id = instance_response['Instances'][0]['InstanceId']

time.sleep(15)

print(f"EC2 creada con ID: {instance_id}")