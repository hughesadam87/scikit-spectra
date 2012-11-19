Dependencies/Installation
=========================

Dependencies
------------
In its current state, pyuvvis requires following dependencies:

**pandas**, **scipy**, **chaco**

scipy_ and chaco_, for now, aren't critically important.  Only a few **scipy** modules are used, 
and the implementation of **chaco** is ancillary at this point in time.  As for versions, I would
recommend the most current versions of these packages, as **pyuvvis** has not beed adequately 
tested on various systems at this point in its nascent development.


Installation
------------

Download the source_ and run::

    python setup.py install

This should install to your systems default Python path.  If your defaul Python path is not found, or you have multiple Python distributions,
install to an arbitrary directory using the ``--home'' option:

    python setup.py install --home=/path/to/directory/

This will create a subdirectory with the structure **path/to/directory/lib/python/pyuvvis/**

Copy the pyuvvis folder into your Python distributions site-packages directory.  

Testing Installation
--------------------

Substantial tests are coming.  For now, to test if the program is correctly installed, open a Python shell and run the following:

    from pyuvvis import *
    from pyuvvis.data import *

This should result in no errors.  

.. source_: https://github.com/hugadams/pyuvvis





　

　

　
