import boto3
import time
import os
from troposphere import Base64, FindInMap, GetAtt, Join, Output
from troposphere import Parameter, Ref, Tags, Template
from troposphere.ec2 import PortRange, NetworkAcl, Route, \
    SubnetRouteTableAssociation, Subnet, RouteTable, \
    VPCGatewayAttachment, VPC, NetworkInterfaceProperty, NetworkAclEntry, \
    SubnetNetworkAclAssociation, EIP, Instance, InternetGateway

def region_input():
    while True:
        # try:
            # choice = input("Enter the Region: ")
            choice = 'eu-west-2'
            if choice in availableregions:
                break
            else:
                print("Invalid Region...Enter a valid Region")
                print("Valid Regions are {0}".format(', '.join(availableregions)))
                raise Exception('Invalid Choice')
        # except:
        #      continue

    return choice

timestr = time.strftime("%Y%m%d-%H%M%S")

#this call can be made without valid aws credentials configured
availableregions = boto3.session.Session().get_available_regions('ec2')
reg = region_input()

#minimum ec2 describe permissions needed for the following boto calls
ec2c = boto3.client('ec2', region_name=reg)
azresp = ec2c.describe_availability_zones(Filters=[{'Name':'state','Values':['available']}])
availableazs = [i['ZoneName'] for i in azresp['AvailabilityZones']]


t = Template()

t.add_version('2010-09-09')

t.add_resource(VPC(
    "VPC",
    EnableDnsSupport="true",
    CidrBlock="10.100.0.0/16",
    EnableDnsHostnames="true",
    Tags=Tags(
        Application=Ref("AWS::StackName"),
        Network="{0} Spot Instance VPC".format(reg),
        Name="{0} Spot Instance VPC".format(reg),
    )
))

t.add_resource(InternetGateway(
    "InternetGateway",
    Tags=Tags(
        Application=Ref("AWS::StackName"),
        Network="{0} Spot Instance VPC".format(reg),
        Name="{0} Spot Instance VPC IGW".format(reg),
    )
))

t.add_resource(VPCGatewayAttachment(
    "IGWAttachment",
    VpcId=Ref("VPC"),
    InternetGatewayId=Ref("InternetGateway"),
))

t.add_resource(NetworkAcl(
    "NetworkAcl",
    VpcId=Ref("VPC"),
    Tags=Tags(
        Application=Ref("AWS::StackName"),
        Network="{0} Spot Instance VPC".format(reg),
    )
))

t.add_resource(NetworkAclEntry(
    "InboundNetworkAclEntry",
    NetworkAclId=Ref("NetworkAcl"),
    RuleNumber="100",
    Protocol="-1",
    PortRange=PortRange(To="65535", From="0"),
    Egress="false",
    RuleAction="allow",
    CidrBlock="0.0.0.0/0",
))

t.add_resource(NetworkAclEntry(
    "OutboundNetworkAclEntry",
    NetworkAclId=Ref("NetworkAcl"),
    RuleNumber="100",
    Protocol="-1",
    PortRange=PortRange(To="65535", From="0"),
    Egress="true",
    RuleAction="allow",
    CidrBlock="0.0.0.0/0",
))

t.add_resource(RouteTable(
    "RouteTable",
    VpcId=Ref("VPC"),
    Tags=Tags(
        Application=Ref("AWS::StackName"),
        Network="{0} Spot Instance VPC".format(reg),
        Name="Public IGW Routing Table"
    )
))

t.add_resource(Route(
    "IGWRoute",
    DependsOn='IGWAttachment',
    GatewayId=Ref("InternetGateway"),
    DestinationCidrBlock="0.0.0.0/0",
    RouteTableId=Ref("RouteTable"),
))

#loop through usable availability zones for the aws account and create a subnet for each zone
#in the same loop generate subnet associations for the network acl and the route table
for i, az in list(enumerate(availableazs, start=1)):
    t.add_resource(Subnet(
        "PublicSubnet{0}".format(i),
        VpcId=Ref("VPC"),
        CidrBlock="10.100.{0}.0/24".format(i),
        AvailabilityZone="{0}".format(az),
        MapPublicIpOnLaunch=True,
        Tags=Tags(
            Application=Ref("AWS::StackName"),
            Network="{0} Spot Instance VPC".format(reg),
            Name=f"{az} Public Subnet {i}",
        )
    ))
    t.add_resource(
        SubnetNetworkAclAssociation(
            "SubnetNetworkAclAssociation{0}".format(i),
            SubnetId=Ref("PublicSubnet{0}".format(i)),
            NetworkAclId=Ref("NetworkAcl"),
        )
    )
    t.add_resource(SubnetRouteTableAssociation(
        "SubnetRouteTableAssociation{0}".format(i),
        SubnetId=Ref("PublicSubnet{0}".format(i)),
        RouteTableId=Ref("RouteTable"),
    ))

#output the file path
print("Generating VPC template for {0}".format(reg))
print(os.path.join(os.getcwd(), "{0}-dynamic-vpc-{1}.template".format(reg, timestr)))
#generate the cloudformation template as json
# f = open("{0}-dynamic-vpc-{1}.template".format(reg, timestr),"w+")
filename = f"drummonds-VPC-{reg}.template"
f = open("{0}-dynamic-vpc-{1}.template".format(reg, timestr),"w+")
f.write(t.to_json())
f.close()
