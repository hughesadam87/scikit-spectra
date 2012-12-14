''' Monkey-patched dataframe object to represent the core class of PyUvVis: a set of spectral data.'''

import pandas

from specindex import SpecIndex, list_units
from timeindex import TimeIndex

## testing
from numpy.random import randn

######################
### Spectral label ###
######################


pandas.DataFrame.name=None
pandas.DataFrame.baseline=None
### Custom axis methods


def TimeSpectra(*dfargs, **dfkwargs):
    
    ### Pop dataframe related quantities###
    name=dfkwargs.pop('name', 'Spectra')
    specunit=dfkwargs.pop('specunit', None)
    timeunit=dfkwargs.pop('timeunit', None)
    baseline=dfkwargs.pop('baseline', None)
    
    df=pandas.DataFrame(*dfargs, **dfkwargs)
    df.name=name

    ###Set Index as spectral variables
    set_specunit(df, specunit)  #This will automatically convert to a spectral index
    
    ###Set columns as time variables
    set_timeunit(df, timeunit)
    
    return df

### Using this method of property get and set makes it so that the user can access values via attribute style acces
### but not overwrite.  For example, if timeunit() is a funciton, dont' want user to do timeunit=4 and overwrite it.
### This is what would happen if didn't use property getter.  Setter is actually incompatible with DF so workaround it
### by using set_x methods.

@property
def timeunit(self):
    return self.columns.unit

def set_timeunit(self, unit):
    pass

@property
def specunit(self):
    return self.index.unit    
    
def set_specunit(self, unit):
    self.index=self.index._set_spectra(unit) 
        
@property
def spectypes(self):
    return self.index.list_units()

pandas.DataFrame.spectypes=spectypes                
pandas.DataFrame.specunit=specunit
pandas.DataFrame.set_specunit=set_specunit
pandas.DataFrame.timeunit=timeunit
pandas.DataFrame.set_timeunit=set_timeunit

if __name__ == '__main__':
    df=TimeSpectra(specunit='nm')
    print df.spectypes
    df.set_specunit(None)
    df.set_specunit('FELLLAAA')

    #df=pandas.DataFrame([200,300,400])
    #print df
    #df.index=x  
    #df.con('centimeters')
    #print df
    
    