from skspec.units.abcunits import ConversionUnit, UnitError
from datetime import timedelta
from pandas import DatetimeIndex, date_range, Index
import datetime
import numpy as np

class DatetimeCanonicalError(UnitError):
   """ Very specific error USED FOR CATCHING EXCEPTIONS IN TIME INDEX 
   DO NOT CHANGE THE NAME."""

class DateTime(ConversionUnit):
   """ Stores start and stop metadata.  Made for compaitiblity with interval
   unit systems. """

   symbol = 't'
   category = 'time'
   short = 'dti' #So it automatically added to intvlindex rather than Null
   full = 'timestamp'   

   
   # Not static method because requires state access (cumsum)
   def to_canonical(self, x):
      """ """
      raise DatetimeCanonicalError('DateTime unit conversion handled through'
                      ' TimeIndex because state info is required.')  

   def from_canonical(self, x):
      """   """
      raise DatetimeCanonicalError('DateTime unit conversion handled through'
                      ' TimeIndex because state info is required.')      


class IntvlUnit(ConversionUnit):
   """ Interval of time (s, min, hr), to be used in conjunction with
   DatetimeIndex in TimeSpectra.  Timespectra handles the logic of converting
   between Datetime representation and Interval representation."""

   symbol = r'$\delta t$'
   category = 'time' #Should still be time I think
   

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

class Nanoseconds(IntvlUnit):
   short = 'ns'
   full = 'nanoseconds'

   @staticmethod   
   def to_canonical(x):
      return x * 10**-9

   @staticmethod      
   def from_canonical(x):
      return x / 10**-9


class Microseconds(IntvlUnit):
   short = 'us'
   full = 'microseconds'

   @staticmethod   
   def to_canonical(x):
      return x * 10**-6

   @staticmethod      
   def from_canonical(x):
      return x / 10**-6

class Milliseconds(IntvlUnit):
   short = 'ms'
   full = 'milliseconds'

   @staticmethod   
   def to_canonical(x):
      return x * 10**-3

   @staticmethod      
   def from_canonical(x):
      return x / 10**-3

class Hours(IntvlUnit):

   short = 'h'
   full = 'hours'

   @staticmethod   
   def to_canonical(x):
      return x * 3600.0

   @staticmethod      
   def from_canonical(x):
      return x / 3600.0


class Days(IntvlUnit):

   short = 'd'
   full = 'days'

   @staticmethod   
   def to_canonical(x):
      return x * 86400.0

   @staticmethod      
   def from_canonical(x):
      return x / 86400.0


class Years(IntvlUnit):

   short = 'y'
   full = 'years'

   @staticmethod   
   def to_canonical(x):
      return x * 31536000.0

   @staticmethod      
   def from_canonical(x):
      return x / 31536000.0


_intvlunits = (
   DateTime(),
   Nanoseconds(),
   Microseconds(),
   Milliseconds(),
   Seconds(),
   Minutes(),
   Hours(),
   Days(),
   TimeDelta()
)

INTVLUNITS = dict((obj.short, obj) for obj in _intvlunits)

print INTVLUNITS.keys()