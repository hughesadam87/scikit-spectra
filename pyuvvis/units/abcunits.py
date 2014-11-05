""" Unit Class: series of metadata for various index units used throughout.
All class attributes to conserve memory.  Unit conversions are defined
in the respective index classes calling these"""


class UnitError(Exception):
   """ """

class Unit(object):
   """ Basic unit used by pyuvvis Index objects.""" 
   short = None
   full = 'no unit'
   symbol = ''

# Consider adding a better __repr__ to these for when objects are called?
class ConversionUnit(Unit):
   """ Used by conversion indexes to represent units that can be converted
   from one system to another (like feet to miles)
   """
   _canonical = False

   @staticmethod   
   def to_canonical(self):
      NotImplemented
      
   @staticmethod
   def from_canonical(self):
      NotImplemented
