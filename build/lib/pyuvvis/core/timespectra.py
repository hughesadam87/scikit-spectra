import string
from types import NoneType, MethodType
from operator import itemgetter

### PUT THIS IN PANDAS UTILS AND UPATE PACKAGE
from pyuvvis.pandas_utils.metadframe import MetaDataframe, mload, mloads

## LOCAL VERSION OF METADATAFRAME
import sys
#sys.path.append("../pandas_utils")
#from metadframe import MetaDataframe, mload, mloads

#sys.path.append("../pyplots")
#from basic_plots import specplot, absplot, timeplot, range_timeplot

from pandas import DataFrame, DatetimeIndex, Index, Series
from numpy import array_equal

### Absolute pyuvvis imports (DON'T USE RELATIVE IMPORTS)
from pyuvvis.core.specindex import SpecIndex, specunits, get_spec_category
from pyuvvis.core.spec_labeltools import datetime_convert, from_T, to_T, Idic, intvl_dic
from pyuvvis.core.utilities import divby, df_wavelength_slices
from pyuvvis.pyplots.advanced_plots import spec_surface3d
from pyuvvis.custom_errors import badkey_check, null_attributes


## testing (DELETE)
from pandas import date_range
from numpy.random import randn
import matplotlib.pyplot as plt

from pandas import read_csv as df_read_csv

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
def _valid_xunit(value, dic):
    ''' Validates existence of key (usually a unit type like spectral unit in a dictionary such as specunits)'''
    if value == None:
        return None
    else:
        badkey_check(value, dic.keys())
        return value.lower()    
              

def _valid_iunit(sout):
    '''When user is switching spectral intensity units, make sure they do it write.'''
    return _valid_xunit(sout, Idic)

def _valid_intvlunit(sout):
    ''' Validate interval unit.'''
    return _valid_xunit(sout, intvl_dic)

        
def _as_interval(timespectra, unit):#, unit=None):
    ''' Return columns as intervals as computed by datetime_convert function.  Not an instance method
    for calls from objects other than self.'''
    
    ### If current columns is DatetimeIndex, convert
    if timespectra._interval==False:
        return Index(datetime_convert(timespectra.columns, return_as=unit, cumsum=True))#, unit=unit)              

    ### If currently already intervals, convert to datetime, then convert that to new units
    else:
        newcols=_as_datetime(timespectra) #Convert to new unit
        return Index(datetime_convert(newcols, return_as=unit, cumsum=True))#, unit=unit)      

### Time interval computations ###
def _as_datetime(timespectra, periods=None):
    ''' Return datetimeindex given a timespectra object.  Queries the _stop, _start, _freq attributes
        to generate the datetime index.
    
        Parameters
        ----------
        timespectra : TimeSpectra object from which to sample _stop, _start and _freq.
        
        periods: If passed, datetimeindex will be generate from _stop, _periods, _freq.  This is
                 only useful in certain cases such as in the __init__ of TS if a user decides to
                 construct from periods.  In any case, _stop is still stored internally.
    '''

    ### Make sure all attributes are set before converting
    null_attributes(timespectra, '_as_datetime', '_start','_freq')  #Essentially a gate that requires _start, _freq to pass
    
    if periods:
        return DatetimeIndex(start=timespectra._start, periods=timespectra._periods, freq=timespectra._freq)        

    else:      
        null_attributes(timespectra, '_as_datetime', '_stop')
        return DatetimeIndex(start=timespectra._start, end=timespectra._stop, freq=timespectra._freq)

        

##########################################
## TimeSpectra Public Utilities    #######
########################################## 
### Wrapper for df_from_directory
def spec_from_dir(directory, csvargs, sortnames=False, concat_axis=1, shortname=True, cut_extension=False):
    ''' Takes files from a directory, presuming they are identically formatted, and reads them into
    a dataframe by iterating over read_csv().  All arguments that read_csv() would take are passed
    in.  These kwargs are in regard the files themselves, for example, skiprows, skipfooter and header.
        
    For now, no support for glob to take only files of a certain file extension.
    For now, conctaentation occurs along

    Args:
       directory- Path to directory where files are stored.
       csvargs- Dictionary of arguments that are passed directly to the read_csv() function. For example
                skiprows, header, na_values etc... see pandas API for read_csv()
        
    Kwds:
       sortnames- Will attempt to autosort the filelist. Otherwise, files are ordered by the module
                  os.path.listdir().
                  
       concat_axis- How to merge datafiles into a dataframe.  Default is axis=1, which means all files 
                    should share the same index values.  I use this for spectral data where the wavelength
                    column is my dataframe index.
                  
       shortname- If false, full file path is used as the column name.  If true, only the filename is used. 
       
       cut_extension- If kwd shortname is True, this will determine if the file extension is saved or cut from the data.'''
    
    return TimeSpectra(df_from_directory(directory, csvargs, sortnames=sortnames, concat_axis=concat_axis, shortname=shortname, cut_extension=cut_extension))


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
        baseline=dfkwargs.pop('baseline', None)
        
        
        ### NEED TO WORK OUT LOGIC OF THIS INITIALIZATION?
        ### Should I even do anything?
        self._intervalunit=dfkwargs.pop('intvlunit', None)        

        if stop and periods:
            # date_range will throw its own error for this, but I prefer to catch it before it happens            
            raise AttributeError('TimeSpectra cannot be initialized with both periods and stop; please choose one or the other.')

        super(TimeSpectra, self).__init__(*dfargs, **dfkwargs)        

        ### If user passes non datetime index to columns, make sure they didn't accidentally pass SpecIndex by mistake.
        if not isinstance(self._df.columns, DatetimeIndex):
            try:
                if self._df.columns._kind == 'spectral':
                    raise IOError("SpecIndex must be passed as index, not columns.")   ### Can't be an attribute error or next won't be raised             

            ### df.columns has no attribute _kind, meaning it is likely a normal pandas index        
            except AttributeError:
                self._interval=None
                self._start=start
                self._stop=stop
                self._freq=freq

                ### If enough keywords passed, convert to a datetime index at initialization
                if start and freq:
                    if stop:
                        self.to_datetime()                      
                     
                    ### If initialized with periods representation    
                    elif periods:
                        self._df.columns=_as_datetime(self, periods=periods)
                        self._stop=self._df.columns[-1]
                        self._interval=False
                                                   

        ### If DateimIndex already, store attributes directly from array
        else:
            self._interval=False        
            self._start=self._df.columns[0]
            self._stop=self._df.columns[-1]
            self._freq=self._df.columns.freq
            
      
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
        ''' Intensity units of dateframe.  Eg %Transmittance vs. Absorbance'''
        self._list_out(Idic, delim=delim)

    ### Self necessary here or additional df stuff gets printed   
    def list_sunits(self, delim='\t'):
        ''' Print out all available units in a nice format'''
        self._list_out(specunits, delim=delim)         

    def list_intvlunits(self, delim='\t'):
        ''' Print out all possible units to express the columns in 
            interval or referenced notation (eg to=0)'''
        self._list_out(intvl_dic, delim=delim)
        
    def label_stats(self, delim='    '):
        ''' Formatted output of various quantities pertinent to columns/rows of timespectra.  For more
        comprehensive object output, please refert to list_attr() method.'''
        
        ### Human-readable form of self._interval
        tstatsdic={True:'Datetime', False:'Interval/Referenced', None:'Unknown'}
        tstyle=tstatsdic[self._interval]
        
        print '\nTemporal/Columns stats'
        print '-----------------------\n'
        print '%sTime Display Style: %s\n'%(delim, tstyle)
        print '%sDatetimeindex parameters:'%(delim)
        print '%s%sstart=%s, stop=%s, freq=%s\n'%(delim, delim, self._start, self._stop, self._freq)
        print '%sTimeinterval parameters:'%(delim)
        print '%s%sintvlunit=%s\n'%(delim, delim, self.intvlunit)

            
        print '\nSpectral/Index stats'
        print '---------------------\n'
        print '%sspectral category=%s, specunit=%s'%(delim, get_spec_category(self.specunit), self.specunit)
        
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
            filterout=['_intrinsic', 'ix', '_ix', 'list_attr']
            for att in filterout:
                atts.remove(att)
        
        ### Include dataframe attributes if desired
        if dfattr==True:
            atts=atts+[x for x in dir(self._df) if '__' not in x]
        
        ### Remove methods if desired
        if methods==False:
            atts=[attr for attr in atts if isinstance(getattr(self, attr), MethodType) != True]
        else:
            atts.append('ix') #This will
 
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
    
    def wavelength_slices(self, ranges, apply_fcn='mean', **applyfcn_kwds):
        '''Returns sliced averages/sums of wavelength regions. Composite dataframe will nicely
        plot when piped into spec aesthetics timeplot.
        
        
        Parameters:
        -----------
        
            apply_fcn: Chooses the way to collapse data.  Builtin functions include 'mean'
                     'sum', 'simps', 'trapz', 'romb', 'cumtrapz', but any user function that
                     results in collapsed data (eg averging function/integrators/etc...) can 
                     be passed in with any relevant keywords.
                
            
         **apply_fcn_kdws: 
             If user is passing a function to apply_fcn that requires keywords, the get passed in to dfcut.apply() 
          
        Notes
        -----
            See description of 'df_wavelength_slices' in utilities.py for more information. 
            
            WHEN PLOTTING, PLOT THE TRANSPOSE OF THE RETURNED DF.  '''   
        return self._transfer(df_wavelength_slices(self._df, ranges=ranges, apply_fcn=apply_fcn, **applyfcn_kwds))
    
    def area(self, apply_fcn='simps'):
        ''' Returns total area under the spectra vs. time curve.  To choose a slice of the spectrum,
            call wavelength_slices with appropriate ranges and an apply_fcn appropriate to style of integration.
        
        Parameters
        ----------
           apply_fcn: Integration method-'simps', 'trapz', 'romb', 'cumtrapz'

        Notes
        -----
           This is a wrapper for wavelength_sclices, and as such, user can actually pass any function into the apply_fcn. 
           Besides mean/sum which is understands already, one could, for example, pass a euler integration function and
           it should work. 
           
           WHEN PLOTTING, PLOT THE TRANSPOSE OF THE RETURNED DF.
        '''
        return ts.wavelength_slices(ranges=(min(self.index), max(self.index)), apply_fcn=apply_fcn)
       
        
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
    
    ### Temporal/column related functionality
    def set_daterange(*date_range_args):
        ''' Wrapper around pandas.date_range to reset the column
        values on of the data on the fly. See pandas.date_range()
        for use.  In brief:
        
        Parameters
        ----------
           start: time start.  
           freq: Frequency unit
           stop/periods: specifies endpoint given start and freq.
           
        Example
        -------
            timespectra.set_daterange('1/1/2012', period=5, freq='H')
        '''
        
        rng=date_range(*date_range_args)
        self._df.columns=rng
        self._start=rng[0]
        self._stop=rng[1]
        self._freq=rng.freq
        self._intervals=False
    
    @property 
    def freq(self):
        return self._freq
    
    @freq.setter
    def freq(self, unit):
        ''' Freq cannot be set.  This will raise same error as setting datetimeindex.'''
        raise AttributeError('"freq" attribute cannot be set.  Please use set_daterange() \
                               to overwrite current timespectra index.')
    
    @property
    def intvlunit(self):
        return self._intervalunit    
    
    @intvlunit.setter
    def intvlunit(self, unit):
        ''' If _df in interval mode, convert it.  Otherwise just store attributes.'''
        if unit==None:
            unit='intvl'
            print 'Defaulting intvlunit to "intvl"'
            
        if self._interval==True:
            self.to_interval(unit)                
        else:
            self._intervalunit=_valid_intvlunit(unit)
            
    @property
    def full_intvlunit(self):
        if not self._intervalunit:
            return None
        else:
            return intvl_dic[self._intervalunit]
            
    @property
    def timeunit(self):
        ''' Quick reference to current state of time labels.  For comprehensive output, try ts.label_stats()'''
        if self._interval==True:
            return self.intvlunit
        elif self._interval==False:
            return 'Timestamp'
        elif self._interval==None:
            return 'Unknown'
    
    @property
    def timetypes(self):
        return tunits
    
    def to_datetime(self):
        ''' Set columns to DatetimeIndex.  
        
        Notes
        -----
            self._interval can be None, True or False.  This will call _as_datetime() if it's None or True 
            and if not all appropriate attributes are found, an error will be raised.
        '''
        if self._interval != False:       
            self._df.columns=_as_datetime(self)
            self._interval=False
          

    def to_interval(self, unit=None):  
        ''' Set columns to interval as computed by datetime_convert function. '''
        
        ### User calls function with empty call (), if proper attributes, convert it
        if unit==None: 
            null_attributes(self, 'to_interval', '_start', '_stop', '_freq')            
            if self._intervalunit != None:
                unit=self._intervalunit
            else:
                unit='intvl'  #Default if user has not set anything in _intervalunit
                
        ### User calls function with unit
        else:
            unit=_valid_intvlunit(unit)          
            
            ### If _df already interval
            if self._interval==True:
                if unit==self._intervalunit:
                    return         
                    
            
            ### If interval is None or False, do the conversion
            elif self._interval==None:
                ### Make sure proper attributes to get back ater in place
                null_attributes(self, 'to_interval', '_start', '_stop', '_freq')
                
        self._df.columns=_as_interval(self, unit)
        self._interval=True    
        self._intervalunit=unit
        
    def as_interval(self, unit=None):
        ''' Return copy of TimeSpectra as interval.'''
        if isinstance(unit, basestring):
            if unit.lower() in ['none', 'full']:
                unit=None

        tsout=self.deepcopy()        
        tsout.to_interval(unit)
        return tsout        
            

    def as_datetime(self):
        ''' Return copy of TimeSpectra as datetime.'''
        tsout=self.deepcopy()
        tsout.to_datetime()
        return tsout
            
    
    

    ### Spectral Intensity related attributes/conversions
    @property
    def full_iunit(self):
        return Idic[self._itype]
    
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
        return Idic
        
                
    def _dfgetattr(self, attr, *fcnargs, **fcnkwargs):
        ''' This is overwritten from MetaDataframe to account for the use_base option.'''

        use_base=fcnkwargs.pop('use_base', False)
 
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
            
            tsout=self._transfer(out)
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
    
        
    def to_csv(self, path_or_buff, meta_separate=False, **csv_kwargs):
        ''' Output to CSV file.  
        
            Parameters:
            ----------
               path_or_buff: string path to outfile destination.
               
               meta_separate: 
                   If None: metadata is lost and self._df.to_csv(**csv_kwargs) is called.
                   If False: metadata is serialized and output at taile file the path_or_buff file.
                   If True: metadata is added to it's own file named path_or_buff.mdf
                       
               csv_kwargs: csv formatting arguments passed directoy to self._df.to_csv()
               
            Notes:
            ------
               MetaData is gotten from self.__dict__.
               In future, may opt to implement the option to choose the meta_separate filename if 
               output is separated (eg meta_separate=True)
                   
        '''
        
        meta=cPickle.dumps(self.__dict__)
        self._df.to_csv(path_or_buff, **csv_kwargs)
        if meta_separate == None:
            return
        elif meta_separate == True:
            raise NotImplemented('Not yet implemented this style of csv output')
        elif meta_separate==False:
            o=open(path_or_buff, 'a') #'w'?#
            o.write(meta)
            o.close()
                   
    #################
    ### CSV Output###
    #################
                   
    def from_csv(path_or_buff, meta_separate=False, **csv_kwargs):
        ''' Read from CSV file.
        
            Parameters:
            ----------
               path_or_buff: string path to infile destination.
               
               meta_separate: 
                   If None: metadata is lost and self._df.to_csv(**csv_kwargs) is called.
                   If False: metadata is serialized and output at taile file the path_or_buff file.
                   If True: metadata is added to it's own file named path_or_buff.mdf
                       
               csv_kwargs: csv formatting arguments passed directoy to self._df.to_csv()
               
            Notes:
            ------
               MetaData is gotten from self.__dict__.
               In future, may opt to implement the option to choose the meta_separate filename if 
               output is separated (eg meta_separate=True)
               
               
            Returns: TimeSpectra
                 '''
        if meta_separate == None:
            return TimeSpectra(read_csv(path_or_buff, **csv_kwargs))

        elif meta_separate == False:
            fileHandle = open(path_or_buff, 'r')
            lineList = fileHandle.readlines()
            fileHandle.close()
            meta=cPickle.loads(lineList[-1])        
            ### This could be buggy if __init__() from all the keywords is working correctly.
            
            ### Make sure user skips last line in file that was added in addition via meta_sepaarte
            csv_kwargs['skip_footer']=csv_kwargs.pop('skip_footer', 0) + 1
            df=df_read_csv(path_or_buff, **csv_kwargs)
            
            ### This is hard part, how to set meta data
        
        elif meta_separate == True:
            raise NotImplementedError("Haven't resolved, but this hsould return meta and df")
        
        ### Initialize timespectra from meta.  Is this how I want to do it?
        ts=TimeSpectra(df, **meta) 
        

#### TESTING ###
if __name__ == '__main__':

    ### Be careful when generating test data from Pandas Index/DataFrame objects, as this module has overwritten their defaul behavior
    ### best to generate them in other modules and import them to simulate realisitc usec ase

    spec=SpecIndex([400.,500.,600.])
    testdates=date_range(start='3/3/12',periods=3,freq='h')
    testdates2=date_range(start='3/3/12',periods=3,freq='45s')
    
    ts=TimeSpectra(abs(randn(3,3)), columns=testdates, index=spec, baseline=[1.,2.,3.])  
    t2=TimeSpectra(abs(randn(3,3)), columns=testdates2, index=spec, baseline=[1.,2.,3.])    
    
    ts.iunit='a'
    
    ts.to_interval()
    ts._stop=None    
    ts._freq=None
    ts._start=None
    ts.to_datetime()

    ts.to_csv('junk')
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
