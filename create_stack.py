import time

import boto3
from botocore.exceptions import ClientError
from collections import OrderedDict


from build_vpc_template import build_vpc_stack_template


def vpc_stack_name():
    return 'django-prod'


def list_stacks():
    """List all the stacks that have completed or rolled back in the default Region"""
    client = boto3.client('cloudformation')  # Default region
    response = client.list_stacks(StackStatusFilter=['CREATE_COMPLETE', 'ROLLBACK_COMPLETE'])
    names = []
    for stack in response["StackSummaries"]:
        names.append(stack['StackName'])
    return names

def get_active_stacks():
    """Get info on the production stack"""
    client = boto3.client('cloudformation')  # Default region
    response = client.list_stacks()
    active_stacks = [x for x in response["StackSummaries"]
                     if x['StackStatus'] not in ['DELETE_COMPLETE'] and x['StackName'] == vpc_stack_name()]
    return active_stacks

def get_logical_id(security_group):
    try:
        tag_dict = {t['Key']: t['Value'] for t in security_group.tags}
        return tag_dict['aws:cloudformation:logical-id']
    except (KeyError, TypeError):  # Get typeeorror if not tags
        return 'default'


def get_instance_name(instance):
    try:
        tag_dict = {t['Key']: t['Value'] for t in instance.tags}
        return tag_dict['H3:Name']
    except (KeyError, TypeError):  # Get typeeorror if not tags
        return ''


class VPCInfo:
    def __init__(self):
        self._stacks = get_active_stacks()
        ec2 = boto3.resource('ec2')
        client = boto3.client('ec2')  # Default region
        if len(self._stacks) == 1:
            # Add all the items as properties
            # TODO BUG once you have added and then they disappear all dynamic properties stay
            for key, value in self._stacks[0].items():
                self.__dict__[key] = value
            self.get_vpc_info(client)
            self.get_subnets(ec2, client)
            self.get_security_groups(ec2)
            self.get_instances(ec2)
            # get stack description
            cf_client = boto3.client('cloudformation')  # Default region
            response = cf_client.describe_stacks(
                StackName=self.StackId,
                NextToken='1'
            )

    @property
    def vpc_stack_name(self):
        return vpc_stack_name()

    @property
    def key_name(self):
        return 'EUWest2KeyPair'

    def get_vpc_info(self, client):
        # Get VPC's
        response = client.describe_vpcs(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': ['django-prod VPC',]
                },
            ]
        )
        resp = response['Vpcs']
        self.vpc_id = None
        for stack in resp:
            try:
                tag_dict = {t['Key']: t['Value'] for t in stack['Tags']}  # Convert tags to dictionary
                if tag_dict['aws:cloudformation:stack-name'] == vpc_stack_name():  # Found
                    if self.vpc_id is None:
                        self.vpc_id = stack['VpcId']
            except KeyError:  # If not stackname then certainly not the stack we are interested in.
                pass
        if len(resp) == 0:
            print('No VPC found')

    def get_subnets(self, ec2, client):
        """Get subnets and divide them into public and private"""
        filters = [{'Name': 'vpc-id', 'Values': [self.vpc_id]}]
        self.subnets = list(ec2.subnets.filter(Filters=filters))
        public_subnets = OrderedDict()
        private_subnets = OrderedDict()

        for subnet in self.subnets:
            subnet_full = client.describe_subnets(
                SubnetIds=[subnet.id]).get('Subnets')[0]
            tag_dict = {t['Key'] : t['Value'] for t in subnet_full['Tags']}
            try:
                network = tag_dict['Network']
            except KeyError:
                network = None
            name = tag_dict['Name']
            if name[:6].lower() == 'public':
                public_subnets[tag_dict['Name']] = {'Name' : name, 'id' : subnet.id}
            elif name[:7].lower() == 'private':
                private_subnets[tag_dict['Name']] = {'Name': name, 'id': subnet.id}
        sorted_public_subnets = [public_subnets[x] for x in sorted(public_subnets)]
        sorted_private_subnets = [private_subnets[x] for x in sorted(private_subnets)]
        self.public_subnets = sorted_public_subnets
        self.private_subnets = sorted_private_subnets

    def get_security_groups(self, ec2):
        """Get Security groups"""
        vpc = ec2.Vpc(self.vpc_id)
        self.security_groups = {get_logical_id(sg): {'id': sg.id, 'description': sg.description, 'group_name': sg.group_name} for sg in vpc.security_groups.all()}

    def get_instances(self, ec2):
        """Get Instances"""
        vpc = ec2.Vpc(self.vpc_id)
        self.instances = [{get_instance_name(i) : i.id} for i in vpc.instances.all()]
        self.NAT_instances = [{get_instance_name(i) : i.id} \
                              for i in vpc.instances.all() \
                              if get_instance_name(i) == 'NAT Instance']

    @property
    def stack_running(self):
        return len(self._stacks) == 1 and self._stacks[0]['StackStatus'] == 'CREATE_COMPLETE'

    @property
    def stack_stopped(self):
        return len(self._stacks) == 0


            # r = {'name_id': subnet_full['SubnetId'],
            #      'id': subnet_full['SubnetId'],
            #      'VPC id': subnet_full['VpcId'],
            #      'cidr': subnet_full['CidrBlock'],
            #      'availibilty_zone': subnet_full['AvailabilityZone'],
            #      'name': tag_dict['Name'],
            #      'network': network
            #      }


    def __str__(self):
        result = f'Checking for VPC {vpc_stack_name()}\n'
        if self.stack_running:
            result += 'Stack running\n'
            try:
                result += f'StackId = {self.StackId}\n'
            except:
                result += f'No StackId and there should be. Dict =  {self.__dict__}\n'
            result += f"VPC id = {self.vpc_id}\n"
            result += f"Public Subnets =  {[sn['Name'] for sn in self.public_subnets]}\n"
            result += f"Private Subnets =  {[sn['Name'] for sn in self.private_subnets]}\n"
            result +=f"Security groups = {[key for key,value in self.security_groups.items()]}\n"
            result +=f"Instances {self.instances}\n"
            result +=f"NAT Instance {self.NAT_instances}\n"
            if len(self.NAT_instances)  == 0:
                result +=f">>No NAT Instance and there should be one\n"
            elif len(self.NAT_instances)  > 1:
                result +=f">> Too many NAT Instances ({len(self.NAT_instances)}), delete some by hand\n"
            result +=f"Bastion in progress\n"
        else:
            if self.stack_stopped:
                result += 'No stacks running\n'
            else:
                result += 'Stack in transition\n'
        return result


def vpc_stack_deleted():
    # TODO if being deleted DELETE_IN_PROGRESS then should wait until delete finishes or fails
    # Delete takes minutes to run
    return vpc_stack_name() not in set(list_stacks())


def build_vpc_stack(retry_count = 0):
    print('**If there are lambda instances deployed in this VPC then you \n'
          + 'will not able to delete or rebuild the VPC until all the lamda \n'
          + 'instances are undeployed. Also network instances detached and deleted.')
    if vpc_stack_deleted():
        print('Building VPC stack')
        filename = build_vpc_stack_template()
        with open(filename) as f:
            template = f.read()
        client = boto3.client('cloudformation')  # Default region
        result = client.create_stack(
            StackName = vpc_stack_name(),
            TemplateBody = template
        )
        wait_till_finished(in_progress='CREATE_IN_PROGRESS')
    else:
        if retry_count < 1:
            print('Not building VPC stack as already exists.  Will delete and try again')
            delete_vpc_stack()
            build_vpc_stack(retry_count=retry_count+1)
        else:
            print(f'Have retried to build VPC but failed after {retry_count} attempts.')


def delete_vpc_stack(client=None):
    """Deletes stack, if no stack to start with returns happily quickly"""
    if client is None:
        client = boto3.client('cloudformation')  # Default region
    result = client.delete_stack(
        StackName=vpc_stack_name(),
    )
    wait_till_finished(in_progress='DELETE_IN_PROGRESS')


def wait_till_finished(estimated_time = 120, in_progress='DELETE_IN_PROGRESS'):  # estimate time in seconds
    client = boto3.client('cloudformation')  # Default region
    count = 0
    running = True
    while running and count < estimated_time:
        count += 1
        try:
            response = client.describe_stacks(StackName=vpc_stack_name())
            status = response['Stacks'][0]['StackStatus']
        except ClientError:
            status = ''  # There is no stack
        running = status == in_progress
        if count % 100 == 0:
            print('.', flush=True)
        else:
            print('.', end='', flush=True)
        #running = response == finsihed state
        if running:
            time.sleep(1)
        else:
            print(f"\n>> {status}. Waited ca {count} seconds.")

def launch_stack():
    pass




def test():  # estimate time in seconds
    client = boto3.client('cloudformation')  # Default region
    response = client.describe_stacks(StackName=vpc_stack_name())
    status = response['Stacks'][0]['StackStatus']
    print(status == 'CREATE_COMPLETE')
    print(f" >> {status}")

if __name__ == "__main__":
    info = VPCInfo()
    print(info)
    # print('List of stacks:')
    # a = list_stacks()
    # print('List of stacks:')
    # for name in a:
    #     print(f'  {name}')
    # build_vpc_stack()
    # # delete_vpc_stack()
