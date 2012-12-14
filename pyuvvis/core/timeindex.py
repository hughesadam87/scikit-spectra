''' Monkey-patched dataframe object to represent the core class of PyUvVis: a set of spectral data.'''

import pandas

from pyuvvis.core.spec_labeltools import datetime_convert, allunits


pandas.Index.kind=None
pandas.Index.unit=None

allunits={'ns':'nanoseconds', 'us':'microseconds', 'ms':'milliseconds', 's':'seconds', 
          'm':'minutes', 'h':'hours','d':'days', 'y':'years'}

def TimeError(value):
    ''' Custom Error for when user tries to pass a bad spectral unit'''
    return NameError('Invalid time unit, "%s".  See df.timetypes for available units'%value)

def list_units(self, delim='\t'):
    ''' Print out all available units in a nice format'''
    print '\nUnit',delim,'Description'
    print '-------------------\n'

    for (k,v) in sorted(allunits.items()):
        print k,delim,v
    print '\n'

### **kwargs needs to be in here
def _set_time(self, outunit, **kwargs):
    '''Returns new index with converted unit and axis values.'''  

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
            raise TimeError(outunit)

    ###If converting from x to y, ensure proper units and then convert values and reassign unit attribute
    outunit=outunit.lower()
    if outunit not in allunits:
        raise TimeError(outunt)
    else:
        raise NotImplementedError('Need a canonical axis and way to convert representations')
        #out=spectral_convert(self, self.unit, outunit)
        #out=SpecIndex(out)
        #out.unit=outunit
        #return out
    
def TimeIndex(data, **defattr):
    ''' Lets other programs call this custom Index object.  Index must be called with array values
    by default (aka Index() will fail)
    
    **deft attributes are those defined above, 'kind, unit and name'''

    name=defattr.pop('name', 'Time')
    kind=defattr.pop('kind', 'temporal')
    unit=defattr.pop('unit', None)
    
    index=pandas.Index(inp, *args, **defattr)  #Enforce dtype=Float?
    
    index.unit=unit ; index.name=name ; index.kind=kind
        
    ### If bad unit is passed as input ###    
    if index.unit not in allunits and index.unit != None:
        print 'Cannot assign spectral unit, "%s"'%index.unit  
        index.unit=None        
    return index
            
### Assign custom methods            
pandas.Index._set_time=_set_time
pandas.Index.list_units=list_units


if __name__ == '__main__':
    pass 
    
    