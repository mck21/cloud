#!/bin/bash

################################################################################
# Script de creación de infraestructura AWS VPC
# Descripción: Crea una VPC con subredes públicas/privadas, NAT Gateway,
#              tablas de ruteo, NACLs, Security Groups y lanza 2 instancias EC2.
# Recursos: Todos llevan sufijo -mck21 y tag key=tag value=mck21
################################################################################

set -e  # Salir si hay error

################################################################################
# VARIABLES DE CONFIGURACIÓN
################################################################################
TAG_KEY="tag"
TAG_VALUE="mck21"
SUFFIX="-mck21"
VPC_CIDR="10.10.0.0/16"
PUB_SUB1_CIDR="10.10.1.0/24"
PUB_SUB2_CIDR="10.10.2.0/24"
PRIV_SUB1_CIDR="10.10.3.0/24"
PRIV_SUB2_CIDR="10.10.4.0/24"
REGION="us-east-1"
KEY_NAME="vockey"
AMI_ID="ami-0ecb62995f68bb549"

# Zonas de disponibilidad
AZ1="${REGION}a"
AZ2="${REGION}b"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

################################################################################
# FUNCIONES AUXILIARES
################################################################################

# Función para imprimir mensajes con formato
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Función para verificar si un recurso existe
resource_exists() {
    local resource_id=$1
    if [[ -n "$resource_id" && "$resource_id" != "None" ]]; then
        return 0
    else
        return 1
    fi
}

################################################################################
# 1. CREAR VPC
################################################################################
print_message "$YELLOW" "\n=== CREANDO VPC ==="

# Verificar si existe VPC con el tag
EXISTING_VPC=$(aws ec2 describe-vpcs \
    --filters "Name=tag:$TAG_KEY,Values=$TAG_VALUE" \
    --query 'Vpcs[0].VpcId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_VPC"; then
    print_message "$GREEN" "✓ VPC ya existe: $EXISTING_VPC"
    VPC_ID=$EXISTING_VPC
else
    VPC_ID=$(aws ec2 create-vpc \
        --cidr-block $VPC_CIDR \
        --tag-specifications "ResourceType=vpc,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=vpc$SUFFIX}]" \
        --query 'Vpc.VpcId' \
        --output text)
    
    # Habilitar DNS
    aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames
    aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support
    
    print_message "$GREEN" "✓ VPC creada: $VPC_ID"
fi

################################################################################
# 2. CREAR SUBREDES
################################################################################
print_message "$YELLOW" "\n=== CREANDO SUBREDES ==="

# Subred pública 1
EXISTING_PUB_SUB1=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=public-subnet-1$SUFFIX" \
    --query 'Subnets[0].SubnetId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_PUB_SUB1"; then
    print_message "$GREEN" "✓ Subred pública 1 ya existe: $EXISTING_PUB_SUB1"
    PUB_SUB1=$EXISTING_PUB_SUB1
else
    PUB_SUB1=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block $PUB_SUB1_CIDR \
        --availability-zone $AZ1 \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=public-subnet-1$SUFFIX}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    
    # Auto-asignar IP pública
    aws ec2 modify-subnet-attribute --subnet-id $PUB_SUB1 --map-public-ip-on-launch
    print_message "$GREEN" "✓ Subred pública 1 creada: $PUB_SUB1 ($PUB_SUB1_CIDR - $AZ1)"
fi

# Subred pública 2
EXISTING_PUB_SUB2=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=public-subnet-2$SUFFIX" \
    --query 'Subnets[0].SubnetId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_PUB_SUB2"; then
    print_message "$GREEN" "✓ Subred pública 2 ya existe: $EXISTING_PUB_SUB2"
    PUB_SUB2=$EXISTING_PUB_SUB2
else
    PUB_SUB2=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block $PUB_SUB2_CIDR \
        --availability-zone $AZ2 \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=public-subnet-2$SUFFIX}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    
    aws ec2 modify-subnet-attribute --subnet-id $PUB_SUB2 --map-public-ip-on-launch
    print_message "$GREEN" "✓ Subred pública 2 creada: $PUB_SUB2 ($PUB_SUB2_CIDR - $AZ2)"
fi

# Subred privada 1
EXISTING_PRIV_SUB1=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=private-subnet-1$SUFFIX" \
    --query 'Subnets[0].SubnetId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_PRIV_SUB1"; then
    print_message "$GREEN" "✓ Subred privada 1 ya existe: $EXISTING_PRIV_SUB1"
    PRIV_SUB1=$EXISTING_PRIV_SUB1
else
    PRIV_SUB1=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block $PRIV_SUB1_CIDR \
        --availability-zone $AZ1 \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=private-subnet-1$SUFFIX}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    print_message "$GREEN" "✓ Subred privada 1 creada: $PRIV_SUB1 ($PRIV_SUB1_CIDR - $AZ1)"
fi

# Subred privada 2
EXISTING_PRIV_SUB2=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=private-subnet-2$SUFFIX" \
    --query 'Subnets[0].SubnetId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_PRIV_SUB2"; then
    print_message "$GREEN" "✓ Subred privada 2 ya existe: $EXISTING_PRIV_SUB2"
    PRIV_SUB2=$EXISTING_PRIV_SUB2
else
    PRIV_SUB2=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block $PRIV_SUB2_CIDR \
        --availability-zone $AZ2 \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=private-subnet-2$SUFFIX}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    print_message "$GREEN" "✓ Subred privada 2 creada: $PRIV_SUB2 ($PRIV_SUB2_CIDR - $AZ2)"
fi

################################################################################
# 3. CREAR Y ASOCIAR INTERNET GATEWAY
################################################################################
print_message "$YELLOW" "\n=== CONFIGURANDO INTERNET GATEWAY ==="

# Verificar si existe IGW asociado a la VPC
EXISTING_IGW=$(aws ec2 describe-internet-gateways \
    --filters "Name=attachment.vpc-id,Values=$VPC_ID" \
    --query 'InternetGateways[0].InternetGatewayId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_IGW"; then
    print_message "$GREEN" "✓ Internet Gateway ya existe y está asociado: $EXISTING_IGW"
    IGW=$EXISTING_IGW
else
    IGW=$(aws ec2 create-internet-gateway \
        --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=igw$SUFFIX}]" \
        --query 'InternetGateway.InternetGatewayId' \
        --output text)
    
    # Asociar a VPC
    aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW
    print_message "$GREEN" "✓ Internet Gateway creado y asociado: $IGW"
fi

################################################################################
# 4. CREAR ELASTIC IP Y NAT GATEWAY
################################################################################
print_message "$YELLOW" "\n=== CONFIGURANDO NAT GATEWAY ==="

# Verificar si existe NAT Gateway
EXISTING_NAT=$(aws ec2 describe-nat-gateways \
    --filter "Name=vpc-id,Values=$VPC_ID" "Name=state,Values=available,pending" \
    --query 'NatGateways[0].NatGatewayId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_NAT"; then
    print_message "$GREEN" "✓ NAT Gateway ya existe: $EXISTING_NAT"
    NAT=$EXISTING_NAT
else
    # Crear Elastic IP
    EIP=$(aws ec2 allocate-address \
        --domain vpc \
        --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=eip$SUFFIX}]" \
        --query 'AllocationId' \
        --output text)
    print_message "$GREEN" "✓ Elastic IP creada: $EIP"
    
    # Crear NAT Gateway
    NAT=$(aws ec2 create-nat-gateway \
        --subnet-id $PUB_SUB1 \
        --allocation-id $EIP \
        --tag-specifications "ResourceType=natgateway,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=ngw$SUFFIX}]" \
        --query 'NatGateway.NatGatewayId' \
        --output text)
    
    print_message "$YELLOW" "⏳ Esperando a que NAT Gateway esté disponible..."
    aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT
    print_message "$GREEN" "✓ NAT Gateway creado y disponible: $NAT"
fi

################################################################################
# 5. CREAR TABLAS DE RUTEO
################################################################################
print_message "$YELLOW" "\n=== CONFIGURANDO TABLAS DE RUTEO ==="

# Tabla de ruteo pública 1
EXISTING_RT_PUB1=$(aws ec2 describe-route-tables \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=public-rt-1$SUFFIX" \
    --query 'RouteTables[0].RouteTableId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_RT_PUB1"; then
    print_message "$GREEN" "✓ Tabla de ruteo pública 1 ya existe: $EXISTING_RT_PUB1"
    RT_PUB1=$EXISTING_RT_PUB1
else
    RT_PUB1=$(aws ec2 create-route-table \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=route-table,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=public-rt-1$SUFFIX}]" \
        --query 'RouteTable.RouteTableId' \
        --output text)
    
    # Añadir ruta a Internet Gateway
    aws ec2 create-route --route-table-id $RT_PUB1 --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW
    
    # Asociar a subred pública 1
    aws ec2 associate-route-table --subnet-id $PUB_SUB1 --route-table-id $RT_PUB1 > /dev/null
    print_message "$GREEN" "✓ Tabla de ruteo pública 1 creada y asociada: $RT_PUB1"
fi

# Tabla de ruteo pública 2
EXISTING_RT_PUB2=$(aws ec2 describe-route-tables \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=public-rt-2$SUFFIX" \
    --query 'RouteTables[0].RouteTableId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_RT_PUB2"; then
    print_message "$GREEN" "✓ Tabla de ruteo pública 2 ya existe: $EXISTING_RT_PUB2"
    RT_PUB2=$EXISTING_RT_PUB2
else
    RT_PUB2=$(aws ec2 create-route-table \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=route-table,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=public-rt-2$SUFFIX}]" \
        --query 'RouteTable.RouteTableId' \
        --output text)
    
    aws ec2 create-route --route-table-id $RT_PUB2 --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW
    aws ec2 associate-route-table --subnet-id $PUB_SUB2 --route-table-id $RT_PUB2 > /dev/null
    print_message "$GREEN" "✓ Tabla de ruteo pública 2 creada y asociada: $RT_PUB2"
fi

# Tabla de ruteo privada 1
EXISTING_RT_PRIV1=$(aws ec2 describe-route-tables \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=private-rt-1$SUFFIX" \
    --query 'RouteTables[0].RouteTableId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_RT_PRIV1"; then
    print_message "$GREEN" "✓ Tabla de ruteo privada 1 ya existe: $EXISTING_RT_PRIV1"
    RT_PRIV1=$EXISTING_RT_PRIV1
else
    RT_PRIV1=$(aws ec2 create-route-table \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=route-table,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=private-rt-1$SUFFIX}]" \
        --query 'RouteTable.RouteTableId' \
        --output text)
    
    # Añadir ruta a NAT Gateway
    aws ec2 create-route --route-table-id $RT_PRIV1 --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT
    
    # Asociar a subred privada 1
    aws ec2 associate-route-table --subnet-id $PRIV_SUB1 --route-table-id $RT_PRIV1 > /dev/null
    print_message "$GREEN" "✓ Tabla de ruteo privada 1 creada y asociada: $RT_PRIV1"
fi

# Tabla de ruteo privada 2
EXISTING_RT_PRIV2=$(aws ec2 describe-route-tables \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=private-rt-2$SUFFIX" \
    --query 'RouteTables[0].RouteTableId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_RT_PRIV2"; then
    print_message "$GREEN" "✓ Tabla de ruteo privada 2 ya existe: $EXISTING_RT_PRIV2"
    RT_PRIV2=$EXISTING_RT_PRIV2
else
    RT_PRIV2=$(aws ec2 create-route-table \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=route-table,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=private-rt-2$SUFFIX}]" \
        --query 'RouteTable.RouteTableId' \
        --output text)
    
    aws ec2 create-route --route-table-id $RT_PRIV2 --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT
    aws ec2 associate-route-table --subnet-id $PRIV_SUB2 --route-table-id $RT_PRIV2 > /dev/null
    print_message "$GREEN" "✓ Tabla de ruteo privada 2 creada y asociada: $RT_PRIV2"
fi

################################################################################
# 6. CONFIGURAR NETWORK ACLs
################################################################################
print_message "$YELLOW" "\n=== CONFIGURANDO NETWORK ACLs ==="

# NACL para subredes públicas
EXISTING_NACL_PUB=$(aws ec2 describe-network-acls \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=public-nacl$SUFFIX" \
    --query 'NetworkAcls[0].NetworkAclId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_NACL_PUB"; then
    print_message "$GREEN" "✓ NACL pública ya existe: $EXISTING_NACL_PUB"
    NACL_PUB=$EXISTING_NACL_PUB
else
    NACL_PUB=$(aws ec2 create-network-acl \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=network-acl,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=public-nacl$SUFFIX}]" \
        --query 'NetworkAcl.NetworkAclId' \
        --output text)
    
    # Reglas de entrada (Ingress) - Solo HTTP, HTTPS, SSH y puertos efímeros
    aws ec2 create-network-acl-entry --network-acl-id $NACL_PUB --ingress --rule-number 100 --protocol tcp --port-range From=80,To=80 --cidr-block 0.0.0.0/0 --rule-action allow
    aws ec2 create-network-acl-entry --network-acl-id $NACL_PUB --ingress --rule-number 110 --protocol tcp --port-range From=443,To=443 --cidr-block 0.0.0.0/0 --rule-action allow
    aws ec2 create-network-acl-entry --network-acl-id $NACL_PUB --ingress --rule-number 120 --protocol tcp --port-range From=22,To=22 --cidr-block 0.0.0.0/0 --rule-action allow
    aws ec2 create-network-acl-entry --network-acl-id $NACL_PUB --ingress --rule-number 130 --protocol tcp --port-range From=1024,To=65535 --cidr-block 0.0.0.0/0 --rule-action allow
    
    # Reglas de salida (Egress) - Permitir todo el tráfico saliente
    aws ec2 create-network-acl-entry --network-acl-id $NACL_PUB --egress --rule-number 100 --protocol -1 --cidr-block 0.0.0.0/0 --rule-action allow
    
    # Asociar a subredes públicas
    ASSOC_PUB1=$(aws ec2 describe-network-acls \
        --filters "Name=association.subnet-id,Values=$PUB_SUB1" \
        --query 'NetworkAcls[0].Associations[?SubnetId==`'$PUB_SUB1'`].NetworkAclAssociationId' \
        --output text)
    aws ec2 replace-network-acl-association --association-id $ASSOC_PUB1 --network-acl-id $NACL_PUB > /dev/null
    
    ASSOC_PUB2=$(aws ec2 describe-network-acls \
        --filters "Name=association.subnet-id,Values=$PUB_SUB2" \
        --query 'NetworkAcls[0].Associations[?SubnetId==`'$PUB_SUB2'`].NetworkAclAssociationId' \
        --output text)
    aws ec2 replace-network-acl-association --association-id $ASSOC_PUB2 --network-acl-id $NACL_PUB > /dev/null
    
    print_message "$GREEN" "✓ NACL pública creada y asociada: $NACL_PUB"
fi

# NACL para subredes privadas
EXISTING_NACL_PRIV=$(aws ec2 describe-network-acls \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=private-nacl$SUFFIX" \
    --query 'NetworkAcls[0].NetworkAclId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_NACL_PRIV"; then
    print_message "$GREEN" "✓ NACL privada ya existe: $EXISTING_NACL_PRIV"
    NACL_PRIV=$EXISTING_NACL_PRIV
else
    NACL_PRIV=$(aws ec2 create-network-acl \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=network-acl,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=private-nacl$SUFFIX}]" \
        --query 'NetworkAcl.NetworkAclId' \
        --output text)
    
    # Reglas de entrada (Ingress) - Solo tráfico desde la VPC interna
    aws ec2 create-network-acl-entry --network-acl-id $NACL_PRIV --ingress --rule-number 100 --protocol -1 --cidr-block 10.10.0.0/16 --rule-action allow
    
    # Reglas de salida (Egress) - Permitir todo el tráfico saliente
    aws ec2 create-network-acl-entry --network-acl-id $NACL_PRIV --egress --rule-number 100 --protocol -1 --cidr-block 0.0.0.0/0 --rule-action allow
    
    # Asociar a subredes privadas
    ASSOC_PRIV1=$(aws ec2 describe-network-acls \
        --filters "Name=association.subnet-id,Values=$PRIV_SUB1" \
        --query 'NetworkAcls[0].Associations[?SubnetId==`'$PRIV_SUB1'`].NetworkAclAssociationId' \
        --output text)
    aws ec2 replace-network-acl-association --association-id $ASSOC_PRIV1 --network-acl-id $NACL_PRIV > /dev/null
    
    ASSOC_PRIV2=$(aws ec2 describe-network-acls \
        --filters "Name=association.subnet-id,Values=$PRIV_SUB2" \
        --query 'NetworkAcls[0].Associations[?SubnetId==`'$PRIV_SUB2'`].NetworkAclAssociationId' \
        --output text)
    aws ec2 replace-network-acl-association --association-id $ASSOC_PRIV2 --network-acl-id $NACL_PRIV > /dev/null
    
    print_message "$GREEN" "✓ NACL privada creada y asociada: $NACL_PRIV"
fi

################################################################################
# 7. CREAR SECURITY GROUPS
################################################################################
print_message "$YELLOW" "\n=== CONFIGURANDO SECURITY GROUPS ==="

# Security Group público (Bastion)
EXISTING_SG_PUB=$(aws ec2 describe-security-groups \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=public-sg$SUFFIX" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_SG_PUB"; then
    print_message "$GREEN" "✓ Security Group público ya existe: $EXISTING_SG_PUB"
    SG_PUB=$EXISTING_SG_PUB
else
    SG_PUB=$(aws ec2 create-security-group \
        --group-name "public-sg$SUFFIX" \
        --description "Security Group for public subnet - Bastion" \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=security-group,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=public-sg$SUFFIX}]" \
        --query 'GroupId' \
        --output text)
    
    # Permitir SSH desde cualquier lugar
    aws ec2 authorize-security-group-ingress --group-id $SG_PUB --protocol tcp --port 22 --cidr 0.0.0.0/0
    
    # Permitir HTTP desde cualquier lugar
    aws ec2 authorize-security-group-ingress --group-id $SG_PUB --protocol tcp --port 80 --cidr 0.0.0.0/0
    
    print_message "$GREEN" "✓ Security Group público creado: $SG_PUB"
fi

# Security Group privado (Solo acceso desde SG público)
EXISTING_SG_PRIV=$(aws ec2 describe-security-groups \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=private-sg$SUFFIX" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_SG_PRIV"; then
    print_message "$GREEN" "✓ Security Group privado ya existe: $EXISTING_SG_PRIV"
    SG_PRIV=$EXISTING_SG_PRIV
else
    SG_PRIV=$(aws ec2 create-security-group \
        --group-name "private-sg$SUFFIX" \
        --description "Security Group for private subnet - Only accessible from public SG" \
        --vpc-id $VPC_ID \
        --tag-specifications "ResourceType=security-group,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=private-sg$SUFFIX}]" \
        --query 'GroupId' \
        --output text)
    
    # Permitir SSH SOLO desde el Security Group público (encadenamiento)
    aws ec2 authorize-security-group-ingress --group-id $SG_PRIV --protocol tcp --port 22 --source-group $SG_PUB > /dev/null
    
    # Permitir ICMP desde el Security Group público (para pruebas de ping)
    aws ec2 authorize-security-group-ingress --group-id $SG_PRIV --protocol icmp --port -1 --source-group $SG_PUB > /dev/null
    
    print_message "$GREEN" "✓ Security Group privado creado: $SG_PRIV"
fi

################################################################################
# 8. LANZAR INSTANCIAS EC2 DE PRUEBA
################################################################################
print_message "$YELLOW" "\n=== LANZANDO INSTANCIAS EC2 DE PRUEBA ==="

# Pequeña pausa para asegurar la propagación de las tablas de ruteo
print_message "$YELLOW" "⏳ Pausa de 10 segundos para propagación de rutas..."
sleep 10

# Instancia Bastion (pública)
EXISTING_BASTION=$(aws ec2 describe-instances \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=bastion-public-mck21" "Name=instance-state-name,Values=pending,running" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_BASTION"; then
    print_message "$GREEN" "✓ Instancia Bastion ya existe: $EXISTING_BASTION"
    BASTION_ID=$EXISTING_BASTION
else
    BASTION_OUTPUT=$(aws ec2 run-instances \
        --image-id $AMI_ID \
        --instance-type t2.micro \
        --key-name $KEY_NAME \
        --subnet-id $PUB_SUB1 \
        --security-group-ids $SG_PUB \
        --associate-public-ip-address \
        --tag-specifications "ResourceType=instance,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=bastion-public-mck21}]" \
        --query 'Instances[0].[InstanceId, PublicIpAddress]' \
        --output text)
    
    BASTION_ID=$(echo $BASTION_OUTPUT | awk '{print $1}')
    BASTION_IP=$(echo $BASTION_OUTPUT | awk '{print $2}')
    print_message "$GREEN" "✓ Instancia Bastion lanzada: $BASTION_ID (IP: $BASTION_IP)"
fi


# Instancia Privada
EXISTING_PRIVATE_SERVER=$(aws ec2 describe-instances \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=server-private-mck21" "Name=instance-state-name,Values=pending,running" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text 2>/dev/null)

if resource_exists "$EXISTING_PRIVATE_SERVER"; then
    print_message "$GREEN" "✓ Instancia Privada ya existe: $EXISTING_PRIVATE_SERVER"
    PRIVATE_SERVER_ID=$EXISTING_PRIVATE_SERVER
else
    PRIVATE_SERVER_ID=$(aws ec2 run-instances \
        --image-id $AMI_ID \
        --instance-type t2.micro \
        --key-name $KEY_NAME \
        --subnet-id $PRIV_SUB1 \
        --security-group-ids $SG_PRIV \
        --tag-specifications "ResourceType=instance,Tags=[{Key=$TAG_KEY,Value=$TAG_VALUE},{Key=Name,Value=server-private-mck21}]" \
        --query 'Instances[0].InstanceId' \
        --output text)
    
    print_message "$GREEN" "✓ Instancia Privada lanzada: $PRIVATE_SERVER_ID"
fi

################################################################################
# 9. RESUMEN DE RECURSOS CREADOS
################################################################################
print_message "$GREEN" "\n╔════════════════════════════════════════════════════════════════╗"
print_message "$GREEN" "║          INFRAESTRUCTURA AWS CREADA EXITOSAMENTE              ║"
print_message "$GREEN" "╚════════════════════════════════════════════════════════════════╝"

echo ""
echo "┌─────────────────────────────────────────────────────────────────┐"
echo "│ VPC Y CONECTIVIDAD                                              │"
echo "├─────────────────────────────────────────────────────────────────┤"
echo "│ VPC ID:              $VPC_ID"
echo "│ VPC CIDR:            $VPC_CIDR"
echo "│ Internet Gateway:    $IGW"
echo "│ NAT Gateway:         $NAT"
echo "└─────────────────────────────────────────────────────────────────┘"

echo ""
echo "┌─────────────────────────────────────────────────────────────────┐"
echo "│ SUBREDES                                                        │"
echo "├─────────────────────────────────────────────────────────────────┤"
echo "│ Subred Pública 1:    $PUB_SUB1 ($PUB_SUB1_CIDR - $AZ1)"
echo "│ Subred Privada 1:    $PRIV_SUB1 ($PRIV_SUB1_CIDR - $AZ1)       │"
echo "└─────────────────────────────────────────────────────────────────┘"

echo ""
echo "┌─────────────────────────────────────────────────────────────────┐"
echo "│ TABLAS DE RUTEO                                                 │"
echo "├─────────────────────────────────────────────────────────────────┤"
echo "│ RT Pública 1:        $RT_PUB1 → IGW                            │"
echo "│ RT Privada 1:        $RT_PRIV1 → NAT                           │"
echo "└─────────────────────────────────────────────────────────────────┘"

echo ""
echo "┌─────────────────────────────────────────────────────────────────┐"
echo "│ INSTANCIAS DE PRUEBA LANZADAS                                   │"
echo "├─────────────────────────────────────────────────────────────────┤"
echo "│ Bastion ID:          ${BASTION_ID:-N/A}"
echo "│ Bastion IP Pública:  ${BASTION_IP:-N/A}"
echo "│ Servidor Privado ID: ${PRIVATE_SERVER_ID:-N/A}"
echo "└─────────────────────────────────────────────────────────────────┘"

echo ""
print_message "$YELLOW" "════════════════════════════════════════════════════════════════"
print_message "$YELLOW" "  INSTRUCCIONES DE ACCESO"
print_message "$YELLOW" "════════════════════════════════════════════════════════════════"
echo ""
echo "Para conectarte al Bastion, usa tu clave ($KEY_NAME) y la IP Pública:"
echo "ssh -i $KEY_NAME.pem ec2-user@${BASTION_IP:-PUBLIC_IP_DEL_BASTION}"
echo ""
echo "Una vez en el Bastion, puedes acceder a la instancia privada usando el reenvío de agente (Agent Forwarding) o copiando tu clave a Bastion:"
echo "ssh ec2-user@<IP_PRIVADA_DEL_SERVER_PRIVADO>"
echo ""

print_message "$GREEN" "✓ Script completado exitosamente"