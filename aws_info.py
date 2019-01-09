"""Check AWS information
Aim is to look at waht information is stored in .aws and then to have versions to allow collecting information
from AWS"""

import boto3
import os
from pathlib import Path

import configparser

def check_aws_connection():
    print('Checking AWS connection')
    print('Looking at ~/.aws which is where default information is stored.')
    aws_rootpath = '~/.aws'
    p = Path(aws_rootpath).expanduser()
    if p.exists():
        print(f'Found AWS root path, {aws_rootpath}.')
        for root, dirs, files in os.walk(p):
            for name in files:
                fp = os.path.join(root, name)
                print(fp)
                with open(fp) as f:
                    print(' ' + f.read())
            for name in dirs:
                print(os.path.join(root, name))
        credentials_f = p.joinpath('credentials')
        if credentials_f.exists():
            print('Found credentials file')
            config = configparser.ConfigParser()
            config.read(credentials_f)
            print(f"AWS Access key ID = {config['default']['aws_access_key_id']}")
            region_f = p.joinpath('config')
            if region_f.exists():
                print('Found config file')
                config = configparser.ConfigParser()
                config.read(region_f)
                print(f"AWS default region = {config['default']['region']}")
                print('Now read to try connection')
                s3 = boto3.resource('s3')  # boto3 picks up credentials
                s3client = boto3.client('s3')
                response = s3client.list_buckets()
                for bucket in response["Buckets"]:
                    print(bucket['Name'])
            else:
                print(f'>>Amazon credentials file does not exist, {credentials_f}')
        else:
            print(f'>>Amazon credentials file does not exist, {credentials_f}')
            credentials_f = p.joinpath('credentials')
    else:
        print(f'>> The AWS root path, {aws_rootpath} does not exist.')




if __name__ == '__main__':
    check_aws_connection()
