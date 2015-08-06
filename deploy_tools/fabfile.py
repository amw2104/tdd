from fabric.contrib.files import append, exists, sed
from fabric.api import env, local, run, sudo
import random

REPO_URL = 'https://github.com/amw2104/tdd.git'

#env.user = 'ubuntu'
#env.hosts = ['superlists-staging.thoughtful.software']

def deploy():
    site_folder = '/home/elspeth/sites/%s' % (env.host,)
    source_folder = site_folder + '/source'
    _create_directory_structure_if_necessary(site_folder)
    _get_latest_source(source_folder)
    _update_settings(source_folder, env.host)
    _update_virtualenv(source_folder)
    _update_static_files(source_folder)
    _update_database(source_folder)

def _create_directory_structure_if_necessary(site_folder):
    for subfolder in ('database', 'static', 'virtualenv', 'source'):
        sudo('mkdir -p %s/%s' % (site_folder, subfolder), user='elspeth')

def _get_latest_source(source_folder):
    if exists(source_folder + '/.git'):
        sudo('cd %s && git fetch' % (source_folder,), user='elspeth')
    else:
        sudo('git clone %s %s' % (REPO_URL, source_folder), user='elspeth')
    current_commit = local("git log -n 1 --format=%H", capture=True)
    sudo('cd %s && git reset --hard %s' % (source_folder, current_commit), user='elspeth')

def _update_settings(source_folder, site_name):
    settings_path = source_folder + '/superlists/settings.py'
    sed(settings_path, "DEBUG=True", "DEBUG=False", use_sudo=True)
    sed(settings_path, 'ALLOWED_HOSTS =.+$', 'ALLOWED_HOSTS = ["%s"]' % (site_name,), use_sudo=True)
    secret_key_file = source_folder + '/superlists/secret_key.py'
    if not exists(secret_key_file):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        key = ''.join(random.SystemRandom().choice(chars) for _ in range(50))
        append(secret_key_file, "SECRET_KEY = '%s'" % (key,), use_sudo=True)
    append(settings_path, '\nfrom .secret_key import SECRET_KEY', use_sudo=True)

def _update_virtualenv(source_folder):
    virtualenv_folder = source_folder + '/../virtualenv'
    if not exists(virtualenv_folder + '/bin/pip'):
        sudo('virtualenv --python=python3 %s' % (virtualenv_folder,), user='elspeth')
    sudo('%s/bin/pip install -r %s/requirements.txt' % (virtualenv_folder, source_folder), user='elspeth')

def _update_static_files(source_folder):
    sudo('cd %s && ../virtualenv/bin/python3 manage.py collectstatic --noinput' % (source_folder,), user='elspeth')

def _update_database(source_folder):
    sudo('cd %s && ../virtualenv/bin/python3 manage.py migrate --noinput' % (source_folder,), user='elspeth')
