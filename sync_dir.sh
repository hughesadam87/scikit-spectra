#!/bin/sh

#Remove pyc files from directory
sh removepyc.sh

#Look for lib directory and delete it

#Run python setup.py
python setup.py install --home='..'

#Go to '../lib/python'
#record both directory and filename
#Go to site packages
#If found pyuvis directory delete (maybe just leave eggfile as it will change with version and manually click replace when prompt shows)
#paste


