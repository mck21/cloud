import boto3
import time

# Cliente de EC2
ec2 = boto3.client('ec2')
rds = boto3.client('rds')

def create_infrastructure():
    # 1. Crear VPC
    print("Creando VPC...")
    vpc = ec2.create_vpc(
        CidrBlock='172.0.0.0/16',
        TagSpecifications=[{
            'ResourceType': 'vpc',
            'Tags': [{'Key': 'Name', 'Value': 'mck21-vpc'}, {'Key': 'Project', 'Value': 'mck21'}]
        }]
    )
    vpc_id = vpc['Vpc']['VpcId']
    print(f"VPC creada: {vpc_id}")
    
    # Habilitar DNS
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
    
    # 2. Crear Internet Gateway
    print("Creando Internet Gateway...")
    igw = ec2.create_internet_gateway(
        TagSpecifications=[{
            'ResourceType': 'internet-gateway',
            'Tags': [{'Key': 'Name', 'Value': 'mck21-igw'}, {'Key': 'Project', 'Value': 'mck21'}]
        }]
    )
    igw_id = igw['InternetGateway']['InternetGatewayId']
    ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    
    # 3. Crear Subnets
    azs = ['us-east-1a', 'us-east-1b', 'us-east-1c']
    public_subnets = []
    private_subnets = []
    
    print("Creando subnets públicas...")
    for i, az in enumerate(azs):
        subnet = ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock=f'172.0.{i}.0/24',
            AvailabilityZone=az,
            TagSpecifications=[{
                'ResourceType': 'subnet',
                'Tags': [
                    {'Key': 'Name', 'Value': f'mck21-public-subnet-{i+1}'},
                    {'Key': 'Project', 'Value': 'mck21'}
                ]
            }]
        )
        public_subnets.append(subnet['Subnet']['SubnetId'])
        print(f"Subnet pública {i+1} creada: {subnet['Subnet']['SubnetId']}")
    
    print("Creando subnets privadas...")
    for i, az in enumerate(azs):
        subnet = ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock=f'172.0.{i+10}.0/24',
            AvailabilityZone=az,
            TagSpecifications=[{
                'ResourceType': 'subnet',
                'Tags': [
                    {'Key': 'Name', 'Value': f'mck21-private-subnet-{i+1}'},
                    {'Key': 'Project', 'Value': 'mck21'}
                ]
            }]
        )
        private_subnets.append(subnet['Subnet']['SubnetId'])
        print(f"Subnet privada {i+1} creada: {subnet['Subnet']['SubnetId']}")
    
    # 4. Crear Route Tables
    print("Creando route table pública...")
    public_rt = ec2.create_route_table(
        VpcId=vpc_id,
        TagSpecifications=[{
            'ResourceType': 'route-table',
            'Tags': [{'Key': 'Name', 'Value': 'mck21-public-rt'}, {'Key': 'Project', 'Value': 'mck21'}]
        }]
    )
    public_rt_id = public_rt['RouteTable']['RouteTableId']
    
    # Ruta a Internet Gateway
    ec2.create_route(RouteTableId=public_rt_id, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw_id)
    
    # Asociar subnets públicas
    for subnet_id in public_subnets:
        ec2.associate_route_table(SubnetId=subnet_id, RouteTableId=public_rt_id)
    
    # 5. Crear Security Groups
    print("Creando Security Groups...")
    
    # gs-ec2 (permite SSH)
    sg_ec2 = ec2.create_security_group(
        GroupName='mck21-gs-ec2',
        Description='Security group para instancias EC2',
        VpcId=vpc_id,
        TagSpecifications=[{
            'ResourceType': 'security-group',
            'Tags': [{'Key': 'Name', 'Value': 'mck21-gs-ec2'}, {'Key': 'Project', 'Value': 'mck21'}]
        }]
    )
    sg_ec2_id = sg_ec2['GroupId']
    
    ec2.authorize_security_group_ingress(
        GroupId=sg_ec2_id,
        IpPermissions=[{
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH access'}]
        }]
    )
    print(f"Security Group EC2 creado: {sg_ec2_id}")
    
    # gs-proxy (intermediario)
    sg_proxy = ec2.create_security_group(
        GroupName='mck21-gs-proxy',
        Description='Security group proxy intermediario',
        VpcId=vpc_id,
        TagSpecifications=[{
            'ResourceType': 'security-group',
            'Tags': [{'Key': 'Name', 'Value': 'mck21-gs-proxy'}, {'Key': 'Project', 'Value': 'mck21'}]
        }]
    )
    sg_proxy_id = sg_proxy['GroupId']
    
    # Permitir MySQL desde gs-ec2
    ec2.authorize_security_group_ingress(
        GroupId=sg_proxy_id,
        IpPermissions=[{
            'IpProtocol': 'tcp',
            'FromPort': 3306,
            'ToPort': 3306,
            'UserIdGroupPairs': [{'GroupId': sg_ec2_id, 'Description': 'MySQL from EC2'}]
        }]
    )
    print(f"Security Group Proxy creado: {sg_proxy_id}")
    
    # gs-rds (permite MySQL desde gs-proxy)
    sg_rds = ec2.create_security_group(
        GroupName='mck21-gs-rds',
        Description='Security group para RDS MySQL',
        VpcId=vpc_id,
        TagSpecifications=[{
            'ResourceType': 'security-group',
            'Tags': [{'Key': 'Name', 'Value': 'mck21-gs-rds'}, {'Key': 'Project', 'Value': 'mck21'}]
        }]
    )
    sg_rds_id = sg_rds['GroupId']
    
    ec2.authorize_security_group_ingress(
        GroupId=sg_rds_id,
        IpPermissions=[{
            'IpProtocol': 'tcp',
            'FromPort': 3306,
            'ToPort': 3306,
            'UserIdGroupPairs': [{'GroupId': sg_proxy_id, 'Description': 'MySQL from Proxy'}]
        }]
    )
    print(f"Security Group RDS creado: {sg_rds_id}")
    
    # 6. Crear Instancias EC2
    print("Creando instancias EC2...")
    # Obtener la AMI más reciente de Amazon Linux 2
    amis = ec2.describe_images(
        Owners=['amazon'],
        Filters=[
            {'Name': 'name', 'Values': ['amzn2-ami-hvm-*-x86_64-gp2']},
            {'Name': 'state', 'Values': ['available']}
        ]
    )
    latest_ami = sorted(amis['Images'], key=lambda x: x['CreationDate'], reverse=True)[0]['ImageId']
    
    ec2_instances = []
    for i, subnet_id in enumerate(public_subnets):
        instance = ec2.run_instances(
            ImageId=latest_ami,
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1,
            NetworkInterfaces=[{
                'SubnetId': subnet_id,
                'DeviceIndex': 0,
                'AssociatePublicIpAddress': True,
                'Groups': [sg_ec2_id, sg_proxy_id]
            }],
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [
                    {'Key': 'Name', 'Value': f'mck21-ec2-{i+1}'},
                    {'Key': 'Project', 'Value': 'mck21'}
                ]
            }]
        )
        ec2_instances.append(instance['Instances'][0]['InstanceId'])
        print(f"Instancia EC2 {i+1} creada: {instance['Instances'][0]['InstanceId']}")
    
    # 7. Crear DB Subnet Group
    print("Creando DB Subnet Group...")
    rds.create_db_subnet_group(
        DBSubnetGroupName='mck21-db-subnet-group',
        DBSubnetGroupDescription='Subnet group para RDS mck21',
        SubnetIds=private_subnets,
        Tags=[{'Key': 'Project', 'Value': 'mck21'}]
    )
    
    # 8. Crear instancias RDS
    print("Creando instancias RDS (esto puede tardar varios minutos)...")
    rds_instances = []
    for i in range(3):
        db_instance = rds.create_db_instance(
            DBInstanceIdentifier=f'mck21-rds-{i+1}',
            DBInstanceClass='db.t3.micro',
            Engine='mysql',
            MasterUsername='admin',
            MasterUserPassword='Mck21Password123!',
            AllocatedStorage=20,
            VpcSecurityGroupIds=[sg_rds_id],
            DBSubnetGroupName='mck21-db-subnet-group',
            BackupRetentionPeriod=0,
            PubliclyAccessible=False,
            Tags=[{'Key': 'Project', 'Value': 'mck21'}]
        )
        rds_instances.append(db_instance['DBInstance']['DBInstanceIdentifier'])
        print(f"Instancia RDS {i+1} en creación: {db_instance['DBInstance']['DBInstanceIdentifier']}")
    
    print("\n=== RESUMEN DE RECURSOS CREADOS ===")
    print(f"VPC: {vpc_id}")
    print(f"Internet Gateway: {igw_id}")
    print(f"Subnets públicas: {public_subnets}")
    print(f"Subnets privadas: {private_subnets}")
    print(f"Security Group EC2: {sg_ec2_id}")
    print(f"Security Group Proxy: {sg_proxy_id}")
    print(f"Security Group RDS: {sg_rds_id}")
    print(f"Instancias EC2: {ec2_instances}")
    print(f"Instancias RDS: {rds_instances}")
    print("\nInfraestructura creada exitosamente!")
    print("NOTA: Las instancias RDS pueden tardar 10-15 minutos en estar disponibles.")

if __name__ == '__main__':
    create_infrastructure()