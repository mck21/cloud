import boto3
import time
import sys

# ==============================================================================
# SCRIPT DE CREACIÓN DE INFRAESTRUCTURA AWS VPC (Boto3)
# Descripción: Crea una VPC con subredes públicas/privadas, NAT Gateway,
#              tablas de ruteo, NACLs, Security Groups y lanza 2 instancias EC2.
# Recursos: Todos llevan sufijo -mck21 y tag key=tag value=mck21
# ==============================================================================

# ==============================================================================
# VARIABLES DE CONFIGURACIÓN
# ==============================================================================
TAG_KEY = "tag"
TAG_VALUE = "mck21" # El tag es para borrar los recursos después con clean_mck21.py
SUFFIX = "-mck21"
VPC_CIDR = "10.10.0.0/16"
PUB_SUB1_CIDR = "10.10.1.0/24"
PUB_SUB2_CIDR = "10.10.2.0/24"
PRIV_SUB1_CIDR = "10.10.3.0/24"
PRIV_SUB2_CIDR = "10.10.4.0/24"
REGION = "us-east-1"
#REGION2 = "us-west-2"  
KEY_NAME = "vockey"
#OREGON_KEY_NAME = "oregon-key"  
AMI_ID = "ami-07ff62358b87c7116"  # Amazon Linux 2 AMI (x86_64) en us-east-1 
#OREGON_AMI_ID = "ami-00a8151272c45cd8e"  # Amazon Linux 2 AMI (x86_64) en us-west-2

AZ1 = f"{REGION}a"
AZ2 = f"{REGION}b"

# Colores para output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
NC = '\033[0m' # No Color

# Cliente EC2
ec2 = boto3.client('ec2', region_name=REGION)
ec2_resource = boto3.resource('ec2', region_name=REGION)

# Variables para almacenar IDs de recursos
VPC_ID = None
PUB_SUB1 = None
PUB_SUB2 = None
PRIV_SUB1 = None
PRIV_SUB2 = None
IGW = None
EIP = None
NAT = None
RT_PUB1 = None
RT_PUB2 = None
RT_PRIV1 = None
RT_PRIV2 = None
NACL_PUB = None
NACL_PRIV = None
SG_PUB = None
SG_PRIV = None
BASTION_ID = None
BASTION_IP = None
PRIVATE_SERVER_ID = None

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def print_message(color, message):
    """Función para imprimir mensajes con formato."""
    print(f"{color}{message}{NC}")

def create_tags(resource_id, name):
    """Función auxiliar para aplicar tags de Name y mck21."""
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
    
    # Manejo específico para VPCs y NAT Gateways (que requieren el filtro de estado)
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
        # Filtra el default SG
        groups = [sg for sg in response['SecurityGroups'] if sg['GroupName'] != 'default']
        return groups[0]['GroupId'] if groups else None
        
    return None

def get_existing_instance(tag_name):
    """Busca una instancia EC2 existente por el tag de Name y estado running/pending."""
    filters = [
        {'Name': 'vpc-id', 'Values': [VPC_ID]},
        {'Name': 'tag:Name', 'Values': [tag_name]},
        {'Name': 'instance-state-name', 'Values': ['pending', 'running']},
    ]
    response = ec2.describe_instances(Filters=filters)
    
    if response['Reservations'] and response['Reservations'][0]['Instances']:
        instance = response['Reservations'][0]['Instances'][0]
        instance_id = instance['InstanceId']
        # Si es la Bastion, intenta obtener la IP pública
        ip_address = instance.get('PublicIpAddress')
        return instance_id, ip_address
    return None, None

# ==============================================================================
# 1. CREAR VPC
# ==============================================================================
print_message(YELLOW, "\n=== CREANDO VPC ===")

try:
    VPC_ID = get_existing_resource_by_tag('vpcs', 'vpc')
    
    if VPC_ID:
        print_message(GREEN, f"✓ VPC ya existe: {VPC_ID}")
    else:
        response = ec2.create_vpc(
            CidrBlock=VPC_CIDR,
            TagSpecifications=[
                {'ResourceType': 'vpc', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'vpc{SUFFIX}'}
                ]}
            ]
        )
        VPC_ID = response['Vpc']['VpcId']
        
        # Habilitar DNS
        ec2.modify_vpc_attribute(VpcId=VPC_ID, EnableDnsHostnames={'Value': True})
        ec2.modify_vpc_attribute(VpcId=VPC_ID, EnableDnsSupport={'Value': True})
        
        print_message(GREEN, f"✓ VPC creada: {VPC_ID}")
except Exception as e:
    print_message(RED, f"Error al crear VPC: {e}")
    sys.exit(1)

# ==============================================================================
# 2. CREAR SUBREDES
# ==============================================================================
print_message(YELLOW, "\n=== CREANDO SUBREDES ===")

# Subred pública 1
try:
    PUB_SUB1 = get_existing_resource_by_tag('subnets', 'public-subnet-1')
    if PUB_SUB1:
        print_message(GREEN, f"✓ Subred pública 1 ya existe: {PUB_SUB1}")
    else:
        response = ec2.create_subnet(
            VpcId=VPC_ID,
            CidrBlock=PUB_SUB1_CIDR,
            AvailabilityZone=AZ1,
            TagSpecifications=[
                {'ResourceType': 'subnet', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'public-subnet-1{SUFFIX}'}
                ]}
            ]
        )
        PUB_SUB1 = response['Subnet']['SubnetId']
        # Auto-asignar IP pública
        ec2.modify_subnet_attribute(SubnetId=PUB_SUB1, MapPublicIpOnLaunch={'Value': True})
        print_message(GREEN, f"✓ Subred pública 1 creada: {PUB_SUB1} ({PUB_SUB1_CIDR} - {AZ1})")

    # Subred pública 2
    PUB_SUB2 = get_existing_resource_by_tag('subnets', 'public-subnet-2')
    if PUB_SUB2:
        print_message(GREEN, f"✓ Subred pública 2 ya existe: {PUB_SUB2}")
    else:
        response = ec2.create_subnet(
            VpcId=VPC_ID,
            CidrBlock=PUB_SUB2_CIDR,
            AvailabilityZone=AZ2,
            TagSpecifications=[
                {'ResourceType': 'subnet', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'public-subnet-2{SUFFIX}'}
                ]}
            ]
        )
        PUB_SUB2 = response['Subnet']['SubnetId']
        ec2.modify_subnet_attribute(SubnetId=PUB_SUB2, MapPublicIpOnLaunch={'Value': True})
        print_message(GREEN, f"✓ Subred pública 2 creada: {PUB_SUB2} ({PUB_SUB2_CIDR} - {AZ2})")

    # Subred privada 1
    PRIV_SUB1 = get_existing_resource_by_tag('subnets', 'private-subnet-1')
    if PRIV_SUB1:
        print_message(GREEN, f"✓ Subred privada 1 ya existe: {PRIV_SUB1}")
    else:
        response = ec2.create_subnet(
            VpcId=VPC_ID,
            CidrBlock=PRIV_SUB1_CIDR,
            AvailabilityZone=AZ1,
            TagSpecifications=[
                {'ResourceType': 'subnet', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'private-subnet-1{SUFFIX}'}
                ]}
            ]
        )
        PRIV_SUB1 = response['Subnet']['SubnetId']
        print_message(GREEN, f"✓ Subred privada 1 creada: {PRIV_SUB1} ({PRIV_SUB1_CIDR} - {AZ1})")

    # Subred privada 2
    PRIV_SUB2 = get_existing_resource_by_tag('subnets', 'private-subnet-2')
    if PRIV_SUB2:
        print_message(GREEN, f"✓ Subred privada 2 ya existe: {PRIV_SUB2}")
    else:
        response = ec2.create_subnet(
            VpcId=VPC_ID,
            CidrBlock=PRIV_SUB2_CIDR,
            AvailabilityZone=AZ2,
            TagSpecifications=[
                {'ResourceType': 'subnet', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'private-subnet-2{SUFFIX}'}
                ]}
            ]
        )
        PRIV_SUB2 = response['Subnet']['SubnetId']
        print_message(GREEN, f"✓ Subred privada 2 creada: {PRIV_SUB2} ({PRIV_SUB2_CIDR} - {AZ2})")

except Exception as e:
    print_message(RED, f"Error al crear subredes: {e}")
    sys.exit(1)


# ==============================================================================
# 3. CREAR Y ASOCIAR INTERNET GATEWAY
# ==============================================================================
print_message(YELLOW, "\n=== CONFIGURANDO INTERNET GATEWAY ===")

try:
    # Buscar IGW asociado a la VPC
    response = ec2.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [VPC_ID]}])
    IGW = response['InternetGateways'][0]['InternetGatewayId'] if response['InternetGateways'] else None

    if IGW:
        print_message(GREEN, f"✓ Internet Gateway ya existe y está asociado: {IGW}")
    else:
        # Crea IGW
        response = ec2.create_internet_gateway(
            TagSpecifications=[
                {'ResourceType': 'internet-gateway', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'igw{SUFFIX}'}
                ]}
            ]
        )
        IGW = response['InternetGateway']['InternetGatewayId']
        
        # Asociar a VPC
        ec2.attach_internet_gateway(VpcId=VPC_ID, InternetGatewayId=IGW)
        print_message(GREEN, f"✓ Internet Gateway creado y asociado: {IGW}")
        
except Exception as e:
    print_message(RED, f"Error al configurar IGW: {e}")
    sys.exit(1)


# ==============================================================================
# 4. CREAR ELASTIC IP Y NAT GATEWAY
# ==============================================================================
print_message(YELLOW, "\n=== CONFIGURANDO NAT GATEWAY ===")

# Buscar NAT Gateway existente (disponible o pendiente)
try:
    NAT = get_existing_resource_by_tag('nat-gateways', 'ngw')
    
    if NAT:
        # Si se encuentra, intenta obtener su EIP
        response = ec2.describe_nat_gateways(NatGatewayIds=[NAT])
        EIP = response['NatGateways'][0]['NatGatewayAddresses'][0]['AllocationId']
        print_message(GREEN, f"✓ NAT Gateway ya existe: {NAT}")
        print_message(GREEN, f"✓ Elastic IP asociada: {EIP}")
    else:
        # Crear Elastic IP
        response = ec2.allocate_address(
            Domain='vpc',
            TagSpecifications=[
                {'ResourceType': 'elastic-ip', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'eip{SUFFIX}'}
                ]}
            ]
        )
        EIP = response['AllocationId']
        print_message(GREEN, f"✓ Elastic IP creada: {EIP}")
        
        # Crear NAT Gateway
        response = ec2.create_nat_gateway(
            SubnetId=PUB_SUB1,
            AllocationId=EIP,
            TagSpecifications=[
                {'ResourceType': 'natgateway', 'Tags': [
                    {'Key': TAG_KEY, 'Value': TAG_VALUE},
                    {'Key': 'Name', 'Value': f'ngw{SUFFIX}'}
                ]}
            ]
        )
        NAT = response['NatGateway']['NatGatewayId']
        
        print_message(YELLOW, "⏳ Esperando a que NAT Gateway esté disponible...")
        waiter = ec2.get_waiter('nat_gateway_available')
        waiter.wait(NatGatewayIds=[NAT])
        print_message(GREEN, f"✓ NAT Gateway creado y disponible: {NAT}")

except Exception as e:
    print_message(RED, f"Error al configurar NAT Gateway: {e}")
    sys.exit(1)


# ==============================================================================
# 5. CREAR TABLAS DE RUTEO
# ==============================================================================
print_message(YELLOW, "\n=== CONFIGURANDO TABLAS DE RUTEO ===")

def create_and_configure_rt(name, subnet_id, target_id, target_type, rt_var_name):
    """Crea, etiqueta, añade ruta y asocia una Route Table."""
    global RT_PUB1, RT_PUB2, RT_PRIV1, RT_PRIV2
    
    rt_id = get_existing_resource_by_tag('route-tables', name)
    
    if rt_id:
        print_message(GREEN, f"✓ Tabla de ruteo {name} ya existe: {rt_id}")
        return rt_id
    
    # Crear Route Table
    response = ec2.create_route_table(
        VpcId=VPC_ID,
        TagSpecifications=[
            {'ResourceType': 'route-table', 'Tags': [
                {'Key': TAG_KEY, 'Value': TAG_VALUE},
                {'Key': 'Name', 'Value': f'{name}{SUFFIX}'}
            ]}
        ]
    )
    rt_id = response['RouteTable']['RouteTableId']
    
    # Añadir ruta por defecto (0.0.0.0/0)
    route_params = {
        'RouteTableId': rt_id,
        'DestinationCidrBlock': '0.0.0.0/0',
    }
    if target_type == 'igw':
        route_params['GatewayId'] = target_id
    elif target_type == 'nat':
        route_params['NatGatewayId'] = target_id
        
    ec2.create_route(**route_params)
    
    # Asociar a subred
    ec2.associate_route_table(SubnetId=subnet_id, RouteTableId=rt_id)
    
    print_message(GREEN, f"✓ Tabla de ruteo {name} creada y asociada: {rt_id}")
    return rt_id

try:
    # RT Pública 1 (apunta a IGW)
    RT_PUB1 = create_and_configure_rt('public-rt-1', PUB_SUB1, IGW, 'igw', 'RT_PUB1')
    
    # RT Pública 2 (apunta a IGW, solo se crea/etiqueta/asocia, la ruta ya se crea en la 1)
    RT_PUB2 = create_and_configure_rt('public-rt-2', PUB_SUB2, IGW, 'igw', 'RT_PUB2')
    
    # RT Privada 1 (apunta a NAT)
    RT_PRIV1 = create_and_configure_rt('private-rt-1', PRIV_SUB1, NAT, 'nat', 'RT_PRIV1')
    
    # RT Privada 2 (apunta a NAT)
    RT_PRIV2 = create_and_configure_rt('private-rt-2', PRIV_SUB2, NAT, 'nat', 'RT_PRIV2')

except Exception as e:
    print_message(RED, f"Error al configurar tablas de ruteo: {e}")
    sys.exit(1)


# ==============================================================================
# 6. CONFIGURAR NETWORK ACLs
# ==============================================================================
print_message(YELLOW, "\n=== CONFIGURANDO NETWORK ACLs ===")

def create_and_configure_nacl(name, subnet_ids, ingress_rules, egress_rules):
    """Crea, etiqueta, configura reglas y asocia una NACL."""
    nacl_id = get_existing_resource_by_tag('network-acls', name)
    
    if nacl_id:
        print_message(GREEN, f"✓ NACL {name} ya existe: {nacl_id}")
        return nacl_id

    # Crear NACL
    response = ec2.create_network_acl(
        VpcId=VPC_ID,
        TagSpecifications=[
            {'ResourceType': 'network-acl', 'Tags': [
                {'Key': TAG_KEY, 'Value': TAG_VALUE},
                {'Key': 'Name', 'Value': f'{name}{SUFFIX}'}
            ]}
        ]
    )
    nacl_id = response['NetworkAcl']['NetworkAclId']

    # Las NACLs por defecto deniegan todo, pero Boto3 crea una con una regla DENY *
    # Es necesario reemplazar las asociaciones por defecto por las nuevas.

    # Configurar reglas de entrada
    for rule in ingress_rules:
        ec2.create_network_acl_entry(
            NetworkAclId=nacl_id,
            Egress=False,
            RuleNumber=rule['RuleNumber'],
            Protocol=rule['Protocol'],
            RuleAction=rule['RuleAction'],
            CidrBlock=rule['CidrBlock'],
            PortRange=rule.get('PortRange')
        )
        
    # Configurar reglas de salida
    for rule in egress_rules:
        ec2.create_network_acl_entry(
            NetworkAclId=nacl_id,
            Egress=True,
            RuleNumber=rule['RuleNumber'],
            Protocol=rule['Protocol'],
            RuleAction=rule['RuleAction'],
            CidrBlock=rule['CidrBlock'],
            PortRange=rule.get('PortRange')
        )

    # Asociar a subredes
    for subnet_id in subnet_ids:
        # Encontrar la asociación por defecto para reemplazarla
        response = ec2.describe_network_acls(
            Filters=[{'Name': 'association.subnet-id', 'Values': [subnet_id]}]
        )
        # Buscar la ID de asociación de la NACL por defecto para esa subred
        # Puede haber más de una, pero buscamos la que asocia la subred
        assoc_id = None
        for acl in response['NetworkAcls']:
            for assoc in acl['Associations']:
                if assoc['SubnetId'] == subnet_id:
                    assoc_id = assoc['NetworkAclAssociationId']
                    break
            if assoc_id:
                break
        
        if assoc_id:
            ec2.replace_network_acl_association(
                AssociationId=assoc_id,
                NetworkAclId=nacl_id
            )
        else:
            # En caso de que no haya asociación, forzar una nueva. (Esto no debería pasar en la VPC por defecto)
            ec2.associate_network_acl(
                NetworkAclId=nacl_id,
                SubnetId=subnet_id
            )

    print_message(GREEN, f"✓ NACL {name} creada y asociada: {nacl_id}")
    return nacl_id

try:
    # NACL Pública
    ingress_pub_rules = [
        # HTTP
        {'RuleNumber': 100, 'Protocol': '6', 'RuleAction': 'allow', 'CidrBlock': '0.0.0.0/0', 'PortRange': {'From': 80, 'To': 80}},
        # HTTPS
        {'RuleNumber': 110, 'Protocol': '6', 'RuleAction': 'allow', 'CidrBlock': '0.0.0.0/0', 'PortRange': {'From': 443, 'To': 443}},
        # SSH
        {'RuleNumber': 120, 'Protocol': '6', 'RuleAction': 'allow', 'CidrBlock': '0.0.0.0/0', 'PortRange': {'From': 22, 'To': 22}},
        # Puertos efímeros (TCP)
        {'RuleNumber': 130, 'Protocol': '6', 'RuleAction': 'allow', 'CidrBlock': '0.0.0.0/0', 'PortRange': {'From': 1024, 'To': 65535}},
    ]
    egress_pub_rules = [
        # Todo saliente
        {'RuleNumber': 100, 'Protocol': '-1', 'RuleAction': 'allow', 'CidrBlock': '0.0.0.0/0'},
    ]
    NACL_PUB = create_and_configure_nacl('public-nacl', [PUB_SUB1, PUB_SUB2], ingress_pub_rules, egress_pub_rules)

    # NACL Privada
    ingress_priv_rules = [
        # Todo entrante desde el CIDR de la VPC (10.10.0.0/16)
        {'RuleNumber': 100, 'Protocol': '-1', 'RuleAction': 'allow', 'CidrBlock': VPC_CIDR},
    ]
    egress_priv_rules = [
        # Todo saliente (incluye efímeros para respuestas, tráfico NAT/IGW)
        {'RuleNumber': 100, 'Protocol': '-1', 'RuleAction': 'allow', 'CidrBlock': '0.0.0.0/0'},
    ]
    NACL_PRIV = create_and_configure_nacl('private-nacl', [PRIV_SUB1, PRIV_SUB2], ingress_priv_rules, egress_priv_rules)

except Exception as e:
    print_message(RED, f"Error al configurar NACLs: {e}")
    sys.exit(1)


# ==============================================================================
# 7. CREAR SECURITY GROUPS
# ==============================================================================
print_message(YELLOW, "\n=== CONFIGURANDO SECURITY GROUPS ===")

def create_and_configure_sg(name, description, ingress_rules):
    """Crea, etiqueta y configura las reglas de entrada de un Security Group."""
    sg_id = get_existing_resource_by_tag('security-groups', name)
    
    if sg_id:
        print_message(GREEN, f"✓ Security Group {name} ya existe: {sg_id}")
        return sg_id
    
    # Crear Security Group
    response = ec2.create_security_group(
        GroupName=f'{name}{SUFFIX}',
        Description=description,
        VpcId=VPC_ID,
        TagSpecifications=[
            {'ResourceType': 'security-group', 'Tags': [
                {'Key': TAG_KEY, 'Value': TAG_VALUE},
                {'Key': 'Name', 'Value': f'{name}{SUFFIX}'}
            ]}
        ]
    )
    sg_id = response['GroupId']
    
    # Configurar reglas de entrada
    ip_permissions = []
    for rule in ingress_rules:
        perm = {
            'IpProtocol': rule['Protocol'],
            'FromPort': rule['FromPort'],
            'ToPort': rule['ToPort'],
        }
        if 'CidrBlock' in rule:
            perm['IpRanges'] = [{'CidrIp': rule['CidrBlock']}]
        if 'SourceSecurityGroupId' in rule:
            perm['UserIdGroupPairs'] = [{'GroupId': rule['SourceSecurityGroupId']}]
        
        ip_permissions.append(perm)
    
    if ip_permissions:
        ec2.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=ip_permissions)
    
    print_message(GREEN, f"✓ Security Group {name} creado: {sg_id}")
    return sg_id

try:
    # Security Group público (Bastion)
    ingress_pub_rules = [
        # SSH desde cualquier lugar
        {'Protocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'CidrBlock': '0.0.0.0/0'},
        # HTTP desde cualquier lugar
        {'Protocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'CidrBlock': '0.0.0.0/0'},
    ]
    SG_PUB = create_and_configure_sg('public-sg', "Security Group for public subnet - Bastion", ingress_pub_rules)

    # Security Group privado
    ingress_priv_rules = [
        # SSH SOLO desde el Security Group público
        {'Protocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'SourceSecurityGroupId': SG_PUB},
        # ICMP SOLO desde el Security Group público
        {'Protocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 'SourceSecurityGroupId': SG_PUB},
    ]
    SG_PRIV = create_and_configure_sg('private-sg', "Security Group for private subnet - Only accessible from public SG", ingress_priv_rules)

except Exception as e:
    print_message(RED, f"Error al configurar Security Groups: {e}")
    sys.exit(1)


# ==============================================================================
# 8. LANZAR INSTANCIAS EC2 DE PRUEBA
# ==============================================================================
print_message(YELLOW, "\n=== LANZANDO INSTANCIAS EC2 DE PRUEBA ===")

# Pausa para propagación de tablas de ruteo
print_message(YELLOW, "⏳ Pausa de 10 segundos para propagación de rutas...")
time.sleep(10)

def launch_instance(name, subnet_id, sg_id, associate_public_ip):
    """Lanza o encuentra una instancia EC2 de prueba."""
    tag_name = name
    instance_id, public_ip = get_existing_instance(tag_name)
    
    if instance_id:
        print_message(GREEN, f"✓ Instancia {name} ya existe: {instance_id}")
        return instance_id, public_ip
    
    # Crear instancia
    response = ec2.run_instances(
        ImageId=AMI_ID,
        InstanceType='t2.micro',
        KeyName=KEY_NAME,
        MinCount=1,
        MaxCount=1,
        NetworkInterfaces=[{
            'DeviceIndex': 0,
            'SubnetId': subnet_id,
            'Groups': [sg_id],
            'AssociatePublicIpAddress': associate_public_ip,
        }],
        TagSpecifications=[
            {'ResourceType': 'instance', 'Tags': [
                {'Key': TAG_KEY, 'Value': TAG_VALUE},
                {'Key': 'Name', 'Value': tag_name}
            ]}
        ]
    )
    
    instance_id = response['Instances'][0]['InstanceId']
    
    # Esperar a que la instancia esté running para obtener la IP
    print_message(YELLOW, f"⏳ Esperando a que la instancia {name} esté disponible...")
    instance = ec2_resource.Instance(instance_id)
    instance.wait_until_running()
    
    # Recargar datos de la instancia
    instance.reload()
    public_ip = instance.public_ip_address if associate_public_ip else None

    print_message(GREEN, f"✓ Instancia {name} lanzada: {instance_id} (IP: {public_ip or 'N/A'})")
    return instance_id, public_ip

try:
    # Instancia Bastion (pública)
    BASTION_ID, BASTION_IP = launch_instance('bastion-public-mck21', PUB_SUB1, SG_PUB, True)

    # Instancia Privada
    PRIVATE_SERVER_ID, _ = launch_instance('server-private-mck21', PRIV_SUB1, SG_PRIV, False)

except Exception as e:
    print_message(RED, f"Error al lanzar instancias: {e}")
    # Continuar para el resumen

# ==============================================================================
# 9. RESUMEN DE RECURSOS CREADOS
# ==============================================================================
print_message(GREEN, "\n╔════════════════════════════════════════════════════════════════╗")
print_message(GREEN, "║          INFRAESTRUCTURA AWS CREADA EXITOSAMENTE              ║")
print_message(GREEN, "╚════════════════════════════════════════════════════════════════╝")

# Buscar IP privada de la instancia privada (solo si se creó)
PRIVATE_IP = "N/A"
if PRIVATE_SERVER_ID and PRIVATE_SERVER_ID != 'None':
    try:
        response = ec2.describe_instances(InstanceIds=[PRIVATE_SERVER_ID])
        PRIVATE_IP = response['Reservations'][0]['Instances'][0].get('PrivateIpAddress', 'N/A')
    except:
        pass


print("\n┌─────────────────────────────────────────────────────────────────┐")
print("│ VPC Y CONECTIVIDAD                                              │")
print("├─────────────────────────────────────────────────────────────────┤")
print(f"│ VPC ID:              {VPC_ID}")
print(f"│ VPC CIDR:            {VPC_CIDR}")
print(f"│ Internet Gateway:    {IGW}")
print(f"│ NAT Gateway:         {NAT}")
print("└─────────────────────────────────────────────────────────────────┘")

print("\n┌─────────────────────────────────────────────────────────────────┐")
print("│ SUBREDES                                                        │")
print("├─────────────────────────────────────────────────────────────────┤")
print(f"│ Subred Pública 1:    {PUB_SUB1} ({PUB_SUB1_CIDR} - {AZ1})")
print(f"│ Subred Privada 1:    {PRIV_SUB1} ({PRIV_SUB1_CIDR} - {AZ1})")
print("└─────────────────────────────────────────────────────────────────┘")

print("\n┌─────────────────────────────────────────────────────────────────┐")
print("│ TABLAS DE RUTEO                                                 │")
print("├─────────────────────────────────────────────────────────────────┤")
print(f"│ RT Pública 1:        {RT_PUB1} → IGW")
print(f"│ RT Privada 1:        {RT_PRIV1} → NAT")
print("└─────────────────────────────────────────────────────────────────┘")

print("\n┌─────────────────────────────────────────────────────────────────┐")
print("│ INSTANCIAS DE PRUEBA LANZADAS                                   │")
print("├─────────────────────────────────────────────────────────────────┤")
print(f"│ Bastion ID:          {BASTION_ID or 'N/A'}")
print(f"│ Bastion IP Pública:  {BASTION_IP or 'N/A'}")
print(f"│ Servidor Privado ID: {PRIVATE_SERVER_ID or 'N/A'}")
print(f"│ Servidor IP Privada: {PRIVATE_IP}")
print("└─────────────────────────────────────────────────────────────────┘")

print("\n")
print_message(YELLOW, "════════════════════════════════════════════════════════════════")
print_message(YELLOW, "  INSTRUCCIONES DE ACCESO")
print_message(YELLOW, "════════════════════════════════════════════════════════════════")
print("\n")
print(f"Para conectarte al Bastion, usa tu clave ({KEY_NAME}) y la IP Pública:")
print(f"ssh -i {KEY_NAME}.pem ubuntu@{BASTION_IP or 'PUBLIC_IP_DEL_BASTION'}")
print("\n")
print("Una vez en el Bastion, puedes acceder a la instancia privada usando el reenvío de agente (Agent Forwarding) o copiando tu clave a Bastion:")
print(f"ssh ubuntu@{PRIVATE_IP}")
print("\n")

print_message(GREEN, "✓ Script completado exitosamente")