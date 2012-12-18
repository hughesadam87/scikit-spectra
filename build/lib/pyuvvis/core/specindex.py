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

from pyuvvis.core.spec_labeltools import spectral_convert


### Define new attributes (default values provided in SpecIndex())
pandas.Index.unit=None
pandas.Index._kind=None  #Used to identify SpecIndex by other PyUvVis methods (don't overwrite) (SET TO 'spectral' later)

### List of valid units.  Must be identical to that of spectral_convert method (ALL CHARACTERS MUST BE LOWERCASE )
specunits={'m':'meters', 'nm':'nanometers', 'cm':'centimeters', 'um':'micrometers', 'k':'wavenumber(cm-1)',
    'ev':'electron volts', 'nm-1':'nanometers inverse', 'f':'frequency(hz)', 'w':'angular frequency(rad/s)'}

_specinverse=dict((v,k) for k,v in specunits.iteritems()) #Used for lookup by value

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
        raise SpecError(unit)

def SpecIndex(inp, *args, **defattr):
    ''' Lets other programs call this custom Index object.  Index must be called with array values
    by default (aka Index() will fail)
    
    **deft attributes are those defined above, 'kind, unit and name.'''

    name=defattr.pop('name', 'Wavelength')  #Do I want a dic to have wavelength/wavenumber/energy/frequency and try to associate it?
    unit=defattr.pop('unit', None)
    
    ### Transfer unit key to actual unit name
    unit=_unit_valid(unit)
    
    index=pandas.Index(inp, *args, **defattr)  #Enforce dtype=Float?
        
    index.unit=unit 
    index.name=name  
    index._kind='spectral'  #DONT CHANGE
          
    return index

def SpecError(value):
    ''' Custom Error for when user tries to pass a bad spectral unit.  Implementation actually defers user
    to see an attribute in the dataframe rather that calling list_sunits directly'''
    return NameError('Invalid spectral unit, "%s".  See df.list_sunits for valid spectral units'%value)

### Self necessary here or additional df stuff gets printed   
def list_sunits(self, delim='\t'):
    ''' Print out all available units in a nice format'''
    print '\nUnit',delim,'Description'
    print '-------------------\n'

    for (k,v) in sorted(specunits.items()):
        print k,delim,v
    print '\n'

### **kwargs needs to be in here to work
def _convert_spectra(self, outunit, **kwargs):
    '''Handles requests to change spectral axis unit, and hence values.  Ensures that transformations involving unit=None
    are handles properly, and that only valid units are passed to the actual converting function, "spectral_convert".'''  
  
    outunit=_unit_valid(outunit)  
  
    ###If converting to None, don't change the index values
    if outunit==None or self.unit==None:    
        self.unit=outunit
        return self
    
    else:
        out=spectral_convert(self, self.unit, outunit)
        return SpecIndex(out, unit=outunit, name=self.name) #_kind automatically assigned by SpecIndex
                
### Assign custom methods            
pandas.Index._convert_spectra=_convert_spectra
pandas.Index.list_sunits=list_sunits

if __name__ == '__main__':
    x=SpecIndex([200,300,400])
    x=x._convert_spectra('centimeters')
    
    ## DONT EVER SET UNIT USING INDEX.UNIT DIRECTLY

    
    