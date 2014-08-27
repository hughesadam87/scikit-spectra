"""Provides core "TimeSpectra" class and associated utilities."""

import logging
from pyuvvis.logger import decode_lvl, logclass
from pandas import DatetimeIndex, Index
from pyuvvis.core.spec_labeltools import datetime_convert, intvl_dic
from pyuvvis.core.spectra import _valid_xunit
from spectra import Spectra

logger = logging.getLogger(__name__) 

def _valid_intvlunit(sout):
    """ Validate interval unit."""
    return _valid_xunit(sout, intvl_dic)


# Ignore all class methods!
@logclass(log_name=__name__, skip = ['wraps','_dfgetattr', 'from_csv', 
                                     '_comment', '_transfer'])
class TimeSpectra(Spectra):
    """ Provides core TimeSpectra composite pandas DataFrame to represent a set 
    of spectral data.  Enforces spectral data along the index and temporal 
    data as columns.  The spectral index is controlled from the specindex module, 
    which has a psuedo-class called SpecIndex (really a monkey patched Index). 
    Temporal data is stored using a DatetimeIndex or a modified interval 
    reprentation.  The need to support two types of temporal index, one of 
    which is Pandas builtin DatetimeIndex is what led me to not create a 
    special index object (like SpecIndex).  Other spectral axis types (like 
    Temperature axis) should probably be built close to the manner of Spec index.
    The TimeSpectra dataframe actually stores enough temporal metadatato go back 
    and forth between DatetimeIndex and Interval representations.  
    It does this by generating one or the other on the fly, and never relies on 
    the current label object to generate teh next object.
    """
    
    
    # Has to be this way because class methods not accessible via metadataframe __getattr__()
    def __init__(self, *dfargs, **dfkwargs):
#        dfkwargs['force_index'] = SpecIndex
        dfkwargs['force_columns'] = None
        

        # Should I even do anything?
        self._intervalunit = dfkwargs.pop('intvlunit', None)        
        self._interval = None                                                  
        self._dtindex = None            
        
        super(TimeSpectra, self).__init__(*dfargs, **dfkwargs)

        # Datetime index is hardcoded
        if not isinstance(self._df.columns, DatetimeIndex):
            # Try to force coluns to DatetimeIndex THIS MIGHT BE A MISTAKE BECUASE
            # DATETIME INDEX IS A BIT SOFT ON CHECKS; SHOULD DO EXTRA VALIDATION
            try:
                self._df.columns = DatetimeIndex(self._df.columns)
            except Exception:
                logger.info("Spectra initialized without DatetimeIndex-"
                            "compatible column labels.")
            else:
                self._interval = False
                self._dtindex = self._df.columns

        # If DateimIndex already, store attributes directly from array
        else:
            self._interval = False      
            self._dtindex = self._df.columns        


    # DELETE ME ONCE REFACTORED INDEX (SPECTRA HAS A GENERAL DEFINITION OF THIS)
    def list_varunits(self, delim='\t'):
        """ Print out all available temporal units in a nice format"""
        
        # Put in a separte file of constants?
        tunits={'ns':'Nanoseconds', 
                'us':'Microseconds',
                'ms':'Milliseconds', 
                's':'Seconds', 
                'm':'Minutes', 
                'h':'Hours',
                'd':'Days', 
                'y':'Years'}  #ADD NULL VALUE? Like None:'No Time Unit' (iunit/specunit do this)        
        self._list_out(tunits, delim=delim)
            

    def list_intvlunits(self, delim='\t'):
        """ Print out all possible units to express the columns in 
            interval or referenced notation (eg to=0)"""
        self._list_out(intvl_dic, delim=delim)
        
    # Temporal/column related functionality
    def set_daterange(self, **date_range_args):
        """ Wrapper around pandas.date_range to reset the column
        values on of the data on the fly. See pandas.date_range()
        for use.  In brief:
        
        Parameters
        ----------
        start: 
            time start.  
        freq: 
            Frequency unit
        stop/periods: 
            specifies endpoint given start and freq.
           
        Examples
        --------
        timespectra.set_daterange('1/1/2012', period=5, freq='H')
        """
        
        rng = date_range(**date_range_args)
        self._df.columns = rng        
        self._dtindex = rng
        self._interval = False
        

    @property
    def intvlunit(self):
        return self._intervalunit    
    
    @intvlunit.setter
    def intvlunit(self, unit):
        """ If _df in interval mode, convert it.  Otherwise just store attributes."""
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
    def varunit(self):
        """ Quick reference to current state of time labels.  For comprehensive
        output, try ts.label_stats() 
        """
                
        if self._interval == True:
            return self.intvlunit
        elif self._interval == False:
            return 'Timestamp'
        elif self._interval == None:
            return None

        
    @property
    def full_varunit(self):
        """ Quick reference to current state of time labels, except calls full_intvlunit instead of timeunit"""
        if self._interval == True:
            return self.full_intvlunit
        elif self._interval == False:
            return 'Timestamp'
        elif self._interval == None:
            return None
    
    
    def to_datetime(self):
        """ Set columns to DatetimeIndex.  
        
        Notes
        -----
            self._interval can be None, True or False.  This will call _as_datetime() if it's None or True 
            and if not all appropriate attributes are found, an error will be raised.
        """
        if self._interval != False:       
            self._df.columns=self._as_datetime()
            self._interval=False
          

    def to_interval(self, unit=None):  
        """ Set columns to interval as computed by datetime_convert function. """
        
        # User calls function with empty call (), if proper attributes, convert it
        if unit==None: 

            self._parse_dtindex()
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
                self._parse_dtindex()

                
        self._df.columns = self._as_interval(unit)
        self._interval = True    
        self._intervalunit = unit

        
    def as_interval(self, unit=None):
        """ Return copy of Spectra as interval."""
        if isinstance(unit, basestring):
            if unit.lower() in ['none', 'full']:
                unit=None

        tsout = self.deepcopy()        
        tsout.to_interval(unit)
        return tsout        
            

    def as_datetime(self):
        """ Return copy of Spectra as datetime."""
        tsout = self.deepcopy()
        tsout.to_datetime()
        return tsout
    
    def _as_interval(self, unit):
        """ Return columns as intervals as computed by datetime_convert function."""
        
        # If current columns is DatetimeIndex, convert
        if self._interval == False:
            return Index(datetime_convert(self.columns, return_as=unit, cumsum=True))              
    
        # If currently already intervals, convert to datetime, then convert that to new units
        else:
            newcols = self._as_datetime() #Convert to new unit
            return Index(datetime_convert(newcols, return_as=unit, cumsum=True))          
            
    def _as_datetime(self):
        """ Return datetimeindex given a timespectra object.  Merely sets the _dtindex
            attribute of a timespectra. """
    
        # Make sure all attributes are set before converting
        self._parse_dtindex()
        return self._dtindex

    def _parse_dtindex(self):
        """ Raise error if dtindex is none.  Mostly used in cases of user 
        error, like convert to interval when no datetime is stored."""

        if self._dtindex is None:
            raise IndexError("Cannot convert representations without interally "
            "stored datetimeindex.")    
    

    #############################################
    ## OVERWRITE METADATFRAME MAGIC METHODS ###
    #############################################
    def __setattr__(self, name, value):
        """ Don't want to let users overwite dataframe columns or index without letting timespectra know it's happening."""
        super(Spectra, self).__setattr__(name, value)        
 
        # Intercept user's column attribute call and set private attributes accordingly.
        if name=='columns':
            if isinstance(self.columns, DatetimeIndex):
                self._dtindex = self.columns
                self._interval = False
            else:
                self._dtindex = None
                self._interval = None
    

## TESTING ###
if __name__ == '__main__':
    from specindex import SpecIndex
    from pandas import date_range
    import numpy as np

    # Be careful when generating test data from Pandas Index/DataFrame objects, as this module has overwritten their defaul behavior
    # best to generate them in other modules and import them to simulate realisitc usec ase


    ## For testing 
    #import matplotlib.pyplot as plt


    #from pyuvvis.data import aunps_water, aunps_glass
    #from pyuvvis.plotting import splot, range_timeplot
    #ts_water = aunps_glass()
##    ax1, ax2 = splot(1,2)
    
##    ts_water.plot(ax=ax1)
    #range_timeplot(ts_water.wavelength_slices(8))
##    bline = ts_water.baseline
##    bline.plot(ax=ax1, lw=5, color='r')
    #plt.show()

    

    spec=SpecIndex(range(400, 700,1), unit='nm')
###    spec=SpecIndex([400.,500.,600.])
    testdates = date_range(start='3/3/12',periods=30,freq='h')
    ##testdates2 = date_range(start='3/3/12',periods=30,freq='45s')
    
    ts=TimeSpectra(abs(np.random.randn(300,30)), 
                   columns=testdates, 
                   index=spec, 
                   name='ts1')  

    ##t2=TimeSpectra(abs(np.random.randn(300,30)), 
                   ##columns=testdates2, 
                   ##index=spec, 
                   ##name='ts2') 
    
    from pyuvvis.data import solvent_evap
    import matplotlib.pyplot as plt
    from pyuvvis.plotting import areaplot
    ts = solvent_evap()
   # ts.index = SpecIndex(ts.index)

    t2 = ts.ix[1500.0:1000.0]
    print ts.index
    print t2.index
    

    #t2 = ts.as_interval('m')

    #t2 = t2.as_iunit('r')

    ##stack = ts.split_by(1)
    ##stack.iunit = 'a'

    ##ts[ts.columns[0]].plot(colormap='RdBu')
    ##plt.show()
    #t2 = ts.as_interval('m')
    ##t2 = ts.as_iunit('r')
    ##ts.area().plot()
    ##import sys
    ##sys.exit()
    
###    stack.plot(title='Big bad plots')
    #from pyuvvis.plotting import six_plot
    #import matplotlib.pyplot as plt
    #six_plot(ts, striplegend=True)
    #plt.show()
    ##t1 = ts.as_interval()
    ##print t1.columns
    ##t1.plot(cbar=True)
    ##t1.to_datetime()
    ##t1.ix[500.0:600.0]
    ##t2 = ts.as_specunit('ev')
    ##t3 = ts.as_iunit('a')
    ##print t2.specunit, 'hi t2'
    ##print t3.specunit, 'hi t3'
    ##print t2.specunit, 'hi t2'
    ##specplot(ts, cbar=True)


    
###    a=ts.area()
###    print 'hi', a.specunit
###    ts.specunit = 'ev'
    ###from pyuvvis.plotting import specplot, areaplot
    ###areaplot(ts)
    ###plt.show()
   
    ###from pyuvvis.IO.gwu_interfaces import from_spec_files, get_files_in_dir
    ###from pyuvvis.exampledata import get_exampledata
    ###ts=from_spec_files(get_files_in_dir(get_exampledata('NPSAM'), sort=True), name='foofromfile')

    ###ts.to_interval('s')
    ###ts=ts.ix[440.0:700.0,0.0:100.0]
    ###ts.reference=0    
    ###print ts._baseline.shape, ts.shape
    
    #### Goes to site packages because using from_spec_files, which is site package module
    ###ts.run_pca()
 ####   ts.pca_evals

    ####from pandas import Panel
    ####Panel._constructor_sliced=TimeSpectra
    ####pdic={'ts':ts}
    ####tp=Panel.from_dict(pdic)
    
    ###d={'start':2/22/12, 'periods':len(ts.columns), 'freq':'45s'}
    ###ts.set_daterange(start='2/22/12', periods=len(ts.columns), freq='45s')
    
    ###ts.baseline=ts.reference
    ###ts.sub_base()

    #### THIS FAILS WHEN INDEX=SPEC 
    ###t3=TimeSpectra(abs(np.random.randn(ts.baseline.shape[0], 30)), columns=\
                   ###testdates, 
                   ###baseline=ts._baseline, name='foobar')  

    
       
    ####ts._reference.x='I WORK'
    ####ts._reference.name='joe'
    ###ts.baseline=Series([20,30,50,50], index=[400., 500., 600., 700.])
#####    t2.baseline=ts.baseline
    ####ts._df.ix[:, 0:4]
    ####ts.ix[:,0:4]
    ####ts.pvutils.boxcar(binwidth=20, axis=1)
    ####x=ts.ix[450.0:650.]
    ####y=t2.ix[500.:650.]
    
    ####ts.cnsvdmeth='name'
        
    ###from pyuvvis.pandas_utils.metadframe import mload
    ####from pyuvvis import areaplot, absplot
    ###ts=mload('rundata.pickle')    
    ###ts=ts.as_interval('m')
    ###x=ts.area()    
    ###print 'hi', x
    ####ts.reference=0
    ####ts=ts[ts.columns[800.0::]]
    ####ts=ts.ix[400.0:800.0]
    ####c=haiss_m2(ts, peak_width=2.0, ref_width=2.0)
    ####a=haiss_m3(ts, 0.000909, peak_width=None, dilution=0.1)
    ####b=haiss_conc(ts, 12.0)
    #####b2=haiss_conc(ts, 12.0, dilution=0.2)
    
#####    bline=ts[ts.columns[0]]
#####    ts=ts.ix[:,25.0:30.0]
#####    ts.reference=bline
 
    ####uv_ranges=((430.0,450.0))#, (450.0,515.0), (515.0, 570.0), (570.0,620.0), (620.0,680.0))
    
    ####tssliced=ts.wavelength_slices(uv_ranges, apply_fcn='mean')
        
    ####from pyuvvis.core.utilities import find_nearest
    ####x=ts.ix[500.:510, 0]
    ####b=pvutils.maxmin_xy(x)
    ####a=find_nearest(x, .15)
    ####ts.iunit=None
    ####ts.iunit='a'
    ####ts.iunit=None
    
    
    ####ts.to_csv('junk')
    ####range_timeplot(ts)

    ####ts.a=50; ts.b='as'
    ####ts.iunit='t'

    ####ts.list_attr(dfattr=False, methods=False, types=True)    
    ####ts.as_iunit('a')
    ####x=ts.as_iunit('a')
    #####ts.as_interval()
    #####spec_surface3d(ts)  ##Not working because of axis format problem
    #####plt.show()
#####    ts.rank(use_base=True)
    ####x=ts.dumps()
    ####ts=mloads(x)
