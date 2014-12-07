"""Provides core "TimeSpectra" class and associated utilities."""

import logging
from skspec.logger import decode_lvl, logclass
from pandas import DatetimeIndex, Index
from skspec.core.spectra import _valid_xunit
from skspec.units.intvlunit import INTVLUNITS, DatetimeCanonicalError
from skspec.core.timeindex import TimeIndex
from spectra import Spectra

logger = logging.getLogger(__name__) 

def _valid_intvlunit(sout):
    """ Validate interval unit."""
    return _valid_xunit(sout, intvl_dic)

# Ignore all class methods!
#@logclass(log_name=__name__, skip = ['wraps','_framegetattr', 'from_csv', 
 #                                    '_comment', '_transfer'])
class TimeSpectra(Spectra):
    """ Spectra that enforces a TimeIndex.  TimeIndex converts representations
    between DatetimeIndex and Intervals.

    Parameters
    ----------

    force_datetime: bool (False)
        Convienence method for when a user is passing in datetimes, but does
        not have them in a DatetimeIndex.  The only use case we've found is
        trying to parse CSV files; the datetimes are a list of strings and
    """


    # Has to be this way because class methods not accessible via metadataframe __getattr__()
    def __init__(self, *dfargs, **dfkwargs):
        dfkwargs.setdefault('strict_columns', TimeIndex)            
        super(TimeSpectra, self).__init__(*dfargs, **dfkwargs)
        


## TESTING ###
if __name__ == '__main__':
    from specindex import SpecIndex
    from pandas import date_range
    import numpy as np
    from skspec.data import solvent_evap, aunps_glass, aunps_water
    
    x = AnyFrame(np.random.randn(50,50))
    print x

    def sumdiff(array, absolute=False, cumsum=False):
        """ Sum of the differences of an array (usually array of areas).  If absolute, absolute difference is used.
        If cumsum, the cumulative sum is returned.
        """
        sdiff = []
        # Compute the forward difference up to i=final -1
    #    array = array.values
        for idx, value in enumerate(array):
            if idx < len(array)-1:
                new = array[idx+1]
                out = new-value          
                if absolute:
                    out = abs(out)        
                sdiff.append(out)
    
        if cumsum:
            sdiff = list(np.cumsum(sdiff)) 
        sdiff.append(sdiff[-1]) #REPEAST LAST VALUE
        return sdiff

    ts = aunps_glass()

    ts.iunit = None #is the most accurate
    ts.varunit = 'm'
    from pandas import Index
    ts.columns = Index(ts.columns)
    area = ts.area()
    
    DIFF = area.apply(sumdiff, axis=1, raw=False)
    

    # Be careful when generating test data from Pandas Index/DataFrame objects, as this module has overwritten their defaul behavior
    # best to generate them in other modules and import them to simulate realisitc usec ase


    ## For testing 
    #import matplotlib.pyplot as plt


    #from skspec.data import aunps_water, aunps_glass
    #from skspec.plotting import splot, range_timeplot
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

    #ts=TimeSpectra(abs(np.random.randn(300,30)), 
##                   columns=testdates, 
                    #index=spec, 
                    #name='ts1')  

    #print ts.list_varunits()
    #print ts.list_specunits()

    ###t2=TimeSpectra(abs(np.random.randn(300,30)), 
                    ###columns=testdates2, 
                    ###index=spec, 
                    ###name='ts2') 

    import matplotlib.pyplot as plt
    from skspec.plotting import areaplot
    ts = solvent_evap()
    ts = ts.as_varunit('m')

    from pandas import DataFrame
    df = DataFrame(np.random.randn(50,50), index=np.linspace(0,50,50))
    
#    ts.nearby[900:]
    ts.nearby[[1200,1400]]
        
    ts.iloc[:, 2:4.4].columns
    ts._frame.iloc[:, 2:4.4].columns
#    ts = aunps_glass()
    print ts.ix[1505.0:1500.0]
    #ts.loc[:, 50.5, 520.0]
    ##area = ts.area()
    ##tf=ts[ts.columns[-1]]
    ##print tf 
    #cols = ts.columns[0:5]
    #c2 = ts.columns[0:5].convert('m')
    #c2.datetimeindex
    #mins = cols.convert('m')
    #print mins
    #ts.as_varunit('m')

    #t2 = ts.ix[1500.0:1000.0]
    #print ts.index
    #print t2.index


    ##t2 = ts.as_interval('m')

    ##t2 = t2.as_iunit('r')

    ###stack = ts.split_by(1)
    ###stack.iunit = 'a'

    ###ts[ts.columns[0]].plot(colormap='RdBu')
    ###plt.show()
    ##t2 = ts.as_interval('m')
    ###t2 = ts.as_iunit('r')
    ###ts.area().plot()
    ###import sys
    ###sys.exit()

####    stack.plot(title='Big bad plots')
    ##from skspec.plotting import six_plot
    ##import matplotlib.pyplot as plt
    ##six_plot(ts, striplegend=True)
    ##plt.show()
    ###t1 = ts.as_interval()
    ###print t1.columns
    ###t1.plot(cbar=True)
    ###t1.to_datetime()
    ###t1.ix[500.0:600.0]
    ###t2 = ts.as_specunit('ev')
    ###t3 = ts.as_iunit('a')
    ###print t2.specunit, 'hi t2'
    ###print t3.specunit, 'hi t3'
    ###print t2.specunit, 'hi t2'
    ###specplot(ts, cbar=True)



####    a=ts.area()
####    print 'hi', a.specunit
####    ts.specunit = 'ev'
    ####from skspec.plotting import specplot, areaplot
    ####areaplot(ts)
    ####plt.show()

    ####from skspec.IO.gwu_interfaces import from_spec_files, get_files_in_dir
    ####from skspec.exampledata import get_exampledata
    ####ts=from_spec_files(get_files_in_dir(get_exampledata('NPSAM'), sort=True), name='foofromfile')

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
    ####ts._frame.ix[:, 0:4]
    ####ts.ix[:,0:4]
    ####ts.pvutils.boxcar(binwidth=20, axis=1)
    ####x=ts.ix[450.0:650.]
    ####y=t2.ix[500.:650.]

    ####ts.cnsvdmeth='name'

    ###from skspec.pandas_utils.metadframe import mload
    ####from skspec import areaplot, absplot
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

    ####from skspec.core.utilities import find_nearest
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