API
===

Primary Structures: Spectrum, Spectra, SpecStack
------------------------------------------------
Each DataStructure below is the Spectroscopic extension of a Pandas object:

   - `Spectrum` : pandas.Series
   - `Spectra` : pandas.DataFrame
   - `SpecStack` : pandas.Panel

As such, each is constructed similar to its pandas equivalent::

   Spectra(array, index, columns, specunit='nm', varunit='s')

Please see the `basic tutorial`_ for more on `scikit-spectra` datastructures and their instantiations.

   .. _`basic tutorial` :   http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/tutorial_1.ipynb?create=1

.. currentmodule:: skspec.core

Spectrum
~~~~~~~~

.. autosummary::
   :toctree: generated/

   spectra.Spectrum

Spectra
~~~~~~~

.. autosummary::
   :toctree: generated/

   anyspectra.AnyFrame
   spectra.Spectra
   timespectra.TimeSpectra
   tempspectra.TempSpectra

SpecStack
~~~~~~~~~

.. autosummary::
   :toctree: generated/

   specstack.SpecStack
   ...

Index Objects
-------------

Full Modules Documentation (messy)
==================================

.. toctree::
    skspec.config
    skspec.exampledata
    skspec.exceptions
    skspec.logger
    skspec.IO
    skspec.bundled
    skspec.chaco_interface
    skspec.core
    skspec.correlation
    skspec.data
    skspec.interact
    skspec.nptools
    skspec.pandas_utils
    skspec.plotting
    skspec.scripts
    skspec.tests
    skspec.units
