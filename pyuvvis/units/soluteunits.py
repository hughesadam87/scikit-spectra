from abcunits import ConversionUnit

class SoluteUnit(ConversionUnit):
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
   

 ### FOR TESTING
_soluteunits = (
               Moles(), 
               Millimoles(),
               ConversionUnit() #For null case
               ) 

SOLUTEUNITS = dict((obj.short, obj) for obj in _soluteunits)
