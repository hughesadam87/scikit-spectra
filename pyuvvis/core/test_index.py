from pandas import Float64Index
import numpy as np
from units import SPECUNITS, UnitError, TEMPUNITS

def _parse_unit(unit, unitdict):
   """ Given a string unit (ie nm), returns the corresponding unit
   class."""
   if unit not in unitdict:
      raise UnitError('Invalid unit "%s".  Choose from %s' % 
                      (unit, sorted(unitdict.keys()) ) )
   return unitdict[unit]  

class ConversionIndex(Float64Index):
   """ Base class for pyuvvis.  To overwrite, requires:
        - replace unitdict with a dictionary from units.py, eg SPECUNITS
        - overwrite convert(), which defines conversions on the unit types.
   Since we are subclassing a numpy array and not a basic python object, 
   we don't write __init__(); rather, __new__ and __array_finalize__ are
   employed (http://docs.scipy.org/doc/numpy/user/basics.subclassing.html)
   """

   unitdict = None 

   def __new__(cls, input_array, unit=None):
      """ Unit is valid key of unitdict """
      obj = np.asarray(input_array).view(cls)
      obj._unit = _parse_unit(unit, cls.unitdict)
      return obj

   # I am not really worred about other constructors yet...
   def __array_finalize__(self, obj):
      """No matter what constructor called, this will get called, so does
      all the housekeeping."""
      if obj is None: 
         return
      
      # Can be called form slicing or other reasons, and I don't always know
      # if unit is still a string/Non_e, or if it's already a Unit class.
      # Thus, I let both cases work, even though don't know when is what
      self._unit = getattr(obj, 'unit', None)

##      if isinstance(unit, str) or unit is None:
##         self._unit = _parse_unit(unit, self.unitdict)
##      else:
          #self._unit = unit

   def convert(self, outunit):
      """Convert spectral values based on string outunit.  First converts
      the current unit to the canonical unit (eg, nanometers goes to meters)
      then to the outunit (eg, meters to eV).  This is done through the unit
      methods, .to_canonical() and .from_canonical() where in the case of
      spectral units, canonical refers to meters.
      """
      outunit = _parse_unit(outunit, self.unitdict)
      inunit = self._unit

      # Unit not changed, or set to None
      if outunit == self._unit or not outunit.short:
         return self.__class__(self, unit=inunit)

      # If current unit is None, just set new unit
      if not self._unit.short:
         return self.__class__(self, unit = outunit.short)

      # Convert non-null unit to another non-null unit   
      else: 
         canonical = inunit.to_canonical(np.array(self))
         arrayout = outunit.from_canonical(canonical)
         return self.__class__(arrayout, unit=outunit.short)      
         

   def _parse_unit(self, unit):
      """ Given a string unit (ie nm), returns the corresponding unit
      class."""
      if unit not in self.unitdict:
         raise UnitError('Invalid unit "%s".  Choose from %s' % 
                         (unit, sorted(self.unitdict.keys()) ) )
      return self.unitdict[unit]      


   #Email list about this distinction
   #def __repr__(self):
      #""" Used internally in code, like if I print self fromin function."""
      #out = super(ConversionIndex, self).__repr__()        
      #return out.replace(self.__class__.__name__, '%s[%s]' %
                         #(self.__class__.__name__, self._unit.short))

   def __unicode__(self):
      """ Returned on printout call.  Not sure why repr not called... """
      out = super(ConversionIndex, self).__unicode__()        
      return out.replace(self.__class__.__name__, '%s[%s]' % 
                         (self.__class__.__name__, self._unit.short))

   # PROMOTED UNIT METHODS
   def __getattr__(self, attr):
      """ Defer attribute call to self._unit"""
      try:
         return getattr(self._unit, attr)
      except AttributeError:
         raise AttributeError('%s has no attribute "%s".' % 
                              (self.__class__.__name__, attr) )

   @property
   def unit(self):
      return self._unit.short


class SpecIndex(ConversionIndex):
   """ """
   unitdict = SPECUNITS   
   
from units import SOLUTEUNITS

class SoluteIndex(ConversionIndex):
   """ """
   unitdict = SOLUTEUNITS
   
class TempIndex(ConversionIndex):
   """ """
   unitdict = TEMPUNITS


if __name__ == '__main__':
   x = SpecIndex(np.linspace(0,50), unit='nm')
#   from pyuvvis.data import aunps_glass
   
   #ts = aunps_glass()
   #ts.index = SpecIndex(ts.index)
   #print ts.index
#   y = SoluteIndex(np.linspace(0,50), unit='M')
#   print y
   print x
   print x.convert('m')
   print x.convert('cm')
   print x.convert('um')   
   print x.convert('f')
   print x.convert('ev')
   print x.convert('w')
   
   z = TempIndex(np.linspace(50,100), unit='F')
   print z
   print z.convert('C')
   print z.convert('K')
   
   
   
#   print ts.index =
#   y = Float64Index(np.linspace(0,50))
#   print y*70
   #print x**2
   #print x.unit
   #y = x**2
   #print y.unit
#   print np.asarray(x)
#   print x*80

#   print x
#   print x.categor
#   _unit_valid('nm')