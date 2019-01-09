from fabric.api import *
import fabric.contrib.project as project
import os
from unipath import Path

from fabric.api import local, env, task

import aws_info

@task
def check():
    """Check the AWS connection"""
    aws_info.check_aws_connection()

@task
def build():
    print('This will build an enviroment')
    print('Create VPC template')
    local('python build_vpc_template.py')

@task
def destroy():
    print('This will destroy an enviroment with safegaurds')


@task(alias="dia")
def do_it_all():
    """update all (production and localsite)"""
    build()
    destroy()


