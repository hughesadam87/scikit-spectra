from types import MethodType, NoneType
from copy import deepcopy
import inspect
import functools
import cPickle

from pandas import DataFrame, DatetimeIndex, Index, Series
from numpy import array_equal

### Local imports (REPLACE WITH PYUVVIS IMPORTS)
from specindex import SpecIndex, specunits
from spec_labeltools import datetime_convert
from spec_labeltools import from_T, to_T, Tdic
from pyuvvis.core.spec_utilities import divby
from pyuvvis import spec_surface3d

#### These are used to overwrite pandas string formatting 
#from StringIO import StringIO #For overwritting dataframe output methods
#from pandas.util import py3compat
#import pandas.core.common as com

## testing (DELETE)
from numpy.random import randn
from testimport import dates as testdates
import matplotlib.pyplot as plt


tunits={'ns':'nanoseconds', 'us':'microseconds', 'ms':'milliseconds', 's':'seconds', 
        'm':'minutes', 'h':'hours','d':'days', 'y':'years'}


#################
##Custom Errors##
#################

def TimeError(value):
    ''' Custom Error for when user tries to pass a bad spectral unit'''
    return NameError('Invalid time unit, "%s".  See df.timetypes for available units'%value)

def ItypeError(value):
    ''' Custom Error for when user tries to pass a bad spectral intensity style (T, %T, A etc...)'''
    return NameError('Invalid intensity type "%s".  See df.list_iunits() for valid spectral intenisty styles'%value)

def BaselineError(index, timespectra):
    ''' Error raised when a user-supplied iterable does not have same spectral values as those of the timespectra.'''
    sunit=timespectra.specunit
    return Exception('Cannot resolve length %s baseline (%s%s - %s%s) and length %s %s (%s%s - %s%s)'\
                      %(len(index), index[0], sunit,  index[-1], sunit, len(timespectra.baseline), \
                        timespectra.name, timespectra.df.index[0], sunit, timespectra.df.index[-1], sunit) )


######################
## Helper Functions###
######################

### Loading.  These are both giving recursion errors, where instance methods or not.
def ts_load(inname):
    ''' Load TimeSpectra from file'''
    if isinstance(inname, basestring):
        inname=open(inname, 'r')
    return cPickle.load(inname)

def ts_loads(string):
    ''' Load a TimeSpectra from string stored in memory.'''
    ### BUG WHY DOESNT THIS WORK
    return cPickle.loads(string)    

### Unit validations###
def _valid_iunit(sout):
    '''When user is switching spectral intensity units, make sure they do it write.'''
    if sout==None:
        return sout
    sout=sout.lower()
    if sout in Tdic.keys():
        return sout
    else:
        raise ItypeError(sout)    


def _as_interval(timespectra, unit):#, unit=None):
    ''' Return columns as intervals as computed by datetime_convert function.  Not an instance method
    for calls from objects other than self.'''
    ### If current columns is DatetimeIndex, convert
    if timespectra._interval==False:
        return Index(datetime_convert(timespectra.columns, return_as=unit, cumsum=True))#, unit=unit)              

    ### If currently already intervals, convert to datetime, then convert that to new units
    else:
        newcols=_as_datetime(timespectra)
        return Index(datetime_convert(newcols, return_as=unit, cumsum=True))#, unit=unit)      

### Time interval computations ###
def _as_datetime(timespectra):
    ''' Return datetimeindex from either stop,start or start, periods.'''
    if self.stop:
        self.df.columns=DatetimeIndex(start=timespectra.start, end=timespectra.stop, freq=timespectra.freq)
    else:
        self.df.columns=DatetimeIndex(start=timespectra.start, periods=timespectra.periods, freq=timespectra.freq)


class TimeSpectra(object):
    ''' Provides core TimeSpectra composite pandas DataFrame to represent a set of spectral data.  Enforces spectral data 
    along the index and temporal data as columns.  The spectral index is controlled from the specindex
    module, which has a psuedo-class called SpecIndex (really a monkey patched Index).  Temporal data is stored using a DatetimeIndex or
    a modified interval reprentation.  The need to support two types of temporal index, one of which is Pandas builtin DatetimeIndex is what led me
    to not create a special index object (like SpecIndex).  Other spectral axis types (like Temperature axis) should probably be built close to the manner of 
    Spec index.  The TimeSpectra dataframe actually stores enough temporal metadatato go back an forth between DatetimeIndex and
    Interval representations.  It does this by generating one or the other on the fly, and never relies on the current label object to generate teh next object.'''

    def __init__(self, *dfargs, **dfkwargs):
        ### Pop default DataFrame keywords before initializing###
        self.name=dfkwargs.pop('name', 'TimeSpectra')

        ###Spectral index-related keywords
        specunit=dfkwargs.pop('specunit', None)

        ###Intensity data-related stuff
        iunit=dfkwargs.pop('iunit', None)

        ###Time index-related keywords  (note, the are only used if a DatetimeIndex is not passed in)
        freq=dfkwargs.pop('freq', None)    
        start=dfkwargs.pop('start', None)
        stop= dfkwargs.pop('stop', None)    
        periods=dfkwargs.pop('periods',None)
        timeunit=dfkwargs.pop('timeunit',None) #Not the same as freq, but inferred from it
        baseline=dfkwargs.pop('baseline', None)
        

        if stop and periods:
            raise AttributeError('TimeSpectra cannot be initialized with both periods and stop; please choose one or the other.')

        df=DataFrame(*dfargs, **dfkwargs)

        ### If user passes non datetime index to columns, make sure they didn't accidetnally pass SpecIndex by mistake.
        if not isinstance(df.columns, DatetimeIndex):
            try:
                if df.columns._kind == 'spectral':
                    raise IOError("SpecIndex must be passed as index, not columns.")   ### Can't be an attribute error or next won't be raised             

            ### df.columns has no attribute _kind, meaning it is likely a normal pandas index        
            except AttributeError:
                self._interval=True
                self.start=start
                self.stop=stop
                self.freq=freq
                self.timeunit=timeunit

        ### Take Datetime info and use to recreate the array
        else:
            self._interval=False        
            self.start=df.columns[0]
            self.stop=df.columns[-1]
            self.freq=df.columns.freq

            ### ADD TRANSLATION FOR FREQ--> basetimeuint
#       self.timeunit=get_time_from_freq(df.columns.freq)

        ### Have to do it here instead of defaulting on instantiation.
        df._tkind='temporal'

        ### Assign spectral intensity related stuff but 
        ### DONT CALL _set_itype function
        iunit=_valid_iunit(iunit)
        self._itype=iunit

        self.df=df
        
        ### This has to be done AFTER self.df has been set
        self._baseline=self._baseline_valid(baseline)#SHOULD DEFAULT TO NONE SO USER CAN PASS NORMALIZED DATA WITHOUT REF        

        ###Set Index as spectral variables
        self.specunit = specunit  #This will automatically convert to a spectral index


    #############################################################################    
    ### Methods ( @property decorators ensure use can't overwrite methods) ######   
    #############################################################################

    ### Unit printouts
    def _list_out(self, outdic, delim='\t'):
        ''' Generic output method for shortname:longname iterables.  Prints out various
        dictionaries, and is independent of the various datastructures contained'''
        print '\nKey',delim,'Description'
        print '-------------------\n'

        for (k,v) in sorted(outdic.items()):
            print k,delim,v
        print '\n'

    def list_tunits(self, delim='\t'):
        ''' Print out all available temporal units in a nice format'''
        self._list_out(tunits, delim=delim)

    def list_iunits(self, delim='\t'):
        self._list_out(Tdic, delim=delim)

    ### Self necessary here or additional df stuff gets printed   
    def list_sunits(self, delim='\t'):
        ''' Print out all available units in a nice format'''
        self._list_out(specunits, delim=delim)         

    ### Timeunit conversions/manipulations

    def as_datetime(self):
        ''' Return columns as DatetimeIndex'''
        self.df.columns=_as_datetime(self)
        self._tkind='temporal'    
        self._interval=False


    def as_interval(self, unit='interval'):  
        ''' Return columns as intervals as computed by datetime_convert function'''
        self.df.columns=_as_interval(self, unit)
        self._tkind='temporal'
        self._interval=True    



    @property
    def baseline(self):
        ''' This is stored as a Series unless user has set it otherwise.'''
        return self._baseline

    @baseline.setter
    def baseline(self, baseline, force_series=True):  
        ''' Before changing baseline, first validates.  Then considers various cases, and changes 
        class attributes and dataframe values appropriately.'''

        ### Adding or changing baseline
        if not isinstance(baseline, NoneType):

            ### If data is in raw/full mode (itype=None)
            if self._itype == None:
                baseline=self._baseline_valid(baseline, force_series=force_series)                  
                self._baseline=baseline

            ### Let _set_itype() do lifting.  Basically convert to full and back to current itype. 
            else:
                self._set_itype(self._itype, ref=baseline)



        ### Removing baseline.  
        else:
            ### If current baseline is not None, convert
            if not isinstance(self._baseline, NoneType):  #Can't do if array==None
                self._set_itype(None, ref=self._baseline)
                self._baseline=None



    def remove_baseline(self):
        ''' Convience method for setting to None'''
        self.baseline=None
        
    def as_dataframe(self):
        ''' Convience method for self.df'''
        return self.df

    ### Spectral column attributes/properties
    @property
    def specunit(self):
        return self.df.index.unit    #Short name key

    @property
    def full_specunit(self):
        return specunits[self.df.index.unit]

    @specunit.setter
    def specunit(self, unit):
        self.df.index=self.df.index._convert_spectra(unit) 
        
    def as_specunit(self, unit):
        ''' Returns new dataframe with different spectral unit on the index.'''
        tsout=self.deepcopy()
        tsout.specunit=unit
        return tsout

    @property
    def spectypes(self):
        return specunits


    ### Temporal column attributes
    @property
    def timetypes(self):
        return tunits

    ### Spectral Intensity related attributes/conversions
    @property
    def full_iunit(self):
        return Tdic[self._itype]
    
    @property
    def iunit(self):
        return self._itype
    
    @iunit.setter
    def iunit(self, unit):     
        ''' Change iunit in place.'''
        if isinstance(unit, basestring):
            if unit.lower() in ['none', 'full']:
                unit=None

        self._set_itype(unit)        


    def as_iunit(self, unit, baseline=None):
        ''' Returns new TimeSpectra of modified iunit.  Useful if in-place operation not desirable.  
        Also has the option of manually passing a new baseline for on-the-fly rereferencing.'''
        if isinstance(unit, basestring):
            if unit.lower() in ['none', 'full']:
                unit=None

        tsout=self.deepcopy()        
        tsout._set_itype(unit, baseline)
        return tsout

    def _set_itype(self, sout, ref=None):
        '''Function used to change spectral intensity representation in a convertible manner. Not called on
        initilization of TimeSpectra(); rather, only called by as_iunit() method.'''

        sout=_valid_iunit(sout)
        sin=self._itype
        df=self.df #for convienence/back compatibility

        # Corner case, for compatibility with baseline.setter
        if sin==None and sout==None:
            return

        ########################################################################
        ### Case 1: User converting from full data down to referenced data.#####
        ########################################################################
        if sin==None and sout != None:
            rout=self._baseline_valid(ref)

            ### If user tries to downconvert but doesn't pass reference, use stored one
            if rout == None:
                rout=self._baseline

            ### If ref not passed, use current baseline.  Want to make sure it is 
            ### not none, but have to roundabout truthtest
            if isinstance(rout, NoneType):
                raise TypeError('Cannot convert spectrum to iunit %s without a baseline'%sout)                
            else:
                df=divby(df, divisor=rout)
                df=df.apply(from_T[sout])                    
            #Assumes typeerror is due to rout not being a series/array, but doesn't further test it.  EG do another
            #typeerror check of try: if rout == None: raise error


        ################################################################   
        ### Case 2: Changing spectral representation of converted data.#
        ################################################################     
        elif sin !=None and sout != None:

            ### If user changing reference on the fly, need to change ref ###
            if not isinstance(ref, NoneType): #and ref != self._baseline:
                rout=self._baseline_valid(ref)

                ### Make this it's own method called change baseline?
                df=df.apply(to_T[sin])
                df=df.mul(self._baseline, axis=0)  
                df=divby(df, divisor=rout)
                df=df.apply(from_T[sout])                        


            else:
                rout=self._baseline #For sake of consistent transferring at end of this function
                df=df.apply(to_T[sin])
                df=df.apply(from_T[sout])        


        #############################################################    
        ### Case 3: User converting referenced data up to full data.#
        #############################################################
        elif sin !=None and sout==None:
            rout=self._baseline_valid(ref)
            df=df.apply(to_T[sin])
            df=df.mul(rout, axis=0)  #Multiply up!

        self._baseline=rout       
        self._itype=sout        
        self.df=df    

    @property
    def itypes(self):
        return Tdic
    
    ### Save methods.  (Load/loads can't be instance methods or recursion errors)    
    def save(self, outname):
        ''' Takes in str or opened file and saves. cPickle.dump wrapper.'''
        if isinstance(outname, basestring):
            outname=open(outname, 'w')
        cPickle.dump(self, outname)

    
    def dumps(self):
        ''' Output TimeSpectra into a pickled string in memory.'''
        return cPickle.dumps(self)
    
    def deepcopy(self):
        ''' Make a deepcopy of self, including the dataframe.'''
        return self._deepcopy(self.df)

    #################################
    ### Dataframe METHOD Overwrites##   
    #################################
    def __getitem__(self, key):
        ''' Item lookup'''
        return self.df.__getitem__(key)    

    def __setitem__(self, key, value):
        self.df.__setitem__(key, value)    

    def __getattr__(self, attr, *fcnargs, **fcnkwargs):
        ''' Tells python how to handle all attributes that are not found.  Basic attributes 
        are directly referenced to self.df; however, instance methods (like df.corr() ) are
        handled specially using a special private parsing method, _dfgetattr().'''

        ### Return basic attribute
        refout=getattr(self.df, attr)
        if not isinstance(refout, MethodType):
            return refout

        ### Handle instance methods using _dfgetattr().
        ### see http://stackoverflow.com/questions/3434938/python-allowing-methods-not-specifically-defined-to-be-called-ala-getattr
        else:         
            return functools.partial(self._dfgetattr, attr, *fcnargs, **fcnkwargs)
            ### This is a reference to the fuction (aka a wrapper) not the function itself


    def _deepcopy(self, dfnew):
        ''' Copies all attribtues into a new object except has to store current dataframe
        in memory as this can't be copied correctly using copy.deepcopy.  Probably a quicker way...
        
        dfnew is used if one wants to pass a new dataframe in.  This is used primarily in calls from __getattr__.'''
        ### Store old value of df
        olddf=self.df.copy(deep=True)
        self.df=None
        
        ### Create new object and apply new df
        newobj=deepcopy(self)
        newobj.df=dfnew
        
        ### Restore old value of df and return new object
        self.df=olddf
        return newobj
        
       
    def _dfgetattr(self, attr, use_base=False, *fcnargs, **fcnkwargs):
        ''' Called by __getattr__ as a wrapper, this private method is used to ensure that any
        DataFrame method that returns a new DataFrame will actually return a TimeSpectra object
        instead.  It does so by typechecking the return of attr().
        
        **kwargs: use_base - If true, program attempts to call attribute on the baseline.  Baseline ought
        to be maintained as a series, and Series/Dataframe API's must be same.
        
        *fcnargs and **fcnkwargs are passed to the dataframe method.
        
        Note: tried to ad an as_new keyword to do this operation in place, but doing self=tsout instead of return tsout
        didn't work.  Could try to add this at the __getattr__ level; however, may not be worth it.'''
 
        out=getattr(self.df, attr)(*fcnargs, **fcnkwargs)
        
        ### If operation returns a dataframe, return new TimeSpectra
        if isinstance(out, DataFrame):
            
            ### Should this operation be called on baseline?
            if use_base == True:
                try:
                    baseout=getattr(self.baseline, attr)(*fcnargs, **fcnkwargs)
                except Exception:
                    ### There may be cases where df.x() and series.x() aren't available!
                    raise Exception('Could not successfully perform operation "%s" on baseline.  Please check\
                    Pandas Series API'%attr)            
            
            tsout=self._deepcopy(out)
            if use_base==True:
                ### Have to convert back down to a series ### (IF FORCED BASELINE TO DATAFRAME)
                ### and Series(df) does not work correctly!! VERY HACKy
#                tsout.baseline=Series(baseout[baseout.columns[0]])
                
                tsout.baseline=baseout
            
            return tsout
        
        ### Otherwise return whatever the method return would be
        else:
            return out
        
    ### ERRORS ARE NOT DUE TO WHAT I'M DOING, BUT DO TO OVERWRITING THIS INT HE FIRST PLACE
    ### EVEN IF I JUST PRINT 'HI' IT BUGS OUT WITHOUT ANY REF TO df.__repr__()
    #def __repr__(self):
        #''' Add some header and spectral data information to the standard output of the dataframe.'''
        ##"""
        ##Just ads a bit of extra data to the dataframe on printout.  Literally just copied directly from dataframe.__repr__ and
        ##added print statements.  Dataframe also has a nice ___reprhtml___ method for html accessibility.
        ##"""
        ##delim='\t'
        ##if self.specunit==None:
            ##specunitout='None'
        ##else:
            ##specunitout=self.full_specunit

        ##outline='**',self.name,'**', delim, 'Spectral unit:', specunitout, delim, 'Time unit:', 'Not Implemented','\n'   
        ##return ''.join(outline)+self.df.__repr__()
        #return self._deepcopy(self.df.__repr__()

 
    @property
    def ix(self):    
        return self._deepcopy(self.df.ix)
    
    ### Operator overloading ####
    ### In place operations need to overwrite self.df
    def __add__(self, x):
        return self._deepcopy(self.df.__add__(x))

    def __sub__(self, x):
        return self._deepcopy(self.df.__sub__(x))

    def __mul__(self, x):
        return self._deepcopy(self.df.__mul__(x))

    def __div__(self, x):
        return self._deepcopy(self.df.__div__(x))

    def __truediv__(self, x):
        return self._deepcopy(self.df.__truediv__(x))

    ### From what I can tell, __pos__(), __abs__() builtin to df, just __neg__()    
    def __neg__(self):  
        return self._deepcopy(self.df.__neg__() )

    ### Object comparison operators
    def __lt__(self, x):
        return self._deepcopy(self.df.__lt__(x))

    def __le__(self, x):
        return self._deepcopy(self.df.__le__(x))

    def __eq__(self, x):
        return self._deepcopy(self.df.__eq__(x))

    def __ne__(self, x):
        return self._deepcopy(self.df.__ne__(x))

    def __ge__(self, x):
        return self._deepcopy(self.df.__ge__(x))

    def __gt__(self, x):
        return self._deepcopy(self.df.__gt__(x))     


    ### DataFrame __x__ method ovewrites.  Prevents TimeSpectra
    ### from calling these from python object
    def __len__(self):
        return self.df.__len__()

    def __nonzero__(self):
        return self.df.__nonzero__()

    def __contains__(self, x):
        return self.df.__contains__(x)

    def __iter__(self):
        return self.df.__iter__()

    def _baseline_valid(self, ref, force_series=True):
        ''' Helper method for to handles various scenarios of valid references.  Eg user wants to 
        convert the spectral representation, this evaluates manually passed ref vs. internally stored one.

        **force_seires - If true, program will convert if user explictly passing a non-series iterable.
        
        This goes through several cases to determine baseline.  In order, it attempts to get the baseline from:
            1. Column name from dataframe.
            2. Column index from dataframe.
            3. Uses ref itself.
               a. If series, checks for compatibility between spectral indicies.
               b. If dataframe, ensures proper index and shape (1-d) and converts to series (if force_series True).
               c. If iterable, converts to series (if force_series True)
               
        Errors will be thrown if new baseline does not have identical spectral values to self.df.index as evaluated by
        numpy.array_equal()

        Returns baseline. '''
        
        
        if isinstance(ref, NoneType):
            return ref

        ### First, try ref is itself a column name
        try:
            rout=self.df[ref]
        except (KeyError, ValueError):  #Value error if ref itself is a dataframe
            pass

        ### If rtemp is an integer, return that column value.  
        ### NOTE: IF COLUMN NAMES ARE ALSO INTEGERS, THIS CAN BE PROBLEMATIC.
        if isinstance(ref, int):
            rout=self.df[self.df.columns[ref]]        

        ### Finally if ref is itself a series, make sure it has the correct spectral index
        elif isinstance(ref, Series):
            if array_equal(ref.index, self.df.index) == False:
                raise BaselineError(ref.index, self)
            else:
                rout=ref
            
        ### Finally if array or other iterable, force to a series
        else:
            if force_series:
                
                ### If user passes dataframe, downconvert to series 
                if isinstance(ref, DataFrame):
                    if ref.shape[1] != 1:
                        raise TypeError('Baseline must be a dataframe of a single column with index values equivalent to those of %s'%self.name)
                    if ref.index.all() != self.df.index.all():
                        raise BaselineError(ref, self)                    
                    else:
                        rout=Series(ref[ref.columns[0]], index=ref.index) 
   
                ### Add index to current iterable 
                else:
                    if len(ref) != len(self.df.index):
                        raise BaselineError(ref, self)
                    else:
                        rout=Series(ref, index=self.df.index)

            ### Return itrable as is
            else:
                rout=ref

        return rout  #MAKES MORE SENSE TO MAKE THIS A 1D DATAFRAME


#### TESTING ###
if __name__ == '__main__':

    ### Be careful when generating test data from Pandas Index/DataFrame objects, as this module has overwritten their defaul behavior
    ### best to generate them in other modules and import them to simulate realisitc usec ase

    spec=SpecIndex([400.,500.,600.])
    ts=TimeSpectra(abs(randn(3,3)), columns=testdates, index=spec, specunit='k', timeunit='s', baseline=[1.,2.,3.])    
    ts.iunit='t'
    x=ts.as_iunit('a')
    #ts.as_interval()
    #spec_surface3d(ts)  ##Not working because of axis format problem
    #plt.show()
#    ts.rank(use_base=True)
    x=ts.dumps()
    ts=ts_loads(x)
    print 'hi'
