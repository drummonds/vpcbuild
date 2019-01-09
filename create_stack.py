import time

import boto3
from botocore.exceptions import ClientError


from build_vpc_template import build_vpc_stack_template


def vpc_stack_name():
    return 'django-prod'


def list_stacks():
    client = boto3.client('cloudformation')  # Default region
    response = client.list_stacks(StackStatusFilter=['CREATE_COMPLETE'])
    names = []
    for stack in response["StackSummaries"]:
        names.append(stack['StackName'])
    return names


def vpc_stack_deleted():
    return vpc_stack_name() not in set(list_stacks())


def build_vpc(retry_count = 0):
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
            build_vpc(retry_count=retry_count+1)
        else:
            print(f'Have retried to build VPC but failed after {retry_count} attempts.')


def delete_vpc_stack(client = None):
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
    a = list_stacks()
    print('List of stacks:')
    for name in a:
        print(f'  {name}')
    #build_vpc()
    delete_vpc_stack()
