from pyuvvis.core.abcindex import ConversionIndex
from pyuvvis.units.intvlunit import INTVLUNITS, TimeDelta
import numpy as np

class IntvlIndex(ConversionIndex):
   """ """
   unitdict = INTVLUNITS

   _forcetype = False #timedeltas not necessarily floats


   @classmethod
   def from_datetime(cls, datetimeindex, cumsum=True, unit='intvl'):
      """ Construct IntervalIndex from a pandas DatetimeIndex.
      
      Parameters
      ----------      
      datetimeindex: DateTimeIndex
      
      cumsum: bool (True)
          Interval will be returned as running sum.  Ie 0,3,6 for 3 second
          intervals.  If not, returns 3, 3, 3
          
      Returns
      -------
      IntervalIndex"""


      if unit == 'intvl':
         indexout = np.diff(datetimeindex.to_pydatetime()) # intervals as timedelta objects.
         seconds = TimeDelta.to_canonical(indexout)
         
      else:
         nanoseconds = np.diff(datetimeindex.asi8)       
         seconds = nanoseconds * 10**-9
         
      # Add a t=0 index.  Uses first element minus itself to preserve timestamp
      # unit if intervals  
      indexout=np.insert(indexout, 0, indexout[0]-indexout[0])
      
      if cumsum:
          indexout = indexout.cumsum()
      
      return cls(indexout, unit=unit)
      

if __name__ == '__main__':
   from pandas import date_range
   
   idx = IntvlIndex([1,2,3])
   idx = idx.convert('s')
   idx = idx.convert('m')
   idx = IntvlIndex.from_datetime(date_range(start='3/3/12',periods=30,freq='45s'))
   print idx
   print idx.to_canonical(idx)
