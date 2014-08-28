from pyuvvis.core.abcindex import ConversionIndex
from pyuvvis.units.intvlunit import INTVLUNITS

class IntvlIndex(ConversionIndex):
   """ """
   unitdict = INTVLUNITS
   
if __name__ == '__main__':
   idx = IntvlIndex([1,2,3])
   idx = idx.convert('s')
   idx = idx.convert('m')
   print idx