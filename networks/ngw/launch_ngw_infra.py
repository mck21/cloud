#!/usr/bin/env python3

"""
Script: Crear VPC con subred pública, privada e Internet Gateway
Paso 3: VPC + DNS + subnets + IGW
"""

import boto3
import sys
from botocore.exceptions import ClientError


class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'


# ------------------------------
# Configuración general
# ------------------------------
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
def get_vpc_by_tag(ec2, name):
    """Busca VPC por nombre y tag=mck21"""
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
    """Crea VPC si no existe"""
    existing = get_vpc_by_tag(ec2, VPC_NAME)
    if existing:
        return existing

    try:
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

        return vpc_id

    except ClientError as e:
        print_color(Colors.RED, f"✗ Error creando VPC: {e}")
        sys.exit(1)


def find_subnet(ec2, cidr, vpc_id):
    """Busca subnet por CIDR"""
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
    existing = find_subnet(ec2, cidr, vpc_id)
    if existing:
        return existing

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

        return response["Subnet"]["SubnetId"]

    except ClientError as e:
        print_color(Colors.RED, f"✗ Error creando subnet {name}: {e}")
        sys.exit(1)


def find_igw(ec2, vpc_id):
    """Busca IGW asociado a la VPC"""
    try:
        response = ec2.describe_internet_gateways(
            Filters=[
                {"Name": "attachment.vpc-id", "Values": [vpc_id]},
                {"Name": f"tag:{TAG_KEY}", "Values": [TAG_VALUE]},
            ]
        )
        if response["InternetGateways"]:
            return response["InternetGateways"][0]["InternetGatewayId"]
        return None
    except ClientError as e:
        print_color(Colors.RED, f"Error buscando IGW: {e}")
        return None


def create_internet_gateway(ec2, vpc_id):
    """Crea IGW si no existe"""
    existing = find_igw(ec2, vpc_id)
    if existing:
        return existing

    try:
        response = ec2.create_internet_gateway(
            TagSpecifications=[
                {
                    "ResourceType": "internet-gateway",
                    "Tags": [
                        {"Key": "Name", "Value": "igw-mck21"},
                        {"Key": TAG_KEY, "Value": TAG_VALUE},
                    ],
                }
            ]
        )

        igw_id = response["InternetGateway"]["InternetGatewayId"]

        ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)

        return igw_id

    except ClientError as e:
        print_color(Colors.RED, f"✗ Error creando o adjuntando IGW: {e}")
        sys.exit(1)


# ------------------------------
# Main
# ------------------------------
def main():
    print_color(Colors.GREEN, "\n=== Creación de infraestructura base (VPC + Subnets + IGW) ===\n")

    ec2 = boto3.client("ec2")

    # Paso 1: VPC
    print_color(Colors.YELLOW, "[1/4] Creando o verificando VPC...")
    vpc_id = create_vpc(ec2)
    print_color(Colors.GREEN, f"✓ VPC lista: {vpc_id}")

    # Paso 2: Subnet pública
    print_color(Colors.YELLOW, "\n[2/4] Creando subnet pública...")
    public_subnet_id = create_subnet(ec2, vpc_id, PUBLIC_SUBNET_CIDR, PUBLIC_SUBNET_NAME)
    print_color(Colors.GREEN, f"✓ Subnet pública lista: {public_subnet_id}")

    # Paso 3: Subnet privada
    print_color(Colors.YELLOW, "\n[3/4] Creando subnet privada...")
    private_subnet_id = create_subnet(ec2, vpc_id, PRIVATE_SUBNET_CIDR, PRIVATE_SUBNET_NAME)
    print_color(Colors.GREEN, f"✓ Subnet privada lista: {private_subnet_id}")

    # Paso 4: Internet Gateway
    print_color(Colors.YELLOW, "\n[4/4] Creando Internet Gateway...")
    igw_id = create_internet_gateway(ec2, vpc_id)
    print_color(Colors.GREEN, f"✓ Internet Gateway listo: {igw_id}")

    # Resumen
    print_color(Colors.GREEN, "\n========================================")
    print_color(Colors.GREEN, "  Recursos creados exitosamente")
    print_color(Colors.GREEN, "========================================")
    print(f"VPC ID:              {vpc_id}")
    print(f"Public Subnet ID:    {public_subnet_id}")
    print(f"Private Subnet ID:   {private_subnet_id}")
    print(f"Internet Gateway ID: {igw_id}")
    print(f"CIDR VPC:            {VPC_CIDR}")
    print(f"CIDR Public:         {PUBLIC_SUBNET_CIDR}")
    print(f"CIDR Private:        {PRIVATE_SUBNET_CIDR}")
    print(f"Tag global:          {TAG_KEY}={TAG_VALUE}")
    print_color(Colors.GREEN, "========================================\n")

    print_color(Colors.GREEN, "✓ Script completado exitosamente\n")


if __name__ == "__main__":
    main()
