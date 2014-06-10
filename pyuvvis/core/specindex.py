''' Monkey-patched pandas Index object to represent numerical spectral data.  Most methods are intended to be
    actually called directly from the DataFrame, but calls to df.index.method() should work fine.  
    Warning: The layout of this file, especially the order of imports and monkey patch assignment is important, 
    so try to follow it when making other pathced Index objects.
    
    Attributes:  
       _kind= defaults to 'spectral' (potentially used by other pyuvis methods as an identifier)
       unit= variety of spectral data units (nm, cm etc...) or None
       name= Actually just overwrites default behavior or "Wavelength"
       
    Methods:
    list_units= return all valid spectral units for axis conversion.
    _convert_spectra= Converts spectral axis values to new unit style.
    SpecIndex= functiont that is intended to seem like a class constructor, so that a call to
               SpecIndex() returns the monkeypatched index.
       
       The layout of this Index should be followed if making different types of custom index.  This layout, while
       strange, will be very compatable with monkey-patched DataFrames, to ensure correct default behaviors and stuff.'''


import pandas
import numpy as np
from collections import Iterable 

from pandas import DatetimeIndex

from pyuvvis.core.spec_labeltools import spectral_convert

### Define new attributes (default values provided in SpecIndex())
pandas.Index.unit=None
pandas.Index._kind=None  #Used to identify SpecIndex by other PyUvVis methods (don't overwrite) (SET TO 'spectral' later)

# Store old printout of specindex for later redefinition
pandas.Index.old__unicode__ = pandas.Index.__unicode__

# List of valid units.  Must be identical to that of spectral_convert method (ALL CHARACTERS MUST BE LOWERCASE )

# Before messing this up, realize that _unit_valid() relies on it!
specunits={'m':'meters', 
           'nm':'nanometers', 
           'cm':'centimeters', 
           'um':'micrometers', 
           'k':'wavenumber(cm-1)',
           'ev':'electron volts', 
           'nm-1':'nanometers inverse', 
           'f':'frequency(hz)', 
           'w':'angular frequency(rad/s)',
            None:'No Spectral Unit'}

_specinverse=dict((v,k) for k,v in specunits.iteritems()) #Used for lookup by value

### Catetegorical representation
speccats={'Wavelength':('m','nm','cm', 'um'), 'Wavenumber':('k', 'nm-1'), 'Energy':('ev'), 'Frequency':('f'), 
          'Ang. Frequency':('w') }


def UnitError(value):
    ''' Custom Error for when user tries to pass a bad spectral unit.  Implementation actually defers user
    to see an attribute in the dataframe rather that calling list_sunits directly'''
    return NameError('Invalid spectral unit, "%s".  See TimeSpectra.list_sunits for valid spectral units'%value)


def get_spec_category(unit):
    ''' Given a unit key ('m', 'f' etc...), returns the key in speccats to which it belongs.'''
    if unit != None:
        for key in speccats:
            ### Handle length one case separately (eg Energy: ev)
            if isinstance(speccats[key], basestring):
                if speccats[key]==unit:
                    return key
            ### Length N case (eg Wavelength: 'm', 'nm'...etc..
            else:
                for value in speccats[key]:                    
                    if value==unit:
                        return key
    return None


def _unit_valid(unit):
    ''' Checks to make sure unit is valid.  If unit is in specunits.keys(), returns it. 
    If unit is passed by value (like '''

    if unit==None:
        return unit
    
    unit=unit.lower()
    if unit in specunits:
        return unit
    elif unit in _specinverse:
        return _specinverse[unit]
    else:
        raise UnitError(unit)

    
def SpecIndex(inp, *args, **defattr):
    ''' Lets other programs call this custom Index object.  Index must be called with array values
    by default (aka Index() will fail)
    
    **deft attributes are those defined above, 'kind, unit and name.'''

    unit=defattr.pop('unit', None)
    
    ### Transfer unit key to actual unit name
    unit=_unit_valid(unit)
    
    index=pandas.Index(inp, *args, **defattr)  #Enforce dtype=Float?

    ### Assign unit and category
    index.unit=unit 
    if unit:
        index.name = get_spec_category(unit) 
        
    index._kind='spectral'  #DONT CHANGE
          
    return index


### DONT CHANGE THE NAME OF THIS METHOD WITHOUT UPDATED TIMESPECTRA() __INIT__ WHICH LOOKS FOR IT!
def _convert_spectra(self, outunit, **kwargs):
    '''Handles requests to change spectral axis unit, and hence values.  Ensures that transformations involving unit=None
    are handles properly, and that only valid units are passed to the actual converting function, "spectral_convert".'''  
  
    outunit=_unit_valid(outunit)  
  
    ###If converting to None, don't change the index values
    if outunit==None or self.unit==None:    
        self.unit = outunit
        self.name = get_spec_category(self.unit)
        return self
    
    else:
        out = spectral_convert(self, self.unit, outunit)
        return SpecIndex(out, 
                         unit=outunit, 
                         name=get_spec_category(outunit)
                         ) #_kind automatically assigned by SpecIndex
               
def __unicode__(self):
    ''' Add some printout before Index type.  Don't change __name__ which will change between float index, int64 index etc... because this
    is nice to the type of data (see index method __unicode__ which is called by __repr__) '''
    if self.unit==None:
        sout=''
    else:
        sout=self.unit
    return 'Spectra(%s): %s'%(sout, self.old__unicode__())

### Utilities ###

def set_sindex(start, stop, numpts, unit=None):
    '''Wrapper to np.linspace that returns a specindex object.  Supplemented
     by timespectra method, set_specindex() which imposed further restraints
     on the call signature and shape concerns.'''
    return SpecIndex(np.linspace(start, stop, numpts), unit=unit)

                
#X MONKEY PATCHING: Assign custom methods            
pandas.Index._convert_spectra=_convert_spectra
pandas.Index.__unicode__=__unicode__ #Overload the new printout

if __name__ == '__main__':
    x=SpecIndex([200,300,400])
    print x
    x=x._convert_spectra('centimeters')
    x=x._convert_spectra('ev')
    print x
    
    ## DONT EVER SET UNIT USING INDEX.UNIT DIRECTLY

    
    