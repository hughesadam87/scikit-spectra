"""Provides core "TempSpectra" class and associated utilities."""

import logging
from skspec.logger import decode_lvl, logclass
from skspec.core.spectra import Spectra
from skspec.units import TEMPUNITS
from skspec.core.specindex import SpecIndex
from skspec.core.abcindex import ConversionIndex

logger = logging.getLogger(__name__) 


class TempIndex(ConversionIndex):
   """ Temperature Index """
   unitdict = TEMPUNITS  

# Ignore all class methods!
@logclass(log_name=__name__, skip = ['wraps','_dfgetattr', 'from_csv', 
                                     '_comment', '_transfer'])
class TempSpectra(Spectra):
   """Spectral Index (rows) with Temperature Variation (columns) """
   def __init__(self, *dfargs, **dfkwargs):
      dfkwargs['force_columns'] = TempIndex
      dfkwargs['force_index'] = SpecIndex
      super(TempSpectra, self).__init__(*dfargs, **dfkwargs)
      
if __name__ == '__main__':
   import numpy as np
   import matplotlib.pyplot as plt
   tempspec = TempSpectra(np.random.randn(50,50), specunit='cm-1', varunit='C')
   tempspec.plot(cbar=True)
   plt.show()