from abcunits import ConversionUnit


KFACTOR = 273.15 #Difference Kelvin, C (how precise is this known?)

   
class TempUnit(ConversionUnit):
   """ Temperature units.  ALl conversions go through Kelvin. """

#http://www.metric-conversions.org/temperature/fahrenheit-to-kelvin.htm
class Kelvin(TempUnit):
   short = 'K'
   full = 'Kelvin' #Proper names, keep this way?
   symbol = 'r$^{\deg}K$' #Isn't degree Kelvin technially wrong?
   _canonical = True
   
   @staticmethod
   def to_canonical(x):
      return x
      
   @staticmethod
   def from_canonical(x):
      return x

class Celsius(TempUnit):
   short = 'C'
   full = 'Celsius'
   symbol = 'r$^{\deg}C$'
   
   @staticmethod
   def to_canonical(x):
      return x + KFACTOR
      
   @staticmethod
   def from_canonical(x):
      return x - KFACTOR


class Farenheiht(TempUnit):
   short = 'F'
   full = 'Farenheiht'
   symbol = 'r$^{\deg}F$'
   
   @staticmethod
   def to_canonical(x):
      return ((x - 32.00)/1.80) + 273.15
      
   @staticmethod
   def from_canonical(x):
      return ((x - KFACTOR) * 1.80) + 32.00


_tempunits = (Kelvin(),
              Celsius(),
              Farenheiht(),
              ConversionUnit() #For null case
              )
TEMPUNITS = dict((obj.short, obj) for obj in _tempunits)