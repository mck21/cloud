import boto3
import time
import sys

# ==============================================================================
# SCRIPT DE CREACIÓN DE INFRAESTRUCTURA AWS - APLICACIÓN 3 CAPAS
# Descripción: VPC con frontend público, backend y DB privados con NAT Gateway
# Subredes: 15.0.0.0/20 -> Frontend: 15.0.1.0/24, Backend: 15.0.2.0/24, DB: 15.0.3.0/24
# Recursos: Todos llevan tag key=tag value=mck21
# ==============================================================================

# ==============================================================================
# VARIABLES DE CONFIGURACIÓN
# ==============================================================================
TAG_KEY = "tag"
TAG_VALUE = "mck21"
SUFFIX = "-mck21"
VPC_CIDR = "15.0.0.0/20"
FRONTEND_CIDR = "15.0.1.0/24"
BACKEND_CIDR = "15.0.2.0/24"
DATABASE_CIDR = "15.0.3.0/24"
REGION = "us-east-1"
KEY_NAME = "vockey"
AMI_ID = "ami-07ff62358b87c7116"  # Amazon Linux 2 AMI (x86_64) en us-east-1
AZ1 = f"{REGION}a"

# Colores para output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# Cliente EC2
ec2 = boto3.client('ec2', region_name=REGION)
ec2_resource = boto3.resource('ec2', region_name=REGION)

# Variables globales
VPC_ID = None
FRONTEND_SUBNET = None
BACKEND_SUBNET = None
DATABASE_SUBNET = None
IGW = None
EIP = None
NAT = None
RT_PUBLIC = None
RT_PRIVATE = None
NACL_PUBLIC = None
NACL_PRIVATE = None
SG_FRONTEND = None
SG_BACKEND = None
SG_DATABASE = None
FRONTEND_INSTANCE_ID = None
BACKEND_INSTANCE_ID = None
DATABASE_INSTANCE_ID = None

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def print_message(color, message):
    """Función para imprimir mensajes con formato."""
    print(f"{color}{message}{NC}")

def create_tags(resource_id, name):
    """Función auxiliar para aplicar tags."""
    ec2.create_tags(
        Resources=[resource_id],
        Tags=[
            {'Key': TAG_KEY, 'Value': TAG_VALUE},
            {'Key': 'Name', 'Value': name}
        ]
    )

def get_existing_resource_by_tag(resource_type, tag_name):
    """Busca un recurso existente por el tag de Name."""
    filters = [
        {'Name': f'tag:Name', 'Values': [f'{tag_name}{SUFFIX}']},
        {'Name': f'tag:{TAG_KEY}', 'Values': [TAG_VALUE]},
    ]
    
    if resource_type == 'vpcs':
        response = ec2.describe_vpcs(Filters=filters)
        return response['Vpcs'][0]['VpcId'] if response['Vpcs'] else None
    
    elif resource_type == 'nat-gateways':
        filters.append({'Name': 'state', 'Values': ['available', 'pending']})
        response = ec2.describe_nat_gateways(Filter=filters)
        return response['NatGateways'][0]['NatGatewayId'] if response['NatGateways'] else None
        
    elif resource_type == 'subnets':
        filters.append({'Name': 'vpc-id', 'Values': [VPC_ID]})
        response = ec2.describe_subnets(Filters=filters)
        return response['Subnets'][0]['SubnetId'] if response['Subnets'] else None
        
    elif resource_type == 'route-tables':
        filters.append({'Name': 'vpc-id', 'Values': [VPC_ID]})
        response = ec2.describe_route_tables(Filters=filters)
        return response['RouteTables'][0]['RouteTableId'] if response['RouteTables'] else None
    
    elif resource_type == 'network-acls':
        filters.append({'Name': 'vpc-id', 'Values': [VPC_ID]})
        response = ec2.describe_network_acls(Filters=filters)
        return response['NetworkAcls'][0]['NetworkAclId'] if response['NetworkAcls'] else None
        
    elif resource_type == 'security-groups':
        filters.append({'Name': 'vpc-id', 'Values': [VPC_ID]})
        response = ec2.describe_security_groups(Filters=filters)
        groups = [sg for sg in response['SecurityGroups'] if sg['GroupName'] != 'default']
        return groups[0]['GroupId'] if groups else None
        
    return None

def get_existing_instance(tag_name):
    """Busca una instancia EC2 existente."""
    filters = [
        {'Name': 'vpc-id', 'Values': [VPC_ID]},
        {'Name': 'tag:Name', 'Values': [tag_name]},
        {'Name': 'instance-state-name', 'Values': ['pending', 'running']},
    ]
    response = ec2.describe_instances(Filters=filters)
    
    if response['Reservations'] and response['Reservations'][0]['Instances']:
        instance = response['Reservations'][0]['Instances'][0]
        return instance['InstanceId'], instance.get('PublicIpAddress'), instance.get('PrivateIpAddress')
    return None, None, None

# ==============================================================================
# 1. CREAR VPC
# ==============================================================================
print_message(YELLOW, "\n╔═══════════════════════════════════════════════════════════╗")
print_message(YELLOW, "║     INFRAESTRUCTURA AWS - APLICACIÓN 3 CAPAS            ║")
print_message(YELLOW, "╚═══════════════════════════════════════════════════════════╝")
print_message(BLUE, "\n=== PASO 1: CREANDO VPC ===")

try:
    VPC_ID = get_existing_resource_by_tag('vpcs', 'vpc-3tier')
    
    if VPC_ID:
        print_message(GREEN, f"✓ VPC ya existe: {VPC_ID}")
    else:
        response = ec2.create_vpc(
            CidrBlock=VPC_CIDR,
            TagSpecifications=[
                {'ResourceType': 'vpc', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'vpc-3tier{SUFFIX}'}
                ]}
            ]
        )
        VPC_ID = response['Vpc']['VpcId']
        
        # Habilitar DNS
        ec2.modify_vpc_attribute(VpcId=VPC_ID, EnableDnsHostnames={'Value': True})
        ec2.modify_vpc_attribute(VpcId=VPC_ID, EnableDnsSupport={'Value': True})
        
        print_message(GREEN, f"✓ VPC creada: {VPC_ID} ({VPC_CIDR})")
except Exception as e:
    print_message(RED, f"✗ Error al crear VPC: {e}")
    sys.exit(1)

# ==============================================================================
# 2. CREAR SUBREDES
# ==============================================================================
print_message(BLUE, "\n=== PASO 2: CREANDO SUBREDES (Frontend, Backend, Database) ===")

try:
    # Subred Frontend (Pública)
    FRONTEND_SUBNET = get_existing_resource_by_tag('subnets', 'frontend-subnet')
    if FRONTEND_SUBNET:
        print_message(GREEN, f"✓ Subred Frontend ya existe: {FRONTEND_SUBNET}")
    else:
        response = ec2.create_subnet(
            VpcId=VPC_ID,
            CidrBlock=FRONTEND_CIDR,
            AvailabilityZone=AZ1,
            TagSpecifications=[
                {'ResourceType': 'subnet', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'frontend-subnet{SUFFIX}'}
                ]}
            ]
        )
        FRONTEND_SUBNET = response['Subnet']['SubnetId']
        ec2.modify_subnet_attribute(SubnetId=FRONTEND_SUBNET, MapPublicIpOnLaunch={'Value': True})
        print_message(GREEN, f"✓ Subred Frontend creada: {FRONTEND_SUBNET} ({FRONTEND_CIDR})")

    # Subred Backend (Privada)
    BACKEND_SUBNET = get_existing_resource_by_tag('subnets', 'backend-subnet')
    if BACKEND_SUBNET:
        print_message(GREEN, f"✓ Subred Backend ya existe: {BACKEND_SUBNET}")
    else:
        response = ec2.create_subnet(
            VpcId=VPC_ID,
            CidrBlock=BACKEND_CIDR,
            AvailabilityZone=AZ1,
            TagSpecifications=[
                {'ResourceType': 'subnet', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'backend-subnet{SUFFIX}'}
                ]}
            ]
        )
        BACKEND_SUBNET = response['Subnet']['SubnetId']
        print_message(GREEN, f"✓ Subred Backend creada: {BACKEND_SUBNET} ({BACKEND_CIDR})")

    # Subred Database (Privada)
    DATABASE_SUBNET = get_existing_resource_by_tag('subnets', 'database-subnet')
    if DATABASE_SUBNET:
        print_message(GREEN, f"✓ Subred Database ya existe: {DATABASE_SUBNET}")
    else:
        response = ec2.create_subnet(
            VpcId=VPC_ID,
            CidrBlock=DATABASE_CIDR,
            AvailabilityZone=AZ1,
            TagSpecifications=[
                {'ResourceType': 'subnet', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'database-subnet{SUFFIX}'}
                ]}
            ]
        )
        DATABASE_SUBNET = response['Subnet']['SubnetId']
        print_message(GREEN, f"✓ Subred Database creada: {DATABASE_SUBNET} ({DATABASE_CIDR})")

except Exception as e:
    print_message(RED, f"✗ Error al crear subredes: {e}")
    sys.exit(1)

# ==============================================================================
# 3. CREAR Y ASOCIAR INTERNET GATEWAY
# ==============================================================================
print_message(BLUE, "\n=== PASO 3: CONFIGURANDO INTERNET GATEWAY ===")

try:
    response = ec2.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [VPC_ID]}])
    IGW = response['InternetGateways'][0]['InternetGatewayId'] if response['InternetGateways'] else None

    if IGW:
        print_message(GREEN, f"✓ Internet Gateway ya existe: {IGW}")
    else:
        response = ec2.create_internet_gateway(
            TagSpecifications=[
                {'ResourceType': 'internet-gateway', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'igw-3tier{SUFFIX}'}
                ]}
            ]
        )
        IGW = response['InternetGateway']['InternetGatewayId']
        ec2.attach_internet_gateway(VpcId=VPC_ID, InternetGatewayId=IGW)
        print_message(GREEN, f"✓ Internet Gateway creado y asociado: {IGW}")
        
except Exception as e:
    print_message(RED, f"✗ Error al configurar IGW: {e}")
    sys.exit(1)

# ==============================================================================
# 4. CREAR ELASTIC IP Y NAT GATEWAY
# ==============================================================================
print_message(BLUE, "\n=== PASO 4: CONFIGURANDO NAT GATEWAY ===")

try:
    NAT = get_existing_resource_by_tag('nat-gateways', 'ngw-3tier')
    
    if NAT:
        response = ec2.describe_nat_gateways(NatGatewayIds=[NAT])
        EIP = response['NatGateways'][0]['NatGatewayAddresses'][0]['AllocationId']
        print_message(GREEN, f"✓ NAT Gateway ya existe: {NAT}")
    else:
        response = ec2.allocate_address(
            Domain='vpc',
            TagSpecifications=[
                {'ResourceType': 'elastic-ip', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'eip-nat{SUFFIX}'}
                ]}
            ]
        )
        EIP = response['AllocationId']
        print_message(GREEN, f"✓ Elastic IP creada: {EIP}")
        
        response = ec2.create_nat_gateway(
            SubnetId=FRONTEND_SUBNET,
            AllocationId=EIP,
            TagSpecifications=[
                {'ResourceType': 'natgateway', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'ngw-3tier{SUFFIX}'}
                ]}
            ]
        )
        NAT = response['NatGateway']['NatGatewayId']
        
        print_message(YELLOW, "⏳ Esperando a que NAT Gateway esté disponible...")
        waiter = ec2.get_waiter('nat_gateway_available')
        waiter.wait(NatGatewayIds=[NAT])
        print_message(GREEN, f"✓ NAT Gateway creado y disponible: {NAT}")

except Exception as e:
    print_message(RED, f"✗ Error al configurar NAT Gateway: {e}")
    sys.exit(1)

# ==============================================================================
# 5. CREAR TABLAS DE RUTEO
# ==============================================================================
print_message(BLUE, "\n=== PASO 5: CONFIGURANDO TABLAS DE RUTEO ===")

try:
    # Tabla de ruteo pública (Frontend -> IGW)
    RT_PUBLIC = get_existing_resource_by_tag('route-tables', 'rt-public-frontend')
    
    if RT_PUBLIC:
        print_message(GREEN, f"✓ Tabla de ruteo pública ya existe: {RT_PUBLIC}")
    else:
        response = ec2.create_route_table(
            VpcId=VPC_ID,
            TagSpecifications=[
                {'ResourceType': 'route-table', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'rt-public-frontend{SUFFIX}'}
                ]}
            ]
        )
        RT_PUBLIC = response['RouteTable']['RouteTableId']
        
        ec2.create_route(
            RouteTableId=RT_PUBLIC,
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=IGW
        )
        
        ec2.associate_route_table(SubnetId=FRONTEND_SUBNET, RouteTableId=RT_PUBLIC)
        print_message(GREEN, f"✓ Tabla de ruteo pública creada: {RT_PUBLIC} → IGW")

    # Tabla de ruteo privada (Backend + Database -> NAT)
    RT_PRIVATE = get_existing_resource_by_tag('route-tables', 'rt-private-backend-db')
    
    if RT_PRIVATE:
        print_message(GREEN, f"✓ Tabla de ruteo privada ya existe: {RT_PRIVATE}")
    else:
        response = ec2.create_route_table(
            VpcId=VPC_ID,
            TagSpecifications=[
                {'ResourceType': 'route-table', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'rt-private-backend-db{SUFFIX}'}
                ]}
            ]
        )
        RT_PRIVATE = response['RouteTable']['RouteTableId']
        
        ec2.create_route(
            RouteTableId=RT_PRIVATE,
            DestinationCidrBlock='0.0.0.0/0',
            NatGatewayId=NAT
        )
        
        ec2.associate_route_table(SubnetId=BACKEND_SUBNET, RouteTableId=RT_PRIVATE)
        ec2.associate_route_table(SubnetId=DATABASE_SUBNET, RouteTableId=RT_PRIVATE)
        print_message(GREEN, f"✓ Tabla de ruteo privada creada: {RT_PRIVATE} → NAT")

except Exception as e:
    print_message(RED, f"✗ Error al configurar tablas de ruteo: {e}")
    sys.exit(1)

# ==============================================================================
# 6. CREAR SECURITY GROUPS
# ==============================================================================
print_message(BLUE, "\n=== PASO 6: CONFIGURANDO SECURITY GROUPS ===")

try:
    # SG Frontend (HTTP/HTTPS/SSH desde Internet)
    SG_FRONTEND = get_existing_resource_by_tag('security-groups', 'gs-frontend')
    
    if SG_FRONTEND:
        print_message(GREEN, f"✓ Security Group Frontend ya existe: {SG_FRONTEND}")
    else:
        response = ec2.create_security_group(
            GroupName=f'gs-frontend{SUFFIX}',
            Description='Security Group para Frontend - Accesible desde Internet',
            VpcId=VPC_ID,
            TagSpecifications=[
                {'ResourceType': 'security-group', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'gs-frontend{SUFFIX}'}
                ]}
            ]
        )
        SG_FRONTEND = response['GroupId']
        
        # Reglas de entrada
        ec2.authorize_security_group_ingress(
            GroupId=SG_FRONTEND,
            IpPermissions=[
                {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            ]
        )
        print_message(GREEN, f"✓ Security Group Frontend creado: {SG_FRONTEND}")
        print_message(GREEN, "  → Permite HTTP (80), HTTPS (443), SSH (22) desde 0.0.0.0/0")

    # SG Backend (solo accesible desde Frontend)
    SG_BACKEND = get_existing_resource_by_tag('security-groups', 'gs-backend')
    
    if SG_BACKEND:
        print_message(GREEN, f"✓ Security Group Backend ya existe: {SG_BACKEND}")
    else:
        response = ec2.create_security_group(
            GroupName=f'gs-backend{SUFFIX}',
            Description='Security Group para Backend - Solo accesible desde Frontend',
            VpcId=VPC_ID,
            TagSpecifications=[
                {'ResourceType': 'security-group', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'gs-backend{SUFFIX}'}
                ]}
            ]
        )
        SG_BACKEND = response['GroupId']
        
        # Reglas de entrada
        ec2.authorize_security_group_ingress(
            GroupId=SG_BACKEND,
            IpPermissions=[
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 
                 'UserIdGroupPairs': [{'GroupId': SG_FRONTEND}]},
                {'IpProtocol': 'tcp', 'FromPort': 8080, 'ToPort': 8080, 
                 'UserIdGroupPairs': [{'GroupId': SG_FRONTEND}]},
                {'IpProtocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 
                 'UserIdGroupPairs': [{'GroupId': SG_FRONTEND}]},
            ]
        )
        print_message(GREEN, f"✓ Security Group Backend creado: {SG_BACKEND}")
        print_message(GREEN, "  → Permite SSH (22), App (8080), ICMP desde Frontend SG")

    # SG Database (solo accesible desde Backend)
    SG_DATABASE = get_existing_resource_by_tag('security-groups', 'gs-database')
    
    if SG_DATABASE:
        print_message(GREEN, f"✓ Security Group Database ya existe: {SG_DATABASE}")
    else:
        response = ec2.create_security_group(
            GroupName=f'gs-database{SUFFIX}',
            Description='Security Group para Database - Solo accesible desde Backend',
            VpcId=VPC_ID,
            TagSpecifications=[
                {'ResourceType': 'security-group', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'gs-database{SUFFIX}'}
                ]}
            ]
        )
        SG_DATABASE = response['GroupId']
        
        # Reglas de entrada
        ec2.authorize_security_group_ingress(
            GroupId=SG_DATABASE,
            IpPermissions=[
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 
                 'UserIdGroupPairs': [{'GroupId': SG_FRONTEND}]},
                {'IpProtocol': 'tcp', 'FromPort': 3306, 'ToPort': 3306, 
                 'UserIdGroupPairs': [{'GroupId': SG_BACKEND}]},
                {'IpProtocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 
                 'UserIdGroupPairs': [{'GroupId': SG_FRONTEND}]},
            ]
        )
        print_message(GREEN, f"✓ Security Group Database creado: {SG_DATABASE}")
        print_message(GREEN, "  → Permite MySQL (3306) desde Backend SG, SSH desde Frontend SG")

except Exception as e:
    print_message(RED, f"✗ Error al configurar Security Groups: {e}")
    sys.exit(1)

# ==============================================================================
# 7. LANZAR INSTANCIAS EC2
# ==============================================================================
print_message(BLUE, "\n=== PASO 7: LANZANDO INSTANCIAS EC2 ===")

print_message(YELLOW, "⏳ Pausa de 10 segundos para propagación...")
time.sleep(10)

try:
    # Instancia Frontend (Pública)
    FRONTEND_INSTANCE_ID, frontend_public_ip, frontend_private_ip = get_existing_instance('frontend-web-mck21')
    
    if FRONTEND_INSTANCE_ID:
        print_message(GREEN, f"✓ Instancia Frontend ya existe: {FRONTEND_INSTANCE_ID}")
    else:
        response = ec2.run_instances(
            ImageId=AMI_ID,
            InstanceType='t2.micro',
            KeyName=KEY_NAME,
            MinCount=1,
            MaxCount=1,
            NetworkInterfaces=[{
                'DeviceIndex': 0,
                'SubnetId': FRONTEND_SUBNET,
                'Groups': [SG_FRONTEND],
                'AssociatePublicIpAddress': True,
            }],
            TagSpecifications=[
                {'ResourceType': 'instance', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': 'frontend-web-mck21'}
                ]}
            ]
        )
        
        FRONTEND_INSTANCE_ID = response['Instances'][0]['InstanceId']
        
        print_message(YELLOW, "⏳ Esperando a que Frontend esté disponible...")
        instance = ec2_resource.Instance(FRONTEND_INSTANCE_ID)
        instance.wait_until_running()
        instance.reload()
        frontend_public_ip = instance.public_ip_address
        frontend_private_ip = instance.private_ip_address
        
        print_message(GREEN, f"✓ Instancia Frontend lanzada: {FRONTEND_INSTANCE_ID}")
        print_message(GREEN, f"  → IP Pública: {frontend_public_ip}")

    # Instancia Backend (Privada)
    BACKEND_INSTANCE_ID, _, backend_private_ip = get_existing_instance('backend-app-mck21')
    
    if BACKEND_INSTANCE_ID:
        print_message(GREEN, f"✓ Instancia Backend ya existe: {BACKEND_INSTANCE_ID}")
    else:
        response = ec2.run_instances(
            ImageId=AMI_ID,
            InstanceType='t2.micro',
            KeyName=KEY_NAME,
            MinCount=1,
            MaxCount=1,
            NetworkInterfaces=[{
                'DeviceIndex': 0,
                'SubnetId': BACKEND_SUBNET,
                'Groups': [SG_BACKEND],
                'AssociatePublicIpAddress': False,
            }],
            TagSpecifications=[
                {'ResourceType': 'instance', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': 'backend-app-mck21'}
                ]}
            ]
        )
        
        BACKEND_INSTANCE_ID = response['Instances'][0]['InstanceId']
        
        print_message(YELLOW, "⏳ Esperando a que Backend esté disponible...")
        instance = ec2_resource.Instance(BACKEND_INSTANCE_ID)
        instance.wait_until_running()
        instance.reload()
        backend_private_ip = instance.private_ip_address
        
        print_message(GREEN, f"✓ Instancia Backend lanzada: {BACKEND_INSTANCE_ID}")
        print_message(GREEN, f"  → IP Privada: {backend_private_ip}")

    # Instancia Database (Privada)
    DATABASE_INSTANCE_ID, _, database_private_ip = get_existing_instance('database-db-mck21')
    
    if DATABASE_INSTANCE_ID:
        print_message(GREEN, f"✓ Instancia Database ya existe: {DATABASE_INSTANCE_ID}")
    else:
        response = ec2.run_instances(
            ImageId=AMI_ID,
            InstanceType='t2.micro',
            KeyName=KEY_NAME,
            MinCount=1,
            MaxCount=1,
            NetworkInterfaces=[{
                'DeviceIndex': 0,
                'SubnetId': DATABASE_SUBNET,
                'Groups': [SG_DATABASE],
                'AssociatePublicIpAddress': False,
            }],
            TagSpecifications=[
                {'ResourceType': 'instance', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': 'database-db-mck21'}
                ]}
            ]
        )
        
        DATABASE_INSTANCE_ID = response['Instances'][0]['InstanceId']
        
        print_message(YELLOW, "⏳ Esperando a que Database esté disponible...")
        instance = ec2_resource.Instance(DATABASE_INSTANCE_ID)
        instance.wait_until_running()
        instance.reload()
        database_private_ip = instance.private_ip_address
        
        print_message(GREEN, f"✓ Instancia Database lanzada: {DATABASE_INSTANCE_ID}")
        print_message(GREEN, f"  → IP Privada: {database_private_ip}")

except Exception as e:
    print_message(RED, f"✗ Error al lanzar instancias: {e}")

# ==============================================================================
# 8. RESUMEN FINAL
# ==============================================================================
print_message(GREEN, "\n╔═══════════════════════════════════════════════════════════╗")
print_message(GREEN, "║     INFRAESTRUCTURA 3 CAPAS CREADA EXITOSAMENTE          ║")
print_message(GREEN, "╚═══════════════════════════════════════════════════════════╝")

print("\n┌───────────────────────────────────────────────────────────────┐")
print("│ VPC Y CONECTIVIDAD                                            │")
print("├───────────────────────────────────────────────────────────────┤")
print(f"│ VPC ID:              {VPC_ID}")
print(f"│ VPC CIDR:            {VPC_CIDR}")
print(f"│ Internet Gateway:    {IGW}")
print(f"│ NAT Gateway:         {NAT}")
print("└───────────────────────────────────────────────────────────────┘")

print("\n┌───────────────────────────────────────────────────────────────┐")
print("│ SUBREDES                                                      │")
print("├───────────────────────────────────────────────────────────────┤")
print(f"│ Frontend (Pública):  {FRONTEND_SUBNET} ({FRONTEND_CIDR})")
print(f"│ Backend (Privada):   {BACKEND_SUBNET} ({BACKEND_CIDR})")
print(f"│ Database (Privada):  {DATABASE_SUBNET} ({DATABASE_CIDR})")
print("└───────────────────────────────────────────────────────────────┘")