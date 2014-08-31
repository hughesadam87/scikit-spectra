from pyuvvis.units.abcunits import Unit, UnitError
from datetime import timedelta
from pandas import DatetimeIndex, date_range
import datetime
import numpy as np


class DateTime(Unit):
   """ Stores start and stop metadata.  Made for compaitiblity with interval
   unit systems. """

   symbol = 't'
   category = 'time'
   short = 'dti' #So it automatically added to intvlindex rather than Null
   full = 'timestamp'
  
   cumsum = True #Disable for absolute intervals
   
   start = None
   end = None
   
   # Not static method because requires state access (cumsum)
   def to_canonical(self, x):
      """ Converts a datetime index to seconds interval"""
      if not isinstance(x, DatetimeIndex):
         x = DatetimeIndex(x)
      nanoseconds = np.diff(x.asi8)  #asi8 only defined on DatetimeIndex      
      seconds = nanoseconds * 10**-9  
      seconds = np.insert(seconds, 0, seconds[0]-seconds[0])
      if self.cumsum:
         seconds = seconds.cumsum()
      return seconds     
      
      
   # Not static method because requires state access (start, stop etc...)
   # http://pandas.pydata.org/pandas-docs/stable/generated/pandas.date_range.html
   def from_canonical(self, x):
      """ Generates new DateTimeIndex form start, end.  Period is inferred
      from length of x.  Does not support 'freq'.  """
      return self.old_datetime(0)
      #if not self.start and self.stop:
         #raise UnitError("Cannot convert to datetimeindex without a start,"
                         #" and stop timestamp.")

      #else:
         #return date_range(start=self.start, end=self.end, periods=len(x))
      
      ##Does the above logic take into account all cases?      
      #raise UnitError('Could not generate DatetimeIndex from interval,'
            ' requires start+end+freq or start+periods or end+periods.') 

   @classmethod
   def from_datetime(cls, dti):
      out = cls()
      out.start = dti[0]
      out.end = dti[-1]
      return out



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