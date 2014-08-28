from pyuvvis.units.abcunits import Unit
from datetime import timedelta
import numpy as np


class IntvlUnit(Unit):
   """ Interval of time (s, min, hr), to be used in conjunction with
   DatetimeIndex in TimeSpectra.  Timespectra handles the logic of converting
   between Datetime representation and Interval representation."""
   
   symbol = r'$\delta t$'
   category = 'time delta'
   
class TimeDelta(IntvlUnit):
   """ TimeDelta; does not transform to seconds etc... because that requires
   access to original index.  This is here for completeness, but all transforms
   done through TimeSpectra.
   """
   short = 'intvl'
   full = 'interval'

   @staticmethod   
   def to_canonical(x):
      """ Convert datetimeindex to index to seconds.  Build for backwards
      compat with IntvlIndex.from_datetime() class method."""
      if hasattr(x, '__iter__'):
         return np.array([v.total_seconds() for v in x], dtype='float64')
      else:
         return x.total_seconds()

   @staticmethod      
   def from_canonical(x):
      """ This will return purely seconds, so an originally formatted HMS
      timedelta like (0,10,30), or 10min 30sec, after going to_canconical
      and back to from_canonical will be (0,0,630) IE 630 seconds.
      """
      if hasattr(x, '__iter__'):
         return np.array([datetime.timedelta(seconds=v) for v in x])
      else:
         return datetime.timedelta(seconds=x)
      
   
class Seconds(IntvlUnit):
   short = 's'
   full = 'seconds'
   _canonical = True #Or timedelta?

   @staticmethod   
   def to_canonical(x):
      return x 

   @staticmethod      
   def from_canonical(x):
      return x
   
   
class Minutes(IntvlUnit):
   short = 'm'
   full = 'minutes'

   @staticmethod   
   def to_canonical(x):
      return x * 60.0

   @staticmethod      
   def from_canonical(x):
      return x / 60.0
   
   
_intvlunits = (
              Seconds(),
              Minutes(),
              TimeDelta()
             )

INTVLUNITS = dict((obj.short, obj) for obj in _intvlunits)
