from math import pi

""" Unit Class: series of metadata for various index units used throughout.
All class attributes to conserve memory.  Unit conversions are defined
in the respective index classes calling these"""

### Change spectral labels ###
h = 6.626068*10**-34          #Planck's constant m**2 kg / s
eVtoJ = 1.60217646 * 10**-19  #Number of Joules in one eV (needed becasue eV is not the standard MKS unit of energy)
c = 299792458.0               #speed of light m/s

class UnitError(Exception):
   """ """


# Consider adding a better __repr__ to these for when objects are called?
class Unit(object):
   """ """
   short = ''
   full = ''
   symbol = ''
   mapping = 1.0
   proportional = True
   
   @property
   def reciprocal(self):
      if self.proportional:
         return False
      else:
         return True
   

# How to do temperature conversions with +/- 273   
class TempUnit(Unit):
   """ Temperature units.  ALl conversions go through Kelvin. """
   proportional = True

class Kelvin(TempUnit):
   short = 'K'
   full = 'Kelvin' #Proper names, keep this way?
   symbol = 'r$^{\deg}K$' #Isn't degree Kelvin technially wrong?
   mapping = 1.0

class Celsius(TempUnit):
   short = 'C'
   full = 'Celsius'
   symbol = 'r$^{\deg}C$'
#   mapping = #273 - ??? How

class SoluteUnit(Unit):
   """ Goes through molar.  Test case """
   proportional = True 
   
class Moles(SoluteUnit):
   short = 'M'
   full = 'moles'
   symbol = 'M'
   mapping = 1.0
   
class Millimoles(SoluteUnit):
   short = 'mM'
   full = 'millimoles'
   symbol = 'mM' #Kind of redundant
   mapping = .001

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
   mapping = 1.0   
   category = ''
   proportional = True
   
class Meters(SpecUnit):
   short = 'm'
   full = 'meters'
   category = 'wavelength'
   proportional = True
   mapping = 1.0

class Centimeters(SpecUnit):
   short = 'cm'
   full = 'centimeters'
   category = 'wavelength'
   proportional = True
   mapping = .01
   
class Micrometers(SpecUnit):
   short = 'um'
   full = 'microns'
   category = 'wavelength'
   proportional = True
   mapping = .000001   
   
class Nanometers(SpecUnit):
   short = 'nm'
   full = 'nanometers'
   category = 'wavelength'
   proportional = True
   mapping = .000000001
   
class Metersinverse(SpecUnit):
   """ Cycles per distance/wavenumber"""
   short = 'k'
   full = 'inverse meters' #or cycles per meter or radians per meter
   category = 'wavenumber'
   proportional = False
   mapping = 1  #Right?  not factor 2 pi.  Tested with a conversion utility
   
class Centimetersinverse(SpecUnit):
   short = 'cm-1'
   full = 'inverse centimeters'
   category = 'wavenumber'
   proportional = False
   mapping = .01
   
class Micrometersinverse(SpecUnit):
   short = 'um-1'
   full = 'inverse microns'
   category = 'wavenumber'
   proportional = False
   mapping = .01   
   
class Nanometersinverse(SpecUnit):
   short = 'nm-1'
   full = 'inverse nanometers'
   category = 'wavenumber'
   proportional = False
   mapping = .01      
   
class Frequency(SpecUnit):
   short = 'f'
   full = 'hertz'
   category = 'frequency'
   proportional = False
   mapping = c 
   
class Angularfrequency(SpecUnit):
   short = 'w'
   full = 'radians per second'
   category = 'frequency'
   proportional = False
   mapping = 2.0 * pi * c
   
class Electronvolts(SpecUnit):
   short = 'ev'
   full = 'electron volts'
   category = 'energy'
   proportional = False
   mapping = h*c/(eVtoJ)

   
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
