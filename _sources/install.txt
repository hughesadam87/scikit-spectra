Installation
============

Dependencies
------------
In its current state, scikit-spectra requires following dependencies:

**pandas (0.14)**, **scipy**, **IPython Notebook 0.2 or higher**

.. _scipy: http://www.scipy.org

.. warning::
    Pandas 0.14 is the only supported version at the moment due to API changes in 0.15.  We apologize for the inconvenience.

To use the newer features if scikit-spectra such as the IPython notebook GUIs, please install:

   - `IPython Notebook 3.0.0 Dev. Version <https://github.com/ipython/ipython>`_
   - `MPLD3 <https://github.com/jakevdp/mpld3>`_

I would recommend using `Enthought Canopy`_ and its excellent
the package manager.  ``scikit-spectra`` is also 
registered on PyPi_.

   .. _PyPi : https://pypi.python.org/pypi/scikit-spectra

   .. _`Enthought Canopy` : https://www.enthought.com/products/canopy/

Pip Install
-----------

Make sure you have pip installed::

   sudo apt-get install python-pip
    
Then::
   
   pip install scikit-spectra
    
To install all of the dependencies, download ``scikit-spectra`` from github, navigate
to the base directory and type::

   pip install -r requirements.txt


Installation from source
------------------------

In the ``skspec`` base directory run::

   python setup.py install

The developmental version can be cloned from github::

   git clone https://github.com/hugadams/scikit-spectra.git
    
This will not install any dependencies.

Download the source_ and run::

   python setup.py install

This should install to your systems default Python path.  If your default Python path is not found, or you have multiple Python distributions,
install to an arbitrary directory using the home keyword option::

   python setup.py install 
  
.. _source: https://github.com/hugadams/scikit-spectra

To install all of the dependencies (pandas, scipy and their various dependencies), download ``scikit-spectra`` from github, navigate
to the base directory and type::

    pip install -r requirements.txt

Testing Installation
--------------------

Open a Python shell and run the following::

   from skspec import *

   from skspec.data import *

This should result in no errors.  

Have a feature request, or want to report a bug?  Please fill out a github
issue_ with the appropriate label.	

.. _issue : https://github.com/hugadams/scikit-spectra/issues
