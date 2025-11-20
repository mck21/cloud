#!/bin/bash

###########################################
# Script 1: Crear infraestructura AWS base
# - VPC, Subnets, Internet Gateway
# - Route Tables, Security Groups
# - Instancias EC2 (pública y privada)
###########################################

set -e

# Colores para logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # Sin color

# Variables de configuración
VPC_CIDR="172.16.0.0/16"
SUBNET_CIDR="172.16.0.0/24"
VPC_NAME="vpc-mck21"
SUBNET_PUBLIC_NAME="subnet-public-mck21"
SUBNET_PRIVATE_NAME="subnet-private-mck21"
IGW_NAME="igw-mck21"
RTB_PUBLIC_NAME="rtb-public-mck21"
RTB_PRIVATE_NAME="rtb-private-mck21"
SG_NAME="gs-mck21"
EC2_PUBLIC_NAME="ec2-public-mck21"
EC2_PRIVATE_NAME="ec2-private-mck21"
KEY_PAIR="vockey"
AMI_ID="ami-0ecb62995f68bb549"

echo -e "${GREEN}=== Iniciando creación de infraestructura AWS ===${NC}\n"

# Función para obtener el ID de un recurso por su nombre
get_resource_id() {
    local resource_type=$1
    local name=$2
    aws ec2 describe-tags --filters "Name=key,Values=Name" "Name=value,Values=$name" "Name=resource-type,Values=$resource_type" --query 'Tags[0].ResourceId' --output text 2>/dev/null
}

###########################################
# 1. CREAR VPC
###########################################
echo -e "${YELLOW}[1/9] Verificando VPC...${NC}"
VPC_ID=$(get_resource_id "vpc" "$VPC_NAME")

if [ "$VPC_ID" == "None" ] || [ -z "$VPC_ID" ]; then
    echo "Creando VPC con CIDR $VPC_CIDR..."
    VPC_ID=$(aws ec2 create-vpc --cidr-block $VPC_CIDR --query 'Vpc.VpcId' --output text)
    aws ec2 create-tags --resources $VPC_ID --tags Key=Name,Value=$VPC_NAME
    aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support
    aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames
    echo -e "${GREEN}✓ VPC creada: $VPC_ID${NC}"
else
    echo -e "${GREEN}✓ VPC ya existe: $VPC_ID${NC}"
fi

###########################################
# 2. CREAR SUBNET PÚBLICA
###########################################
echo -e "\n${YELLOW}[2/9] Verificando Subnet Pública...${NC}"
SUBNET_PUBLIC_ID=$(get_resource_id "subnet" "$SUBNET_PUBLIC_NAME")

if [ "$SUBNET_PUBLIC_ID" == "None" ] || [ -z "$SUBNET_PUBLIC_ID" ]; then
    echo "Creando subnet pública con CIDR $SUBNET_CIDR..."
    SUBNET_PUBLIC_ID=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block $SUBNET_CIDR --query 'Subnet.SubnetId' --output text)
    aws ec2 create-tags --resources $SUBNET_PUBLIC_ID --tags Key=Name,Value=$SUBNET_PUBLIC_NAME
    aws ec2 modify-subnet-attribute --subnet-id $SUBNET_PUBLIC_ID --map-public-ip-on-launch
    echo -e "${GREEN}✓ Subnet pública creada: $SUBNET_PUBLIC_ID${NC}"
else
    echo -e "${GREEN}✓ Subnet pública ya existe: $SUBNET_PUBLIC_ID${NC}"
fi

###########################################
# 3. CREAR SUBNET PRIVADA
###########################################
echo -e "\n${YELLOW}[3/9] Verificando Subnet Privada...${NC}"
SUBNET_PRIVATE_ID=$(get_resource_id "subnet" "$SUBNET_PRIVATE_NAME")

if [ "$SUBNET_PRIVATE_ID" == "None" ] || [ -z "$SUBNET_PRIVATE_ID" ]; then
    echo "Creando subnet privada con CIDR 172.16.1.0/24..."
    SUBNET_PRIVATE_ID=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 172.16.1.0/24 --query 'Subnet.SubnetId' --output text)
    aws ec2 create-tags --resources $SUBNET_PRIVATE_ID --tags Key=Name,Value=$SUBNET_PRIVATE_NAME
    echo -e "${GREEN}✓ Subnet privada creada: $SUBNET_PRIVATE_ID${NC}"
else
    echo -e "${GREEN}✓ Subnet privada ya existe: $SUBNET_PRIVATE_ID${NC}"
fi

###########################################
# 4. CREAR INTERNET GATEWAY
###########################################
echo -e "\n${YELLOW}[4/9] Verificando Internet Gateway...${NC}"
IGW_ID=$(get_resource_id "internet-gateway" "$IGW_NAME")

if [ "$IGW_ID" == "None" ] || [ -z "$IGW_ID" ]; then
    echo "Creando Internet Gateway..."
    IGW_ID=$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text)
    aws ec2 create-tags --resources $IGW_ID --tags Key=Name,Value=$IGW_NAME
    aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
    echo -e "${GREEN}✓ Internet Gateway creado y asociado: $IGW_ID${NC}"
else
    echo -e "${GREEN}✓ Internet Gateway ya existe: $IGW_ID${NC}"
fi

###########################################
# 5. CREAR ROUTE TABLE PÚBLICA
###########################################
echo -e "\n${YELLOW}[5/9] Verificando Route Table Pública...${NC}"
RTB_PUBLIC_ID=$(get_resource_id "route-table" "$RTB_PUBLIC_NAME")

if [ "$RTB_PUBLIC_ID" == "None" ] || [ -z "$RTB_PUBLIC_ID" ]; then
    echo "Creando Route Table pública..."
    RTB_PUBLIC_ID=$(aws ec2 create-route-table --vpc-id $VPC_ID --query 'RouteTable.RouteTableId' --output text)
    aws ec2 create-tags --resources $RTB_PUBLIC_ID --tags Key=Name,Value=$RTB_PUBLIC_NAME
    aws ec2 create-route --route-table-id $RTB_PUBLIC_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
    aws ec2 associate-route-table --route-table-id $RTB_PUBLIC_ID --subnet-id $SUBNET_PUBLIC_ID
    echo -e "${GREEN}✓ Route Table pública creada y asociada: $RTB_PUBLIC_ID${NC}"
else
    echo -e "${GREEN}✓ Route Table pública ya existe: $RTB_PUBLIC_ID${NC}"
fi

###########################################
# 6. CREAR ROUTE TABLE PRIVADA
###########################################
echo -e "\n${YELLOW}[6/9] Verificando Route Table Privada...${NC}"
RTB_PRIVATE_ID=$(get_resource_id "route-table" "$RTB_PRIVATE_NAME")

if [ "$RTB_PRIVATE_ID" == "None" ] || [ -z "$RTB_PRIVATE_ID" ]; then
    echo "Creando Route Table privada..."
    RTB_PRIVATE_ID=$(aws ec2 create-route-table --vpc-id $VPC_ID --query 'RouteTable.RouteTableId' --output text)
    aws ec2 create-tags --resources $RTB_PRIVATE_ID --tags Key=Name,Value=$RTB_PRIVATE_NAME
    aws ec2 associate-route-table --route-table-id $RTB_PRIVATE_ID --subnet-id $SUBNET_PRIVATE_ID
    echo -e "${GREEN}✓ Route Table privada creada y asociada: $RTB_PRIVATE_ID${NC}"
else
    echo -e "${GREEN}✓ Route Table privada ya existe: $RTB_PRIVATE_ID${NC}"
fi

###########################################
# 7. CREAR SECURITY GROUP
###########################################
echo -e "\n${YELLOW}[7/9] Verificando Security Group...${NC}"
SG_ID=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=$SG_NAME" --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null)

if [ "$SG_ID" == "None" ] || [ -z "$SG_ID" ]; then
    echo "Creando Security Group..."
    SG_ID=$(aws ec2 create-security-group --group-name $SG_NAME --description "Security group for mck21 instances" --vpc-id $VPC_ID --query 'GroupId' --output text)
    aws ec2 create-tags --resources $SG_ID --tags Key=Name,Value=$SG_NAME
    
    # Permitir SSH desde cualquier lugar
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0
    
    # Permitir ICMP (ping) desde la VPC
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol icmp --port -1 --cidr $VPC_CIDR
    
    # Permitir todo el tráfico saliente
    aws ec2 authorize-security-group-egress --group-id $SG_ID --protocol -1 --cidr 0.0.0.0/0 2>/dev/null || true
    
    echo -e "${GREEN}✓ Security Group creado: $SG_ID${NC}"
else
    echo -e "${GREEN}✓ Security Group ya existe: $SG_ID${NC}"
fi


###########################################
# 8. CREAR INSTANCIAS EC2
###########################################
echo -e "\n${YELLOW}[9/9] Verificando Instancias EC2...${NC}"

# EC2 Pública
EC2_PUBLIC_ID=$(get_resource_id "instance" "$EC2_PUBLIC_NAME")
if [ "$EC2_PUBLIC_ID" == "None" ] || [ -z "$EC2_PUBLIC_ID" ]; then
    echo "Lanzando instancia EC2 pública..."
    EC2_PUBLIC_ID=$(aws ec2 run-instances \
        --image-id $AMI_ID \
        --instance-type t3.micro \
        --key-name $KEY_PAIR \
        --subnet-id $SUBNET_PUBLIC_ID \
        --security-group-ids $SG_ID \
        --associate-public-ip-address \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$EC2_PUBLIC_NAME}]" \
        --query 'Instances[0].InstanceId' \
        --output text)
    echo -e "${GREEN}✓ EC2 pública creada: $EC2_PUBLIC_ID${NC}"
else
    echo -e "${GREEN}✓ EC2 pública ya existe: $EC2_PUBLIC_ID${NC}"
fi

# EC2 Privada
EC2_PRIVATE_ID=$(get_resource_id "instance" "$EC2_PRIVATE_NAME")
if [ "$EC2_PRIVATE_ID" == "None" ] || [ -z "$EC2_PRIVATE_ID" ]; then
    echo "Lanzando instancia EC2 privada..."
    EC2_PRIVATE_ID=$(aws ec2 run-instances \
        --image-id $AMI_ID \
        --instance-type t3.micro \
        --key-name $KEY_PAIR \
        --subnet-id $SUBNET_PRIVATE_ID \
        --security-group-ids $SG_ID \
        --no-associate-public-ip-address \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$EC2_PRIVATE_NAME}]" \
        --query 'Instances[0].InstanceId' \
        --output text)
    echo -e "${GREEN}✓ EC2 privada creada: $EC2_PRIVATE_ID${NC}"
else
    echo -e "${GREEN}✓ EC2 privada ya existe: $EC2_PRIVATE_ID${NC}"
fi

###########################################
# RESUMEN FINAL
###########################################
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Infraestructura creada exitosamente${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "VPC ID:              $VPC_ID"
echo -e "Subnet Pública:      $SUBNET_PUBLIC_ID"
echo -e "Subnet Privada:      $SUBNET_PRIVATE_ID"
echo -e "Internet Gateway:    $IGW_ID"
echo -e "Route Table Pública: $RTB_PUBLIC_ID"
echo -e "Route Table Privada: $RTB_PRIVATE_ID"
echo -e "Security Group:      $SG_ID"
echo -e "EC2 Pública:         $EC2_PUBLIC_ID"
echo -e "EC2 Privada:         $EC2_PRIVATE_ID"
echo -e "${GREEN}========================================${NC}\n"

echo -e "${YELLOW}Esperando a que las instancias estén en estado 'running'...${NC}"
aws ec2 wait instance-running --instance-ids $EC2_PUBLIC_ID $EC2_PRIVATE_ID
echo -e "${GREEN}✓ Instancias en estado 'running'${NC}\n"

# Obtener IPs
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $EC2_PUBLIC_ID --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
PRIVATE_IP=$(aws ec2 describe-instances --instance-ids $EC2_PRIVATE_ID --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)

echo -e "${GREEN}IP Pública EC2 pública:  $PUBLIC_IP${NC}"
echo -e "${GREEN}IP Privada EC2 privada:  $PRIVATE_IP${NC}\n"

echo -e "${YELLOW}SIGUIENTE PASO:${NC}"
echo -e "1. Conectarse a la EC2 privada desde la EC2 pública"
echo -e "2. Verificar que el ping a Internet falla (sin NAT Gateway)"
echo -e "3. Ejecutar el Script 2 para crear el NAT Gateway"
echo -e "4. Verificar que el ping funciona después del NAT Gateway\n"