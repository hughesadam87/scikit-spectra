'''Provides core "TimeSpectra" class and associated utilities.'''

import string
import cPickle
import logging
from types import NoneType, MethodType
from operator import itemgetter

import numpy as np
from pandas import DataFrame, DatetimeIndex, Index, Series, date_range
from scipy import integrate
#from scikits.learn import PCA
from pca_scikit import PCA

from pyuvvis.pandas_utils.metadframe import MetaDataFrame, _MetaIndexer
from pyuvvis.logger import log, configure_logger, decode_lvl, logclass

from pandas import DataFrame, DatetimeIndex, Index, Series
from scipy import integrate
#from scikits.learn import PCA
from pca_scikit import PCA

# pyuvvis imports 
from pyuvvis.core.specindex import SpecIndex, specunits, get_spec_category, \
     set_sindex
from pyuvvis.core.spec_labeltools import datetime_convert, from_T, to_T, \
    Idic, intvl_dic, spec_slice
from pyuvvis.core.utilities import divby, boxcar, maxmin_xy
from pyuvvis.pyplots.advanced_plots import spec_surface3d

# Merge
from pyuvvis.exceptions import badkey_check, badcount_error, RefError, BaselineError

# Put in a separte file of constants?
tunits={'ns':'Nanoseconds', 'us':'Microseconds', 'ms':'Milliseconds', 's':'Seconds', 
        'm':'Minutes', 'h':'Hours','d':'Days', 'y':'Years'}  #ADD NULL VALUE? Like None:'No Time Unit' (iunit/specunit do this)

logger = logging.getLogger(__name__) 
   
##########################################
## TimeSpectra Private Utilities   #######
##########################################
_dtmissing='Cannot convert representations without interally stored datetimeindex.'

# Unit validations###
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

              
##########################################
## TimeSpectra Public Utilities    #######
######################################## 

def array_truthtest(array, raiseerror=False, errorstring=None):
    ''' Truth test array/series attributes, since can't evaluate them with standard python.'''

    # If error passed, automatically enable error raising
    if errorstring:
        raiseerror=True

    # Evaluates to true or false
    try:
        return array.any()
    # Evaluates to None
    except AttributeError as atterror:
        
        # Throw custom error or standard error
        if raiseerror:
            if errorstring:
                raise(AttributeError(errorstring))
            else:
                raise(atterror)
        # Return None
        return None


# Wrapper for df_from_directory
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


@logclass(log_name=__name__, skip = ['wraps','_dfgetattr', '_comment', '_transfer'])
class TimeSpectra(MetaDataFrame):
    ''' Provides core TimeSpectra composite pandas DataFrame to represent a set of spectral data.  Enforces spectral data 
    along the index and temporal data as columns.  The spectral index is controlled from the specindex
    module, which has a psuedo-class called SpecIndex (really a monkey patched Index).  Temporal data is stored using a DatetimeIndex or
    a modified interval reprentation.  The need to support two types of temporal index, one of which is Pandas builtin DatetimeIndex is what led me
    to not create a special index object (like SpecIndex).  Other spectral axis types (like Temperature axis) should probably be built close to the manner of 
    Spec index.  The TimeSpectra dataframe actually stores enough temporal metadatato go back an forth between DatetimeIndex and
    Interval representations.  It does this by generating one or the other on the fly, and never relies on the current label object to generate teh next object.'''

    def __init__(self, *dfargs, **dfkwargs):
        # Pop default DataFrame keywords before initializing###
        self.name = str(dfkwargs.pop('name', ''))
        
        # Spectral index-related keywords
        specunit = dfkwargs.pop('specunit', None)

        # Intensity data-related stuff
        iunit = dfkwargs.pop('iunit', None)

        # Time index-related keywords  (note, the are only used if a DatetimeIndex is not passed in)
        reference = dfkwargs.pop('reference', None)        
        bline = dfkwargs.pop('baseline', None)
        
        # Logging __init__() in @logclass can't access self.name
        logger.info('Initializing %s' %  '%s:(name = %s)' % 
                    (self.__class__.__name__, self.name))

        
        # NEED TO WORK OUT LOGIC OF THIS INITIALIZATION?
        # Should I even do anything?
        self._intervalunit=dfkwargs.pop('intvlunit', None)        

        super(TimeSpectra, self).__init__(*dfargs, **dfkwargs)        

        # If user passes non datetime index to columns, make sure they didn't accidentally pass SpecIndex by mistake.
        if not isinstance(self._df.columns, DatetimeIndex):
            try:
                if self._df.columns._kind == 'spectral':
                    raise IOError("SpecIndex must be passed as index, not columns.")   # Can't be an attribute error or next won't be raised             

            # df.columns has no attribute _kind, meaning it is likely a normal pandas index        
            except AttributeError:
                self._interval=None                                                  

        # If DateimIndex already, store attributes directly from array
        else:
            self._interval=False      
            self._dtindex=self._df.columns
      
        # Assign spectral intensity related stuff but 
        # DONT CALL _set_itype function
        iunit=_valid_iunit(iunit)
        self._itype=iunit
        
        # This has to be done AFTER self._df has been set
        self._reference=self._reference_valid(reference)#SHOULD DEFAULT TO NONE SO USER CAN PASS NORMALIZED DATA WITHOUT REF        

        ###Set Index as spectral variables, take care of 4 cases of initialization.
        if not hasattr(self._df.index, '_convert_spectra'):  #Better to find method than index.unit attribute
            # No index, no specunit
            if specunit == None:
                self.specunit = None
            # No index, specunit
            else:
                self.specunit = specunit   #Property setter will do validation         
    
        else:
            # Index, no specunit
            if specunit == None:
                self.specunit = self._df.index.unit
                
            # Index, specunit---> Convert down
            else:
                old_unit=self._df.index.unit
                self.specunit=specunit 
                if old_unit != specunit:
                    logger.warn('SpecIndex unit was changed internally from '
                                  '"%s" to "%s"'%(old_unit, specunit))
                
        # Baseline Initialization (UNTESTED)
        self._base_sub = False 
        self._baseline = None  
        
        if not isinstance(bline, NoneType):
            self.baseline = bline
        
               
        # Store intrinsic attributes for output later by listattr methods
        self._intrinsic=self.__dict__.keys()
        self._intrinsic.remove('name') #Not a private attr
        
        # Which attributes/methods are manipulated along with the dataframe
        self._cnsvdattr=['_reference', '_baseline']
        self._cnsvdmeth=['_slice', 'boxcar'] #_slice is ix


    def _comment(self, statement, level='info'):
        prefix = ''
        if self.name:
            prefix = self.name + ': '

        statement = '%s%s' % (prefix, statement)
        logger.log(decode_lvl(level), statement)


    ###########################################################################    
    # Methods ( @property decorators ensure use can't overwrite methods) ####   
    #############################################################################

    # Unit printouts (change to pretty print?)
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

    # Self necessary here or additional df stuff gets printed   
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
        
        # Human-readable form of self._interval
        tstatsdic={True:'Datetime', False:'Interval/Referenced', None:'Unknown'}
        tstyle=tstatsdic[self._interval]
        
        print '\nTemporal/Columns stats'
        print '-----------------------\n'
        print '%sTime Display Style: %s\n'%(delim, tstyle)
        print '%sDatetimeindex parameters:'%(delim)
        if array_truthtest(self._dtindex):
            print '%s%sstart=%s, stop=%s, freq=%s\n'%(delim, delim, self._dtindex[0], self._dtindex[-1], self._dtindex.freq)
        else:
            print '%s%sDatetimeIndex not stored\n'%(delim, delim)            

        print '%sTimeinterval parameters:'%(delim)
        print '%s%sintvlunit=%s\n'%(delim, delim, self.intvlunit)

            
        print '\nSpectral/Index stats'
        print '---------------------\n'
        print '%sspectral category=%s, specunit=%s'%(delim, get_spec_category(self.specunit), self.specunit)
        
    # ADD PYTHON STRING FORMATTING TO THIS
    def list_attr(self, privattr=False, dfattr=False, methods=False, types=False, delim='\t', sortby='name'): #values=False,):
        ''' Outputs various attributes in the namespace, as well as their types.
        
        Parameters
        ----------
           privattr: Should private attributes be listed.
           dfattr: Should dataframe's attributes (eg shape, columns) be listed
           methods: If True, methods will be output; otherwise, only non-method attributes are listed.
           types: Output the type of attribute along with it?
           delim: For formatting.
           sortby: If outputing by type, order by name or by type?
           
        Notes
        -----
           Would like to add "values" but the formatting might get messy.  A good IDE can provide this information anyway,
           for example, Stack Data in windware.  Also increases complexity of the logic below.
           Refer to label_stats() for more detailed information on certain attributes.
      .'''

        # Take all attributes in current instance        
        atts=[x for x in dir(self) if '__' not in x]

        # Remove self._intrinsic (aka class attributes) if desired
        if privattr==False:
            atts=[attr for attr in atts if attr not in self._intrinsic]        
            filterout=['_intrinsic', 'ix', '_ix', 'list_attr'] #Don't want these as attributes
            for att in filterout:
                atts.remove(att)
        
        # Include dataframe attributes if desired
        if dfattr==True:
            atts=atts+[x for x in dir(self._df) if '__' not in x]
        
        # Remove methods if desired
        if methods==False:
            atts=[attr for attr in atts if isinstance(getattr(self, attr), MethodType) != True]
        else:
            atts.append('ix') #This as an attribute but want it to seem like a method
 
        # Should output include types and/or values?
        outheader=['Attribute']
        if types==True: 
            outheader=outheader+['Type']
            atts=[(att, str(type(getattr(self, att))).split()[1].split('>')[0] ) for att in atts]
            #string operation just does str(<type 'int'>) ---> 'int'
            

            # Sort output either by name or type
            badkey_check(sortby, ['name', 'type']) #sortby must be 'name' or 'type'
            
            if sortby == 'name':
                atts=sorted(atts, key=itemgetter(0))
            elif sortby == 'type':
                atts=sorted(atts, key=itemgetter(1))

        # Output to screen
        print delim.join(outheader)    
        print '--------------------'
        for att in atts:
            if types == True:
                print string.rjust(delim.join(att), 7) #MAKE '\N' comprehension if string format never works out
            else:
                print att    
        
        
    @property  #Make log work with this eventually?
    def full_name(self):
        ''' Timespectra:name or Timespectra:unnamed.  Useful for scripts mostly '''
        outname = getattr(self, 'name', 'unnamed')
        return '%s:%s' % (self.__class__.__name__, self.name)
        

    @property
    def data(self):
        ''' Accesses self._df'''
        return self._df

    ###############################
    # reference related operations
    ###############################
    
    @property
    def reference(self):
        ''' This is stored as a Series unless user has set it otherwise.'''
        return self._reference

    @reference.setter
    def reference(self, reference, force_series=True):  
        ''' Before changing reference, first validates.  Then considers various cases, and changes 
        class attributes and dataframe values appropriately.'''

        # Adding or changing reference
        if not isinstance(reference, NoneType):

            # If data is in raw/full mode (itype=None)
            if self._itype == None:
                reference=self._reference_valid(reference, force_series=force_series)                  
                
                self._reference=reference

            # Let _set_itype() do lifting.  Basically convert to full and back to current itype. 
            else:
                self._set_itype(self._itype, ref=reference)

        # Removing reference.  
        else:
            # If current reference is not None, convert
            if not isinstance(self._reference, NoneType):  #Can't do if array==None
                self._set_itype(None, ref=self._reference)
                self._reference=None
                

    def dropref(self):
        ''' Convience method for setting to None'''
        self.reference = None
        
        
    def _reference_valid(self, ref, force_series=True, zero_warn=True, nan_warn=True):
        ''' Helper method for to handles various scenarios of valid references.  Eg user wants to 
        convert the spectral representation, this evaluates manually passed ref vs. internally stored one.

        Parameters:
        -----------
        ref: reference object for inspection.   See notes for more details of validation process.
        force_series:  If true, reference is forced to a Series type.
        zero_warn: If true, a warning is raised if reference contains zeros.
        nan_warn:  If true, a warning is raised if reference contains nans.
        
        Notes:
        ------
        
        This goes through several cases to determine reference.  In order, it attempts to get the reference from:
            1. Column name from dataframe.
            2. Column index from dataframe.
            3. Uses ref itself.
               a. If series, checks for compatibility between spectral indicies.
               b. If dataframe, ensures proper index and shape (1-d) and converts to series (if force_series True).
               c. If iterable, converts to series (if force_series True)
               
        Errors will be thrown if new reference does not have identical spectral values to self._df.index as evaluated by
        numpy.np.array_equal()
        
        Zero_warn and nan_warn are useful when the user plans on changing intensity units of the data.  For example,
        converting from raw data to absorbance data, a relative division will result in hard-to-spot errors due to
        the 0's and nans in the original reference. 
        '''
        
        
        if isinstance(ref, NoneType):
            return ref

        # First, try ref is itself a column name
        try:
            rout=self._df[ref]
        except (KeyError, ValueError):  #Value error if ref itself is a dataframe
            pass

        # If rtemp is an integer, return that column value.  
        # NOTE: IF COLUMN NAMES ARE ALSO INTEGERS, THIS CAN BE PROBLEMATIC.
        if isinstance(ref, int):
            rout=self._df[self._df.columns[ref]]        

        # Finally if ref is itself a series, make sure it has the correct spectral index
        elif isinstance(ref, Series):
            if np.array_equal(ref.index, self._df.index) == False:
                raise RefError(ref.index, self)
            else:
                rout=ref
            
        # Finally if array or other iterable, force to a series
        else:
            if force_series:
                
                # If user passes dataframe, downconvert to series 
                if isinstance(ref, DataFrame):
                    if ref.shape[1] != 1:
                        raise TypeError('reference must be a dataframe of a single column with index values equivalent to those of %s'%self._name)
                    if ref.index.all() != self._df.index.all():
                        raise RefError(ref, self)                    
                    else:
                        rout=Series(ref[ref.columns[0]], index=ref.index) 
   
                # Add index to current iterable 
                else:
                    if len(ref) != len(self._df.index):
                        raise RefError(ref, self)
                    else:
                        rout=Series(ref, index=self._df.index)

            # Return itrable as is
            else:
                rout=ref
                
        if nan_warn:
            if np.isnan(np.sum(rout)):  #Fast way to check for nan's
                logger.error('Nans found in reference.  Error raised because '
                    '"nan_warn" = True in _reference_valid()')
                
                
        if zero_warn:
            if 0.0 in rout:
                logger.error('Zero values found in reference.  Error raised '
                    'because "zero_warn" = True in _reference valid()')

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
                       If user is passing a function to apply_fcn that requires keywords, 
                       the get passed in to dfcut.apply() 
          
        Notes:
        -----_
            See description of 'df_wavelength_slices' in utilities.py for more information. 
            
            For easy plotting, plot the transpose of the returned timespectra.  '''   

        dflist=[]; snames=[]
        
        if isinstance(ranges, float) or isinstance(ranges, int):
            ranges=spec_slice(self.index, ranges)           
        
        # If single range is passed in, want to make sure it can still be iterated over...
        if len(ranges)==2:
            ranges=[ranges]
        
        for rng in ranges:
            if len(rng)!=2:
                raise AttributeError("In slices function, all ranges passed in must be len 2, aka a start and stop \
                pair.  %s of length %s was entered"%rng, len(rng))
            else:
                dfcut=self.ix[rng[0]:rng[1]]
                snames.append('%s:%s'%(rng[0],rng[1]))
                
                if isinstance(apply_fcn, str):
        
                    # Pandas cython operations ###
                    if apply_fcn.lower() == 'mean': 
                        series=dfcut.mean(axis=0)
                    elif apply_fcn.lower() == 'sum':
                        series=dfcut.sum(axis=0)
                    
                        
                    # Integration isn't the same as sum because it takes the units of the x-axis into account through x
                    # parameter.  If interval is odd, last interval is used w/ trapezoidal rule
                    elif apply_fcn.lower() == 'simps':
                        series=dfcut.apply(integrate.simps, x=dfcut.index, even='last')
                        
                    elif apply_fcn.lower() == 'trapz':
                        series=dfcut.apply(integrate.trapz, x=dfcut.index)     
                        
                    elif apply_fcn.lower() == 'romb':
                        series=dfcut.apply(integrate.romb, x=dfcut.index)
                        
                    elif apply_fcn.lower() == 'cumtrapz':
                        series=dfcut.apply(integrate.trapz, x=dfcut.index, ititial=None)           
                        
                    else:
                        raise AttributeError('apply_fcn in wavelength slices, as a string, must be one of the following: \
                        (mean, sum, simps, trapz, romb, cumtrapz) but %s was entered.  Alternatively, you can pass \
                        a function to apply_fcn, with any relevant **kwds')
        
                # Try to apply arbirtrary function.  Note, function can't depend on dfcut, since 
                # that is created in here
                else:
                    series=dfcut.apply(apply_fcn, **applyfcn_kwds)
                    
                    
                # OK
                dflist.append(series)
                
        return self._transfer(DataFrame(dflist, index=snames))
        

    def boxcar(self, binwidth, axis=1):
        '''Performs boxcar averaging by binning data.
        
        Parameters
        ----------
           binwidth: Width of the slice overwhich to average.
           axis: 1/0 for index/column averaging respectively.
        '''
        if axis==0 and self._interval==False:
            raise NotImplementedError('Cannot boxcar along DateTime axis.')
        
        return self._transfer(boxcar(self, binwidth=binwidth, axis=axis))
    
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
        return self.wavelength_slices((min(self.index), max(self.index)), apply_fcn=apply_fcn)
    
    
    # PCA INTERFACE #    
    _pca=None   #Instance method?
    
    def _pcagate(self, attr):
        ''' Raise an error if use calls inaccessible PCA method.'''
        if not self._pca:
            raise AttributeError('Please run .pca() method before calling %s'%attr)    
        
    def run_pca(self, n_components=None, fit_transform=True):# k=None, kernel=None, extern=False):           
            '''         

            Adaptation of Alexis Mignon's pca.py script
            
            Adapted to fit PyUvVis 5/6/2013.  
            Original credit to Alexis Mignon:
            Module for Principal Component Analysis.
    
            Author: Alexis Mignon (c)
            Date: 10/01/2012
            e-mail: alexis.mignon@gmail.com
            (https://code.google.com/p/pypca/source/browse/trunk/PCA.py)
                        
            Constructor arguments:
            * k: number of principal components to compute. 'None'
                 (default) means that all components are computed.
            * kernel: perform PCA on kernel matrices (default is False)
            * extern: use extern product to perform PCA (default is 
                   False). Use this option when the number of samples
                   is much smaller than the number of features.            

            See pca.py constructor for more info.
            
            This will initialize PCA class and fit current values of timespectra.
            
            Notes:
            ------
                The pcakernel.py module is more modular.  These class methods
                make it easier to perform PCA on a timespectra, but are less 
                flexible than using the module functions directly.
            
                timespectra gets transposed as PCA module expects rows as 
                samples and columns as features.
                
                Changes to timespectra do not retrigger PCA refresh.  This 
                method should be called each time changes are made to the data.
                
                
            '''
            self._pca=PCA(n_components=n_components, index=self.index)                
            if fit_transform:
                return self._pca.fit_transform(self._df.transpose())
            else:    
                self._pca.fit(self._df.transpose())
                
                        
    @property
    def pca(self):
        self._pcagate('pca')
        return self._pca 
    
    @property
    def pca_evals(self):
        self._pcagate('eigen values')
        # Index is not self.columns because eigenvalues are still computed with
        # all timepoints, not a subset of the columns        
        return Series(self._pca.eigen_values_)
    
    @property
    def pca_evecs(self):
        self._pcagate('eigen vectors')
        return DataFrame(self._pca.eigen_vectors_)
            
    def load_vec(self, k):
        ''' Return loading vector series for k.  If k > number of components
            computed with runpca(), this raises an error rather than 
            recomputing.'''
        self._pcagate('load_vec')
        if k > len(ts.columns):
            raise AttributeError('Principle components must be <= number of timepoints %s'%len(ts))


        # Decided to put impetus on user to recompute when not using enough principle components
        # rather then trying to figure out logic of all use cases.

        # If k > currently stored eigenvectors, recomputes pca
        if self._pca._k:
            if k > len(self.pca_evals):            
                raise AttributeError('Only %s components were computed.  Please call run_pca() with \
                more principle components returned.'%self._pca._k)

        return Series(self._pca.eigen_vectors_[:,k], index=self._pca._index) 
        
    # Spectral column attributes/properties
    @property
    def specunit(self):
        return self._df.index.unit    #Short name key

    @property
    def full_specunit(self):
        return specunits[self._df.index.unit]

    @specunit.setter
    def specunit(self, unit):
        self._df.index=self._df.index._convert_spectra(unit) 
    #    self.index=self._df.index #Necessary because this is done sloppily
        
    def as_specunit(self, unit):
        ''' Returns new dataframe with different spectral unit on the index.'''
        tsout=self.deepcopy()
        tsout.specunit=unit
        return tsout

    @property
    def spectypes(self):
        return specunits
    
    # Temporal/column related functionality
    def set_daterange(self, **date_range_args):
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
        
        rng = date_range(**date_range_args)
        self._df.columns = rng        
        self._dtindex = rng
        self._interval = False
        
        
    def set_specindex(self, start=None, stop=None, spacing=None, unit=None):
        '''Helper method to generate a spectral index.  Works similarly to
           pandas.daterange().  Takes in start, stop and spacing.  Users can use
           either start and stop, start and spacing or stop and spacing (but not 
           start, stop and spacing) to generate specindex.
           
           Parameters
           ----------
               start: Wavelength start value.
               stop: Wavelength stop value.
               spacing: Wavelength spacing.
               unit: Valid specunit type.  Note, if None is passed, current specunit of
                     object is used.  To force a null unit, use special keyword 'null'.
                     
           Notes
           -----
              User must pass 2 of the 3 keywords start, stop or spacing.  Function
              will compute the other using the length of the current dfindex.  
              For example, if df.index is 100 entries and user enters start=0, stop=1000,
              then spacing is set to ten to retain 100 entries.  
              If user enters start and spacing, then stop is determined to retain 100
              entries.
              User can also enter stop and spacing, and start is inferred by counting
              backwards from stop at steps equal to spacing size.
            
              To generate less restricted SpecIndex from start, stop AND spacing, try
              set_sindex() function in specindex.py module.
              
              Under the hood this calls set_sindex() which is a wrapper to
              np.linspace().  '''        

        numpts=float(len(self.index))
        
        # If no unit passed, conserve current one
        if not unit:
            unit=self.specunit
            
        # If user wants to force a null unit
        else:
            if unit.lower()=='null':
                unit=None
                
        # Bad keyword cases
        if start and stop and spacing:
            raise badcount_error(2,3,3, argnames='start, stop, keywords')
        
        if not start and not stop and not spacing:
            raise badcount_error(2,0,3, argnames='start, stop, keywords')
      
        # User enters start and stop    
        if start and stop:
            start=float(start)            
            stop=float(stop)
            
        # User enters spacing and start or spacing and stop.
        if spacing:    
            spacing=float(spacing)            
            if start:
                start=float(start)                
                stop= start + (spacing * numpts)           
            elif stop:
                stop=float(stop)
                start=stop - (spacing * numpts)

        # If user only entered one keyword, then all three will not be generated by this point 
        if not start or not stop:
            raise badcount_error(2,1,3, argnames='start, stop, keywords')
        
        self._df.index=set_sindex(start, stop, numpts, unit=unit)

    
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
    def timetypes(self):
        return tunits        
            
    @property
    def timeunit(self):
        ''' Quick reference to current state of time labels.  For comprehensive output, try ts.label_stats()'''
        if self._interval==True:
            return self.intvlunit
        elif self._interval==False:
            return 'Timestamp'
        elif self._interval==None:
            return None
        
    @property
    def full_timeunit(self):
        ''' Quick reference to current state of time labels, except calls full_intvlunit instead of timeunit'''
        if self._interval==True:
            return self.full_intvlunit
        elif self._interval==False:
            return 'Timestamp'
        elif self._interval==None:
            return None
    
    
    def to_datetime(self):
        ''' Set columns to DatetimeIndex.  
        
        Notes
        -----
            self._interval can be None, True or False.  This will call _as_datetime() if it's None or True 
            and if not all appropriate attributes are found, an error will be raised.
        '''
        if self._interval != False:       
            self._df.columns=self._as_datetime()
            self._interval=False
          

    def to_interval(self, unit=None):  
        ''' Set columns to interval as computed by datetime_convert function. '''
        
        # User calls function with empty call (), if proper attributes, convert it
        if unit==None: 

            array_truthtest(self._dtindex, errorstring=_dtmissing)
            if self._intervalunit != None:
                unit=self._intervalunit
            else:
                unit='intvl'  #Default if user has not set anything in _intervalunit
                
        # User calls function with unit
        else:
            unit=_valid_intvlunit(unit)          
            
            # If _df already interval
            if self._interval==True:
                if unit==self._intervalunit:
                    return         
                    
            
            # If interval is None or False, do the conversion
            elif self._interval==None:
                # Make sure proper attributes to get back ater in place
                array_truthtest(self._dtindex, errorstring=_dtmissing)

                
        self._df.columns=self._as_interval(unit)
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
    
    def _as_interval(self, unit):
        ''' Return columns as intervals as computed by datetime_convert function.'''
        
        # If current columns is DatetimeIndex, convert
        if self._interval==False:
            return Index(datetime_convert(self.columns, return_as=unit, cumsum=True))              
    
        # If currently already intervals, convert to datetime, then convert that to new units
        else:
            newcols=self._as_datetime() #Convert to new unit
            return Index(datetime_convert(newcols, return_as=unit, cumsum=True))          
            
    def _as_datetime(self):
        ''' Return datetimeindex given a timespectra object.  Merely sets the _dtindex
            attribute of a timespectra. '''
    
        # Make sure all attributes are set before converting
        array_truthtest(self._dtindex, errorstring=_dtmissing)
        return self._dtindex
    
    ###################################
    # Baseline related operations ###
    ###################################

    # SHOULD ALSO ENFORCE DATATYPES
    def _base_gate(self):
        ''' Quick check to see if self._baseline is found or missing.  If missing,
            raises error.  If found, passes.'''
        if isinstance(self._baseline, NoneType):
            raise AttributeError('Baseline not found.')        

    def sub_base(self):
        ''' Subtracts baseline from entire dataset.
        
            Notes:
            -----
              Does have to call self._df.  Just doing self.sub will not work, even though
              calling ts.sub() from an outside program does in fact work.  Behavior is due
              to way in which python classes deal with overwrites of self.'''

        # self._baseline is not none
        self._base_gate()

        # Only subtract if baseline isn't currently subtracted
        if not self._base_sub:
            # Index, although should be correct, is type object and is getting falses for entries...
            logger.critical('Subtracting baseline, but may not have all: elements being equal.  Fix index')
            self._df = self._df.sub(self._baseline, axis=0)
            self._base_sub = True
            
        else:
            logger.warn('Baseline is already subtracted.')

    def add_base(self):
        ''' Adds baseline to data that currently has it subtracted.'''

        # self._baseline is not none
        self._base_gate()
        
        # Only add if baseline is currently in a subtracted state
        if self._base_sub:
            self._df = self._df.add(self._baseline, axis=0)        
            self._base_sub = False
            
        #else:
            #print 'raise waring? already added'        

    @property
    def base_sub(self):
        ''' Is baseline currently subtracted from spectral data.'''
        self._base_gate()
        return self._base_sub
        
    def _valid_baseline(self, baseline):
        ''' Validates user-supplied baseline before setting.  Mostly,
            ensures that baseline.index == self._df.index'''
        

        if baseline is None:
            self._comment('Baseline is None')
            return 
        
        # If baseline not iterable, return series of constant values
        try:
            baseline.__iter__
        except AttributeError:
            self._comment('Baseline is not iterable; filling with constant '
                         'value %s' % baseline)
            return Series(baseline, index=self._df.index)
        

        # If Series compare index values
        # NEED A SPEC INDEX CLASS, THEN REMOE MOST OF THIS
        if isinstance(baseline, Series):
            if baseline.shape != self.index.shape:
                raise BaselineError('Baseline shape mismatch %s vs %s %s'
                        %(baseline.shape, self.name, self.index.shape))
            else:
                if np.array_equal(baseline.index, self._df.index):
                    self._comment('Baseline is a series; has identical index ' 
                                  'to self._df.index')
                    return baseline
                else:
                    self._comment('Baseline is a series; shape identical to'
                                 ' self.index.shape; but elements are not equal.')
                    mytype = self._df.index.dtype
                    bline_type = baseline.index.dtype

                    try:
                        baseline.index.dtype = mytype
                    except Exception:
                        raise BaselineError('Baseline index (%s) could not be cast to  '
                                'self.index.type (%s)' % (bline_type, mytype))
                    else:
                        logger.warn('Baseline index type (%s) converted to self.index '
                                    'type (%s)' % (bline_type, mytype))
                        if np.array_equal(baseline.index, self._df.index):
                            return baseline
                        else:
                            raise BaselineError('Baseline index != self._df.index')

       # If other type of iterable, make series
        else:
            # Make sure length is correct
            if len(baseline) == len(self._df.index):
                self._comment("Baseline is iterable, but not a Series; converting")
                return Series(baseline, index=self._df.index, dtype=float)
            else:
                raise BaselineError('Baseline must be of length %s to '
                    'match the current spectral index.'%len(self._df.index))

           
    @property
    def baseline(self):
        return self._baseline
            
    
    @baseline.setter
    def baseline(self, bline):
        ''' Allows user to set a baseline curve with a variety of options.'''
        ## Logic.  Need validation for various cases.
        # Depending on type/length, force or set index?  What about non-equal length types,
        # try an interpolation?
        # End th "valid_base" 

        bline=self._valid_baseline(bline)
        
        # Data does not current contain subtracted baseline
        if not self._base_sub:
            self._baseline=bline
 
        # Data does contain subtracted baseline
        else:
            self.add_base()
            self._baseline=bline
            # If baseline is not none, go ahead and re-subtract
            if bline is not None:
                self.sub_base()
             

    # Spectral Intensity related attributes/conversions
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


    def as_iunit(self, unit, reference=None):
        ''' Returns new TimeSpectra of modified iunit.  Useful if in-place operation not desirable.  
        Also has the option of manually passing a new reference for on-the-fly rereferencing.'''
        if isinstance(unit, basestring):
            if unit.lower() in ['none', 'full']:
                unit=None

        tsout=self.deepcopy()        
        tsout._set_itype(unit, reference)
        return tsout

    def _set_itype(self, sout, ref=None):
        '''Function used to change spectral intensity representation in a convertible manner. Not called on
        initilization of TimeSpectra(); rather, only called by as_iunit() method.'''

        sout=_valid_iunit(sout)
        sin=self._itype
        df=self._df #Could also work just by calling self...

        # Corner case, for compatibility with reference.setter
        if sin==None and sout==None:
            return

        ########################################################################
        # Case 1: User converting from full data down to referenced data.#####
        ########################################################################
        if sin==None and sout != None:
            rout=self._reference_valid(ref)

            # If user tries to downconvert but doesn't pass reference, use stored one
            if rout == None:
                rout=self._reference

            # If ref not passed, use current reference.  Want to make sure it is 
            # not none, but have to roundabout truthtest
            if isinstance(rout, NoneType):
                raise TypeError('Cannot convert spectrum to iunit %s without a reference'%sout)                
            else:
                df=divby(df, divisor=rout)
                df=df.apply(from_T[sout])                    
            #Assumes typeerror is due to rout not being a series/array, but doesn't further test it.  EG do another
            #typeerror check of try: if rout == None: raise error


        ##############################################################   
        # Case 2: Changing spectral representation of converted data.#
        ##############################################################     
        elif sin !=None and sout != None:

            # If user changing reference on the fly, need to change ref ###
            if not isinstance(ref, NoneType): #and ref != self._reference:
                rout=self._reference_valid(ref)

                # Make this it's own method called change reference?
                df=df.apply(to_T[sin])
                df=df.mul(self._reference, axis=0)  
                df=divby(df, divisor=rout)
                df=df.apply(from_T[sout])                        


            else:
                rout=self._reference #For sake of consistent transferring at end of this function
                df=df.apply(to_T[sin])
                df=df.apply(from_T[sout])        


        ###########################################################    
        # Case 3: User converting referenced data up to full data.#
        #############################################################
        elif sin !=None and sout==None:
            rout=self._reference_valid(ref)
            
            if rout == None:
                rout=self._reference
            
            df=df.apply(to_T[sin])
            df=df.mul(rout, axis=0)  #Multiply up!

        self._reference=rout       
        self._itype=sout        
        self._df=df    

    @property
    def itypes(self):
        return Idic
        
    ############################################ 
    #####Overwrite MetaDataFrame behavior ########
    ############################################    
    
    
    @property
    def cnsvdattr(self):
        ''' attr:value of conserved attributes'''
        csvdout={}
        for attr in self._cnsvdattr:
            if hasattr(self, attr):
                csvdout[attr]=getattr(self, attr)
            else:
                csvdout[attr]=None
        return csvdout
    
    @cnsvdattr.setter
    def cnsvdattr(self, attrs):
        ''' Set which attributes are mutated in DataFrame operations via cons_methods.'''
        if isinstance(attrs, basestring):
            attrs=[attrs]
            
        consout=[]
        for attr in attrs:
            try:
                consout.append(attrgetter(attr, self))
            except AttributeError:
                raise AttributeError('%s not found on object %s'%(attr, self)) 

        self._cnsvdattr=consout
        
    @property
    def cnsvdmeth(self):
        return self._cnsvdmeth
    
    @cnsvdmeth.setter
    def cnsvdmeth(self, attrs):
        # Do I even want to do anything more than setter?
        if isinstance(attrs, basestring):
            attrs=[attrs]

        for attr in attrs:
            if hasattr(self, attr):
                pass
            else:
                raise AttributeError('%s has no attribute "%s"'%(self.name, attr))
            
        self._cnsvdmeth=attrs        
        
    def _dfgetattr(self, attr, *fcnargs, **fcnkwargs):
        ''' This is overwritten from MetaDataFrame to allow special attributes to
        be manipulated under dataframe operations.  For example, if a user slices the dataframe,
        then the reference auto get sliced on the return array; otherwise, get tough-to-track
        length mismatch issues.
        
        Notes:
        -----
        Since new series items always have a name by default, an originally unnamed series
        attribute (such as reference) will end with a name=_reference afterwards.  Added a hack
        to intercept this highly common attribute and apply to output.'''
 
        out=getattr(self._df, attr)(*fcnargs, **fcnkwargs)
                
        # If operation returns a dataframe, return new TimeSpectra
        if isinstance(out, DataFrame):
            
            # Are there specially conserved attributes?
            csvdout=None
            if attr in self._cnsvdmeth:    
                if self._cnsvdattr:
                    cnsvdattr=dict((k,v) for k, v in self.cnsvdattr.iteritems() if v is not None)
                                    
                                    
                    csvdf=DataFrame(cnsvdattr)  #STILL WORKS WITH NONEQUAL LENGTH
                    _csvdfattrs=dict((attr, (cnsvdattr[attr].__dict__)) for attr in cnsvdattr)
                                        
                    try:
                        csvdout=getattr(csvdf, attr)(*fcnargs, **fcnkwargs)
                    except Exception:
                        raise Exception('Could not successfully perform operation "%s" on one or multiple \
                        conserved attributes %s.'%attr, '","'.join(csvdout.columns))                               
            
            # Create new timespectra object
            tsout = self._transfer(out)
            
            if not isinstance(csvdout, NoneType):
                                
                for col in csvdout:
                    
                    # Restore custom attributes on the cnsvdattributes
                    restattr=[attr for attr in _csvdfattrs[col] if attr not in csvdout[col].__dict__]
                    if restattr:
                        for attr in restattr:
                            setattr(csvdout[col], attr, _csvdfattrs[col][attr]) 

                        # Hack to conserve "name" attribute of series return
                        try:
                            setattr(csvdout[col], 'name', _csvdfattrs[col]['name']) 
                        except KeyError:
                            pass
                
                    # Apply conserved attributes to new dataframe                        
                    setattr(tsout, col, csvdout[col])
            
            return tsout
        
        # Otherwise return whatever the method return would be
        else:
            return out
        
    def _transfer(self, dfnew):
        ''' See metadataframe _transfer for basic use.  Had to overwrite here to add 
        a hack to apply the spectral unit.  See issue #33 on pyuvvis github for explanation. '''
        sunit=self.specunit
        newobj=super(TimeSpectra, self)._transfer(dfnew)   
        newobj.specunit=sunit
        return newobj
        
    #############################################
    ## OVERWRITE METADATFRAME MAGIC METHODS ###
    #############################################
    def __setattr__(self, name, value):
        ''' Don't want to let users overwite dataframe columns or index without letting timespectra know it's happening.'''
        super(TimeSpectra, self).__setattr__(name, value)        
 
        # Intercept user's column attribute call and set private attributes accordingly.
        if name=='columns':
            if isinstance(self.columns, DatetimeIndex):
                self._dtindex=self.columns
                self._interval=False
            else:
                self._dtindex=None
                self._interval=None
        
            
    def __repr__(self):
        ''' Add some header and spectral data information to the standard output of the dataframe.
        Just ads a bit of extra data to the dataframe on printout.  This is called by __repr__, which 
        can either return unicode or bytes.  This is better than overwriting __repr__()'''
        delim='\t'
        if self.specunit==None:
            specunitout='None'
        else:
            specunitout=self.full_specunit
            
        if not self.name:
            outname='Unnamed' #If user explicitly sets self.name=None; defaults to timespectra 
        else:
            outname=self.name

        outline='**',outname,'**', delim, 'Spectral unit:', specunitout, delim, 'Time unit:', 'Not Implemented','\n'   
        return ''.join(outline)+'\n'+self._df.__repr__()    
    
    ######################
    # CUSTOM SLICING ###
    ######################
        
    def tidx(self, *sliceargs):
        ''' Column slicing by index'''
        return self.ts[ts.columns[slice(*sliceargs)]]
    
    def xidx(self, *sliceargs):
        ''' Row slicing by index'''
        return self.ts.ix[ts.index[slice(*sliceargs)]]    
       
    def xval(self, *sliceargs):
        ''' Row slicing by value '''
        return self.ts.ix[slice(*sliceargs), :]
    
    def tval(self, *sliceargs):
        ''' Column slicing by value.
        
        Notes:
        -----
           This is not straightforward as ts['c1:c4'] tends to query rows for 
           convienence.  Thanks to Jeff Reback for his suggestion of the private _slice().'''
        return self.ts._slice(slice(*sliceargs), 1)

        
 
    
                   
    #################
    # CSV Output###
    #################
                           
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
            # This could be buggy if __init__() from all the keywords is working correctly.
            
            # Make sure user skips last line in file that was added in addition via meta_sepaarte
            csv_kwargs['skip_footer']=csv_kwargs.pop('skip_footer', 0) + 1
            df=df_read_csv(path_or_buff, **csv_kwargs)
            
            # This is hard part, how to set meta data
        
        elif meta_separate == True:
            raise NotImplementedError("Haven't resolved, but this hsould return meta and df")
        
        # Initialize timespectra from meta.  Is this how I want to do it?
        ts=TimeSpectra(df, **meta) 
              

## TESTING ###
if __name__ == '__main__':

    # Be careful when generating test data from Pandas Index/DataFrame objects, as this module has overwritten their defaul behavior
    # best to generate them in other modules and import them to simulate realisitc usec ase


    # For testing 
    import matplotlib.pyplot as plt


    from pyuvvis.nptools.haiss import *
    from pandas import read_csv as df_read_csv
    

    spec=SpecIndex(range(400, 700,1) )
#    spec=SpecIndex([400.,500.,600.])
    testdates = date_range(start='3/3/12',periods=30,freq='h')
    testdates2 = date_range(start='3/3/12',periods=30,freq='45s')
    
    ts=TimeSpectra(abs(np.random.randn(300,30)), columns=testdates, index=spec, name='ts1')  
    t2=TimeSpectra(abs(np.random.randn(300,30)), columns=testdates2, index=spec, name='ts2') 
   
   
    from pyuvvis.IO.gwu_interfaces import from_spec_files, get_files_in_dir
    from pyuvvis.exampledata import get_exampledata
    ts=from_spec_files(get_files_in_dir(get_exampledata('NPSAM'), sort=True), name='foofromfile')

    ts.to_interval('s')
    ts=ts.ix[440.0:700.0,0.0:100.0]
    ts.reference=0    
    print ts._baseline.shape, ts.shape
    
    # Goes to site packages because using from_spec_files, which is site package module
    ts.run_pca()
 #   ts.pca_evals

    #from pandas import Panel
    #Panel._constructor_sliced=TimeSpectra
    #pdic={'ts':ts}
    #tp=Panel.from_dict(pdic)
    
    d={'start':2/22/12, 'periods':len(ts.columns), 'freq':'45s'}
    ts.set_daterange(start='2/22/12', periods=len(ts.columns), freq='45s')
    
    ts.baseline=ts.reference
    ts.sub_base()

    # THIS FAILS WHEN INDEX=SPEC 
    t3=TimeSpectra(abs(np.random.randn(ts.baseline.shape[0], 30)), columns=\
                   testdates, 
                   baseline=ts._baseline, name='foobar')  

    
       
    #ts._reference.x='I WORK'
    #ts._reference.name='joe'
    ts.baseline=Series([20,30,50,50], index=[400., 500., 600., 700.])
##    t2.baseline=ts.baseline
    #ts._df.ix[:, 0:4]
    #ts.ix[:,0:4]
    #ts.boxcar(binwidth=20, axis=1)
    #x=ts.ix[450.0:650.]
    #y=t2.ix[500.:650.]
    
    #ts.cnsvdmeth='name'
        
    from pyuvvis.pandas_utils.metadframe import mload
    #from pyuvvis import areaplot, absplot
    ts=mload('rundata.pickle')    
    ts=ts.as_interval('m')
    x=ts.area()    
    print 'hi', x
    #ts.reference=0
    #ts=ts[ts.columns[800.0::]]
    #ts=ts.ix[400.0:800.0]
    #c=haiss_m2(ts, peak_width=2.0, ref_width=2.0)
    #a=haiss_m3(ts, 0.000909, peak_width=None, dilution=0.1)
    #b=haiss_conc(ts, 12.0)
    ##b2=haiss_conc(ts, 12.0, dilution=0.2)
    
##    bline=ts[ts.columns[0]]
##    ts=ts.ix[:,25.0:30.0]
##    ts.reference=bline
 
    #uv_ranges=((430.0,450.0))#, (450.0,515.0), (515.0, 570.0), (570.0,620.0), (620.0,680.0))
    
    #tssliced=ts.wavelength_slices(uv_ranges, apply_fcn='mean')
        
    #from pyuvvis.core.utilities import find_nearest
    #x=ts.ix[500.:510, 0]
    #b=maxmin_xy(x)
    #a=find_nearest(x, .15)
    #ts.iunit=None
    #ts.iunit='a'
    #ts.iunit=None
    
    
    #ts.to_csv('junk')
    #range_timeplot(ts)

    #ts.a=50; ts.b='as'
    #ts.iunit='t'

    #ts.list_attr(dfattr=False, methods=False, types=True)    
    #ts.as_iunit('a')
    #x=ts.as_iunit('a')
    ##ts.as_interval()
    ##spec_surface3d(ts)  ##Not working because of axis format problem
    ##plt.show()
##    ts.rank(use_base=True)
    #x=ts.dumps()
    #ts=mloads(x)
