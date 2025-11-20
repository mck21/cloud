#!/bin/bash

###########################################
# Script 2: Crear NAT Gateway y configurar routing
# - Elastic IP
# - NAT Gateway en subnet pública
# - Actualizar Route Table privada
###########################################

set -e

# Colores para logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # Sin color

# Variables de configuración
EIP_NAME="eip-mck21"
NAT_NAME="nat-mck21"
SUBNET_PUBLIC_NAME="subnet-public-mck21"
RTB_PRIVATE_NAME="rtb-private-mck21"

echo -e "${GREEN}=== Iniciando creación de NAT Gateway ===${NC}\n"

# Función para obtener el ID de un recurso por su nombre
get_resource_id() {
    local resource_type=$1
    local name=$2
    aws ec2 describe-tags --filters "Name=key,Values=Name" "Name=value,Values=$name" "Name=resource-type,Values=$resource_type" --query 'Tags[0].ResourceId' --output text 2>/dev/null
}

###########################################
# 1. OBTENER SUBNET PÚBLICA
###########################################
echo -e "${YELLOW}[1/4] Obteniendo Subnet Pública...${NC}"
SUBNET_PUBLIC_ID=$(get_resource_id "subnet" "$SUBNET_PUBLIC_NAME")

if [ "$SUBNET_PUBLIC_ID" == "None" ] || [ -z "$SUBNET_PUBLIC_ID" ]; then
    echo -e "${RED}✗ Error: No se encontró la subnet pública '$SUBNET_PUBLIC_NAME'${NC}"
    echo -e "${RED}  Asegúrate de haber ejecutado el Script 1 primero${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Subnet pública encontrada: $SUBNET_PUBLIC_ID${NC}"

###########################################
# 2. OBTENER ROUTE TABLE PRIVADA
###########################################
echo -e "\n${YELLOW}[2/4] Obteniendo Route Table Privada...${NC}"
RTB_PRIVATE_ID=$(get_resource_id "route-table" "$RTB_PRIVATE_NAME")

if [ "$RTB_PRIVATE_ID" == "None" ] || [ -z "$RTB_PRIVATE_ID" ]; then
    echo -e "${RED}✗ Error: No se encontró la route table privada '$RTB_PRIVATE_NAME'${NC}"
    echo -e "${RED}  Asegúrate de haber ejecutado el Script 1 primero${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Route Table privada encontrada: $RTB_PRIVATE_ID${NC}"

###########################################
# 3. CREAR ELASTIC IP
###########################################
echo -e "\n${YELLOW}[3/4] Verificando Elastic IP...${NC}"

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
# 4. CREAR NAT GATEWAY
###########################################
echo -e "\n${YELLOW}[4/4] Verificando NAT Gateway...${NC}"
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
# 5. ACTUALIZAR ROUTE TABLE PRIVADA
###########################################
echo -e "\n${YELLOW}[5/5] Actualizando Route Table Privada...${NC}"

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
# RESUMEN FINAL
###########################################
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  NAT Gateway configurado exitosamente${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Elastic IP:          $EIP_ADDRESS"
echo -e "Allocation ID:       $EIP_ALLOCATION_ID"
echo -e "NAT Gateway ID:      $NAT_GATEWAY_ID"
echo -e "Subnet Pública:      $SUBNET_PUBLIC_ID"
echo -e "Route Table Privada: $RTB_PRIVATE_ID"
echo -e "${GREEN}========================================${NC}\n"

echo -e "${YELLOW}VERIFICACIÓN:${NC}"
echo -e "1. Conectarse a la EC2 pública mediante SSH"
echo -e "2. Desde la EC2 pública, conectarse a la EC2 privada"
echo -e "3. Ejecutar ping desde la EC2 privada"
echo -e "4. El ping ahora debería funcionar correctamente\n"

echo -e "${GREEN}✓ Script completado exitosamente${NC}\n"