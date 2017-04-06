""" Unit Class: series of metadata for various index units used throughout.
All class attributes to conserve memory.  Unit conversions are defined
in the respective index classes calling these"""


class UnitError(Exception):
   """ """

class Unit(object):
   """ Basic unit used by skspec Index objects.""" 
   short = None
   full = 'No unit' #None works, but literaly prints None 
   symbol = ''
   category = None
   
   def __init__(self, **kwargs):
      
      if 'short' in kwargs and 'full' not in kwargs or \
         'full' in kwargs and 'short' not in kwargs:
         raise UnitError('Please enter both a short and full Unit name.')
      
      for key in kwargs:
         setattr(self, key, kwargs[key])
        
   # Alternative representations for plotting/headres (not sure if useful)_
   @property
   def cat_short(self):
      """ Category(short) eg wavelength(nm)"""
      return '%s (%s)' % (self.category, self.short)

   @property         
   def cat_full(self):
      """ Category(long) eg wavelength(nanometers) """
      return '%s (%s)' % (self.category, self.full)
            
            
class IUnit(Unit):
   """ Intensity unit """
   category = 'Intensity' #Better one?
   symbol = 'I'


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
      
if __name__ == '__main__':
   unit = Unit(short='bar')
   print unit.__dict__
   print unit.short
   unit.short = 'foo'
   print unit.short