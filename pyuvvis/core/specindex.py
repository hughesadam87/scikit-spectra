''' Monkey-patched pandas Index object to represent numerical spectral data.  Most methods are intended to be
    actually called directly from the DataFrame, but calls to df.index.method() should work fine.  
    Warning: The layout of this file, especially the order of imports and monkey patch assignment is important, 
    so try to follow it when making other pathced Index objects.
    
    Attributes:  
       kind= defaults to 'spectral'
       unit= variety of spectral data units (nm, cm etc...) or None
       name= Actually just overwrites default behavior or "Wavelength"
       
    Methods:
    list_units= return all valid spectral units for axis conversion.
    _set_spectra= Converts spectral axis values to new unit style.
    SpecIndex= functiont that is intended to seem like a class constructor, so that a call to
               SpecIndex() returns the monkeypatched index.
       
       The layout of this Index should be followed if making different types of custom index.  This layout, while
       strange, will be very compatable with monkey-patched DataFrames, to ensure correct default behaviors and stuff.'''

import pandas

from pyuvvis.core.spec_labeltools import spectral_convert


### Define new attributes (default values provided in SpecIndex())
pandas.Index.kind=None
pandas.Index.unit=None

### List of valid units.  Must be identical to that of spectral_convert method
allunits={'m':'meters', 'nm':'nanometers', 'cm':'centimeters', 'um':'micrometers', 'k':'wavenumber(cm-1)',
    'ev':'electron volts', 'nm-1':'nanometers inverse', 'f':'frequency(Hz)', 'w':'angular frequency(rad/s)'}

def SpecIndex(inp, *args, **defattr):
    ''' Lets other programs call this custom Index object.  Index must be called with array values
    by default (aka Index() will fail)
    
    **deft attributes are those defined above, 'kind, unit and name'''

    name=defattr.pop('name', 'Wavelength')
    kind=defattr.pop('kind', 'spectral')
    unit=defattr.pop('unit', None)
    
    index=pandas.Index(inp, *args, **defattr)  #Enforce dtype=Float?
    
    index.unit=unit ; index.name=name ; index.kind=kind
        
    ### If bad unit is passed as input ###    
    if index.unit not in allunits and index.unit != None:
        print 'Cannot assign spectral unit, "%s"'%index.unit  
        index.unit=None        
    return index

def SpecError(value):
    ''' Custom Error for when user tries to pass a bad spectral unit'''
    return NameError('Invalid spectral unit, "%s".  See df.spectypes for available units'%value)

def list_units(self, delim='\t'):
    ''' Print out all available units in a nice format'''
    print '\nUnit',delim,'Description'
    print '-------------------\n'

    for (k,v) in sorted(allunits.items()):
        print k,delim,v
    print '\n'

### **kwargs needs to be in here to work
def _set_spectra(self, outunit, **kwargs):
    '''Handles requests to change spectral axis unit.  Ensures that transformations involving unit=None
    are handles properly, and that only valid units are passed to the actual converting function, "spectral_convert".'''  

    ###If converting to None, don't change the index values
    if outunit==None:    
        self.unit=outunit
        return self
    
    ###If converting from None, just make sure new unit is valid then assign
    if self.unit==None:
        if outunit in allunits:
            self.unit=outunit
            return self
        else:
            raise SpecError(outunit)

    ###If converting from x to y, ensure proper units and then convert values and reassign unit attribute
    outunit=outunit.lower()
    if outunit not in allunits:
        raise SpecError(outunt)
    else:
        out=spectral_convert(self, self.unit, outunit)
        out=SpecIndex(out)
        out.unit=outunit
        return out
                
### Assign custom methods            
pandas.Index._set_spectra=_set_spectra
pandas.Index.list_units=list_units

if __name__ == '__main__':
    x=SpecIndex([200,300,400])
    x.unit='nanometers'
    x=x._set_spectra('centimeters')

    
    