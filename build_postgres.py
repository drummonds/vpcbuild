"""Fabric commands to build a Postgres server"""
import environ
from fabric.api import hide, sudo, put

from fab_utils import apt_update, FabricCommandError, wait_for_port_to_be_up

# Load operating system environment variables and then prepare to use them
env = environ.Env()
env.read_env()

def create_template():
    with open("secrets/postgres_template", "w") as f:
        password = env.str('POSTGRES_PASSWORD')
        f.write(f"ALTER USER postgres WITH PASSWORD '{password}';\n")
        f.write('\\q\n')


def cmd_postgres_install():
    """Run a test command and check instance working ok"""
    # print(run('sudo apt update'))
    print('>> install postgresql')
    with hide('output'):
        r = sudo('apt -y install postgresql postgresql-contrib')
    if r.find('Success. You can now start the database server') == -1:
        raise FabricCommandError(f'Result = {r}')
    print('>>> Success install postgresql')



def install_postgres(instance):
    """Try installing Postgres"""
    apt_update()
    cmd_postgres_install()
    local_ip_cidr = env.str('LOCAL_IP_CIDR')
    print(sudo(f'sed -i "$ a host all all {local_ip_cidr} md5" /etc/postgresql/10/main/pg_hba.conf'))
    sed_command = """sudo sed -i "s:\#listen_addresses = 'localhost':listen_addresses = '*':" /etc/postgresql/10/main/postgresql.conf"""
    print(f'--> sed command = {sed_command}')
    print(sudo(sed_command))
    print(sudo('/etc/init.d/postgresql reload'))  # Reload postgres to add port
    # Change user password in Postgres
    create_template()
    upload = put('secrets/postgres_template', 'postgres_template')
    if not upload.succeeded:
        raise FabricCommandError('Failed to upload template file')
    print(sudo('su postgres -c "psql -f postgres_template"'))
    try:
        print(sudo('reboot'))
    except:
        pass
    wait_for_port_to_be_up(instance, 5432)
    print('>>> Completed build of Postgres should be accessible')


if __name__ == "__main__":
    create_template()