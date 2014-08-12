""" Unit Class: series of metadata for various index units used throughout.
All class attributes to conserve memory.  Unit conversions are defined
in the respective index classes calling these"""


class UnitError(Exception):
   """ """

# Consider adding a better __repr__ to these for when objects are called?
class Unit(object):
   """ """
   short = None
   full = 'No Unit'
   symbol = ''
   _canonical = False

   @staticmethod   
   def to_canonical(self):
      NotImplemented
      
   @staticmethod
   def from_canonical(self):
      NotImplemented
