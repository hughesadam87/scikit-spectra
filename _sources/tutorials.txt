Tutorials
=========

Videos
------

Video 1: IPython Notebook Spectroscopy GUI

.. youtube:: RhMHgQbP__A
    :height: 150
    :width: 250
    :align: left

10 Minutes to scikit-spectra
----------------------------
**<COMING SOON>**

IPython Notebooks
-----------------

The current documentation (and in-a-pinch test suite) is a series of example notebooks 
(`IPython Notebook`_), which cover most of the basics. These have been linked below:

   .. _`IPython Notebook`: http://ipython.org/notebook.html?utm_content=buffer83c2c&utm_source=buffer&utm_medium=twitter&utm_campaign=Buffer

Getting Started
~~~~~~~~~~~~~~~
   - `TimeSpectra tutorial (part 1)`_
   - `TimeSpectra tutorial (part 2)`_
   - `Sampling and Selecting Data`_

Plotting
~~~~~~~~
   - `Intro to Plotting`_
   - `Intro to 2D and 3D Plots`_
   - `Interactive Plots with Plotly`_

   Don't forget that `pandas itself has a rich plotting api`_.  Use **spectra.data** to retrieve the DataFrame or Series from the skspec object.


   .. _`pandas itself has a rich plotting api` : http://pandas.pydata.org/pandas-docs/version/0.15.0/visualization.html#visualization-scatter

IO and Datasets
~~~~~~~~~~~~~~~
   - `Bundled Datasets`_
   - `IO: Importing and Exporting`_
   - `Intro to Multiple Datasets (SpecStack)`_

   .. _`Sampling and Selecting Data` : http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/slicing.ipynb?create=1
   .. _`IO: Importing and Exporting` :   http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/io.ipynb?create=1
   .. _`Intro to Plotting` :   http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/Plotting.ipynb?create=1
   .. _`Intro to 2D and 3D Plots` :   http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/plotting_2d3d.ipynb?create=1
   .. _`Interactive Plots with Plotly` :   http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/plotly.ipynb?create=1
   .. _`Bundled Datasets` :   http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/testdata.ipynb?create=1
   .. _`Intro to Multiple Datasets (SpecStack)` :   http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/specstack.ipynb?create=1
   .. _`TimeSpectra tutorial (part 1)` :   http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/tutorial_1.ipynb?create=1
   .. _`TimeSpectra tutorial (part 2)` :   http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/tutorial_2.ipynb?create=1


Research Applications
~~~~~~~~~~~~~~~~~~~~~
   - `Measuring plasmon resonance shift on gold nanoparticles when binding proteins.`_

   .. _`Measuring plasmon resonance shift on gold nanoparticles when binding proteins.` : http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/grad_presentation.ipynb

Customization
~~~~~~~~~~~~~
   - `Custom units`_
   - `Custom units with convertable representations (inch --> foot --> meter)`_

   .. _`Custom units` : http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/units.ipynb
   .. _`Custom units with convertable representations (inch --> foot --> meter)` : http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/basic_units.ipynb

Two-Dimensional Correlation Spectroscopy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Two-Dimensional Correlation Spectroscopy (2DCS) is a field spectral analysis that pertains to analyzing the the relationship between the instantaneous changes in a spectrum.  It is useful for resolving information about the order and time at which peaks grow, fade or shift.  Scikit-spectra tries to provide an API for 2DCS.  For literature on the subject, see `Noda/Ozaki`_.

   - `2D correlation spectroscopy: Part 1`_
   - `2D correlation spectroscopy example pipeline`_

   .. _`Noda/Ozaki` : http://science.kwansei.ac.jp/~ozaki/NIR2DCorl_e.html

   .. _`2D correlation spectroscopy: Part 1` : http://nbviewer.ipython.org/urls/raw.github.com/hugadams/scikit-spectra/master/examples/Notebooks/correlation_p1.ipynb
   .. _`2D correlation spectroscopy example pipeline` : http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/corr_pipeline.ipynb


Special Topics
~~~~~~~~~~~~~~
   - Sizing Gold Nanoparticles through UVVis Spectra 


Miscellaneous
~~~~~~~~~~~~~
   - `Matplotlib Color Maps`_
   - `Principle Component Analysis on Spectral Data (DRAFT)`_


   .. _`Matplotlib Color Maps` : http://nbviewer.ipython.org/github/hugadams/pyparty/blob/master/examples/Notebooks/gwu_maps.ipynb?create=1
   .. _`Principle Component Analysis on Spectral Data (DRAFT)` : http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/PCA_part1.ipynb

Legacy documentation_ is generously hosted by github_.

   .. _github: http://github.com
 
   .. _documentation: http://hugadams.github.com/pyuvvis/

