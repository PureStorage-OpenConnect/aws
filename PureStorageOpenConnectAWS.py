# Assumptions softwares installed/Downloaded: python is installed,           #
# AWScli in                                                                  # 
# User has the aws_access_key_id and aws_secret_access_key of the            #
# aws account ans has set the ssm policy in IAM role                         #
# This code will use the xml conf file and get the values from the           #
# conf file.                                                                 #
#                                                                            #
#This Automation helps setup Pure Storage All-Flash Array with the           #
#AWS solution and the deployment steps to setup and configure connectivity   #
#between Pure Storage box that is in an Equinix datacenter to an AWS cloud   #
#with direct connect.                                                        #
# The different components that will be explained are:                       #
# Deployment guidance for AWS– Private Subnet, Public Subnet,                #
#Route Table, VPC, VPC Wizard, Customer Gateways, and Virtual Private Gateway#  
#                                                                            #
# Access EC2 instance                                                        #
# Connectivity to FlashArray–Host and volume creation in PureStorage and     # 
#connecting a Pure Storage Volume to AWS EC2 instance.                       #
# Connect Pure Storage volume to AWS EC2 instance.                           #
#                                                                            #
# Configure - Routing and Iscsi initiator                                    #
# This script does basic plumbing of connection setup with Diskspd.exe to    #
#give user an idea of IOPS, latency and Bandwidth.                           #                                                          #
#                                                                            #
# Refer to the video of the PS AWS Direct connect for more details.###########
##############################################################################
##install awscli
#install boto3
#os.system('pip install boto3')
import os
import sys
import time
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
# This is the AWS configuration file containing parameter values. This config file is expected to be present in the
# Current working directory Or where the script is downloaded. All parameters defined in the config file are mandatory.
cwd = os.getcwd()
filename = "\AWSConfFile.xml"
relative_conffilepath = cwd+filename
print(relative_conffilepath)
my_file = Path(relative_conffilepath)
print(my_file)
if my_file.is_file():
    print ("AWS Config File : AWSConfFile.xml exists.") 
else:
    print ("AWS Config File not found at location : my_file")
name = input("Type yes to continue :")
if name==("yes"):
    print("Continuing with AWS setup...")
else:
    sys.exit()
#print ("%s." % name)
def xml():
    import lxml
    from lxml import etree
    import ntpath
    # parse the location of the conf file
    c = "Getting the values form the default conf file at "
    conffileloaction = c+relative_conffilepath
    print(conffileloaction)
    user_input = input("Press Enter key to continue with default Conf file Values Or Exit to Edit :")
    if user_input == "":
        print ("Conitnuing with the default conf file values.")
    else:
        print ("Edit values in Conf file and Rerun the script. Exit Now.")
        sys.exit()
    root = etree.parse(r'%s' % my_file)
    print(" Reading The File" )
    global connectionId,Vlan,BGPASN,BGPAuthKey,VirtualInterfaceName,Tag,ImageId,MinCount,MaxCount,InstanceType,Groupname,KeyName,DestinationIGW,CidrIp,QAddTargetPortal,qlogintarget,AvailabilityZone
    VIDetails = root.xpath('/Parameters/VIDetails/*/text()')
    connectionId = VIDetails[0]
    Vlan = VIDetails[1]
    BGPASN = VIDetails[2]
    BGPAuthKey = VIDetails[3]
    VirtualInterfaceName = VIDetails[4]
    ResourceDetails = root.xpath('/Parameters/ResourceDetails/*/text()')
    Tag = ResourceDetails[0]
    ImageId = ResourceDetails[1]
    InstanceType = ResourceDetails[2]
    Groupname = ResourceDetails[3]
    KeyName = ResourceDetails[4]
    CidrIp = ResourceDetails[5]
    print(CidrIp)
    IscsiDetails = root.xpath('/Parameters/IscsiDetails/*/text()')
    QAddTargetPortal = IscsiDetails[0]
    qlogintarget = IscsiDetails[1]
    
#xml()
#This function will create a vpc with the desired Cidr block in the provided user account
def vpc():
    ec2 = boto3.resource('ec2')
    client = boto3.client('ec2')
    ec2 = boto3.client('ec2')
    global vpc_id,SubnetId,AvailabilityZone
    #install awscli
    aws_access_key_id = input("Enter The  Access Key Id :")
    aws_secret_access_key = input("Enter The Secret Key Id :")
    client = boto3.client('ec2',aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
    print('Accessed AWS')
    print("creating VPC ...")
    Cidrblockk = input("Enter The CIDR value :")
    #print(Cidrblockk)
    try:
        response = client.create_vpc(CidrBlock=Cidrblockk)
        time.sleep(10)
        print(response)
    except ClientError as e:     
        print(e)
        sys.exit()
    print("Describing vpcs")
    response = ec2.describe_vpcs()
    #print(response)
    try:
        vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
        print("VPC Id is :"+vpc_id)
    except IndexError as e:
        print(e)
        sys.exit()
    Subnetcidrblock = input("Enter The  Subnet cidr value :")
    AvailabilityZone = input("Enter The AvailabilityZone :")
    try:
        response = client.create_subnet(CidrBlock=Subnetcidrblock,AvailabilityZone=AvailabilityZone,VpcId=vpc_id,)
        #print(response)
    except ClientError as e:
        print(e)
        sys.exit()
    print("Describing subnets")
    time.sleep(15)
    response = ec2.describe_subnets()
    #print(response)
    try:
        SubnetId = response.get('Subnets', [{}])[0].get('SubnetId', '')
        print("Subnet Id is:"+SubnetId)
    except IndexError as e:
        print(e)
        sys.exit()
#vpc()
    
#vpc()
#This function will create a security group for the created vpc
#The inbound rule can be set for allowing trafic for different ip protocols
def securitygroup():
    ec2 = boto3.client('ec2')
    global GroupId,Groups
    response = ec2.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

    try:
        response = ec2.create_security_group(GroupName='testing',
                                         Description='DESCRIPTION',VpcId=vpc_id)
        security_group_id = response['GroupId']
        print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))
        data = ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {'IpProtocol': 'tcp',
                 'FromPort': 80,
                 'ToPort': 80,
                 'IpRanges': [{'CidrIp': CidrIp}]},
                {'IpProtocol': 'tcp',
                 'FromPort': 3389,
                 'ToPort': 3389,
                 'IpRanges': [{'CidrIp': CidrIp}]},
                {'IpProtocol': 'tcp',
                 'FromPort': 0,
                 'ToPort': 65535,
                 'IpRanges': [{'CidrIp': CidrIp}]}
            ])
        print('Ingress Successfully Set %s' % data)
    except ClientError as e:
        print(e)
        sys.exit()
    response = ec2.describe_security_groups()
    #print(response)
    try:
        GroupID = response.get('SecurityGroups',[{}])[1].get('GroupId', '')
        print(GroupID)
        Group = input("Match the Security Group Id with the newly security group if matches press Enter")
        if Group=="":
            GroupId = GroupID
            Groups = tuple([GroupId])
        if Group!="":
            try:
                Groupid = response.get('SecurityGroups',[{}])[0].get('GroupId', '')
                print(Groupid)
                GroupId = GroupID
                Groups = tuple([GroupId])
            except IndexError as e:
                print(e)
        #else :
            #sys.exit()
    except IndexError as e:
        print(e)
        sys.exit()

#securitygroup()
def create_gateways():
    print("er")
    ec2 = boto3.resource('ec2')
    ec2 = boto3.client('ec2')
    client = boto3.client('ec2')
    global InternetGatewayId,vpg
    print("Creating internet gateway")
    try:
        gateway = ec2.create_internet_gateway()
        print(gateway)
    except ClientError as e:
        print(e)
        sys.exit()
    print("Internet Gateway Created")
    print("Describing internet gateways")
    response = ec2.describe_internet_gateways()
    #print(response)
    try:
        InternetGatewayId = response.get('InternetGateways', [{}])[0].get('InternetGatewayId', '')
        print("Internet Gateway Id is :"+InternetGatewayId)
    except IndexError as e:
        print(e)
        sys.exit()
    print(vpc_id)
    try:
        response = client.attach_internet_gateway(InternetGatewayId=InternetGatewayId,VpcId=vpc_id)
        #print(response)
    except ClientError as e:
        print(e)
        sys.exit()
    except NameError as f:
        print(f)
        sys.exit()
    print ("Creating Virtual Private gateway")
    Type = input("Enter the type of Vitual Private Gateway :")
    try:
        response = client.create_vpn_gateway( AvailabilityZone=AvailabilityZone,Type=Type,)
    except ClientError as e:
        print(e)
    time.sleep(30)
    print("Describing Virtual Private gateways")
    response = ec2.describe_vpn_gateways()
    #print(response)
    try:
        vpg = response.get('VpnGateways', [{}])[0].get('VpnGatewayId', '')
        print("Virtual private gateway Id is:"+vpg)
    except IndexError as e:
        print(e)
        sys.exit()    
    try:
        response = client.attach_vpn_gateway(VpcId=vpc_id,VpnGatewayId=vpg)
        print("Attaching virtual private gateway to vpc")
        #print(response)
    except ClientError as e:
        print(e)
        sys.exit()
    #time.sleep(360)
    
#create_gateways()

def create_routes():
    print(InternetGatewayId)
    ec2 = boto3.resource('ec2')
    ec2 = boto3.client('ec2')
    client = boto3.client('ec2')
    global RouteTableId
    response = ec2.describe_route_tables()
    DestinationIGW = input("Enter The Internet Gateway Destination IP Block :")
    #print(response)
    try:
        RouteTableId = response.get('RouteTables', [{}])[0].get('RouteTableId', '')
        print("RouteTableId is :"+RouteTableId)
    except IndexError as e:
        print(e)
        sys.exit()
    try:
        response = client.create_route(DestinationCidrBlock=DestinationIGW,GatewayId=InternetGatewayId,RouteTableId=RouteTableId)
        print(response)
    except ClientError as e:
        print(e)
        sys.exit()
    VPGDestination = input("Enter The Virtual Private Gateway Destination IP Block :")
    try:
        response = client.create_route(DestinationCidrBlock=VPGDestination,GatewayId=vpg,RouteTableId=RouteTableId)
        print(response)
    except ClientError as e:
        print(e)
        sys.exit()
    try:
        response = client.enable_vgw_route_propagation(GatewayId=vpg,RouteTableId=RouteTableId,)
        print(response)
    except ClientError as e:
        print(e)
        sys.exit()

#create_routes()
def launch_instance():
    client = boto3.client('ec2')
    ec2 = boto3.resource('ec2')
    global InstanceId,start_msiscsi
    print("Tagging resources ...")
    response = client.create_tags(Resources=[vpc_id,SubnetId,vpg,GroupId,RouteTableId,InternetGatewayId],Tags=[{'Key': 'Name','Value': 'testing'}])
    time.sleep(10)
    f = open('String.pem', 'w')
    key_pair = ec2.create_key_pair(KeyName=KeyName)
    KeyPairOut = str(key_pair.key_material)
    f.write(KeyPairOut)
    f.close()
    print("Creating ec2 instance")
    MinimumCount = input("Enter the minimum number of instances to be launched :")
    MinCount = int(MinimumCount)
    MaximumCount = input("Enter the maximum number of instances to be launched :")
    MaxCount = int(MaximumCount)
    try:
        response = ec2.create_instances(ImageId=ImageId,MinCount=MinCount,MaxCount=MaxCount,KeyName=KeyName,NetworkInterfaces=[{'DeviceIndex': 0,'AssociatePublicIpAddress':True,'SubnetId':SubnetId,'Groups':Groups,}],InstanceType=InstanceType)
        time.sleep(30)
        print(response)
    except NameError as e:
        print(e)
        sys.exit()
    except ClientError as f:
        print(f)
        sys.exit()
    time.sleep(360)
    print("Describing Instances")
    response = client.describe_instances()
    print(response)
    try:
        InstanceId = response.get('Reservations', [{}])[0].get('Instances',[{}])[0].get('InstanceId' '')
        print(InstanceId)
    except IndexError as e:
        print(e)
        sys.exit()
    w ='aws ec2 get-password-data --instance-id '
    z = ' --priv-launch-key String.pem > key1.txt'
    Password = w+InstanceId+z
    os.system(Password)
    print("Thank you")
    #Insert the hosted connection Id and vlan number in the conff file
    #create the virtual interface for the hosted connection
    #response = client.create_private_virtual_interface(connectionId='dxcon-fhaxj3eo',newPrivateVirtualInterface={'virtualInterfaceName':'string',
    #'vlan': 186,'asn': 123,'authKey': 'string','addressFamily':'ipv4','virtualGatewayId': vpg })
#print(InstanceId)
#launch_instance()
def initiator_iscsi():
    #client = boto3.client('ec2',aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
    ec2 = boto3.resource('ec2')
    client = boto3.client('ec2')
    response = client.describe_instances()
    #print(response)
    #time.sleep(60)
    try:
        InstanceId = response.get('Reservations', [{}])[0].get('Instances',[{}])[0].get('InstanceId' '')
        print("Your Instance Id id :"+InstanceId)
    except IndexError as e:
        print(e)
        sys.exit()
    ssm = input("Attach IAM role to the instance for sending commands")
    Z='aws ssm send-command --document-name "AWS-RunPowerShellScript" --parameters commands=["iscsicli QAddTargetPortal 192.168.60.13"] --targets "Key=instanceids,Values='
    T = 'aws ssm send-command --document-name "AWS-RunPowerShellScript" --parameters commands=["net start msiscsi"] --targets "Key=instanceids,Values='
    #print(T)
    #os.system('aws ssm send-command --document-name "AWS-RunPowerShellScript" --parameters commands=["sc config msiscsi start= auto"]--targets "Key=instanceids,Values=i-01a996922be03a208")
    start_msiscsi = T+InstanceId
    startvm = input("Press enter after logging into the instance")
    print(start_msiscsi)
    Qaddtargetportal = Z+InstanceId
    os.system(start_msiscsi)
    time.sleep(100)
    print("Check if iscsi service is started or not ...")
    os.system(Qaddtargetportal)
    time.sleep(100)
    print("Configure Flash Array ...")
    c = 'aws ssm send-command --document-name "AWS-RunPowerShellScript" --parameters commands=["iscsicli qlogintarget iqn.2010-06.com.purestorage:flasharray.147d13ae268b222"] --targets "Key=instanceids,Values='
    Qlogin = c+InstanceId
    os.system(Qlogin)
    time.sleep(180)
    print("Bring the disk online")
    os.system('aws ssm send-command --document-name "AWS-RunPowerShellScript" --parameters commands=["iscsicli qlogintarget iqn.2010-06.com.purestorage:flasharray.147d13ae268b222"] --targets "Key=instanceids,Values=i-01a996922be03a208" >> ssm.txt')
    os.system("notepad")
    time.sleep(100)
    do = input("Please copy the wipe.c txt file to the desktop of ec2 instance and then press enter to continue :")
    if Group=="":
        print("Formatting the disk ...")
    else:
        sys.exit()
    d = 'aws ssm send-command --document-name "AWS-RunPowerShellScript" --parameters commands=["Diskpart /S C:/Users/Administrator/Desktop/WipeC.txt"] --targets "Key=instanceids,Values='
    diskpart = d+InstanceId
    os.system(diskpart)
    #os.system('aws ssm send-command --document-name "AWS-RunPowerShellScript" --parameters commands=["Diskpart /S C:/Users/Administrator/Desktop/WipeC.txt"] --targets "Key=instanceids,Values=i-01a996922be03a208" >> ssm.txt')
#initiator_iscsi()
# This is the main function, where we keep all important functional setup steps for AWS. 
# The sequence of execution is of importance. The exception handling is part of the function definition itself.
def main():
    xml()
    vpc()
    securitygroup()
    create_gateways()
    create_routes()
    launch_instance()
    initiator_iscsi()
main()

#print(type(RunningInstanceID))

#time.sleep(300)



