import boto3

from create_stack import VPCInfo, get_instance_name

def build_nat_instance(groups = 'NATSG'):  # Default is to build in NAT group
    """Build NAT instance in a VPC
    For AWS NAT ami-0ca65a55561666293',  # amzn-ami-vpc-nat-hvm-2018.03.0.20181116-x86_64-ebs
    For PFSense """
    nats = ({'Name' : 'Amazon Linux AMI 2018.03.0.20180811 x86_64 VPC NAT HVM EBS', 'ami' : 'ami-e6768381'},
            {'Name' : 'PFsense community edition 2.3.4', 'ami' : 'ami-0748640ba57b52070'},)
    nat = nats[0]  # Select which NAT instance to use
    ec2 = boto3.resource('ec2', region_name='eu-west-2')
    info = VPCInfo()
    if len(info.NAT_instances) == 0:
        print(f"Building {nat['Name']}")
        result = ec2.create_instances(ImageId=nat['ami'],  # amzn-ami-vpc-nat-hvm-2018.03.0.20181116-x86_64-ebs
                             InstanceType='t3.nano',
                             TagSpecifications=[
                                 {
                                     'ResourceType': 'instance',
                                     'Tags': [{'Key': 'H3:Name', 'Value': 'NAT Instance'}]
                                 },
                             ],
                             MinCount=1, MaxCount=1,
                             #SecurityGroupIds=[info.security_groups['NATSG']['id']],
                             KeyName=info.key_name,
                             # IamInstanceProfile={
                             #     'Arn': 'arn:aws:iam::123456789012:instanceprofile/ExampleInstanceProfile',
                             #     'Name': 'ExampleInstanceProfile'
                             # },
                             NetworkInterfaces=[
                                  {
                                      'SubnetId': info.public_subnets[0]['id'],
                                      'DeviceIndex': 0,
                                      'AssociatePublicIpAddress': True,
                                      'Groups': [info.security_groups['NATSG']['id']]
                                  }
                              ]
                             )
    else:
        print(f'>> Not building NAT Instances as already {len(info.NAT_instances)} exist.')
        result = []
    return result


"""Build Bastion instance in a VPC
"""
nats = ({'Name': 'Ubuntu Server 18.04 LTS (HVM),EBS General Purpose (SSD) Volume Type.',
         'ami': 'ami-0b0a60c0a2bd40612'},)

def build_bastion_instance(groups = 'BastionSG', instance_name = 'Bastion Instance', public_subnet = True,
                           reliabilty_zone = 0, force_build=False):
    nat = nats[0]  # Select which NAT instance to use
    ec2 = boto3.resource('ec2', region_name='eu-west-2')
    info = VPCInfo()
    vpc = ec2.Vpc(info.vpc_id)
    instance_list = [{get_instance_name(i) : i.id} \
                              for i in vpc.instances.all() \
                              if get_instance_name(i) == instance_name]
    if len(instance_list) == 0 or force_build:
        print(f"Building {nat['Name']}")
        # Sort out the network interface
        if public_subnet:
            subnets = info.public_subnets
        else:
            subnets = info.private_subnets
        network_interfaces = [{
                'SubnetId': subnets[reliabilty_zone]['id'],
                'DeviceIndex': 0,
                'AssociatePublicIpAddress': public_subnet,
                'Groups': [info.security_groups[groups]['id']]
        }]
        result = ec2.create_instances(ImageId=nat['ami'],  # amzn-ami-vpc-nat-hvm-2018.03.0.20181116-x86_64-ebs
                             InstanceType='t3.nano',
                             TagSpecifications=[
                                 {
                                     'ResourceType': 'instance',
                                     'Tags': [{'Key': 'H3:Name', 'Value': instance_name}]
                                 },
                             ],
                             MinCount=1, MaxCount=1,
                             KeyName=info.key_name,
                             NetworkInterfaces=network_interfaces
                             )
    else:
        print(f'>> Not building Bastion Instances as already {len(instance_list)} exist.')
        result = []
    return result


def delete_instance(instance_name, delete_max = 1, should_be_some=True):
    ec2 = boto3.resource('ec2', region_name='eu-west-2')
    info = VPCInfo()
    vpc = ec2.Vpc(info.vpc_id)
    instance_list = [i.id for i in vpc.instances.all() \
                     if get_instance_name(i) == instance_name]
    if len(instance_list) == 0 and should_be_some:
        print(f">>No {instance_name} and there should be some\n")
    elif len(instance_list) == 0:
        pass  # all deleted
    elif len(instance_list) <= delete_max:
        for id in instance_list:
            print(f'--Instance = {id}')
            instance = ec2.Instance(id)
            instance.terminate()
    else:
        print(f">> Too many {instance_name}s ({len(instance_list)}), delete by hand before rebuilding\n")


def delete_nat_instance():
    delete_instance('NAT Instance')


def delete_bastion_instance():
    delete_instance('Bastion Instance')


if __name__ == "__main__":
    build_nat_instance()
    # delete_nat_instance()
