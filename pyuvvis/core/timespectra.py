from types import NoneType, MethodType
from operator import itemgetter
import string

### PUT THIS IN PANDAS UTILS AND UPATE PACKAGE
from pyuvvis.pandas_utils.metadframe import MetaDataframe, mload, mloads

## LOCAL VERSION OF METADATAFRAME
import sys
sys.path.append("../pandas_utils")
#from metadframe import MetaDataframe, mload, mloads

sys.path.append("../pyplots")
from basic_plots import specplot, absplot, timeplot, range_timeplot

from pandas import DataFrame, DatetimeIndex, Index, Series
from numpy import array_equal

### Absolute pyuvvis imports (DON'T USE RELATIVE IMPORTS)
from pyuvvis.core.specindex import SpecIndex, specunits
from pyuvvis.core.spec_labeltools import datetime_convert
from pyuvvis.core.spec_labeltools import from_T, to_T, Tdic
from pyuvvis.core.spec_utilities import divby
from pyuvvis.pyplots.advanced_plots import spec_surface3d
from pyuvvis.custom_errors import badkey_check


## testing (DELETE)
from pandas import date_range
from numpy.random import randn
import matplotlib.pyplot as plt


tunits={'ns':'nanoseconds', 'us':'microseconds', 'ms':'milliseconds', 's':'seconds', 
        'm':'minutes', 'h':'hours','d':'days', 'y':'years'}  #ADD NULL VALUE? Like None:'No Time Unit' (iunit/specunit do it)


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


##########################################
## TimeSpectra Private Utilities   #######
##########################################

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
    if timespectra._stop:
        timespectra._df.columns=DatetimeIndex(start=timespectra._start, end=timespectra._stop, freq=timespectra._freq)
    else:
        timespectra._df.columns=DatetimeIndex(start=timespectra._start, periods=timespectra._periods, freq=timespectra._freq)
        

##########################################
## TimeSpectra Public Utilities    #######
########################################## 


class TimeSpectra(MetaDataframe):
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

        super(TimeSpectra, self).__init__(*dfargs, **dfkwargs)        

        ### If user passes non datetime index to columns, make sure they didn't accidetnally pass SpecIndex by mistake.
        if not isinstance(self._df.columns, DatetimeIndex):
            try:
                if self._df.columns._kind == 'spectral':
                    raise IOError("SpecIndex must be passed as index, not columns.")   ### Can't be an attribute error or next won't be raised             

            ### df.columns has no attribute _kind, meaning it is likely a normal pandas index        
            except AttributeError:
                self._interval=True
                self._start=start
                self._stop=stop
                self._freq=freq
                self._timeunit=timeunit  #Private for property attribute compatibility
                

        ### Take Datetime info and use to recreate the array
        else:
            self._interval=False        
            self._start=self._df.columns[0]
            self._stop=self._df.columns[-1]
            self._freq=self._df.columns.freq
            self._timeunit=timeunit  #Obtain from df somehow
            

            ### ADD TRANSLATION FOR FREQ--> basetimeuint MAKE IT A PROPERTY? BUT ADD INTIIALIZTION SHIT
#       self._timeunit=get_time_from_freq(df.columns.freq)
      


        ### Have to do it here instead of defaulting on instantiation.
        self._df._tkind='temporal'

        ### Assign spectral intensity related stuff but 
        ### DONT CALL _set_itype function
        iunit=_valid_iunit(iunit)
        self._itype=iunit
        
        ### This has to be done AFTER self._df has been set
        self._baseline=self._baseline_valid(baseline)#SHOULD DEFAULT TO NONE SO USER CAN PASS NORMALIZED DATA WITHOUT REF        

        ###Set Index as spectral variables, take care of 4 cases of initialization.
        if not hasattr(self._df.index, '_convert_spectra'):  #Better to find method than index.unit attribute
            # No index, no specunit
            if specunit == None:
                self.specunit=None
            # No index, specunit
            else:
                self.specunit=specunit   #Property setter will do validation         
    
            
        else:
            # Index, no specunit
            if specunit == None:
                self.specunit=self._df.index.unit
                
            # Index, specunit---> Convert down
            else:
                old_unit=self._df.index.unit
                self.specunit=specunit 
                if old_unit != specunit:
                    print 'Alert: SpecIndex unit was changed internally from "%s" to "%s"'%(old_unit, specunit)
                
        
        ###Store intrinsic attributes for output later by listattr methods
        self._intrinsic=self.__dict__.keys()
        self._intrinsic.remove('name') #Not a private attr
        

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
        self._df.columns=_as_datetime(self)
        self._tkind='temporal'    
        self._interval=False


    def as_interval(self, unit='interval'):  
        ''' Return columns as intervals as computed by datetime_convert function'''
        self._df.columns=_as_interval(self, unit)
        self._tkind='temporal'
        self._interval=True    


    @property
    def data(self):
        ''' Instead of directly accessing self._df.'''
        return self.as_dataframe()

    ###############################
    ### Baseline related operations
    ###############################
    
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
               
        Errors will be thrown if new baseline does not have identical spectral values to self._df.index as evaluated by
        numpy.array_equal()

        Returns baseline. '''
        
        
        if isinstance(ref, NoneType):
            return ref

        ### First, try ref is itself a column name
        try:
            rout=self._df[ref]
        except (KeyError, ValueError):  #Value error if ref itself is a dataframe
            pass

        ### If rtemp is an integer, return that column value.  
        ### NOTE: IF COLUMN NAMES ARE ALSO INTEGERS, THIS CAN BE PROBLEMATIC.
        if isinstance(ref, int):
            rout=self._df[self._df.columns[ref]]        

        ### Finally if ref is itself a series, make sure it has the correct spectral index
        elif isinstance(ref, Series):
            if array_equal(ref.index, self._df.index) == False:
                raise BaselineError(ref.index, self)
            else:
                rout=ref
            
        ### Finally if array or other iterable, force to a series
        else:
            if force_series:
                
                ### If user passes dataframe, downconvert to series 
                if isinstance(ref, DataFrame):
                    if ref.shape[1] != 1:
                        raise TypeError('Baseline must be a dataframe of a single column with index values equivalent to those of %s'%self._name)
                    if ref.index.all() != self._df.index.all():
                        raise BaselineError(ref, self)                    
                    else:
                        rout=Series(ref[ref.columns[0]], index=ref.index) 
   
                ### Add index to current iterable 
                else:
                    if len(ref) != len(self._df.index):
                        raise BaselineError(ref, self)
                    else:
                        rout=Series(ref, index=self._df.index)

            ### Return itrable as is
            else:
                rout=ref

        return rout  #MAKES MORE SENSE TO MAKE THIS A 1D DATAFRAME
       
        
    ### Spectral column attributes/properties
    @property
    def specunit(self):
        return self._df.index.unit    #Short name key

    @property
    def full_specunit(self):
        return specunits[self._df.index.unit]

    @specunit.setter
    def specunit(self, unit):
        self._df.index=self._df.index._convert_spectra(unit) 
        
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
    def timeunit(self):
        return self._timeunit
    
    @timeunit.setter
    def timeunit(self, unit):
        #Do checks and validation here!
        self._timeunit=unit
        
    @property
    def full_timeunit(self):
        ### ACTUALLY MAKE THIS WORK
        return 'full unit'+self.timeunit
    
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
        df=self._df #for convienence/back compatibility

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
        self._df=df    

    @property
    def itypes(self):
        return Tdic
        
    ### ADD PYTHON STRING FORMATTING TO THIS
    def list_attr(self, classattr=False, dfattr=False, methods=False, types=False, delim='\t', sortby='name'): #values=False,):
        ''' 
        IF VALUES FIELD IS ADDED, HAVE TO CHANGE HOW SORTING IS DONW, HOW ATTS IS MADE AND ALSO OUTPUT!
        Prints out all the custom attributes that are not builtin attributes of the timespectra.  Should this be 
        in utils as a gneeral function?  Seems kind of useful.'''

        ### Take all attributes in current instance        
        atts=[x for x in dir(self) if '__' not in x]

        ### Remove self._intrinsic (aka class attributes) if desired
        if classattr==False:
            atts=[attr for attr in atts if attr not in self._intrinsic]        
            atts.remove('_intrinsic') 
            atts.remove('list_attr')
        
        ### Include dataframe attributes if desired
        if dfattr==True:
            atts=atts+[x for x in dir(self._df) if '__' not in x]
        
        ### Remove methods if desired
        if methods==False:
            atts=[attr for attr in atts if isinstance(getattr(self, attr), MethodType) != True]
 
        ### Should output include types and/or values?
        outheader=['Attribute']
        if types==True: 
            outheader=outheader+['Type']
            atts=[(att, str(type(getattr(self, att))).split()[1].split('>')[0] ) for att in atts]
            #string operation just does str(<type 'int'>) ---> 'int'
            

            ### Sort output either by name or type
            badkey_check(sortby, ['name', 'type']) #sortby must be 'name' or 'type'
            
            if sortby=='name':
                atts=sorted(atts, key=itemgetter(0))
            elif sortby=='type':
                atts=sorted(atts, key=itemgetter(1))

        ### Output to screen
        print delim.join(outheader)    
        print '--------------------'
        for att in atts:
            if types==True:
                print string.rjust(delim.join(att), 7) #MAKE '\N' comprehension if string format never works out
            else:
                print att
        
       
    def _dfgetattr(self, attr, use_base=False, *fcnargs, **fcnkwargs):
        ''' This is overwritten from MetaDataframe to account for the use_base option.'''
 
        out=getattr(self._df, attr)(*fcnargs, **fcnkwargs)
        
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
        
    ### OVERWRITE METADATFRAME MAGIC METHODS
    def __union__(self):
        ''' Add some header and spectral data information to the standard output of the dataframe.
        Just ads a bit of extra data to the dataframe on printout.  This is called by __repr__, which 
        can either return unicode or bytes.  This is better than overwriting __repr__()'''
        delim='\t'
        if self.specunit==None:
            specunitout='None'
        else:
            specunitout=self.full_specunit

        outline='**',self._name,'**', delim, 'Spectral unit:', specunitout, delim, 'Time unit:', 'Not Implemented','\n'   
        return ''.join(outline)+'\n'+self._df.__union__()    
    
        

#### TESTING ###
if __name__ == '__main__':

    ### Be careful when generating test data from Pandas Index/DataFrame objects, as this module has overwritten their defaul behavior
    ### best to generate them in other modules and import them to simulate realisitc usec ase

    spec=SpecIndex([400.,500.,600.])
    testdates=date_range(start='3/3/12',periods=3,freq='h')
    
    ts=TimeSpectra(abs(randn(3,3)), columns=testdates, index=spec, timeunit='s', baseline=[1.,2.,3.])    
    range_timeplot(ts)

    ts.a=50; ts.b='as'
    ts.iunit='t'

    ts.list_attr(dfattr=False, methods=False, types=True)    
    ts.as_iunit('a')
    x=ts.as_iunit('a')
    #ts.as_interval()
    #spec_surface3d(ts)  ##Not working because of axis format problem
    #plt.show()
#    ts.rank(use_base=True)
    x=ts.dumps()
    ts=mloads(x)

