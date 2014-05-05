.. image:: pyparty/data/coverimage.png
   :height: 100px
   :width: 200 px
   :scale: 50 %
   :alt: alternate text
   :align: left

==========
What's New
==========

===========================================
pyuvvis: Tools for explorative spectroscopy
===========================================

Getting Started
===============

Legacy documentation_ is generously hosted by github_.

   .. _github: http://github.com
 
   .. _documentation: http://hugadams.github.com/pyuvvis/


License
=======

3-Clause Revised BSD_

   .. _BSD : https://github.com/hugadams/pyuvvis/blob/master/LICENSE.txt

Installation
============

Dependencies
------------
In its current state, pyuvvis requires following dependencies:

**pandas**, **scipy**, **chaco**

.. _scipy: http://www.scipy.org
.. _chaco: http://code.enthought.com/chaco/

I would recommend using `Enthought Canopy`_ and its excellent
the package manager; however, ``pyuvvis`` is also 
registered on PyPi_.

   .. _PyPi : https://pypi.python.org/pypi/PyUvVis

   .. _`Enthought Canopy` : https://www.enthought.com/products/canopy/

Pip Install
-----------

Make sure you have pip installed:

    sudo apt-get install python-pip
    
Then:
   
    pip install pyuvvis
    
To install all of the dependencies, download ``pyparty`` from github, navigate
to the base directory and type:

    pip install -r requirements.txt


Installation from source
------------------------

In the ``pyparty`` base directory run:

    python setup.py install

The developmental version can be cloned from github:

    git clone https://github.com/hugadams/pyuvvis.git
    
This will not install any dependencies.

Download the source_ and run::

   python setup.py install

This should install to your systems default Python path.  If your default Python path is not found, or you have multiple Python distributions,
install to an arbitrary directory using the home keyword option::

   python setup.py install 
  
.. _source: https://github.com/hugadams/pyuvvis

Testing Installation
--------------------

Open a Python shell and run the following::

   from pyuvvis import *

   from pyuvvis.data import *

This should result in no errors.  


History and Background
========================

``pyuvvis`` originally began at the George Washington University in an 
effort to develop exploratory visualization techniques with UVVis
data, particularly the output of fiberoptic/nanotechnology research. 

The decision to officialy package these nascent tools was made for the following 
reasons:
 
   1. To faciliate easier sharing and better organization between collaborators.
   2. To document the progress and functionalities of the toolset.
   3. To broadcast the toolkit to the community, and hopefully to merge with other Python spectroscopy packages.

In regard to the final point, ``pyuvvis`` is not an attempt to be the de-facto spectroscopy
toolkit in Python; rather, it is a domain-specific wrapper for pandas.  It should be quite extensible
to other spectroscopy domains, where it may perform a supporting or ancillary role.  It is our 
hope that in the future, other internal GWU tools for fiber optics design and nanomaterial plasmonics,
combined with this package, may form the basis for a crude nano-optics Python package.

Related Libraries
=================
Interested in the Python ecosystem?   Check out some of these related libraries:

   - NumPy_ (Fundamental vectorized numerics in Python)
   - SciPy_ (Collection of core, numpy-based scientific libraries)
   - scikit-image_ (Scipy image processing suite)
   - matplotlib_ (De facto static plotting in Python)
   - pandas_ (Data analysis library : inspired ``pyparty`` ParticleManager API)
   - ilastik_ (Interactive Learning and Segmentation Tool)
   - Pillow_ (Python Image Library)

   .. _Pillow: http://python-imaging.github.io/
   .. _NumPy: http://www.numpy.org/
   .. _pandas: http://pandas.pydata.org/
   .. _SciPy: http://scipy.org/
   .. _matplotlib : http://matplotlib.org/
   .. _ilastik : http://www.ilastik.org/
   
Coming Soon
===========
   -
   -
   -
   
Have a feature request, or want to report a bug?  Please fill out a github
issue_ with the appropriate label.	

.. _issue : https://github.com/hugadams/pyuvvis/issues

About the Author
================

I'm a PhD student at GWU (check me out on researchgate_, Linkedin_ or twitter_(@hughesadam87))
and former Enthought intern. I work in biomolecule sensing and nanophotonics.  
Like any PhD student, my time is stretched across many projects.  As such,
the ``pyparty`` source code may is messy in places, and a test suite has
yet to be developed.  Developing the iPython notebook tutorials 
alongside the code helped served as a basic regression test platform.  

   .. _researchgate : https://www.researchgate.net/profile/Adam_Hughes2/?ev=hdr_xprf
   .. _Linkedin : http://www.linkedin.com/profile/view?id=121484744&goback=%2Enmp_*1_*1_*1_*1_*1_*1_*1_*1_*1_*1_*1&trk=spm_pic
   .. _twitter : https://twitter.com/hughesadam87

Acknowledgements
================
Thank you countless developers who have patiently answered hundreds of 
my questions on too many mailing lists and sites to list.

Thank you `Zhaowen Liu`_ for all of your help with this project, our 
other projects and for your unwaivering encouragement (and for the panda).

    .. _`Zhaowen Liu` : https://github.com/EvelynLiu77
