"""Provides core "TimeSpectra" class and associated utilities."""

import logging
from pyuvvis.logger import decode_lvl, logclass
from spectra import Spectra

logger = logging.getLogger(__name__) 

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
        
        super(TimeSpectra, self).__init__(*dfargs, **dfkwargs)
    
    

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
