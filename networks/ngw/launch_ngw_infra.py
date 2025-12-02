#!/usr/bin/env python3

"""
Script: Crear VPC con tag mck21
Paso 1: VPC básica con DNS habilitado
"""

import boto3
import sys
from botocore.exceptions import ClientError

# Colores para terminal
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # Sin color

# Configuración
VPC_CIDR = "172.16.0.0/16"
VPC_NAME = "vpc-mck21"
TAG_KEY = "tag"
TAG_VALUE = "mck21"

def print_color(color, message):
    """Imprime mensaje con color"""
    print(f"{color}{message}{Colors.NC}")

def get_vpc_by_tag(ec2_client, name):
    """Busca VPC por tag Name"""
    try:
        response = ec2_client.describe_vpcs(
            Filters=[
                {'Name': 'tag:Name', 'Values': [name]},
                {'Name': f'tag:{TAG_KEY}', 'Values': [TAG_VALUE]}
            ]
        )
        if response['Vpcs']:
            return response['Vpcs'][0]['VpcId']
        return None
    except ClientError as e:
        print_color(Colors.RED, f"Error buscando VPC: {e}")
        return None

def create_vpc(ec2_client):
    """Crea la VPC con configuración DNS"""
    print_color(Colors.YELLOW, "[1/1] Verificando VPC...")
    
    # Verificar si ya existe
    vpc_id = get_vpc_by_tag(ec2_client, VPC_NAME)
    
    if vpc_id:
        print_color(Colors.GREEN, f"✓ VPC ya existe: {vpc_id}")
        return vpc_id
    
    # Crear VPC
    try:
        print(f"Creando VPC con CIDR {VPC_CIDR}...")
        response = ec2_client.create_vpc(
            CidrBlock=VPC_CIDR,
            TagSpecifications=[
                {
                    'ResourceType': 'vpc',
                    'Tags': [
                        {'Key': 'Name', 'Value': VPC_NAME},
                        {'Key': TAG_KEY, 'Value': TAG_VALUE}
                    ]
                }
            ]
        )
        vpc_id = response['Vpc']['VpcId']
        
        # Habilitar DNS support
        ec2_client.modify_vpc_attribute(
            VpcId=vpc_id,
            EnableDnsSupport={'Value': True}
        )
        
        # Habilitar DNS hostnames
        ec2_client.modify_vpc_attribute(
            VpcId=vpc_id,
            EnableDnsHostnames={'Value': True}
        )
        
        print_color(Colors.GREEN, f"✓ VPC creada: {vpc_id}")
        return vpc_id
        
    except ClientError as e:
        print_color(Colors.RED, f"✗ Error creando VPC: {e}")
        sys.exit(1)

def main():
    """Función principal"""
    print_color(Colors.GREEN, "=== Iniciando creación de VPC ===\n")
    
    # Crear cliente EC2
    ec2_client = boto3.client('ec2')
    
    # Crear VPC
    vpc_id = create_vpc(ec2_client)
    
    # Resumen
    print_color(Colors.GREEN, "\n========================================")
    print_color(Colors.GREEN, "  VPC creada exitosamente")
    print_color(Colors.GREEN, "========================================")
    print(f"VPC ID: {vpc_id}")
    print(f"CIDR:   {VPC_CIDR}")
    print(f"Tag:    {TAG_KEY}={TAG_VALUE}")
    print_color(Colors.GREEN, "========================================\n")
    
    print_color(Colors.GREEN, "✓ Script completado exitosamente\n")

if __name__ == "__main__":
    main()