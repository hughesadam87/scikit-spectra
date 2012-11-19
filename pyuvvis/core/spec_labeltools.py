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

### Change spectral labels ###
h=6.626068*10**-34          #Planck's constant m**2 kg / s
eVtoJ=1.60217646 * 10**-19  #Number of Joules in one eV (needed becasue eV is not the standard MKS unit of energy)
c=299792458.0               #speed of light m/s

## Dictionary used to convert representation of time from seconds.  Does not
## use domain specific representations of time such as sidereal time or financial time.
sec_conversions={'nanoseconds':10**-9, 'microseconds':10**-6, 'milliseconds':10**-3, \
                    'seconds':1.0, 'minutes':60.0, 'hours':3600.0, \
                    'days':86400.0, 'years':31536000.0}

### Mapping of various spectral units to meters.  
spec_dic= { 'meters':1.0, 'centimeters':.01, 'micrometers':.000001, 'nanometers': .000000001,          
            'cm-1': .01, 'nm-1':.000000001,'freq': c, 
            'angfreq': 2.0*math.pi*c, 'ev':h*c/(eVtoJ)  }
                                                                          

### Index/label utilities.  Leave mapping back to dataframe separate. ###
def datetime_convert(datetimeindex, return_as='interval', cumsum=True):
    ''' Convert a list of datetime labels into either intervals or as rawtime
    seconds, minutes, hours etc... Note, pandas DatetimeIndex has a lot of conversion 
    methods and timespan representations, but this does not rely on them.
    
    Note: M times becomes M-1 intervals, so a t=0 interval is added by default.   

    if cumsum - Intervals are returned as a running sum, rather than the raw time different between.
    '''

    return_as=return_as.lower()
    
    intervals=np.diff(datetimeindex.to_pydatetime()) # intervals as timedelta objects.
    
    if return_as == 'interval' or return_as == 'intervals':
        newindex=intervals


    elif return_as in sec_conversions.keys():

	### Convert intervals to nanoseconds then to seconds as canonical unit
	### to use conversion dictionary above.
	nanoseconds=np.diff(datetimeindex.asi8) 
	seconds=nanoseconds * 10**-9
        newindex= seconds / sec_conversions[return_as]
    
    else:
        valid=sec_conversions.keys()
        valid.append('interval')
        vstring=','.join(valid)
        raise NameError('datetime_convert() return as keyword must be one of the \
        following: %s but %s was entered.'%(vstring, return_as))


    ### Add a t=0 index.  User first element minus itself to take care of the fact 
    newindex=np.insert(newindex, 0, newindex[1]-newindex[1])

    if cumsum:
	newindex=newindex.cumsum()

    return newindex  
    

### Spectral units conversion ###
proportional=['meters', 'nanometers', 'centimeters', 'micrometers'] 
reciprocal=['cm-1', 'ev', 'nm-1', 'freq', 'angfreq']    
allunits=proportional+reciprocal

def spectral_convert(spectral_array, in_unit='nanometers', out_unit='freq'):
    ''' Converts spectral data arrays between spectral units.  This can take in pandas
    Index and will autoconvert to numpyarray, but will only return array, not an Index.
    Valid in and out units below:

    meters                  cm-1: Inverse centimeters
    centimeters             nm-1: Inverse nanometers/Wavenumber
    micrometers             freq: Frequence In Hertz
    nanometers              angfreq: Angular Frequency in Radians/second
    ev: Electron volts '''

    in_unit=in_unit.lower() ; out_unit=out_unit.lower()
        
    if in_unit not in allunits or out_unit not in allunits:
	raise NameError('spectral_convert() input and output units must be in %s.  %s %s were passed.' \
	                %(','.join(allunits), in_unit, out_unit))
    
    ### Allow for pandas Index to be directly passed in
    spectral_array=np.asarray(spectral_array)
        
    ### Adjust for four cases on proportionality between input and output units. ###
    if in_unit in proportional and out_unit in proportional:
	    return (spectral_array * spec_dic[in_unit]) / spec_dic[out_unit]
    
    elif in_unit in proportional and out_unit in reciprocal:
	    return 1.0/( (spectral_array * spec_dic[in_unit]) / spec_dic[out_unit])
    
    elif in_unit in reciprocal and out_unit in proportional:
	    return 1.0/( (spectral_array * spec_dic[out_unit]) / spec_dic[in_unit])   #Output/input
    
    elif in_unit in reciprocal and out_unit in reciprocal:
	    return  (spectral_array * spec_dic[out_unit]) / spec_dic[in_unit]
