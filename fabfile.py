import datetime as dt
from fabric.api import *
import fabric.contrib.project as project
import os
from time import sleep
from unipath import Path

from fabric.api import local, env, task

from build_postgres import install_postgres
from create_stack import  build_vpc_stack, delete_vpc_stack, VPCInfo
from create_nat_instance import build_nat_instance, delete_nat_instance, \
    build_bastion_instance, delete_bastion_instance, \
    delete_instance
from fab_utils import FabricCommandError, wait_for_ssh_to_be_up

import boto3

import aws_info

@task
def check():
    """Check the AWS connection"""
    aws_info.check_aws_connection()

@task
def list():
    """List VPC information"""
    print('Checking VPC info')
    info = VPCInfo()
    print(info)


@task
def build_vpc():
    """Build VPC Environment"""
    print('This will build an environment')
    print('Create VPC template')
    local('python build_vpc_template.py')
    print('Building stack takes about 90 secs')
    build_vpc_stack()

@task
def destroy_vpc():
    print('This will destroy an environment with safeguards')
    delete_vpc_stack()

@task
def build_nat():
    print('This will build a NAT instance in the latest VPC')
    build_nat_instance()

@task
def destroy_nat():
    print('This will destroy the last NAT instance')
    delete_nat_instance()

@task
def build_bastion():
    print('This will build a Bastion instance in the latest VPC')
    build_bastion_instance()

@task
def destroy_bastion():
    print('This will destroy the last Bastion instance')
    delete_bastion_instance()



@task
def destroy_it_all():
    """update all (production and localsite)"""
    destroy_bastion()
    destroy_nat()
    destroy_vpc()


@task(alias="dia")
def do_it_all():
    """update all (production and localsite)"""
    build_vpc()
    build_nat()


env.key_filename = 'C:/Users/HumphreyDrummond/CloudStation/Library/keys/aws/EUWest2KeyPair.pem'


@task
def test_db():
    """Build a Postgres Bastion instance"""
    execute(delete_test_db)
    instance = build_bastion_instance(force_build=True, instance_name = 'Bastion Postgres Instance')[0]
    print(f'Waiting until exists')
    instance.wait_until_exists()
    print(f'Now wait until running')
    instance.wait_until_running()
    print(f'Now running')
    print(f'Instance = {instance}')
    instance.reload()
    print(f'Public IP = {instance.public_ip_address}')
    host_list = [f'ubuntu@{instance.public_ip_address}']
    # Requiring a login but it shouldn't
    print(f'Waiting till run {dt.datetime.today().strftime("%H:%M:%S")}')
    wait_for_ssh_to_be_up(instance)
    print(f'Now ok run  {dt.datetime.today().strftime("%H:%M:%S")}')
    execute(test_command, hosts=host_list)
    execute(install_postgres, instance, hosts=host_list)

import socket
import time

class ServerUpTimeOut(Exception):
    pass

@task
def delete_test_db():
    """Delete all Bastion Postgres database instances"""
    print('Deleting Bastion postres instances')
    delete_instance(instance_name = 'Bastion Postgres Instance', delete_max = 100, should_be_some=False)


@task
def test_2_run():
    """Just run test 2"""
    host_list = [f'ubuntu@18.130.83.114']
    execute(test_command, hosts=host_list)
    # execute(install_postgres, hosts=host_list)


def test_command():
    """Run a test command and check instance working ok"""
    with hide('running'):
        r = run('uname -a', timeout=5)
    if r.find('Linux') == -1:
        raise FabricCommandError(f'Result = {r}')


@task
def test():
    """This will build a Bastion instance in a two public and two private zones"""
    build_bastion_instance(force_build=True)
    #build_bastion_instance(reliabilty_zone=1, force_build=True)
    #build_bastion_instance(public_subnet=False, reliabilty_zone=1, force_build=True)
    #build_bastion_instance(public_subnet=False, reliabilty_zone=2, force_build=True)

# Use this for debugging
if __name__ == "__main__":
    test_db()
    # test_2_run()
