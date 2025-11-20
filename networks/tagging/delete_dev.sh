#!/bin/bash

# Obtén los IDs de las VPCs que tienen la etiqueta entorno=prueba
VPC_IDS=$(aws ec2 describe-vpcs \
    --filters "Name=tag:entorno,Values=prueba" \
    --query "Vpcs[*].VpcId" \
    --output text)

# Recorre cada ID de VPC y elimínala
for VPC_ID in $VPC_IDS; do
    echo "Eliminando VPC $VPC_ID..."
    
    # Eliminar instancias EC2 con tag entorno=prueba PRIMERO
    echo " Buscando instancias EC2 con tag entorno=prueba..."
    INSTANCE_IDS=$(aws ec2 describe-instances \
        --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:entorno,Values=prueba" \
        --query "Reservations[*].Instances[*].InstanceId" \
        --output text)
    
    if [ -n "$INSTANCE_IDS" ]; then
        echo " Deteniendo instancias EC2..."
        aws ec2 terminate-instances --instance-ids $INSTANCE_IDS
        echo " Instancias EC2 $INSTANCE_IDS marcadas para eliminación."
        
        # Esperar a que las instancias se terminen
        echo " Esperando a que las instancias se terminen..."
        aws ec2 wait instance-terminated --instance-ids $INSTANCE_IDS
        echo " Instancias EC2 eliminadas."
    else
        echo " No hay instancias EC2 con tag entorno=prueba."
    fi
    
    # Ahora eliminar subredes
    SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text)
    for SUBNET_ID in $SUBNET_IDS; do
        aws ec2 delete-subnet --subnet-id $SUBNET_ID
        echo " Subnet $SUBNET_ID eliminada."
    done
    
    # Elimina la VPC
    aws ec2 delete-vpc --vpc-id $VPC_ID
    echo "VPC $VPC_ID eliminada."
done