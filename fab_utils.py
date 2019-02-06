import socket
from time import sleep

from fabric.api import hide, sudo


class FabricCommandError(Exception):
    pass


def apt_update():
    """Run a test command and check instance working ok"""
    print('>> apt update')
    with hide('output'):
        r = sudo('apt update')
    if r.find('packages can be upgraded') == -1:
        raise FabricCommandError(f'Result = {r}')
    print('>>> Success apt update')


def wait_for_ssh_to_be_up(instance, retries=120, retry_delay=5):
    wait_for_port_to_be_up(instance, port=22)


class ServerUpTimeOut(Exception):
    pass



def wait_for_port_to_be_up(instance, port, retries=120, retry_delay=5):
    """Once"""
    if True:
        sleep(20)  # TODO
    else:
        retry_count = 0
        while retry_count <= retries:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex((instance.public_ip_address, port))
            finally:
                sock.close()
            if result == 0:
                break
            else:
                sleep(retry_delay)
        if retry_count > retries:
            raise ServerUpTimeOut(f'Have waited over {retries * retry_delay} secs and instance {instance.id} has not come up')


