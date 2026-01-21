import boto3

# Configuración de variables
REGION = "us-east-1"
KEY_NAME = "vockey"
AMI_ID = "ami-07ff62358b87c7116"
TAG_SPEC = [{'ResourceType': 'vpc', 'Tags': [{'Key': 'tag', 'Value': 'mck21'}]},
            {'ResourceType': 'subnet', 'Tags': [{'Key': 'tag', 'Value': 'mck21'}]},
            {'ResourceType': 'internet-gateway', 'Tags': [{'Key': 'tag', 'Value': 'mck21'}]},
            {'ResourceType': 'network-acl', 'Tags': [{'Key': 'tag', 'Value': 'mck21'}]},
            {'ResourceType': 'security-group', 'Tags': [{'Key': 'tag', 'Value': 'mck21'}]},
            {'ResourceType': 'instance', 'Tags': [{'Key': 'tag', 'Value': 'mck21'}]}]

ec2 = boto3.resource('ec2', region_name=REGION)
client = boto3.client('ec2', region_name=REGION)

def create_scenario():
    print("Iniciando creación de escenario AWS...")

    # 1. Crear VPC
    vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16', TagSpecifications=[TAG_SPEC[0]])
    vpc.wait_until_available()
    print(f"VPC creada: {vpc.id}")

    # 2. Crear Subredes
    sub_pub = vpc.create_subnet(CidrBlock='10.0.1.0/24', TagSpecifications=[TAG_SPEC[1]])
    sub_priv = vpc.create_subnet(CidrBlock='10.0.2.0/24', TagSpecifications=[TAG_SPEC[1]])
    print(f"Subred Pública: {sub_pub.id} | Subred Privada: {sub_priv.id}")

    # 3. Internet Gateway para la subred pública
    igw = ec2.create_internet_gateway(TagSpecifications=[TAG_SPEC[2]])
    vpc.attach_internet_gateway(InternetGatewayId=igw.id)
    
    rt_pub = vpc.create_route_table()
    rt_pub.create_route(DestinationCidrBlock='0.0.0.0/0', GatewayId=igw.id)
    rt_pub.associate_with_subnet(SubnetId=sub_pub.id)

    # 4. Configuración de Network ACLs (NACL)
    
    # NACL Pública
    nacl_pub = ec2.create_network_acl(VpcId=vpc.id, TagSpecifications=[TAG_SPEC[3]])
    
    # Inbound: Permitir HTTP (80) y HTTPS (443) desde Internet
    client.create_network_acl_entry(NetworkAclId=nacl_pub.id, RuleNumber=100, Protocol='6', PortRange={'From': 80, 'To': 80}, CidrBlock='0.0.0.0/0', RuleAction='allow', Egress=False)
    client.create_network_acl_entry(NetworkAclId=nacl_pub.id, RuleNumber=110, Protocol='6', PortRange={'From': 443, 'To': 443}, CidrBlock='0.0.0.0/0', RuleAction='allow', Egress=False)
    # IMPORTANTE: Permitir puertos efímeros para respuesta del tráfico (Stateless)
    client.create_network_acl_entry(NetworkAclId=nacl_pub.id, RuleNumber=120, Protocol='6', PortRange={'From': 1024, 'To': 65535}, CidrBlock='0.0.0.0/0', RuleAction='allow', Egress=False)
    
    # Outbound: Permitir todo para simplificar respuesta
    client.create_network_acl_entry(NetworkAclId=nacl_pub.id, RuleNumber=100, Protocol='-1', CidrBlock='0.0.0.0/0', RuleAction='allow', Egress=True)
    
    client.replace_network_acl_association(AssociationId=client.describe_network_acls(Filters=[{'Name': 'association.subnet-id', 'Values': [sub_pub.id]}])['NetworkAcls'][0]['Associations'][0]['NetworkAclAssociationId'], NetworkAclId=nacl_pub.id)

    # NACL Privada
    nacl_priv = ec2.create_network_acl(VpcId=vpc.id, TagSpecifications=[TAG_SPEC[3]])
    # Inbound: Solo desde la subred pública
    client.create_network_acl_entry(NetworkAclId=nacl_priv.id, RuleNumber=100, Protocol='-1', CidrBlock='10.0.1.0/24', RuleAction='allow', Egress=False)
    # Outbound: Hacia la subred pública
    client.create_network_acl_entry(NetworkAclId=nacl_priv.id, RuleNumber=100, Protocol='-1', CidrBlock='10.0.1.0/24', RuleAction='allow', Egress=True)
    
    client.replace_network_acl_association(AssociationId=client.describe_network_acls(Filters=[{'Name': 'association.subnet-id', 'Values': [sub_priv.id]}])['NetworkAcls'][0]['Associations'][0]['NetworkAclAssociationId'], NetworkAclId=nacl_priv.id)

    # 5. Security Groups (naming con gs-)
    sg_pub = ec2.create_security_group(GroupName='gs-public-sg', Description='SG Publico', VpcId=vpc.id, TagSpecifications=[TAG_SPEC[4]])
    sg_pub.authorize_ingress(IpPermissions=[
        {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
    ])

    print("Escenario creado exitosamente con tags 'mck21' y prefijos 'gs-'.")

if __name__ == "__main__":
    create_scenario()