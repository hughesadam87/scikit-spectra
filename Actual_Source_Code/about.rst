About
=====

History and Background
----------------------

``scikit-spectra`` originally began as a set of scripts to use pandas_ for our spectral data.
We found that we were constantly moving metadata around, and that although pandas provided an
excellent basis for our analysis, the datastructures didn't quack the way we wanted.  Therefore,
we decided to roll our own structures that would repurpose aspects of pandas for Spectroscopy.  To
be useful, our library had to do the the following:

   1. Adapt Dataframe, Series and Panel into Spectroscopic objects without losing functionality.
       - `See what this entails... <https://github.com/pydata/pandas/issues/2485>`_
   2. Provide a flexible API so as not to limit users.

   3. Provide general spectroscopic utilities such as:
       -  Indexing for most common spectral unit systems.
       -  Baseline manipulation/Data normalization and transformation (i.e. raw, Abosrbance, % Transmittance)
       -  A uniform plotting API for 1D /2D /3D plots with support for interactivity.

   4.  Provide some GUI-level functionality; most spectroscopists don't want to use the command line.

In regard to the last point, we are very proud to announce we've created GUI's that run fully in the browser
through `IPython's widget system <http://nbviewer.ipython.org/github/ipython/ipython/blob/2.x/examples/Interactive%20Widgets/Widget%20Basics.ipynb>`_.

Related Scipy Libraries
-----------------------
Interested in the Python ecosystem?   Check out some of these related libraries:

   - NumPy_ (Fundamental vectorized numerics in Python)
   - scipy_ (Collection of core, numpy-based scientific libraries)
   - matplotlib_ (De facto static plotting in Python)
   - pandas_ (R on steroids)
   - plotly_ (Interactive/cloud plotting)
   - mpld3_ (Bringing Matplotlib to the Browser)

   .. _NumPy : http://www.numpy.org/
   .. _pandas : http://pandas.pydata.org/
   .. _scipy : http://scipy.org/
   .. _matplotlib : http://matplotlib.org/
   .. _plotly : https://plot.ly/
   .. _mpld3 : http://mpld3.github.io/     

Other Spectroscopy Libraries/Tools in Python
--------------------------------------------

Our goal was never to replace or compete with other spectroscopy libraries in Python.  We were delighted to see that many
Python spectroscopy tools are indeed built around NumPy_.  We wanted to provide rich datastructures that were built on Pandas rather
than numpy, and handled metadata in an intuitive way.  Our structures are general, and don't presume to be the de-facto 
solution to any particular type of spectroscopy (e.g. Ramen, IR, NMR...).  In fact, we'd really love to collaborate to build interoperability
between Python spectroscopy libraries.  

If you manage a library and want to collaborate, please contact me at hughesadam87@gmail.com


Developers
----------

Adam Hughes (researchgate_, Linkedin_ or twitter_ (@hughesadam87)) and `Evelyn Liu`_ are PhD students working
in biomolecule sensing and nanophotonics under `Dr. Mark Reeves Biophysics Group`_.  We started this project
after encountering shortcomings in the open-source spectroscopy toolbelt, and after learning how apt pandas
was for our datasets.

   .. _Evelyn Liu : https://www.researchgate.net/profile/Zhaowen_Liu
   .. _researchgate : https://www.researchgate.net/profile/Adam_Hughes2/?ev=hdr_xprf
   .. _Linkedin : http://www.linkedin.com/profile/view?id=121484744&goback=%2Enmp_*1_*1_*1_*1_*1_*1_*1_*1_*1_*1_*1&trk=spm_pic
   .. _twitter : https://twitter.com/hughesadam87
   .. _`Dr. Mark Reeves Biophysics Group` : http://www.gwu.edu/~condmat/CME/reeves.html

Acknowledgements
----------------
Of the many developers who have patiently answered my questions on various mailing list, I must specifically thank:

   - `Jeff Reback <https://twitter.com/jreback>`_ (pandas)
   - `Stephan Hoyer <https://twitter.com/shoyer>`_ (pandas/xray)
   - Nicholas Bollweg (IPython)
   - `Jonathan March and Robert Kern <https://www.enthought.com/company/team/devs/>`_ (Traits/Enthought) 
   - Juan Nunez-Iglesias, Tony Yu, Setfan van der Walt `(scikit-image) <http://scikit-image.org/>`_

In regard to this website, we've used the autodocumentation library, `Sphinx <http://sphinx-doc.org/>`_, with the awesome `Sphinx-bootstrap theme <http://ryan-roemer.github.io/sphinx-bootstrap-theme/>`_.

Thank you `Zhaowen Liu`_ for all of your help with this project, our 
other projects and for your unwaivering encouragement (and for the panda).

    .. _`Zhaowen Liu` : https://github.com/EvelynLiu77
