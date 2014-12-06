from skspec.core.spectra import Spectra
from skspec.units.abcunits import Unit

class AnyFrame(Spectra):
    """ Spectra with default non-strict columns or index
    """

    def __init__(self, *dfargs, **dfkwargs):
        dfkwargs.setdefault('strict_columns', None)   
        dfkwargs.setdefault('strict_index', None)    
        
        
        dfkwargs.setdefault('specunit', Unit())    
        dfkwargs.setdefault('varunit', Unit())    
        
        
        super(AnyFrame, self).__init__(*dfargs, **dfkwargs)  
        
        
if __name__ == '__main__':
    import numpy as np
    af=AnyFrame(np.random.rand(50,50))
    af.specunit = Unit(short='foo', full='bar')
    print af
