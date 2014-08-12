""" Unit Class: series of metadata for various index units used throughout.
All class attributes to conserve memory.  Unit conversions are defined
in the respective index classes calling these"""


class UnitError(Exception):
   """ """

# Consider adding a better __repr__ to these for when objects are called?
class Unit(object):
   """ """
   short = ''
   full = ''
   symbol = ''
   _canonical = False

   @staticmethod   
   def to_canonical(self):
      NotImplemented
      
   @staticmethod
   def from_canonical(self):
      NotImplemented


class NullUnit(Unit):
   """Used by conversions when unit not specified.  Inherits
   from Unit may cause subclassing problems.  Subclasses  inspection should
   consider NullUnit like "if isnstance(Parent) or isinstance(NullUnit)"""
   short = None
   full = 'No Unit'   
   