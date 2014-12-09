API
===

Primary Structures: Spectrum, Spectra, SpecStack
------------------------------------------------
Each DataStructure below is the Spectroscopic extension of a Pandas object (hyperlinks point to pandas API):

   - `Spectrum` : `pandas.Series <http://pandas.pydata.org/pandas-docs/stable/api.html#series>`_
   - `Spectra` : `pandas.DataFrame <http://pandas.pydata.org/pandas-docs/stable/api.html#dataframe>`_
   - `SpecStack` : pandas.Panel 

As such, each is constructed similar to its pandas equivalent::

   spec = Spectra(array, index, columns, specunit='nm')
   timespec = TimeSpectra(array, index, columns, specunit='nm', varunit='s')

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

These are demoed in the `builtin datasets notebook <http://nbviewer.ipython.org/urls/raw.github.com/hugadams/scikit-spectra/master/examples/Notebooks/testdata.ipynb>`_.

IO
--

The most reliable way to read in your data and export is is through in comma-separated-value **(CSV)** formats.  We are still developing `pickle` and `json` support.  This is done through `Spectra.read_csv()`:

.. autosummary::
   :toctree: generated/

   spectra.Spectra.from_csv
   ...

`Spectra.read_csv()` accepts all arguments of `pandas.read_csv() <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.read_csv.html#pandas.read_csv>`_, and adds the `header_datetime=False` and `index_datetime=False` options for parsing
files with header and index as TimeStamps::

   spec = TimeSpectra.from_csv('path/to/file.csv', index_col=0, header_datetime=True)

`Check out the IO notebook <http://nbviewer.ipython.org/github/hugadams/scikit-spectra/blob/master/examples/Notebooks/io.ipynb>`_


Plotting
--------

Graphical User Interface (GUI)
------------------------------

We've adopted a "GUI when you want it, API when you need it" mindset.  While our GUI support is clearly prototypical at this point, we're very pleased to present GUI's that run entirely in the browser through IPython Notebooks.  The idea behind this was to provide GUI's to quickly do the tedious munging in your spectra (sampling, slicing, basic plotting, loading/saving), directly in the Notebook, without disrupting your workflow.  As such, Spectra generated in the GUI can then be used in subsequent notebook cells.

One major problem with GUI's in the notebook right now is that they don't work unless you're connected to the IPython kernel; i.e., you are running the notebook on your computer.  Hosted static versions of the notebooks (like those in our IPython Notebook tutorials) won't display GUIs.  Work to remedy `this is already underway <https://jakevdp.github.io/blog/2013/12/05/static-interactive-widgets/>`_ by other, more gifted, programmers.

Two-Dimensional Correlation Spectroscopy
----------------------------------------


