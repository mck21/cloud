import boto3
import time
from botocore.exceptions import ClientError

# =====================
# CONFIG
# =====================
REGION_EAST = "us-east-1"
REGION_WEST = "us-west-2"
ACCOUNT_ID = "799197207122" 
KEY_NAME_EAST = "vockey"
KEY_NAME_WEST = "oregon-key"
AMI_ID_EAST = "ami-07ff62358b87c7116"  # Amazon Linux 2 x86_64 us-east-1
AMI_ID_WEST = "ami-00a8151272c45cd8e"  # Amazon Linux 2 x86_64 us-west-2
TAG_SPEC = [{"Key": "tag", "Value": "mck21"}]

ec2_east = boto3.client("ec2", region_name=REGION_EAST)
ec2_west = boto3.client("ec2", region_name=REGION_WEST)

# =====================
# HELPERS
# =====================
def tag(resource_id, client):
    client.create_tags(Resources=[resource_id], Tags=TAG_SPEC)

def wait_for_tgw_available(client, tgw_id):
    print(f"Esperando TGW {tgw_id}...")
    while True:
        state = client.describe_transit_gateways(TransitGatewayIds=[tgw_id])["TransitGateways"][0]["State"]
        if state == "available":
            print(f"TGW {tgw_id} disponible")
            return
        time.sleep(10)

def wait_for_peering_pending_acceptance(client, tgw_id):
    print("Esperando peering en estado pendingAcceptance...")
    while True:
        try:
            resp = client.describe_transit_gateway_peering_attachments(
                Filters=[
                    {"Name": "transit-gateway-id", "Values": [tgw_id]},
                    {"Name": "state", "Values": ["pendingAcceptance"]}
                ]
            )
            attachments = resp.get("TransitGatewayPeeringAttachments", [])
            if attachments:
                att_id = attachments[0]["TransitGatewayAttachmentId"]
                print(f"Peering visible: {att_id}")
                return att_id
        except ClientError:
            pass
        time.sleep(10)

def create_vpc(client, cidr):
    vpc = client.create_vpc(CidrBlock=cidr)["Vpc"]
    vpc_id = vpc["VpcId"]
    tag(vpc_id, client)
    client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={"Value": True})
    client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={"Value": True})
    
    # Crear Internet Gateway
    igw = client.create_internet_gateway()["InternetGateway"]
    igw_id = igw["InternetGatewayId"]
    tag(igw_id, client)
    
    # Adjuntar IGW a la VPC
    client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    
    # Obtener la tabla de rutas principal
    route_tables = client.describe_route_tables(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    )["RouteTables"]
    main_rt_id = route_tables[0]["RouteTableId"]
    
    # Agregar ruta a Internet
    client.create_route(
        RouteTableId=main_rt_id,
        DestinationCidrBlock="0.0.0.0/0",
        GatewayId=igw_id
    )
    
    return vpc_id

def create_subnet(client, vpc_id, cidr, az):
    subnet = client.create_subnet(VpcId=vpc_id, CidrBlock=cidr, AvailabilityZone=az)["Subnet"]
    tag(subnet["SubnetId"], client)
    # Opción 1: auto-assign public IP
    client.modify_subnet_attribute(SubnetId=subnet["SubnetId"], MapPublicIpOnLaunch={"Value": True})
    return subnet["SubnetId"]

def create_security_group(client, vpc_id, name, description):
    sg = client.create_security_group(
        GroupName=name,
        Description=description,
        VpcId=vpc_id
    )
    tag(sg['GroupId'], client)
    # Permitir SSH y ICMP entrante
    client.authorize_security_group_ingress(
        GroupId=sg['GroupId'],
        IpPermissions=[
            {
                'IpProtocol': 'icmp',
                'FromPort': -1,
                'ToPort': -1,
                'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges':[{'CidrIp':'0.0.0.0/0'}]
            }
        ]
    )
    return sg['GroupId']

def create_ec2(client, subnet_id, sg_id, ami_id, key_name):
    instance = client.run_instances(
        ImageId=ami_id,
        InstanceType='t2.micro',
        KeyName=key_name,
        MaxCount=1,
        MinCount=1,
        SubnetId=subnet_id,
        SecurityGroupIds=[sg_id],
        TagSpecifications=[{"ResourceType":"instance","Tags":TAG_SPEC}]
    )['Instances'][0]
    
    instance_id = instance['InstanceId']
    private_ip = instance['PrivateIpAddress']
    public_ip = instance.get('PublicIpAddress')  # Ya existirá gracias al MapPublicIpOnLaunch
    return instance_id, private_ip, public_ip

# =====================
# CREAR VPCS Y SUBNETS
# =====================
vpc_e1 = create_vpc(ec2_east, "10.0.0.0/16")
vpc_e2 = create_vpc(ec2_east, "10.1.0.0/16")
vpc_w  = create_vpc(ec2_west, "10.2.0.0/16")

sub_e1 = create_subnet(ec2_east, vpc_e1, "10.0.1.0/24", "us-east-1a")
sub_e2 = create_subnet(ec2_east, vpc_e2, "10.1.1.0/24", "us-east-1a")
sub_w  = create_subnet(ec2_west, vpc_w,  "10.2.1.0/24", "us-west-2a")

# =====================
# SECURITY GROUPS PARA PING
# =====================
sg_e1 = create_security_group(ec2_east, vpc_e1, "gs-icmp-e1", "Allow ICMP for testing")
sg_e2 = create_security_group(ec2_east, vpc_e2, "gs-icmp-e2", "Allow ICMP for testing")
sg_w  = create_security_group(ec2_west, vpc_w,  "gs-icmp-w",  "Allow ICMP for testing")

# =====================
# CREAR EC2 EN CADA VPC
# =====================
inst_e1_id, inst_e1_priv, inst_e1_pub = create_ec2(ec2_east, sub_e1, sg_e1, AMI_ID_EAST, KEY_NAME_EAST)
inst_e2_id, inst_e2_priv, inst_e2_pub = create_ec2(ec2_east, sub_e2, sg_e2, AMI_ID_EAST, KEY_NAME_EAST)
inst_w_id, inst_w_priv, inst_w_pub   = create_ec2(ec2_west, sub_w, sg_w, AMI_ID_WEST, KEY_NAME_WEST)

print(f"EC2 e1: {inst_e1_id} - Private IP: {inst_e1_priv} - Public IP: {inst_e1_pub}")
print(f"EC2 e2: {inst_e2_id} - Private IP: {inst_e2_priv} - Public IP: {inst_e2_pub}")
print(f"EC2 w:  {inst_w_id} - Private IP: {inst_w_priv} - Public IP: {inst_w_pub}")

# =====================
# CREAR TRANSIT GATEWAYS
# =====================
tgw_east = ec2_east.create_transit_gateway(
    TagSpecifications=[{"ResourceType": "transit-gateway", "Tags": TAG_SPEC}]
)["TransitGateway"]["TransitGatewayId"]

tgw_west = ec2_west.create_transit_gateway(
    TagSpecifications=[{"ResourceType": "transit-gateway", "Tags": TAG_SPEC}]
)["TransitGateway"]["TransitGatewayId"]

wait_for_tgw_available(ec2_east, tgw_east)
wait_for_tgw_available(ec2_west, tgw_west)

# =====================
# VPC ATTACHMENTS
# =====================
ec2_east.create_transit_gateway_vpc_attachment(
    TransitGatewayId=tgw_east,
    VpcId=vpc_e1,
    SubnetIds=[sub_e1],
    TagSpecifications=[{"ResourceType": "transit-gateway-attachment","Tags": TAG_SPEC}]
)

ec2_east.create_transit_gateway_vpc_attachment(
    TransitGatewayId=tgw_east,
    VpcId=vpc_e2,
    SubnetIds=[sub_e2],
    TagSpecifications=[{"ResourceType": "transit-gateway-attachment","Tags": TAG_SPEC}]
)

ec2_west.create_transit_gateway_vpc_attachment(
    TransitGatewayId=tgw_west,
    VpcId=vpc_w,
    SubnetIds=[sub_w],
    TagSpecifications=[{"ResourceType": "transit-gateway-attachment","Tags": TAG_SPEC}]
)

# =====================
# TGW PEERING
# =====================
ec2_east.create_transit_gateway_peering_attachment(
    TransitGatewayId=tgw_east,
    PeerTransitGatewayId=tgw_west,
    PeerAccountId=ACCOUNT_ID,
    PeerRegion=REGION_WEST,
    TagSpecifications=[{"ResourceType": "transit-gateway-attachment","Tags": TAG_SPEC}]
)

# =====================
# ACCEPT PEERING
# =====================
peering_id = wait_for_peering_pending_acceptance(ec2_west, tgw_west)
ec2_west.accept_transit_gateway_peering_attachment(
    TransitGatewayAttachmentId=peering_id
)

print("Transit Gateway Peering aceptado correctamente")