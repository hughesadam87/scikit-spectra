.. _source code: https://github.com/hugadams/pyuvvis

.. _issues: https://github.com/hugadams/pyuvvis/issues

To Do
=====
Most minor issues are posted on the github issues_ section, and only major issues are included here.  

Some major to do's include:

* Having the underlying DataFrame that controls the spectral data have persistent attributes.  For now, a handful of modules in pyuvvis.pandas_utils can transfer/serialize dataframes
with custom attributes; however, this is a major hassle.  Unfortunately, subclassing dataframes in also unreliable.
* Incorporate/merge with other spectroscopy packages, especially those with IR, and Raman spectral tools.  Ideally, this would be best acheived by simple transformation wrapper between our spectral dataframes into the basic class/data structure of the other package.
* Merge into a large branch of optics routins, especially those pertinent to nanotechnology (for example basic Mie Theory).







