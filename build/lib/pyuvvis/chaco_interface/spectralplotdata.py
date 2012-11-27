from pandasplotdatav2 import PandasPlotData
from traits.api import DelegatesTo, Str, Delegate, Enum

## For testing
import numpy as np
from pandas import DataFrame


### Need to pass traits into these so I can overwrite stuff at the beginning and don't have to do all this shit
class SpectralPlotData(PandasPlotData):
    ''' PandasPlotData that is built to store spectral data.  It enforces that 
    wavelength data be added to extras by default.  For aid in unde'''
    
    #Traits used for easy reference of the dataframe labels corresponding to spectral and temporal data.
    # Would prefer delegate!
    temporalaxis=Enum(0,1)  #Default to 0
    specname=Str('Wavelength')
    timename=Str('Time')
    
   
    def __init__(self, dataframe, extras=None, **kwtraits):
        ''' I choose the temporal axis to the primary one.'''
        
        self.sync_trait('temporalaxis', self, 'primaryaxis')
        if self.temporalaxis==0:
            self.sync_trait('specname', self, 'primaryname')
            self.sync_trait('timename', self, 'secondaryname')
        else:
            self.sync_trait('specname', self, 'secondaryname')
            self.sync_trait('timename', self, 'primaryname')            
                  

        super(SpectralPlotData, self).__init__(dataframe, extras=extras, \
                                            add_labels_to_extras=True,\
                                            **kwtraits) 
if __name__=='__main__':
    df=DataFrame((np.random.randn(10,10)) ) 
    data=SpectralPlotData(df, specname='HO')
    print data[0]
    df2=DataFrame((np.random.randn(10,10)) )
    data.update_dataframe(df2)
    print data.extras