from math import pi

""" Unit Class: series of metadata for various index units used throughout.
All class attributes to conserve memory.  Unit conversions are defined
in the respective index classes calling these"""

### Change spectral labels ###
H = 6.626068*10**-34          #Planck's constant m**2 kg / s
eVtoJ = 1.60217646 * 10**-19  #Number of Joules in one eV (needed becasue eV is not the standard MKS unit of energy)
C = 299792458.0               #speed of light m/s

class UnitError(Exception):
   """ """

# Consider adding a better __repr__ to these for when objects are called?
class Unit(object):
   """ """
   short = ''
   full = ''
   symbol = ''
   proportional = True
   _canonical = False
   
   def to_canonical(self):
      NotImplemented
      
   def from_canonical(self):
      NotImplemented
   
# How to do temperature conversions with +/- 273   
class TempUnit(Unit):
   """ Temperature units.  ALl conversions go through Kelvin. """

#http://www.metric-conversions.org/temperature/fahrenheit-to-kelvin.htm
class Kelvin(TempUnit):
   short = 'K'
   full = 'Kelvin' #Proper names, keep this way?
   symbol = 'r$^{\deg}K$' #Isn't degree Kelvin technially wrong?
   _canonical = True
   
   def to_canonical(self, x):
      return x
      
   def from_canonical(self, x):
      return x

class Celsius(TempUnit):
   short = 'C'
   full = 'Celsius'
   symbol = 'r$^{\deg}C$'

class SoluteUnit(Unit):
   """ Goes through molar.  Test case """
   
class Moles(SoluteUnit):
   short = 'M'
   full = 'moles'
   symbol = 'M'
   _canonical = True
   
class Millimoles(SoluteUnit):
   short = 'mM'
   full = 'millimoles'
   symbol = 'mM' #Kind of redundant

# SPECTRAL UNITS   
class SpecUnit(Unit):
   """  Spectroscopy units (nm, m, ev etc...)
   Allow for recpricol units such as cm-1; used by converters.  All 
   conversions go through unit, considered the core unit.  Adds category
   to distinguish between wavelength, wavenumber, energy, frequency."""

   category = ''
   
   @property
   def symbol(self):
      if self.category == 'wavelength':
         return r'$\lambda$'
   
      elif self.category == 'wavenumber':
         return r'$\kappa$'
      
      elif self.category == 'frequency':
         return r'$\nu$'
   
      elif self.category == 'energy':
         return r'$\epsilon$'
      
      elif not self.category: #NullUnit
         return ''
      
      else:
         raise UnitError('invalid category' % self.category)
   
class NullSpecUnit(SpecUnit):
   """Used by conversions when spectral unit not specified.  Inherits
   from Unit may cause subclassing problems.  Subclasses  inspection should
   consider NullUnit like "if isnstance(Parent) or isinstance(NullUnit)"""
   short = None
   full = 'No Spectral Unit'
   category = ''
   
class Meters(SpecUnit):
   short = 'm'
   full = 'meters'
   category = 'wavelength'
   _canonical = True
   
   @classmethod
   def to_canonical(self, x):
      return x
      
   @classmethod
   def from_canonical(self):
      return x

class Centimeters(SpecUnit):
   short = 'cm'
   full = 'centimeters'
   category = 'wavelength'

   @classmethod   
   def to_canonical(self, x):
      return x / 100.0

   @classmethod      
   def from_canonical(self, x):
      return 100.0 * x  
   
class Micrometers(SpecUnit):
   short = 'um'
   full = 'microns'
   category = 'wavelength'
   
   @classmethod
   def to_canonical(self, x):
      return x / 100000.0 
      
   @classmethod
   def from_canonical(self, x):
      return 100000.0 * x
   
class Nanometers(SpecUnit):
   short = 'nm'
   full = 'nanometers'
   category = 'wavelength'
   
   @classmethod
   def to_canonical(self, x):
      return x / 100000000.0 
      
   @classmethod
   def from_canonical(self, x):
      return 100000000.0 * x   
   
class Metersinverse(SpecUnit):
   """ Cycles per distance/wavenumber"""
   short = 'k'
   full = 'inverse meters' #or cycles per meter or radians per meter
   category = 'wavenumber'
   
   # TEST THIS
   @classmethod
   def to_canonical(self, x):
      return 1.0 / x
      
   @classmethod
   def from_canonical(self, x):
      return 1.0 / x
   
class Centimetersinverse(SpecUnit):
   short = 'cm-1'
   full = 'inverse centimeters'
   category = 'wavenumber'

   # DEFINE IN TERMS OF TO METERS?
   @classmethod
   def to_canonical(self, x):
      return (1.0 / x) * (0.01)
      
   @classmethod
   def from_canonical(self, x):
      return 1.0 / (x * 100.0)
   
class Micrometersinverse(SpecUnit):
   short = 'um-1'
   full = 'inverse microns'
   category = 'wavenumber'
   
class Nanometersinverse(SpecUnit):
   short = 'nm-1'
   full = 'inverse nanometers'
   category = 'wavenumber'
        
class Frequency(SpecUnit):
   """ lambda = v/f where v is c for electromagnetic radiation; in general,
   it's called the phase speed. """
   short = 'f'
   full = 'hertz'
   category = 'frequency'
   
   @classmethod
   def to_canonical(self, x):
      meters = Meters.to_canonical(x)
      return C / meters
      
   @classmethod
   def from_canonical(self, x):
      return C / x
   
class Angularfrequency(SpecUnit):
   short = 'w'
   full = 'radians per second'
   category = 'frequency'
   
   @classmethod
   def to_canonical(self, x):
      meters = Meters.to_canonical(x)
      return (2.0 * pi * C) / meters
      
   @classmethod
   def from_canonical(self, x):
      return (2.0 * pi * C) / x
   
class Electronvolts(SpecUnit):
   short = 'ev'
   full = 'electron volts'
   category = 'energy'

   @classmethod
   def to_canonical(self, x):
      meters = Meters.to_canonical(x)
      return (H*C/(eVtoJ) ) / meters
      
   @classmethod
   def from_canonical(self, x):
      return (H*C/(eVtoJ)) / x

   
_specunits = (
             Meters(), 
             Metersinverse(), 
             Nanometers(), 
             Centimeters(), 
             Centimetersinverse(),
             Micrometers(),
             Micrometersinverse(),
             Electronvolts(),
             Frequency(),
             Angularfrequency(),
             NullSpecUnit()
             )

# Dictionary keyed by short for easy use by converters
SPECUNITS = dict((obj.short, obj) for obj in _specunits)

### FOR TESTING
_soluteunits = (Moles(), 
                Millimoles(),
                NullSpecUnit ()) #Just for testing

SOLUTEUNITS = dict((obj.short, obj) for obj in _soluteunits)

if __name__ == '__main__':
   f = Frequency()
   ev = Electronvolts()
   print f.from_canonical(1)
   print ev.to_canonical(1)
