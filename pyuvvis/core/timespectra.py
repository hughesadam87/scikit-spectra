''' Provides core TimeSpectra monkey-patched pandas DadtaFrame  to represent a set of spectral data.  Dataframe with spectral data 
along the index and temporal data as columns (and this orientation is enforced).  The spectral index is controlled from the specindex
module, which has a psuedo-class called SpecIndex (really a monkey patched Index).  Temporal data is stored using a DatetimeIndex or
a modified interval reprentation.  The need to support two types of temporal index, one of which is Pandas builtin DatetimeIndex is what led me
to not create a special index object (like SpecIndex).  Other spectral axis types (like Temperature axis) should probably be built close to the manner of 
Spec index.  The TimeSpectra dataframe actually stores enough information to go back an forth between DatetimeIndex and
Interval representations.  It does this by generating one or the other on the fly, and never relies on the current label object to generate teh next object.'''

import pandas

from specindex import SpecIndex, list_sunits, specunits
from spec_labeltools import datetime_convert

### These are used to overwrite pandas string formatting 
from StringIO import StringIO #For overwritting dataframe output methods
from pandas.util import py3compat
import pandas.core.common as com

## testing (DELETE)
from numpy.random import randn
from testimport import dates as testdates


### EVERYTHING NEEDS DEFAULTED TO NONE!  OTHERWISE, ANY OBJECT IMPORTED OR PASSED IN SEEMS TO HAVE THIS VALUE ASSIGNED.  THUS
### VALUE ASSIGNMENT NEEDS TO OCCUR WITHIN CONSTRUCTING METHODS AND FUNCTIONS
pandas.DataFrame.name=None
pandas.DataFrame.baseline=None

### Time related attributes
pandas.DataFrame.start=None  #MUST BE DATETIME/TIMESTAMPS or w/e is valid in pandas
pandas.DataFrame.stop=None #just make these start and stop? And imply canonical axis
pandas.DataFrame.periods=None
pandas.DataFrame.freq=None 
pandas.DataFrame._interval=None
pandas.DataFrame.timeunit=None

### Time axis special attributes stuff
pandas.Index.unit=None
pandas.Index._kind=None  #Used to identify SpecIndex by other PyUvVis methods (don't overwrite)


tunits={'ns':'nanoseconds', 'us':'microseconds', 'ms':'milliseconds', 's':'seconds', 
          'm':'minutes', 'h':'hours','d':'days', 'y':'years'}

def TimeError(value):
    ''' Custom Error for when user tries to pass a bad spectral unit'''
    return NameError('Invalid time unit, "%s".  See df.timetypes for available units'%value)

def list_tunits(self, delim='\t'):
    ''' Print out all available temporal units in a nice format'''
    print '\nUnit',delim,'Description'
    print '-------------------\n'

    for (k,v) in sorted(tunits.items()):
        print k,delim,v
    print '\n'

def _as_datetime(timespectra):
    ''' Return datetimeindex from either stop,start or start, periods.'''

    if timespectra.stop:
        return pandas.DatetimeIndex(start=timespectra.start, end=timespectra.stop, freq=timespectra.freq)
    else:
        return pandas.DatetimeIndex(start=timespectra.start, periods=timespectra.periods, freq=timespectra.freq)

def as_datetime(self):
    ''' Return columns as DatetimeIndex'''
    self.columns=_as_datetime(self)
    self.columns._kind='temporal'    
    self._interval=False   
    

def _as_interval(timespectra, unit):#, unit=None):
    ''' Return columns as intervals as computed by datetime_convert function.  Not an instance method
   for calls from objects other than self.'''
    ### If current columns is DatetimeIndex, convert
    if timespectra._interval==False:
        return pandas.Index(datetime_convert(timespectra.columns, return_as=unit, cumsum=True))#, unit=unit)              

    ### If currently already intervals, convert to datetime, then convert that to new units
    else:
        newcols=_as_datetime(timespectra)
        return pandas.Index(datetime_convert(newcols, return_as=unit, cumsum=True))#, unit=unit)              
      
    ### Self necessary here or additional df stuff gets printed   
def as_interval(self, unit='interval'):  
    ''' Return columns as intervals as computed by datetime_convert function'''
    self.columns=_as_interval(self, unit)
    self.columns._kind='temporal'
    self._interval=True
    

def TimeSpectra(*dfargs, **dfkwargs):
    ''' Function that returns a customized dataframe with a SpecIndex axis and a TimeIndex column.  SpecIndex is its own
    modified pandas Index object.  TimeSpectra stores temporal data in terms of either a DatetimeIndex or intervals, and enought
    metadata to transform between the represnetations.
    
    TimeSpectra attempts to leave the DataFrame initialization intact.  For example and empty TimeSpectra can be returned.'''

    ### Pop default DataFrame keywords before initializing###
    name=dfkwargs.pop('name', 'TimeSpectra')
    baseline=dfkwargs.pop('baseline', None)    

    ###Spectral index-related keywords
    specunit=dfkwargs.pop('specunit', None)

    ###Time index-related keywords  (note, the are only used if a DatetimeIndex is not passed in)
    freq=dfkwargs.pop('freq', None)    
    start=dfkwargs.pop('start', None)
    stop= dfkwargs.pop('stop', None)    
    periods=dfkwargs.pop('periods',None)
    timeunit=dfkwargs.pop('timeunit',None) #Not the same as freq, but inferred from it
    
    if stop and periods:
        raise AttributeError('TimeSpectra cannot be initialized with both periods and stop; please choose one or the other.')
    
    df=pandas.DataFrame(*dfargs, **dfkwargs)
    df.name=name

    ###Set Index as spectral variables
    set_specunit(df, specunit)  #This will automatically convert to a spectral index
    

    ### If user passes non datetime index to columns, make sure they didn't accidetnally pass SpecIndex by mistake.
    if not isinstance(df.columns, pandas.DatetimeIndex):
        try:
            if df.columns._kind == 'spectral':
                raise IOError("SpecIndex must be passed as index, not columns.")   ### Can't be an attribute error or next won't be raised             
        
        ### df.columns has no attribute _kind, meaning it is likely a normal pandas index        
        except AttributeError:
            df._interval=True
            df.start=start
            df.stop=stop
            df.freq=freq
            df.timeunit=timeunit
            
    ### Take Datetime info and use to recreate the array
    else:
        df._interval=False        
        df.start=df.columns[0]
        df.stop=df.columns[-1]
        df.freq=df.columns.freq
        ### ADD TRANSLATION FOR FREQ--> basetimeuint
#       df.timeunit=get_time_from_freq(df.columns.freq)
        
    ### Have to do it here instead of defaulting on instantiation.
    df.columns._kind='temporal'
    return df


def __newrepr__(self):
    """
    Just ads a bit of extra data to the dataframe on printout.  Literally just copied directly from dataframe.__repr__ and
    added print statements.  Dataframe also has a nice ___reprhtml___ method for html accessibility.
    """
    print 'ababababa'
    buf = StringIO()
    if self._need_info_repr_():
        self.info(buf=buf, verbose=self._verbose_info)
    else:
        self.to_string(buf=buf)
    value = buf.getvalue()

    if py3compat.PY3:
        return unicode(value)
    return com.console_encode(value)

### Using this method of property get and set makes it so that the user can access values via attribute style acces
### but not overwrite.  For example, if freq() is a funciton, dont' want user to do freq=4 and overwrite it.
### This is what would happen if didn't use property getter.  Setter is actually incompatible with DF so workaround it
### by using set_x methods.


#@property
#def timetypes(self):
    #return self.columns.list_units()


### Temporal column attributes/properties
@property
def specunit(self):
    return self.index.unit    #Short name key

@property
def full_specunit(self):
    return specunits[self.index.unit]
    
def set_specunit(self, unit):
    self.index=self.index._set_spectra(unit) 
        
@property
def spectypes(self):
    return specunits

@property
def timetypes(self):
    return tunits


pandas.DataFrame.list_sunits=list_sunits
pandas.DataFrame.list_tunits=list_tunits

pandas.DataFrame.spectypes=spectypes                
pandas.DataFrame.specunit=specunit
pandas.DataFrame.set_specunit=set_specunit

pandas.DataFrame.timetypes=timetypes

pandas.DataFrame.as_interval=as_interval
pandas.DataFrame.as_datetime=as_datetime

###Overwrite output representation
pandas.DataFrame.__repr__=__newrepr__


if __name__ == '__main__':
    
    ### Be careful when generating test data from Pandas Index/DataFrame objects, as this module has overwritten their defaul behavior
    ### best to generate them in other modules and import them to simulate realisitc usec ase
    
    spec=SpecIndex([400,500,600])
    df=TimeSpectra(randn(3,3), columns=testdates, index=spec, specunit='nm')
    


    df.as_interval('nanoseconds')
    print df.spectypes
    df.set_specunit(None)
    df.set_specunit('FELLLAAA')

    #df=pandas.DataFrame([200,300,400])
    #print df
    #df.index=x  
    #df.con('centimeters')
    #print df
    
    