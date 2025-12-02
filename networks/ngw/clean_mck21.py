#!/usr/bin/env python3

"""
Script: Borrar todos los recursos con tag mck21
Elimina en orden correcto: EC2 → NAT Gateway → EIP → Subnets → Route Tables → IGW → VPC
"""

import boto3
import time
import sys
from botocore.exceptions import ClientError

# Colores para terminal
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # Sin color

TAG_KEY = "tag"
TAG_VALUE = "mck21"

def print_color(color, message):
    """Imprime mensaje con color"""
    print(f"{color}{message}{Colors.NC}")

def get_resources_by_tag(ec2_client):
    """Obtiene todos los recursos con el tag especificado"""
    try:
        response = ec2_client.describe_tags(
            Filters=[
                {'Name': 'key', 'Values': [TAG_KEY]},
                {'Name': 'value', 'Values': [TAG_VALUE]}
            ]
        )
        return response.get('Tags', [])
    except ClientError as e:
        print_color(Colors.RED, f"Error obteniendo recursos: {e}")
        return []

def terminate_instances(ec2_client, resources):
    """Termina instancias EC2"""
    instance_ids = [r['ResourceId'] for r in resources if r['ResourceType'] == 'instance']
    
    if not instance_ids:
        print_color(Colors.YELLOW, "No se encontraron instancias EC2")
        return
    
    print_color(Colors.YELLOW, f"\n[1/7] Terminando {len(instance_ids)} instancia(s) EC2...")
    
    try:
        ec2_client.terminate_instances(InstanceIds=instance_ids)
        print_color(Colors.GREEN, f"✓ Instancias marcadas para terminación: {', '.join(instance_ids)}")
        
        # Esperar a que terminen
        print("  Esperando a que las instancias terminen...")
        waiter = ec2_client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=instance_ids)
        print_color(Colors.GREEN, "✓ Instancias terminadas")
        
    except ClientError as e:
        print_color(Colors.RED, f"✗ Error terminando instancias: {e}")

def delete_nat_gateways(ec2_client, resources):
    """Elimina NAT Gateways"""
    nat_ids = [r['ResourceId'] for r in resources if r['ResourceType'] == 'natgateway']
    
    if not nat_ids:
        print_color(Colors.YELLOW, "\n[2/7] No se encontraron NAT Gateways")
        return
    
    print_color(Colors.YELLOW, f"\n[2/7] Eliminando {len(nat_ids)} NAT Gateway(s)...")
    
    for nat_id in nat_ids:
        try:
            ec2_client.delete_nat_gateway(NatGatewayId=nat_id)
            print_color(Colors.GREEN, f"✓ NAT Gateway marcado para eliminación: {nat_id}")
        except ClientError as e:
            print_color(Colors.RED, f"✗ Error eliminando NAT Gateway {nat_id}: {e}")
    
    # Esperar a que se eliminen
    print("  Esperando a que los NAT Gateways se eliminen...")
    for nat_id in nat_ids:
        while True:
            try:
                response = ec2_client.describe_nat_gateways(NatGatewayIds=[nat_id])
                state = response['NatGateways'][0]['State']
                if state == 'deleted':
                    break
                time.sleep(5)
            except:
                break
    print_color(Colors.GREEN, "✓ NAT Gateways eliminados")

def release_eips(ec2_client):
    """Libera Elastic IPs con el tag"""
    print_color(Colors.YELLOW, "\n[3/7] Verificando Elastic IPs...")
    
    try:
        response = ec2_client.describe_addresses(
            Filters=[
                {'Name': f'tag:{TAG_KEY}', 'Values': [TAG_VALUE]}
            ]
        )
        
        eips = response.get('Addresses', [])
        
        if not eips:
            print_color(Colors.YELLOW, "No se encontraron Elastic IPs")
            return
        
        for eip in eips:
            allocation_id = eip['AllocationId']
            try:
                ec2_client.release_address(AllocationId=allocation_id)
                print_color(Colors.GREEN, f"✓ Elastic IP liberada: {allocation_id}")
            except ClientError as e:
                print_color(Colors.RED, f"✗ Error liberando EIP {allocation_id}: {e}")
                
    except ClientError as e:
        print_color(Colors.RED, f"Error buscando Elastic IPs: {e}")

def delete_subnets(ec2_client, resources):
    """Elimina Subnets"""
    subnet_ids = [r['ResourceId'] for r in resources if r['ResourceType'] == 'subnet']
    
    if not subnet_ids:
        print_color(Colors.YELLOW, "\n[4/7] No se encontraron Subnets")
        return
    
    print_color(Colors.YELLOW, f"\n[4/7] Eliminando {len(subnet_ids)} Subnet(s)...")
    
    for subnet_id in subnet_ids:
        try:
            ec2_client.delete_subnet(SubnetId=subnet_id)
            print_color(Colors.GREEN, f"✓ Subnet eliminada: {subnet_id}")
        except ClientError as e:
            print_color(Colors.RED, f"✗ Error eliminando Subnet {subnet_id}: {e}")

def delete_route_tables(ec2_client, resources):
    """Elimina Route Tables (excepto la main)"""
    rtb_ids = [r['ResourceId'] for r in resources if r['ResourceType'] == 'route-table']
    
    if not rtb_ids:
        print_color(Colors.YELLOW, "\n[5/7] No se encontraron Route Tables")
        return
    
    print_color(Colors.YELLOW, f"\n[5/7] Eliminando {len(rtb_ids)} Route Table(s)...")
    
    for rtb_id in rtb_ids:
        try:
            # Verificar si es la route table main
            response = ec2_client.describe_route_tables(RouteTableIds=[rtb_id])
            is_main = any(assoc.get('Main', False) for assoc in response['RouteTables'][0].get('Associations', []))
            
            if is_main:
                print_color(Colors.YELLOW, f"⊘ Route Table {rtb_id} es la main, no se puede eliminar")
                continue
            
            # Desasociar subnets primero
            for assoc in response['RouteTables'][0].get('Associations', []):
                if not assoc.get('Main', False):
                    try:
                        ec2_client.disassociate_route_table(AssociationId=assoc['RouteTableAssociationId'])
                    except:
                        pass
            
            # Eliminar route table
            ec2_client.delete_route_table(RouteTableId=rtb_id)
            print_color(Colors.GREEN, f"✓ Route Table eliminada: {rtb_id}")
        except ClientError as e:
            print_color(Colors.RED, f"✗ Error eliminando Route Table {rtb_id}: {e}")

def detach_and_delete_igw(ec2_client, resources):
    """Desasocia y elimina Internet Gateways"""
    igw_ids = [r['ResourceId'] for r in resources if r['ResourceType'] == 'internet-gateway']
    
    if not igw_ids:
        print_color(Colors.YELLOW, "\n[6/7] No se encontraron Internet Gateways")
        return
    
    print_color(Colors.YELLOW, f"\n[6/7] Eliminando {len(igw_ids)} Internet Gateway(s)...")
    
    for igw_id in igw_ids:
        try:
            # Obtener VPC asociada
            response = ec2_client.describe_internet_gateways(InternetGatewayIds=[igw_id])
            attachments = response['InternetGateways'][0].get('Attachments', [])
            
            # Desasociar de VPC
            for attachment in attachments:
                vpc_id = attachment['VpcId']
                ec2_client.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
                print(f"  Desasociado de VPC {vpc_id}")
            
            # Eliminar IGW
            ec2_client.delete_internet_gateway(InternetGatewayId=igw_id)
            print_color(Colors.GREEN, f"✓ Internet Gateway eliminado: {igw_id}")
        except ClientError as e:
            print_color(Colors.RED, f"✗ Error eliminando IGW {igw_id}: {e}")

def delete_security_groups(ec2_client, resources, vpc_ids):
    """Elimina Security Groups (excepto el default)"""
    sg_ids = [r['ResourceId'] for r in resources if r['ResourceType'] == 'security-group']
    
    if not sg_ids:
        print_color(Colors.YELLOW, "\n[6.5/7] No se encontraron Security Groups")
        return
    
    print_color(Colors.YELLOW, f"\n[6.5/7] Eliminando {len(sg_ids)} Security Group(s)...")
    
    for sg_id in sg_ids:
        try:
            # No eliminar el default security group
            response = ec2_client.describe_security_groups(GroupIds=[sg_id])
            if response['SecurityGroups'][0]['GroupName'] == 'default':
                print_color(Colors.YELLOW, f"⊘ Security Group {sg_id} es default, no se puede eliminar")
                continue
            
            ec2_client.delete_security_group(GroupId=sg_id)
            print_color(Colors.GREEN, f"✓ Security Group eliminado: {sg_id}")
        except ClientError as e:
            print_color(Colors.RED, f"✗ Error eliminando Security Group {sg_id}: {e}")

def delete_vpcs(ec2_client, resources):
    """Elimina VPCs"""
    vpc_ids = [r['ResourceId'] for r in resources if r['ResourceType'] == 'vpc']
    
    if not vpc_ids:
        print_color(Colors.YELLOW, "\n[7/7] No se encontraron VPCs")
        return
    
    print_color(Colors.YELLOW, f"\n[7/7] Eliminando {len(vpc_ids)} VPC(s)...")
    
    for vpc_id in vpc_ids:
        try:
            ec2_client.delete_vpc(VpcId=vpc_id)
            print_color(Colors.GREEN, f"✓ VPC eliminada: {vpc_id}")
        except ClientError as e:
            print_color(Colors.RED, f"✗ Error eliminando VPC {vpc_id}: {e}")

def main():
    """Función principal"""
    print_color(Colors.GREEN, f"=== Iniciando limpieza de recursos con tag {TAG_KEY}={TAG_VALUE} ===\n")
    
    # Crear cliente EC2
    ec2_client = boto3.client('ec2')
    
    # Obtener todos los recursos con el tag
    print_color(Colors.YELLOW, "Buscando recursos con tag mck21...")
    resources = get_resources_by_tag(ec2_client)
    
    if not resources:
        print_color(Colors.YELLOW, "\nNo se encontraron recursos con el tag especificado")
        return
    
    print_color(Colors.GREEN, f"✓ Encontrados {len(resources)} recursos\n")
    
    # Mostrar recursos encontrados
    resource_types = {}
    for r in resources:
        rt = r['ResourceType']
        resource_types[rt] = resource_types.get(rt, 0) + 1
    
    print("Recursos encontrados:")
    for rt, count in resource_types.items():
        print(f"  - {rt}: {count}")
    
    # Confirmar eliminación
    print_color(Colors.RED, "\n⚠️  ADVERTENCIA: Se eliminarán todos estos recursos")
    response = input("¿Continuar? (s/N): ")
    
    if response.lower() != 's':
        print_color(Colors.YELLOW, "Operación cancelada")
        return
    
    # Eliminar recursos en orden
    vpc_ids = [r['ResourceId'] for r in resources if r['ResourceType'] == 'vpc']
    
    terminate_instances(ec2_client, resources)
    delete_nat_gateways(ec2_client, resources)
    release_eips(ec2_client)
    delete_subnets(ec2_client, resources)
    delete_route_tables(ec2_client, resources)
    detach_and_delete_igw(ec2_client, resources)
    delete_security_groups(ec2_client, resources, vpc_ids)
    delete_vpcs(ec2_client, resources)
    
    print_color(Colors.GREEN, "\n========================================")
    print_color(Colors.GREEN, "  Limpieza completada")
    print_color(Colors.GREEN, "========================================\n")
    
    print_color(Colors.GREEN, "✓ Script completado exitosamente\n")

if __name__ == "__main__":
    main()