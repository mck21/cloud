#!/usr/bin/env python3

"""
Script: Crear infraestructura inicial en AWS con tag mck21
Incluye:
- VPC
- Subnet pública
- Subnet privada
- Internet Gateway
- Route Table pública y privada
"""

import boto3
import sys
from botocore.exceptions import ClientError


# ============================
#  Colores terminal
# ============================
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'


def print_color(color, message):
    print(f"{color}{message}{Colors.NC}")


# ============================
#  Configuración
# ============================
VPC_CIDR = "172.16.0.0/16"
VPC_NAME = "vpc-mck21"

TAG_KEY = "tag"
TAG_VALUE = "mck21"

PUBLIC_SUBNET_CIDR = "172.16.1.0/24"
PRIVATE_SUBNET_CIDR = "172.16.2.0/24"


# ============================
#  Funciones VPC
# ============================
def get_vpc_by_tag(ec2, name):
    try:
        response = ec2.describe_vpcs(
            Filters=[
                {'Name': 'tag:Name', 'Values': [name]},
                {'Name': f'tag:{TAG_KEY}', 'Values': [TAG_VALUE]},
            ]
        )
        if response["Vpcs"]:
            return response["Vpcs"][0]["VpcId"]
        return None
    except ClientError as e:
        print_color(Colors.RED, f"Error buscando VPC: {e}")
        return None


def create_vpc(ec2):
    print_color(Colors.YELLOW, "Creando VPC...")

    vpc_id = get_vpc_by_tag(ec2, VPC_NAME)
    if vpc_id:
        print_color(Colors.GREEN, f"✓ VPC ya existe: {vpc_id}")
        return vpc_id

    try:
        response = ec2.create_vpc(
            CidrBlock=VPC_CIDR,
            TagSpecifications=[
                {
                    'ResourceType': 'vpc',
                    'Tags': [
                        {'Key': 'Name', 'Value': VPC_NAME},
                        {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    ],
                }
            ],
        )
        vpc_id = response["Vpc"]["VpcId"]

        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})

        print_color(Colors.GREEN, f"✓ VPC creada: {vpc_id}")
        return vpc_id

    except ClientError as e:
        print_color(Colors.RED, f"✗ Error creando VPC: {e}")
        sys.exit(1)


# ============================
#  Subnets
# ============================
def find_subnet(ec2, cidr):
    try:
        response = ec2.describe_subnets(
            Filters=[
                {"Name": "cidr-block", "Values": [cidr]},
                {"Name": f"tag:{TAG_KEY}", "Values": [TAG_VALUE]},
            ]
        )
        if response["Subnets"]:
            return response["Subnets"][0]["SubnetId"]
        return None
    except ClientError:
        return None


def create_subnet(ec2, vpc_id, cidr, name):
    print_color(Colors.YELLOW, f"Creando subnet {name}...")

    existing = find_subnet(ec2, cidr)
    if existing:
        print_color(Colors.GREEN, f"✓ Subnet {name} ya existe: {existing}")
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
        subnet_id = response["Subnet"]["SubnetId"]

        print_color(Colors.GREEN, f"✓ Subnet {name} creada: {subnet_id}")
        return subnet_id

    except ClientError as e:
        print_color(Colors.RED, f"✗ Error creando subnet {name}: {e}")
        sys.exit(1)


# ============================
#  Internet Gateway
# ============================
def find_igw(ec2, vpc_id):
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
    except ClientError:
        return None


def create_internet_gateway(ec2, vpc_id):
    print_color(Colors.YELLOW, "Creando Internet Gateway...")

    existing = find_igw(ec2, vpc_id)
    if existing:
        print_color(Colors.GREEN, f"✓ IGW ya existe: {existing}")
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

        print_color(Colors.GREEN, f"✓ IGW creado y adjuntado: {igw_id}")
        return igw_id

    except ClientError as e:
        print_color(Colors.RED, f"✗ Error creando IGW: {e}")
        sys.exit(1)


# ============================
#  Route Tables
# ============================
def find_route_table(ec2, vpc_id, name):
    try:
        response = ec2.describe_route_tables(
            Filters=[
                {"Name": "vpc-id", "Values": [vpc_id]},
                {"Name": f"tag:Name", "Values": [name]},
                {"Name": f"tag:{TAG_KEY}", "Values": [TAG_VALUE]},
            ]
        )
        if response["RouteTables"]:
            return response["RouteTables"][0]["RouteTableId"]
        return None
    except ClientError:
        return None


def create_public_route_table(ec2, vpc_id, igw_id, subnet_id):
    print_color(Colors.YELLOW, "Creando Route Table pública...")

    name = "rtb-public-mck21"
    existing = find_route_table(ec2, vpc_id, name)
    if existing:
        print_color(Colors.GREEN, f"✓ Route Table pública ya existe: {existing}")
        return existing

    try:
        response = ec2.create_route_table(
            VpcId=vpc_id,
            TagSpecifications=[
                {
                    "ResourceType": "route-table",
                    "Tags": [
                        {"Key": "Name", "Value": name},
                        {"Key": TAG_KEY, "Value": TAG_VALUE},
                    ],
                }
            ],
        )
        rtb_id = response["RouteTable"]["RouteTableId"]

        # Crear ruta hacia el IGW
        ec2.create_route(
            RouteTableId=rtb_id,
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId=igw_id,
        )

        # Asociar la subnet pública
        ec2.associate_route_table(
            RouteTableId=rtb_id,
            SubnetId=subnet_id,
        )

        print_color(Colors.GREEN, f"✓ RTB pública creada: {rtb_id}")
        return rtb_id

    except ClientError as e:
        print_color(Colors.RED, f"✗ Error creando RTB pública: {e}")
        sys.exit(1)


def create_private_route_table(ec2, vpc_id, subnet_id):
    print_color(Colors.YELLOW, "Creando Route Table privada...")

    name = "rtb-private-mck21"
    existing = find_route_table(ec2, vpc_id, name)
    if existing:
        print_color(Colors.GREEN, f"✓ Route Table privada ya existe: {existing}")
        return existing

    try:
        response = ec2.create_route_table(
            VpcId=vpc_id,
            TagSpecifications=[
                {
                    "ResourceType": "route-table",
                    "Tags": [
                        {"Key": "Name", "Value": name},
                        {"Key": TAG_KEY, "Value": TAG_VALUE},
                    ],
                }
            ]
        )
        rtb_id = response["RouteTable"]["RouteTableId"]

        # Asociar subnet privada
        ec2.associate_route_table(
            RouteTableId=rtb_id,
            SubnetId=subnet_id,
        )

        print_color(Colors.GREEN, f"✓ RTB privada creada: {rtb_id}")
        return rtb_id

    except ClientError as e:
        print_color(Colors.RED, f"✗ Error creando RTB privada: {e}")
        sys.exit(1)


# ============================
#  MAIN
# ============================
def main():
    print_color(Colors.GREEN, "=== Creando infraestructura AWS mck21 ===")

    ec2 = boto3.client("ec2")

    # 1 — VPC
    vpc_id = create_vpc(ec2)

    # 2 — Subnets
    public_subnet_id = create_subnet(ec2, vpc_id, PUBLIC_SUBNET_CIDR, "subnet-public-mck21")
    private_subnet_id = create_subnet(ec2, vpc_id, PRIVATE_SUBNET_CIDR, "subnet-private-mck21")

    # 3 — IGW
    igw_id = create_internet_gateway(ec2, vpc_id)

    # 4 — Route Tables
    public_rtb_id = create_public_route_table(ec2, vpc_id, igw_id, public_subnet_id)
    private_rtb_id = create_private_route_table(ec2, vpc_id, private_subnet_id)

    # Resumen
    print_color(Colors.GREEN, "\n=== RESUMEN DE RECURSOS CREADOS ===")
    print(f"VPC: {vpc_id}")
    print(f"Subnet Pública: {public_subnet_id}")
    print(f"Subnet Privada: {private_subnet_id}")
    print(f"Internet Gateway: {igw_id}")
    print(f"Route Table Pública: {public_rtb_id}")
    print(f"Route Table Privada: {private_rtb_id}")
    print_color(Colors.GREEN, "=====================================\n")


if __name__ == "__main__":
    main()
