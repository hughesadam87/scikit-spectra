''' Utilities for converting time and spectral array.  In particular, for converting 
an array of datetimes into raw times (absolute seconds, minutes etc..) or time intervals.  
Additionally, has a function (spectral_convert() ) to convert arrays of spectral data units.

For now, these functions return numpy arrays and aren't strictlu bound to pandas Index objects.
It is up to the user or calling class to interface these functions to a DataFrame.'''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

### Builtin Imports
import math

### 3rd Party Imports
import numpy as np

from pyuvvis.exceptions import badkey_check

### Change spectral labels ###
h = 6.626068*10**-34          #Planck's constant m**2 kg / s
eVtoJ = 1.60217646 * 10**-19  #Number of Joules in one eV (needed becasue eV is not the standard MKS unit of energy)
c = 299792458.0               #speed of light m/s

## Dictionary used to convert representation of time from seconds.  Does not
## use domain specific representations of time such as sidereal time or financial time.

### Lazy way to cover both kinds of input, short or long unit!
sec_conversions= {
         'ns':10**-9,
         'us':10**-6, 
	 'ms':10**-3, 
         's':1.0, 
	 'm':60.0, 
	 'h':3600.0, 
         'd':86400.0, 
	 'y':31536000.0, 
	 'intvl':None}


intvl_dic={'ns':'Nanoseconds', 
           'us':'Microseconds', 
           'ms':'Milliseconds',
           's':'Seconds', 
           'm':'Minutes', 
           'h':'Hours', 
           'd':'Days', 
           'y':'Years',
           'intvl':'Time Delta'}


### Conversions for intensity data.  Note that T= I(t)/Iref
### Since it's not really a scaling but a mapping, I use lambda operations and their inverses.  Uses Transmittance
### as the base unit, as it is literally curve/ref, hence the natural unit of divby() 
Idic={None:'Counts', #Don't change without updating normplot; relies on these keys 
      't':'Transmittance', 
      '%t':'(%)Transmittance', 
      'r':'Inverse Transmittance (1/T)',
      'a':'Absorbance (base 10)', 
      'a(ln)':'Absorbance (base e)'} 


### Remember, data is already divided by ref before from_T is called, so "r" is base unit, not "t".  
from_T={'t':lambda x: 1.0/x, 
        '%t':lambda x: 100.0 * (1.0/ x), 
        'r':lambda x: x, 
        'a':lambda x: -np.log10(x),
        'a(ln)':lambda x:-np.log(x)}


to_T={'t':lambda x: 1.0/x, 
      '%t':lambda x: (1.0/ x) / 100.0, 
      'r':lambda x: x, 
      'a':lambda x: np.power(10, -x), 
      'a(ln)':lambda x: np.exp(-x)} 


### Index/label utilities.  Leave mapping back to dataframe separate. ###
def datetime_convert(datetimeindex, return_as='intvl', cumsum=True):
    ''' Convert a list of datetime labels into either intervals or as rawtime
    seconds, minutes, hours etc... Note, pandas DatetimeIndex has a lot of conversion 
    methods and timespan representations, but this does not rely on them.

    Note: M times becomes M-1 intervals, so a t=0 interval is added by default.   

    if cumsum - Intervals are returned as a running sum, rather than the raw time different between.
    '''

    valid=sec_conversions.keys()   
    
    badkey_check(return_as, valid)

    return_as=return_as.lower()

    intervals=np.diff(datetimeindex.to_pydatetime()) # intervals as timedelta objects.

    if return_as == 'intvl':
        newindex=intervals


    else:

        ### Convert intervals to nanoseconds then to seconds as canonical unit
        ### to use conversion dictionary above.
        nanoseconds=np.diff(datetimeindex.asi8) 
        seconds=nanoseconds * 10**-9
        newindex= seconds / sec_conversions[return_as]


    ### Add a t=0 index.  Uses first element minus itself to preserve timestamp unit if intervals  
    newindex=np.insert(newindex, 0, newindex[0]-newindex[0])

    if cumsum:
        newindex=newindex.cumsum()

    return newindex  


def spec_slice(spectral_array, bins):
    ''' Simple method that will divide a spectral index into n evenly sliced bins and return as nested tuples.
    Useful for generating wavelength slices with even spacing.  Simply a wrapper around np.histogram.'''
    edges=np.histogram(spectral_array, bins)[1]
    return [ (edges[idx], edges[i]) for idx, i in enumerate( range(1, len(edges)))]
