# python2 to python3 update

apt -y update
apt -y upgrade
apt -y install python3
apt -y install python3-pip

ln -sf /usr/bin/python3 /usr/bin/python
ln -sf /usr/bin/pip3 /usr/bin/pip

pip install requests
pip install python-dateutil
pip install pyserial
pip install smbus
pip install RPi.GPIO

#pip install cherrypy
#pip install manuf
#pip install termcolor
#pip install getmac
#pip install jinja2
#pip install twilio
