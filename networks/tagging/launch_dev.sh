#!/bin/bash

# Crear una VPC y devolver su ID
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 192.168.0.0/24 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=MyVpc},{Key=entorno,Value=prueba}]' \
  --query 'Vpc.VpcId' \
  --output text)

echo "VPC creada con ID: $VPC_ID"

# Habilitar DNS en la VPC
aws ec2 modify-vpc-attribute \
  --vpc-id "$VPC_ID" \
  --enable-dns-hostnames "{\"Value\":true}"

# Crear primera subred dentro de la VPC
SUB_ID_1=$(aws ec2 create-subnet \
  --vpc-id "$VPC_ID" \
  --cidr-block 192.168.0.0/28 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=MiSubred1},{Key=entorno,Value=prueba}]' \
  --query 'Subnet.SubnetId' \
  --output text)

echo "Primera subred creada con ID: $SUB_ID_1"

aws ec2 modify-subnet-attribute --subnet-id $SUB_ID_1 --map-public-ip-on-launch

# Crear segunda subred dentro de la VPC
SUB_ID_2=$(aws ec2 create-subnet \
  --vpc-id "$VPC_ID" \
  --cidr-block 192.168.0.16/28 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=MiSubred2},{Key=entorno,Value=prueba}]' \
  --query 'Subnet.SubnetId' \
  --output text)

echo "Segunda subred creada con ID: $SUB_ID_2"

aws ec2 modify-subnet-attribute --subnet-id $SUB_ID_2 --map-public-ip-on-launch

# Crear EC2 en la primera subred
echo ""
echo "Creando instancia EC2 en subred 1..."
EC2_ID=$(aws ec2 run-instances \
    --image-id ami-0360c520857e3138f \
    --instance-type t3.micro \
    --key-name vockey \
    --subnet-id $SUB_ID_1 \
    --associate-public-ip-address \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=miEc2},{Key=entorno,Value=prueba}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "Espere unos segundos..."

sleep 15

echo ""
echo "Resumen:"
echo "VPC ID: $VPC_ID"
echo "Subred 1 ID: $SUB_ID_1"
echo "Subred 2 ID: $SUB_ID_2"
echo "EC2 creada con ID: $EC2_ID"