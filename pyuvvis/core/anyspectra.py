from pyuvvis.core.spectra import Spectra

class AnyFrame(Spectra):
    """ Spectra with default non-strict columns or index
    """

    def __init__(self, *dfargs, **dfkwargs):
        dfkwargs.setdefault('strict_columns', None)   
        dfkwargs.setdefault('strict_index', None)            
        
        super(AnyFrame, self).__init__(*dfargs, **dfkwargs)  
        
        
if __name__ == '__main__':
    af=AnyFrame()
    #af.specunit
    print af.iloc[0]