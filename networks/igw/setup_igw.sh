#!/bin/bash

# Variables de configuración
REGION="us-east-1"
AVAILABILITY_ZONE="us-east-1a"
VPC_CIDR="192.168.0.0/24"
SUBNET_CIDR="192.168.0.0/26"

echo "=== Creando infraestructura en AWS ==="
echo ""

# Crear VPC
echo "Creando VPC..."
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block $VPC_CIDR \
  --region $REGION \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=MiVpc}]' \
  --query 'Vpc.VpcId' \
  --output text)

echo "✓ VPC creada: $VPC_ID"
echo ""

# Habilitar DNS
echo "Habilitando DNS en la VPC..."
aws ec2 modify-vpc-attribute \
  --vpc-id "$VPC_ID" \
  --enable-dns-hostnames "{\"Value\":true}" \
  --region $REGION

echo "✓ DNS habilitado"
echo ""

# Crear subnet
echo "Creando subred..."
SUB_ID=$(aws ec2 create-subnet \
  --vpc-id "$VPC_ID" \
  --cidr-block $SUBNET_CIDR \
  --availability-zone $AVAILABILITY_ZONE \
  --region $REGION \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=MiSubred}]' \
  --query 'Subnet.SubnetId' \
  --output text)

echo "✓ Subred creada: $SUB_ID"
echo ""

# Habilitar IPs públicas
echo "Habilitando asignación de IPs públicas en la subred..."
aws ec2 modify-subnet-attribute \
  --subnet-id $SUB_ID \
  --map-public-ip-on-launch \
  --region $REGION

echo "✓ IPs públicas habilitadas"
echo ""

# Crear IGW
echo "Creando Internet Gateway..."
IGW_ID=$(aws ec2 create-internet-gateway \
  --region $REGION \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=MiIGW}]' \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)

echo "✓ Internet Gateway creado: $IGW_ID"
echo ""

# Adjuntar IGW a VPC
echo "Adjuntando Internet Gateway a la VPC..."
aws ec2 attach-internet-gateway \
  --internet-gateway-id $IGW_ID \
  --vpc-id $VPC_ID \
  --region $REGION

echo "✓ Internet Gateway adjuntado a la VPC $VPC_ID"
echo ""

# Crear tabla de enrutamiento
echo "Creando tabla de enrutamiento..."
RTB_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --region $REGION \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=MiRTB}]' \
  --query 'RouteTable.RouteTableId' \
  --output text)

echo "✓ Tabla de enrutamiento creada: $RTB_ID"
echo ""

# Agregar ruta a la subnet
echo "Agregando ruta 0.0.0.0/0 hacia el IGW..."
aws ec2 create-route \
  --route-table-id $RTB_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID \
  --region $REGION

echo "✓ Ruta agregada correctamente"
echo ""

# Asociar tabla de enrutamiento a la subnet
echo "Asociando la tabla de enrutamiento a la subred..."
ASSOC_ID=$(aws ec2 associate-route-table \
  --subnet-id $SUB_ID \
  --route-table-id $RTB_ID \
  --region $REGION \
  --query 'AssociationId' \
  --output text)

echo "✓ Tabla de enrutamiento asociada a la subred $SUB_ID"
echo ""

echo "Detalles:"
echo " - VPC ID: $VPC_ID"
echo " - Subred ID: $SUB_ID"
echo " - Internet Gateway: $IGW_ID"
echo " - Route Table: $RTB_ID"
echo " - Asociación RTB: $ASSOC_ID"