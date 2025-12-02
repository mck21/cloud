#!/bin/bash

###########################################
# Script: Crear infraestructura AWS completa con NAT Gateway
# - VPC, Subnets, Internet Gateway
# - Route Tables, Security Groups
# - Instancias EC2 (pública y privada)
# - Elastic IP y NAT Gateway
###########################################

set -e

# Colores para logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # Sin color

# Variables de configuración
VPC_CIDR="172.16.0.0/16"
SUBNET_PUBLIC_CIDR="172.16.0.0/24"
SUBNET_PRIVATE_CIDR="172.16.1.0/24"
VPC_NAME="vpc-mck21"
SUBNET_PUBLIC_NAME="subnet-public-mck21"
SUBNET_PRIVATE_NAME="subnet-private-mck21"
IGW_NAME="igw-mck21"
RTB_PUBLIC_NAME="rtb-public-mck21"
RTB_PRIVATE_NAME="rtb-private-mck21"
SG_NAME="gs-mck21"
EC2_PUBLIC_NAME="ec2-public-mck21"
EC2_PRIVATE_NAME="ec2-private-mck21"
EIP_NAME="eip-mck21"
NAT_NAME="nat-mck21"
KEY_PAIR="vockey"
AMI_ID="ami-0ecb62995f68bb549"

echo -e "${GREEN}=== Iniciando creación de infraestructura AWS completa ===${NC}\n"

# Función para obtener el ID de un recurso por su nombre
get_resource_id() {
    local resource_type=$1
    local name=$2
    aws ec2 describe-tags --filters "Name=key,Values=Name" "Name=value,Values=$name" "Name=resource-type,Values=$resource_type" --query 'Tags[0].ResourceId' --output text 2>/dev/null
}

###########################################
# 1. CREAR VPC
###########################################
echo -e "${YELLOW}[1/12] Verificando VPC...${NC}"
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
echo -e "\n${YELLOW}[2/12] Verificando Subnet Pública...${NC}"
SUBNET_PUBLIC_ID=$(get_resource_id "subnet" "$SUBNET_PUBLIC_NAME")

if [ "$SUBNET_PUBLIC_ID" == "None" ] || [ -z "$SUBNET_PUBLIC_ID" ]; then
    echo "Creando subnet pública con CIDR $SUBNET_PUBLIC_CIDR..."
    SUBNET_PUBLIC_ID=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block $SUBNET_PUBLIC_CIDR --query 'Subnet.SubnetId' --output text)
    aws ec2 create-tags --resources $SUBNET_PUBLIC_ID --tags Key=Name,Value=$SUBNET_PUBLIC_NAME
    aws ec2 modify-subnet-attribute --subnet-id $SUBNET_PUBLIC_ID --map-public-ip-on-launch
    echo -e "${GREEN}✓ Subnet pública creada: $SUBNET_PUBLIC_ID${NC}"
else
    echo -e "${GREEN}✓ Subnet pública ya existe: $SUBNET_PUBLIC_ID${NC}"
fi

###########################################
# 3. CREAR SUBNET PRIVADA
###########################################
echo -e "\n${YELLOW}[3/12] Verificando Subnet Privada...${NC}"
SUBNET_PRIVATE_ID=$(get_resource_id "subnet" "$SUBNET_PRIVATE_NAME")

if [ "$SUBNET_PRIVATE_ID" == "None" ] || [ -z "$SUBNET_PRIVATE_ID" ]; then
    echo "Creando subnet privada con CIDR $SUBNET_PRIVATE_CIDR..."
    SUBNET_PRIVATE_ID=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block $SUBNET_PRIVATE_CIDR --query 'Subnet.SubnetId' --output text)
    aws ec2 create-tags --resources $SUBNET_PRIVATE_ID --tags Key=Name,Value=$SUBNET_PRIVATE_NAME
    echo -e "${GREEN}✓ Subnet privada creada: $SUBNET_PRIVATE_ID${NC}"
else
    echo -e "${GREEN}✓ Subnet privada ya existe: $SUBNET_PRIVATE_ID${NC}"
fi

###########################################
# 4. CREAR INTERNET GATEWAY
###########################################
echo -e "\n${YELLOW}[4/12] Verificando Internet Gateway...${NC}"
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
echo -e "\n${YELLOW}[5/12] Verificando Route Table Pública...${NC}"
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
echo -e "\n${YELLOW}[6/12] Verificando Route Table Privada...${NC}"
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
echo -e "\n${YELLOW}[7/12] Verificando Security Group...${NC}"
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
echo -e "\n${YELLOW}[8/12] Verificando Instancias EC2...${NC}"

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

echo -e "\n${YELLOW}Esperando a que las instancias estén en estado 'running'...${NC}"
aws ec2 wait instance-running --instance-ids $EC2_PUBLIC_ID $EC2_PRIVATE_ID
echo -e "${GREEN}✓ Instancias en estado 'running'${NC}"

###########################################
# 9. CREAR ELASTIC IP
###########################################
echo -e "\n${YELLOW}[9/12] Verificando Elastic IP...${NC}"

# Buscar EIP existente por tag
EIP_ALLOCATION_ID=$(aws ec2 describe-addresses --filters "Name=tag:Name,Values=$EIP_NAME" --query 'Addresses[0].AllocationId' --output text 2>/dev/null)

if [ "$EIP_ALLOCATION_ID" == "None" ] || [ -z "$EIP_ALLOCATION_ID" ]; then
    echo "Creando Elastic IP..."
    EIP_ALLOCATION_ID=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
    aws ec2 create-tags --resources $EIP_ALLOCATION_ID --tags Key=Name,Value=$EIP_NAME
    
    EIP_ADDRESS=$(aws ec2 describe-addresses --allocation-ids $EIP_ALLOCATION_ID --query 'Addresses[0].PublicIp' --output text)
    echo -e "${GREEN}✓ Elastic IP creada: $EIP_ADDRESS (ID: $EIP_ALLOCATION_ID)${NC}"
else
    EIP_ADDRESS=$(aws ec2 describe-addresses --allocation-ids $EIP_ALLOCATION_ID --query 'Addresses[0].PublicIp' --output text)
    echo -e "${GREEN}✓ Elastic IP ya existe: $EIP_ADDRESS (ID: $EIP_ALLOCATION_ID)${NC}"
fi

###########################################
# 10. CREAR NAT GATEWAY
###########################################
echo -e "\n${YELLOW}[10/12] Verificando NAT Gateway...${NC}"
NAT_GATEWAY_ID=$(aws ec2 describe-nat-gateways --filter "Name=tag:Name,Values=$NAT_NAME" "Name=state,Values=available,pending" --query 'NatGateways[0].NatGatewayId' --output text 2>/dev/null)

if [ "$NAT_GATEWAY_ID" == "None" ] || [ -z "$NAT_GATEWAY_ID" ]; then
    echo "Creando NAT Gateway en la subnet pública..."
    NAT_GATEWAY_ID=$(aws ec2 create-nat-gateway \
        --subnet-id $SUBNET_PUBLIC_ID \
        --allocation-id $EIP_ALLOCATION_ID \
        --tag-specifications "ResourceType=natgateway,Tags=[{Key=Name,Value=$NAT_NAME}]" \
        --query 'NatGateway.NatGatewayId' \
        --output text)
    
    echo -e "${GREEN}✓ NAT Gateway creado: $NAT_GATEWAY_ID${NC}"
    echo -e "${YELLOW}  Esperando a que el NAT Gateway esté disponible (esto puede tomar 1-2 minutos)...${NC}"
    aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GATEWAY_ID
    echo -e "${GREEN}✓ NAT Gateway disponible${NC}"
else
    echo -e "${GREEN}✓ NAT Gateway ya existe: $NAT_GATEWAY_ID${NC}"
    
    # Verificar estado
    NAT_STATE=$(aws ec2 describe-nat-gateways --nat-gateway-ids $NAT_GATEWAY_ID --query 'NatGateways[0].State' --output text)
    if [ "$NAT_STATE" == "pending" ]; then
        echo -e "${YELLOW}  NAT Gateway en estado 'pending', esperando...${NC}"
        aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GATEWAY_ID
        echo -e "${GREEN}✓ NAT Gateway disponible${NC}"
    fi
fi

###########################################
# 11. ACTUALIZAR ROUTE TABLE PRIVADA
###########################################
echo -e "\n${YELLOW}[11/12] Actualizando Route Table Privada...${NC}"

# Verificar si ya existe la ruta
ROUTE_EXISTS=$(aws ec2 describe-route-tables --route-table-ids $RTB_PRIVATE_ID --query "RouteTables[0].Routes[?DestinationCidrBlock=='0.0.0.0/0'].NatGatewayId" --output text 2>/dev/null)

if [ -z "$ROUTE_EXISTS" ] || [ "$ROUTE_EXISTS" == "None" ]; then
    echo "Agregando ruta 0.0.0.0/0 hacia NAT Gateway..."
    aws ec2 create-route --route-table-id $RTB_PRIVATE_ID --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GATEWAY_ID
    echo -e "${GREEN}✓ Ruta agregada exitosamente${NC}"
else
    echo -e "${GREEN}✓ Ruta 0.0.0.0/0 ya existe en la route table privada${NC}"
    
    # Verificar si apunta al NAT Gateway correcto
    if [ "$ROUTE_EXISTS" != "$NAT_GATEWAY_ID" ]; then
        echo -e "${YELLOW}  Actualizando ruta para apuntar al NAT Gateway correcto...${NC}"
        aws ec2 replace-route --route-table-id $RTB_PRIVATE_ID --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GATEWAY_ID
        echo -e "${GREEN}✓ Ruta actualizada${NC}"
    fi
fi

###########################################
# 12. OBTENER IPS FINALES
###########################################
echo -e "\n${YELLOW}[12/12] Obteniendo información de las instancias...${NC}"
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $EC2_PUBLIC_ID --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
PRIVATE_IP=$(aws ec2 describe-instances --instance-ids $EC2_PRIVATE_ID --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)

###########################################
# RESUMEN FINAL
###########################################
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Infraestructura completa creada exitosamente${NC}"
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
echo -e "Elastic IP:          $EIP_ADDRESS"
echo -e "Allocation ID:       $EIP_ALLOCATION_ID"
echo -e "NAT Gateway ID:      $NAT_GATEWAY_ID"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}IP Pública EC2 pública:  $PUBLIC_IP${NC}"
echo -e "${GREEN}IP Privada EC2 privada:  $PRIVATE_IP${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "${YELLOW}VERIFICACIÓN:${NC}"
echo -e "1. Conectarse a la EC2 pública mediante SSH:"
echo -e "   ${GREEN}ssh -i vockey.pem ec2-user@$PUBLIC_IP${NC}"
echo -e "2. Desde la EC2 pública, conectarse a la EC2 privada:"
echo -e "   ${GREEN}ssh ec2-user@$PRIVATE_IP${NC}"
echo -e "3. Ejecutar ping desde la EC2 privada:"
echo -e "   ${GREEN}ping -c 4 8.8.8.8${NC}"
echo -e "4. El ping debería funcionar correctamente gracias al NAT Gateway\n"

echo -e "${GREEN}✓ Script completado exitosamente${NC}\n"