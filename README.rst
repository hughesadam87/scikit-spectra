===========================================
pyuvvis: Tools for explorative spectroscopy
===========================================

What is it
==========

**pyuvvis** is a set of wrappers and tools written using the pandas_ library
with the intention of exploring spectral data, especially UV-Vis spectroscopy.

   .. _pandas: http://pandas.pydata.org/index.html

License
=======

BSD

Documentation
=============

The official documentation_ is generously hosted by github_.

   .. _github: http://github.com
 
   .. _documentation: http://hugadams.github.com/pyuvvis/

Goals and Background
====================

``pyuvvis`` originally began at the George Washington University in an 
effort to develop exploratory and visualization techniques with UvVis
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

Installation
============

In the ``pyuvvis`` directory (same one where you found this file), execute::

    python setup.py install

See http://hugadams.github.com/pyuvvis/ for additional help.

The developmental version can be cloned from github:

    git clone https://github.com/hugadams/pyuvvis.git

And installed in a similar manner:

   cd pyuvvis

   python setup.py install

