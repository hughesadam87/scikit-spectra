from abcindex import ConversionFloat64Index
from skspec.units import SPECUNITS

class SpecIndex(ConversionFloat64Index):
    """ """
    unitdict = SPECUNITS   
 

if __name__ == '__main__':
    import numpy as np
    x = SpecIndex(np.linspace(0,50), unit='nm')

    print x
    print x.convert('m')
    print x.convert('cm')
    print x.convert('um')   
    print x.convert('f')
    print x.convert('ev')
    print x.convert('w')
    print x.convert(None)