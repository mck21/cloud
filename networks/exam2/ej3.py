import boto3
import time
from botocore.exceptions import ClientError

# =====================
# CONFIG
# =====================
REGION_EAST = "us-east-1"
REGION_WEST = "us-west-2"
ACCOUNT_ID = "525745232022" 

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
        state = client.describe_transit_gateways(
            TransitGatewayIds=[tgw_id]
        )["TransitGateways"][0]["State"]
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
    return vpc_id

def create_subnet(client, vpc_id, cidr, az):
    subnet = client.create_subnet(
        VpcId=vpc_id,
        CidrBlock=cidr,
        AvailabilityZone=az
    )["Subnet"]
    tag(subnet["SubnetId"], client)
    return subnet["SubnetId"]

# =====================
# CREAR VPCS
# =====================
vpc_e1 = create_vpc(ec2_east, "10.0.0.0/16")
vpc_e2 = create_vpc(ec2_east, "10.1.0.0/16")
vpc_w  = create_vpc(ec2_west, "10.2.0.0/16")

sub_e1 = create_subnet(ec2_east, vpc_e1, "10.0.1.0/24", "us-east-1a")
sub_e2 = create_subnet(ec2_east, vpc_e2, "10.1.1.0/24", "us-east-1a")
sub_w  = create_subnet(ec2_west, vpc_w,  "10.2.1.0/24", "us-west-2a")

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
print("Arquitectura finalizada sin errores")
