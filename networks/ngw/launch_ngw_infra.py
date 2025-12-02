#!/usr/bin/env python3

"""
Script: Crear VPC con subred pública y privada
Paso 2: VPC + DNS + subnets
"""

import boto3
import sys
from botocore.exceptions import ClientError


class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'


# Configuración general
VPC_CIDR = "172.16.0.0/16"
VPC_NAME = "vpc-mck21"
TAG_KEY = "tag"
TAG_VALUE = "mck21"

PUBLIC_SUBNET_CIDR = "172.16.1.0/24"
PRIVATE_SUBNET_CIDR = "172.16.2.0/24"

PUBLIC_SUBNET_NAME = "public-subnet-mck21"
PRIVATE_SUBNET_NAME = "private-subnet-mck21"


def print_color(color, msg):
    print(f"{color}{msg}{Colors.NC}")


# ------------------------------
# Helpers
# ------------------------------
def find_subnet(ec2, cidr, vpc_id):
    """Busca una subnet por CIDR y VPC"""
    try:
        response = ec2.describe_subnets(
            Filters=[
                {"Name": "cidr-block", "Values": [cidr]},
                {"Name": "vpc-id", "Values": [vpc_id]},
                {"Name": f"tag:{TAG_KEY}", "Values": [TAG_VALUE]},
            ]
        )
        if response["Subnets"]:
            return response["Subnets"][0]["SubnetId"]
        return None
    except ClientError as e:
        print_color(Colors.RED, f"Error buscando subnet: {e}")
        return None


def create_subnet(ec2, vpc_id, cidr, name):
    """Crea subred si no existe"""
    print_color(Colors.YELLOW, f"Creando subnet {name} ({cidr})...")

    existing_id = find_subnet(ec2, cidr, vpc_id)
    if existing_id:
        print_color(Colors.GREEN, f"✓ Subnet {name} ya existe: {existing_id}")
        return existing_id

    try:
        response = ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock=cidr,
            TagSpecifications=[
                {
                    "ResourceType": "subnet",
                    "Tags": [
                        {"Key": "Name", "Value": name},
                        {"Key": TAG_KEY, "Value": TAG_VALUE},
                    ],
                }
            ],
        )
        subnet_id = response["Subnet"]["SubnetId"]
        print_color(Colors.GREEN, f"✓ Subnet creada: {subnet_id}")
        return subnet_id

    except ClientError as e:
        print_color(Colors.RED, f"✗ Error creando subnet {name}: {e}")
        sys.exit(1)


def get_vpc_by_tag(ec2, name):
    """Busca VPC por tag Name y tag=mck21"""
    try:
        response = ec2.describe_vpcs(
            Filters=[
                {"Name": "tag:Name", "Values": [name]},
                {"Name": f"tag:{TAG_KEY}", "Values": [TAG_VALUE]},
            ]
        )
        if response["Vpcs"]:
            return response["Vpcs"][0]["VpcId"]
        return None
    except ClientError as e:
        print_color(Colors.RED, f"Error buscando VPC: {e}")
        return None


def create_vpc(ec2):
    print_color(Colors.YELLOW, "[1/3] Verificando VPC...")

    vpc_id = get_vpc_by_tag(ec2, VPC_NAME)
    if vpc_id:
        print_color(Colors.GREEN, f"✓ VPC ya existe: {vpc_id}")
        return vpc_id

    try:
        print(f"Creando VPC con CIDR {VPC_CIDR}...")
        response = ec2.create_vpc(
            CidrBlock=VPC_CIDR,
            TagSpecifications=[
                {
                    "ResourceType": "vpc",
                    "Tags": [
                        {"Key": "Name", "Value": VPC_NAME},
                        {"Key": TAG_KEY, "Value": TAG_VALUE},
                    ],
                }
            ],
        )

        vpc_id = response["Vpc"]["VpcId"]

        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={"Value": True})
        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={"Value": True})

        print_color(Colors.GREEN, f"✓ VPC creada: {vpc_id}")
        return vpc_id

    except ClientError as e:
        print_color(Colors.RED, f"✗ Error creando VPC: {e}")
        sys.exit(1)


# ------------------------------
# Main
# ------------------------------
def main():
    print_color(Colors.GREEN, "\n=== Iniciando creación de VPC y Subnets ===\n")

    ec2 = boto3.client("ec2")

    # Crear o verificar VPC
    vpc_id = create_vpc(ec2)

    # Crear subred pública
    print_color(Colors.YELLOW, "\n[2/3] Creando subnet pública...")
    public_subnet_id = create_subnet(ec2, vpc_id, PUBLIC_SUBNET_CIDR, PUBLIC_SUBNET_NAME)

    # Crear subred privada
    print_color(Colors.YELLOW, "\n[3/3] Creando subnet privada...")
    private_subnet_id = create_subnet(ec2, vpc_id, PRIVATE_SUBNET_CIDR, PRIVATE_SUBNET_NAME)

    # Resumen
    print_color(Colors.GREEN, "\n========================================")
    print_color(Colors.GREEN, "  Recursos creados exitosamente")
    print_color(Colors.GREEN, "========================================")
    print(f"VPC ID:                  {vpc_id}")
    print(f"Public Subnet ID:        {public_subnet_id}")
    print(f"Private Subnet ID:       {private_subnet_id}")
    print(f"CIDR VPC:                {VPC_CIDR}")
    print(f"CIDR Subnet Pública:     {PUBLIC_SUBNET_CIDR}")
    print(f"CIDR Subnet Privada:     {PRIVATE_SUBNET_CIDR}")
    print(f"Tag global:              {TAG_KEY}={TAG_VALUE}")
    print_color(Colors.GREEN, "========================================\n")

    print_color(Colors.GREEN, "✓ Script completado exitosamente\n")


if __name__ == "__main__":
    main()
