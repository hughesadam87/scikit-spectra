API
===

Primary Structures: Spectrum, Spectra, SpecStack
------------------------------------------------
Each DataStructure below is the Spectroscopic extension of a Pandas object (hyperlinks point to pandas API):

   - `Spectrum` : `pandas.Series <http://pandas.pydata.org/pandas-docs/stable/api.html#series>`_
   - `Spectra` : `pandas.DataFrame <http://pandas.pydata.org/pandas-docs/stable/api.html#dataframe>`_
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

The SpecStack is not based on a Panel per-se.  It's more of a custom list to store Spectra.  

.. autosummary::
   :toctree: generated/

   specstack.SpecStack
   ...

Index Objects
-------------

Scikit-spectra uses custom Index objects.  Spectra impose constraints on these.  For example, a `TimeSpectra` requires a `TimeIndex` and `SpecIndex`, while `AnyFrame` imposes no constraints on the Index (any pandas of skspec index is fine).  The advantage of using our indicies is that they will add functionality to your dataset.  For example, the `TimeIndex` hands timestamps, converts between representations of timestamps and intervals in seconds, minutes, etc...  The `SpecIndex` converts representations of wavelengths like nm to eV.

.. autosummary::
   :toctree: generated/

   specindex.SpecIndex
   timeindex.TimeIndex
   tempspectra.TempIndex
   ...

Builtin Datasets
----------------

scikit-spectra is bundled with several datasets::

    from skspec.data import aunps_glass, aunps_water, solvent_evap, trip_peaks
    spectra = aunps_glass()

See more in the <DATSETS NOTEBOOK>


Full Modules Documentation (messy)
----------------------------------

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
