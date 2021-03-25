
# Install LiberaForms

## Install mongodb
https://docs.mongodb.com/manual/tutorial/install-mongodb-on-debian/


## Clone LiberaForms
```
apt-get install git
git clone https://gitlab.com/liberaforms/liberaforms.git /opt/LiberaForms
```

## Create a python3 venv
If you have Python3 on your host
```
apt-get install python3-venv
python3 -m venv /opt/LiberaForms/venv
```
Or if you have old python2 on your host
```
apt-get install virtualenv
virtualenv /opt/LiberaForms/venv --python=python3
```

### Install python packages
```
source /opt/LiberaForms/venv/bin/activate
pip install --upgrade setuptools
pip install wheel
pip install -r /opt/LiberaForms/requirements.txt
pip install gunicorn
```

## Configure

### Session management
Before editing config.cfg, decide if you want session data saved on the filesystem or in memory.

The default configuration is `filesystem`

#### Filesystem
Create this directory. session data will be saved there.
```
mkdir /opt/LiberaForms/liberaforms/flask_session
chown www-data /opt/LiberaForms/liberaforms/flask_session
```

#### Memory
If you prefer to use memcached, you need to do this.
```
apt-get install memcached
source /opt/LiberaForms/venv/bin/activate
pip install pylibmc
```

### Create and edit `/opt/LiberaForms/config.cfg`
```
cd /opt/LiberaForms
cp config.example.cfg config.cfg
```

You can create a SECRET_KEY like this
```
openssl rand -base64 32
```

### File permissions
Protect the config file
```
chown www-data /opt/LiberaForms/config.cfg
chmod go-rw /opt/LiberaForms/config.cfg
```

Admins can upload a logo. You need to give the system user who runs LiberaForms write permission
```
chown -R www-data /opt/LiberaForms/liberaforms/static/images
```

## Test your installation
```
source /opt/LiberaForms/venv/bin/activate
gunicorn -c /opt/LiberaForms/gunicorn.py liberaforms:app
```

## Install Supervisor to manage the LiberaForms process.
```
apt-get install supervisor
```

### Edit `/etc/supervisor/conf.d/LiberaForms.conf`
```
[program:LiberaForms]
command = /opt/LiberaForms/venv/bin/gunicorn -c /opt/LiberaForms/gunicorn.py liberaforms:app
directory = /opt/LiberaForms
user = www-data
```

### Restart supervisor and check if LiberaForms is running.
```
systemctl restart supervisor
supervisorctl status LiberaForms
```

## Debug LiberaForms
You can check supervisor's log at `/var/log/supervisor/...`

You can also run LiberaFroms in degug mode.
```
supervisorctl stop LiberaForms
cd /opt/LiberaForms
source /opt/LiberaForms/venv/bin/activate
python run.py
```

## Configure nginx proxy
See `docs/nginx.example`


## Database backup
Run this and check if a copy is dumped correctly.
```
/usr/bin/mongodump --db=LiberaForms --out="/var/backups/"
```

Add a line to your crontab to run it every night.
```
30 3 * * * /usr/bin/mongodump --db=LiberaForms --out="/var/backups/"
```
Note: This overwrites the last copy. You might want to change that.