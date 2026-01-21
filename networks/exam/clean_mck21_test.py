#!/usr/bin/env python3

"""
Script: Borrar todos los recursos con tag mck21
Elimina en orden correcto: EC2 → NAT Gateway → EIP → Peering → Transit Gateway → Subnets → Route Tables → Security Groups → IGW → VPC
"""

import boto3
import time
from botocore.exceptions import ClientError

# Colores terminal
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'

TAG_KEY = "tag"
TAG_VALUE = "mck21"

def print_color(color, msg):
    print(f"{color}{msg}{Colors.NC}")

def get_resources(ec2):
    """Recopila recursos EC2, subnets, NATs, EIPs, SG, RTB, IGW, VPC, TGW y Peering"""
    resources = []
    # Lista extendida de tipos de recursos
    resource_types = [
        'instance', 'subnet', 'natgateway', 'address', 'route-table', 
        'security-group', 'internet-gateway', 'vpc', 'transit-gateway', 'vpc-peering-connection'
    ]

    for rtype in resource_types:
        try:
            tags_filter = [{'Name': f'tag:{TAG_KEY}', 'Values': [TAG_VALUE]}]

            if rtype == 'instance':
                resp = ec2.describe_instances(Filters=tags_filter)
                for res in resp['Reservations']:
                    for inst in res['Instances']:
                        resources.append({'ResourceId': inst['InstanceId'], 'ResourceType':'instance'})

            elif rtype == 'subnet':
                resp = ec2.describe_subnets(Filters=tags_filter)
                for s in resp['Subnets']:
                    resources.append({'ResourceId': s['SubnetId'], 'ResourceType':'subnet'})

            elif rtype == 'natgateway':
                resp = ec2.describe_nat_gateways(Filters=tags_filter)
                for n in resp['NatGateways']:
                    resources.append({'ResourceId': n['NatGatewayId'], 'ResourceType':'natgateway'})

            elif rtype == 'address':
                resp = ec2.describe_addresses(Filters=tags_filter)
                for a in resp['Addresses']:
                    resources.append({'ResourceId': a['AllocationId'], 'ResourceType':'address'})

            elif rtype == 'route-table':
                resp = ec2.describe_route_tables(Filters=tags_filter)
                for rtb in resp['RouteTables']:
                    resources.append({'ResourceId': rtb['RouteTableId'], 'ResourceType':'route-table'})

            elif rtype == 'security-group':
                resp = ec2.describe_security_groups(Filters=tags_filter)
                for sg in resp['SecurityGroups']:
                    if sg['GroupName'] != 'default':
                        resources.append({'ResourceId': sg['GroupId'], 'ResourceType':'security-group'})

            elif rtype == 'internet-gateway':
                resp = ec2.describe_internet_gateways(Filters=tags_filter)
                for igw in resp['InternetGateways']:
                    resources.append({'ResourceId': igw['InternetGatewayId'], 'ResourceType':'internet-gateway'})

            elif rtype == 'vpc':
                resp = ec2.describe_vpcs(Filters=tags_filter)
                for vpc in resp['Vpcs']:
                    resources.append({'ResourceId': vpc['VpcId'], 'ResourceType':'vpc'})

            elif rtype == 'transit-gateway':
                resp = ec2.describe_transit_gateways(Filters=tags_filter)
                for tgw in resp['TransitGateways']:
                    resources.append({'ResourceId': tgw['TransitGatewayId'], 'ResourceType':'transit-gateway'})

            elif rtype == 'vpc-peering-connection':
                resp = ec2.describe_vpc_peering_connections(Filters=tags_filter)
                for pcx in resp['VpcPeeringConnections']:
                    if pcx['Status']['Code'] != 'deleted':
                        resources.append({'ResourceId': pcx['VpcPeeringConnectionId'], 'ResourceType':'vpc-peering-connection'})

        except ClientError as e:
            print_color(Colors.RED, f"Error obteniendo {rtype}: {e}")

    return resources

def terminate_instances(ec2, resources):
    instance_ids = [r['ResourceId'] for r in resources if r['ResourceType']=='instance']
    if not instance_ids: return
    print_color(Colors.YELLOW, f"Terminando {len(instance_ids)} instancias EC2...")
    ec2.terminate_instances(InstanceIds=instance_ids)
    ec2.get_waiter('instance_terminated').wait(InstanceIds=instance_ids)
    print_color(Colors.GREEN, "Instancias EC2 eliminadas")

def delete_nat_gateways(ec2, resources):
    nat_ids = [r['ResourceId'] for r in resources if r['ResourceType']=='natgateway']
    if not nat_ids: return
    print_color(Colors.YELLOW, f"Eliminando {len(nat_ids)} NAT Gateways...")
    for nat_id in nat_ids:
        try:
            ec2.delete_nat_gateway(NatGatewayId=nat_id)
            while True:
                state = ec2.describe_nat_gateways(NatGatewayIds=[nat_id])['NatGateways'][0]['State']
                if state == 'deleted': break
                time.sleep(5)
        except ClientError: pass
    print_color(Colors.GREEN, "NAT Gateways eliminadas")

def delete_peering_connections(ec2, resources):
    pcx_ids = [r['ResourceId'] for r in resources if r['ResourceType']=='vpc-peering-connection']
    if not pcx_ids: return
    print_color(Colors.YELLOW, f"Eliminando {len(pcx_ids)} VPC Peering Connections...")
    for pcx_id in pcx_ids:
        try:
            ec2.delete_vpc_peering_connection(VpcPeeringConnectionId=pcx_id)
        except ClientError: pass
    print_color(Colors.GREEN, "Peering Connections eliminadas")

def delete_transit_gateways(ec2, resources):
    tgw_ids = [r['ResourceId'] for r in resources if r['ResourceType']=='transit-gateway']
    if not tgw_ids: return
    print_color(Colors.YELLOW, f"Eliminando {len(tgw_ids)} Transit Gateways...")
    for tgw_id in tgw_ids:
        try:
            # Primero eliminamos sus attachments si existieran
            attachments = ec2.describe_transit_gateway_attachments(
                Filters=[{'Name': 'transit-gateway-id', 'Values': [tgw_id]}]
            )['TransitGatewayAttachments']
            
            for att in attachments:
                ec2.delete_transit_gateway_vpc_attachment(TransitGatewayAttachmentId=att['TransitGatewayAttachmentId'])
            
            # Esperar a que los attachments se borren antes de borrar el TGW
            time.sleep(10) 
            ec2.delete_transit_gateway(TransitGatewayId=tgw_id)
        except ClientError: pass
    print_color(Colors.GREEN, "Transit Gateways eliminados")

def release_eips(ec2, resources):
    eips = [r['ResourceId'] for r in resources if r['ResourceType']=='address']
    if not eips: return
    print_color(Colors.YELLOW, f"Liberando {len(eips)} Elastic IPs...")
    for alloc_id in eips:
        try:
            ec2.release_address(AllocationId=alloc_id)
        except ClientError: pass
    print_color(Colors.GREEN, "Elastic IPs liberadas")

def delete_subnets(ec2, resources):
    subnets = [r['ResourceId'] for r in resources if r['ResourceType']=='subnet']
    if not subnets: return
    print_color(Colors.YELLOW, f"Eliminando {len(subnets)} Subnets...")
    for s in subnets:
        try:
            ec2.delete_subnet(SubnetId=s)
        except ClientError: pass
    print_color(Colors.GREEN, "Subnets eliminadas")

def delete_route_tables(ec2, resources):
    rtb = [r['ResourceId'] for r in resources if r['ResourceType']=='route-table']
    if not rtb: return
    print_color(Colors.YELLOW, f"Eliminando {len(rtb)} Route Tables...")
    for rtb_id in rtb:
        try:
            assoc = ec2.describe_route_tables(RouteTableIds=[rtb_id])['RouteTables'][0].get('Associations',[])
            for a in assoc:
                if not a.get('Main', False):
                    ec2.disassociate_route_table(AssociationId=a['RouteTableAssociationId'])
            ec2.delete_route_table(RouteTableId=rtb_id)
        except ClientError: pass
    print_color(Colors.GREEN, "Route Tables eliminadas")

def delete_security_groups(ec2, resources):
    sg_ids = [r['ResourceId'] for r in resources if r['ResourceType']=='security-group']
    if not sg_ids: return
    print_color(Colors.YELLOW, f"Eliminando {len(sg_ids)} Security Groups...")
    for sg in sg_ids:
        try:
            ec2.delete_security_group(GroupId=sg)
        except ClientError: pass
    print_color(Colors.GREEN, "Security Groups eliminados")

def delete_igw(ec2, resources):
    igws = [r['ResourceId'] for r in resources if r['ResourceType']=='internet-gateway']
    if not igws: return
    print_color(Colors.YELLOW, f"Eliminando {len(igws)} Internet Gateways...")
    for igw in igws:
        try:
            attachments = ec2.describe_internet_gateways(InternetGatewayIds=[igw])['InternetGateways'][0].get('Attachments',[])
            for att in attachments:
                ec2.detach_internet_gateway(InternetGatewayId=igw, VpcId=att['VpcId'])
            ec2.delete_internet_gateway(InternetGatewayId=igw)
        except ClientError: pass
    print_color(Colors.GREEN, "Internet Gateways eliminadas")

def delete_vpcs(ec2, resources):
    vpcs = [r['ResourceId'] for r in resources if r['ResourceType']=='vpc']
    if not vpcs: return
    print_color(Colors.YELLOW, f"Eliminando {len(vpcs)} VPCs...")
    for vpc in vpcs:
        try:
            ec2.delete_vpc(VpcId=vpc)
        except ClientError: pass
    print_color(Colors.GREEN, "VPCs eliminadas")

def main():
    print_color(Colors.GREEN, "=== Iniciando limpieza de recursos mck21 ===")
    ec2 = boto3.client('ec2')
    resources = get_resources(ec2)

    if not resources:
        print_color(Colors.YELLOW, "No se encontraron recursos con tag mck21")
        return

    print_color(Colors.GREEN, f"Se encontraron {len(resources)} recursos. Iniciando secuencia...\n")
    
    # Orden de ejecución optimizado para dependencias
    terminate_instances(ec2, resources)
    delete_nat_gateways(ec2, resources)
    release_eips(ec2, resources)
    delete_peering_connections(ec2, resources) # Nuevo
    delete_transit_gateways(ec2, resources)    # Nuevo
    delete_subnets(ec2, resources)
    delete_route_tables(ec2, resources)
    delete_security_groups(ec2, resources)
    delete_igw(ec2, resources)
    delete_vpcs(ec2, resources)
    
    print_color(Colors.GREEN, "\n=== Limpieza completada ===")

if __name__=="__main__":
    main()