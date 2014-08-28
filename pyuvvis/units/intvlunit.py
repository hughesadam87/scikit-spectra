from pyuvvis.units.abcunits import Unit

class IntvlUnit(Unit):
   """ Interval of time (s, min, hr), to be used in conjunction with
   DatetimeIndex in TimeSpectra.  Timespectra handles the logic of converting
   between Datetime representation and Interval representation."""
   
   symbol = 't'
   category = 'time'
   
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
   
# How to implement?  Should this be the canonical unit, not seconds?
class TimeDelta(IntvlUnit):
   """ """
   # Will foring to float in ConversionIndex mess this up??

   
_intvlunits = (
              Seconds(),
              Minutes()
             )

INTVLUNITS = dict((obj.short, obj) for obj in _intvlunits)

