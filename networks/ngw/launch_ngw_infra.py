import boto3
import time
import sys
from botocore.exceptions import ClientError

# --- Configuración ---
AWS_REGION = "us-east-1"
VPC_CIDR = "172.16.0.0/16"
SUBNET_PUBLIC_CIDR = "172.16.0.0/24"
SUBNET_PRIVATE_CIDR = "172.16.1.0/24"

# === CONFIGURACIÓN DE ZONA DE DISPONIBILIDAD ===
# Forzamos TODO en us-east-1a
TARGET_AZ = "us-east-1a"

# Nombres
VPC_NAME = "vpc-mck21"
SUBNET_PUBLIC_NAME = "subnet-public-mck21"
SUBNET_PRIVATE_NAME = "subnet-private-mck21"
IGW_NAME = "igw-mck21"
RTB_PUBLIC_NAME = "rtb-public-mck21"
RTB_PRIVATE_NAME = "rtb-private-mck21"
SG_NAME = "gs-mck21"
EC2_PUBLIC_NAME = "ec2-public-mck21"
EC2_PRIVATE_NAME = "ec2-private-mck21"
EIP_NAME = "eip-mck21"
NAT_NAME = "nat-mck21"

# Instancia
KEY_PAIR = "vockey"
AMI_ID = "ami-0ecb62995f68bb549"

# Colores para logs
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'

ec2 = boto3.client('ec2', region_name=AWS_REGION)

def get_tag_spec(resource_type, name):
    return [
        {
            'ResourceType': resource_type,
            'Tags': [
                {'Key': 'Name', 'Value': name},
                {'Key': 'tag', 'Value': 'mck21'}
            ]
        }
    ]

def get_resource_id(filter_name, filter_value):
    try:
        if filter_name == "vpc":
            response = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [filter_value]}])
            return response['Vpcs'][0]['VpcId'] if response['Vpcs'] else None
        elif filter_name == "subnet":
            response = ec2.describe_subnets(Filters=[{'Name': 'tag:Name', 'Values': [filter_value]}])
            return response['Subnets'][0]['SubnetId'] if response['Subnets'] else None
        elif filter_name == "internet-gateway":
            response = ec2.describe_internet_gateways(Filters=[{'Name': 'tag:Name', 'Values': [filter_value]}])
            return response['InternetGateways'][0]['InternetGatewayId'] if response['InternetGateways'] else None
        elif filter_name == "route-table":
            response = ec2.describe_route_tables(Filters=[{'Name': 'tag:Name', 'Values': [filter_value]}])
            return response['RouteTables'][0]['RouteTableId'] if response['RouteTables'] else None
        elif filter_name == "instance":
            response = ec2.describe_instances(Filters=[
                {'Name': 'tag:Name', 'Values': [filter_value]},
                {'Name': 'instance-state-name', 'Values': ['running', 'pending', 'stopped']}
            ])
            if response['Reservations']:
                return response['Reservations'][0]['Instances'][0]['InstanceId']
            return None
    except ClientError as e:
        print(f"{Colors.RED}Error buscando recurso: {e}{Colors.NC}")
    return None

def main():
    print(f"{Colors.GREEN}=== Iniciando creación de infraestructura AWS (Todo en {TARGET_AZ}) ==={Colors.NC}\n")

    # 1. VPC
    print(f"{Colors.YELLOW}[1/12] Verificando VPC...{Colors.NC}")
    vpc_id = get_resource_id("vpc", VPC_NAME)
    if not vpc_id:
        print(f"Creando VPC {VPC_CIDR}...")
        vpc_res = ec2.create_vpc(
            CidrBlock=VPC_CIDR,
            TagSpecifications=get_tag_spec('vpc', VPC_NAME)
        )
        vpc_id = vpc_res['Vpc']['VpcId']
        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
        ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
        print(f"{Colors.GREEN}✓ VPC creada: {vpc_id}{Colors.NC}")
    else:
        print(f"{Colors.GREEN}✓ VPC ya existe: {vpc_id}{Colors.NC}")

    # 2. Subnet Pública
    print(f"\n{Colors.YELLOW}[2/12] Verificando Subnet Pública ({TARGET_AZ})...{Colors.NC}")
    pub_sub_id = get_resource_id("subnet", SUBNET_PUBLIC_NAME)
    if not pub_sub_id:
        print(f"Creando Subnet Pública {SUBNET_PUBLIC_CIDR}...")
        sub_res = ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock=SUBNET_PUBLIC_CIDR,
            AvailabilityZone=TARGET_AZ,
            TagSpecifications=get_tag_spec('subnet', SUBNET_PUBLIC_NAME)
        )
        pub_sub_id = sub_res['Subnet']['SubnetId']
        ec2.modify_subnet_attribute(SubnetId=pub_sub_id, MapPublicIpOnLaunch={'Value': True})
        print(f"{Colors.GREEN}✓ Subnet pública creada: {pub_sub_id}{Colors.NC}")
    else:
        print(f"{Colors.GREEN}✓ Subnet pública ya existe: {pub_sub_id}{Colors.NC}")

    # 3. Subnet Privada
    print(f"\n{Colors.YELLOW}[3/12] Verificando Subnet Privada ({TARGET_AZ})...{Colors.NC}")
    priv_sub_id = get_resource_id("subnet", SUBNET_PRIVATE_NAME)
    if not priv_sub_id:
        print(f"Creando Subnet Privada {SUBNET_PRIVATE_CIDR}...")
        sub_res = ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock=SUBNET_PRIVATE_CIDR,
            AvailabilityZone=TARGET_AZ,
            TagSpecifications=get_tag_spec('subnet', SUBNET_PRIVATE_NAME)
        )
        priv_sub_id = sub_res['Subnet']['SubnetId']
        print(f"{Colors.GREEN}✓ Subnet privada creada: {priv_sub_id}{Colors.NC}")
    else:
        print(f"{Colors.GREEN}✓ Subnet privada ya existe: {priv_sub_id}{Colors.NC}")

    # 4. Internet Gateway
    print(f"\n{Colors.YELLOW}[4/12] Verificando Internet Gateway...{Colors.NC}")
    igw_id = get_resource_id("internet-gateway", IGW_NAME)
    if not igw_id:
        print("Creando Internet Gateway...")
        igw_res = ec2.create_internet_gateway(
            TagSpecifications=get_tag_spec('internet-gateway', IGW_NAME)
        )
        igw_id = igw_res['InternetGateway']['InternetGatewayId']
        ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        print(f"{Colors.GREEN}✓ IGW creado y adjuntado: {igw_id}{Colors.NC}")
    else:
        print(f"{Colors.GREEN}✓ IGW ya existe: {igw_id}{Colors.NC}")

    # 5. Route Table Pública
    print(f"\n{Colors.YELLOW}[5/12] Verificando Route Table Pública...{Colors.NC}")
    rtb_pub_id = get_resource_id("route-table", RTB_PUBLIC_NAME)
    if not rtb_pub_id:
        print("Creando Route Table Pública...")
        rtb_res = ec2.create_route_table(
            VpcId=vpc_id,
            TagSpecifications=get_tag_spec('route-table', RTB_PUBLIC_NAME)
        )
        rtb_pub_id = rtb_res['RouteTable']['RouteTableId']
        ec2.create_route(RouteTableId=rtb_pub_id, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw_id)
        ec2.associate_route_table(RouteTableId=rtb_pub_id, SubnetId=pub_sub_id)
        print(f"{Colors.GREEN}✓ Route Table pública configurada: {rtb_pub_id}{Colors.NC}")
    else:
        print(f"{Colors.GREEN}✓ Route Table pública ya existe: {rtb_pub_id}{Colors.NC}")

    # 6. Route Table Privada
    print(f"\n{Colors.YELLOW}[6/12] Verificando Route Table Privada...{Colors.NC}")
    rtb_priv_id = get_resource_id("route-table", RTB_PRIVATE_NAME)
    if not rtb_priv_id:
        print("Creando Route Table Privada...")
        rtb_res = ec2.create_route_table(
            VpcId=vpc_id,
            TagSpecifications=get_tag_spec('route-table', RTB_PRIVATE_NAME)
        )
        rtb_priv_id = rtb_res['RouteTable']['RouteTableId']
        ec2.associate_route_table(RouteTableId=rtb_priv_id, SubnetId=priv_sub_id)
        print(f"{Colors.GREEN}✓ Route Table privada creada: {rtb_priv_id}{Colors.NC}")
    else:
        print(f"{Colors.GREEN}✓ Route Table privada ya existe: {rtb_priv_id}{Colors.NC}")

    # 7. Security Group
    print(f"\n{Colors.YELLOW}[7/12] Verificando Security Group...{Colors.NC}")
    sg_id = None
    try:
        sgs = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [SG_NAME]}, {'Name': 'vpc-id', 'Values': [vpc_id]}])
        if sgs['SecurityGroups']:
            sg_id = sgs['SecurityGroups'][0]['GroupId']
    except ClientError:
        pass

    if not sg_id:
        print("Creando Security Group...")
        sg_res = ec2.create_security_group(
            GroupName=SG_NAME,
            Description="Security group for mck21 instances",
            VpcId=vpc_id,
            TagSpecifications=get_tag_spec('security-group', SG_NAME)
        )
        sg_id = sg_res['GroupId']
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 'IpRanges': [{'CidrIp': VPC_CIDR}]}
            ]
        )
        print(f"{Colors.GREEN}✓ Security Group creado: {sg_id}{Colors.NC}")
    else:
        print(f"{Colors.GREEN}✓ Security Group ya existe: {sg_id}{Colors.NC}")

    # 8. Instancias EC2
    print(f"\n{Colors.YELLOW}[8/12] Verificando Instancias EC2...{Colors.NC}")
    
    # Definimos la función para crear instancias
    def create_instance(name, subnet_id):
        instance_id = get_resource_id("instance", name)
        if not instance_id:
            print(f" - Lanzando {name}...")
            run_instances = ec2.run_instances(
                ImageId=AMI_ID,
                InstanceType='t3.micro',
                KeyName=KEY_PAIR,
                SubnetId=subnet_id,
                SecurityGroupIds=[sg_id],
                MinCount=1,
                MaxCount=1,
                TagSpecifications=get_tag_spec('instance', name)
            )
            instance_id = run_instances['Instances'][0]['InstanceId']
            print(f"{Colors.GREEN}   ✓ Creada: {instance_id}{Colors.NC}")
        else:
            print(f"{Colors.GREEN}   ✓ Ya existe {name}: {instance_id}{Colors.NC}")
        return instance_id

    # Llamadas a la función
    ec2_pub_id = create_instance(EC2_PUBLIC_NAME, pub_sub_id)
    ec2_priv_id = create_instance(EC2_PRIVATE_NAME, priv_sub_id)

    print(f"\n{Colors.YELLOW}Esperando a que las instancias estén 'running'...{Colors.NC}")
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[ec2_pub_id, ec2_priv_id])
    print(f"{Colors.GREEN}✓ Instancias activas{Colors.NC}")

    # 9. Elastic IP
    print(f"\n{Colors.YELLOW}[9/12] Verificando Elastic IP...{Colors.NC}")
    eip_alloc_id = None
    eip_res = ec2.describe_addresses(Filters=[{'Name': 'tag:Name', 'Values': [EIP_NAME]}])
    
    if not eip_res['Addresses']:
        print("Creando Elastic IP...")
        alloc_res = ec2.allocate_address(
            Domain='vpc',
            TagSpecifications=get_tag_spec('elastic-ip', EIP_NAME)
        )
        eip_alloc_id = alloc_res['AllocationId']
        eip_address = alloc_res['PublicIp']
        print(f"{Colors.GREEN}✓ Elastic IP creada: {eip_address}{Colors.NC}")
    else:
        eip_alloc_id = eip_res['Addresses'][0]['AllocationId']
        eip_address = eip_res['Addresses'][0]['PublicIp']
        print(f"{Colors.GREEN}✓ Elastic IP ya existe: {eip_address}{Colors.NC}")

    # 10. NAT Gateway
    print(f"\n{Colors.YELLOW}[10/12] Verificando NAT Gateway...{Colors.NC}")
    nat_id = None
    nat_res = ec2.describe_nat_gateways(Filters=[
        {'Name': 'tag:Name', 'Values': [NAT_NAME]},
        {'Name': 'state', 'Values': ['available', 'pending']}
    ])

    if not nat_res['NatGateways']:
        print("Creando NAT Gateway (esto toma tiempo)...")
        nat_create = ec2.create_nat_gateway(
            SubnetId=pub_sub_id,
            AllocationId=eip_alloc_id,
            TagSpecifications=get_tag_spec('natgateway', NAT_NAME)
        )
        nat_id = nat_create['NatGateway']['NatGatewayId']
        print(f"{Colors.GREEN}✓ NAT Gateway creado: {nat_id}. Esperando disponibilidad...{Colors.NC}")
        
        nat_waiter = ec2.get_waiter('nat_gateway_available')
        nat_waiter.wait(NatGatewayIds=[nat_id])
        print(f"{Colors.GREEN}✓ NAT Gateway disponible{Colors.NC}")
    else:
        nat_id = nat_res['NatGateways'][0]['NatGatewayId']
        print(f"{Colors.GREEN}✓ NAT Gateway ya existe: {nat_id}{Colors.NC}")
        if nat_res['NatGateways'][0]['State'] == 'pending':
             ec2.get_waiter('nat_gateway_available').wait(NatGatewayIds=[nat_id])

    # 11. Actualizar Route Table Privada
    print(f"\n{Colors.YELLOW}[11/12] Actualizando Route Table Privada...{Colors.NC}")
    rt_desc = ec2.describe_route_tables(RouteTableIds=[rtb_priv_id])
    routes = rt_desc['RouteTables'][0]['Routes']
    
    route_exists = False
    for r in routes:
        if r.get('DestinationCidrBlock') == '0.0.0.0/0':
            route_exists = True
            if r.get('NatGatewayId') != nat_id:
                print("Actualizando ruta hacia NAT Gateway...")
                ec2.replace_route(RouteTableId=rtb_priv_id, DestinationCidrBlock='0.0.0.0/0', NatGatewayId=nat_id)
            else:
                print(f"{Colors.GREEN}✓ La ruta ya es correcta{Colors.NC}")
            break
    
    if not route_exists:
        print("Agregando ruta 0.0.0.0/0 hacia NAT Gateway...")
        ec2.create_route(RouteTableId=rtb_priv_id, DestinationCidrBlock='0.0.0.0/0', NatGatewayId=nat_id)
        print(f"{Colors.GREEN}✓ Ruta agregada{Colors.NC}")

    # 12. Obtener IPs finales
    print(f"\n{Colors.YELLOW}[12/12] Resumen...{Colors.NC}")
    instances_info = ec2.describe_instances(InstanceIds=[ec2_pub_id, ec2_priv_id])
    
    pub_ip = "N/A"
    priv_ip = "N/A"

    for r in instances_info['Reservations']:
        for i in r['Instances']:
            if i['InstanceId'] == ec2_pub_id:
                pub_ip = i.get('PublicIpAddress', 'N/A')
            elif i['InstanceId'] == ec2_priv_id:
                priv_ip = i.get('PrivateIpAddress', 'N/A')

    print(f"\n{Colors.GREEN}========================================{Colors.NC}")
    print(f"{Colors.GREEN}  Infraestructura Final (Todo en {TARGET_AZ}){Colors.NC}")
    print(f"{Colors.GREEN}========================================{Colors.NC}")
    print(f"Subnet Pública:      {pub_sub_id}")
    print(f"Subnet Privada:      {priv_sub_id}")
    print(f"EC2 Pública IP:      {pub_ip}")
    print(f"EC2 Privada IP:      {priv_ip}")
    print(f"{Colors.GREEN}========================================{Colors.NC}")

if __name__ == "__main__":
    main()