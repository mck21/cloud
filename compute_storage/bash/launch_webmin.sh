#!/bin/bash

# Variables
AMI_ID="ami-0ecb62995f68bb549"
INSTANCE_TYPE="t3.micro"
KEY_NAME="mi-par"
SECURITY_GROUP_NAME="gs-webmin"
USER_DATA_FILE="install_webmin.txt"

# Convertir User Data a LF por si viene de Windows
command -v dos2unix >/dev/null 2>&1 && dos2unix "$USER_DATA_FILE" 2>/dev/null

# Crear Key Pair si no existe
KEY_FILE="./$KEY_NAME.pem"
if [ ! -f "$KEY_FILE" ]; then
    echo "Creando Key Pair '$KEY_NAME'..."
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --query 'KeyMaterial' --output text > "$KEY_FILE"
    chmod 400 "$KEY_FILE"
    echo "Key Pair creado y guardado en $KEY_FILE"
else
    echo "Key Pair ya existe en $KEY_FILE, se usará ese"
fi

# Crear grupo de seguridad si no existe
echo "Creando grupo de seguridad..."
SG_ID=$(aws ec2 describe-security-groups \
    --group-names "$SECURITY_GROUP_NAME" \
    --query "SecurityGroups[0].GroupId" \
    --output text 2>/dev/null)

if [ -z "$SG_ID" ] || [ "$SG_ID" = "None" ]; then
    SG_ID=$(aws ec2 create-security-group \
        --group-name "$SECURITY_GROUP_NAME" \
        --description "Grupo de seguridad para Webmin" \
        --query "GroupId" --output text)
    echo "Grupo de seguridad creado: $SG_ID"
else
    echo "Grupo de seguridad ya existe: $SG_ID"
fi

# Abrir puertos necesarios: SSH (22) y Webmin (10000)
echo "Configurando reglas del grupo de seguridad..."
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 22 --cidr 0.0.0.0/0 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 10000 --cidr 0.0.0.0/0 2>/dev/null || true

# Lanzar instancia
echo "Lanzando instancia EC2 con Webmin..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --user-data file://$USER_DATA_FILE \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ec2-webmin2}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

if [ -z "$INSTANCE_ID" ] || [ "$INSTANCE_ID" = "None" ]; then
    echo "Error: no se pudo lanzar la instancia. Revisa AWS CLI y tus credenciales."
    exit 1
fi

echo "Instancia creada con ID: $INSTANCE_ID"

# Esperar a que esté en ejecución
echo "Esperando a que la instancia esté en estado 'running'..."
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"

# Obtener IP pública
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "Instancia lanzada correctamente."
echo "Conéctate a Webmin en: https://$PUBLIC_IP:10000"
echo "Usuario: root"
echo "Contraseña: Webmin123!"
echo "Si quieres conectarte vía SSH: ssh -i $KEY_FILE ubuntu@$PUBLIC_IP"
