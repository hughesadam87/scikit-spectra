## For testing
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D

import pkgutil

from scipy import integrate
import numpy as np

from pyuvvis.pyplots.advanced_plots import spec_surface3d, surf3d, spec_poly3d
from pyuvvis.pandas_utils.dataframeserial import df_loads
from pyuvvis.pandas_utils.df_attrhandler import transfer_attr
from pyuvvis.core.spec_labeltools import datetime_convert, spectral_convert
from pyuvvis.core.spec_utilities import boxcar, wavelength_slices, divby
from pyuvvis.pyplots.spec_aesthetics import specplot, timeplot, absplot, range_timeplot, _df_colormapper
from pyuvvis.IO.gwu_interfaces import from_gwu_chem_IR, from_timefile_datafile, get_files_in_dir



if __name__=='__main__':
 #   filelist=get_files_in_dir('~./pyuvvis/data/gwuspecdata/NPConcentration')
 #   df=from_gwu_chem_IR(filelist, sortnames=True)
   # df=from_timefile_datafile('./npsam/All_f1_npsam_by_1', './npsam/f1_npsam_timefile.txt')
    
    
    
    df_stream=pkgutil.get_data('pyuvvis', 'data/example_data/spectra.pickle') 
    df=df_loads(df_stream)
    
    ### subtract the dark spectrum
    df=df.sub(df.baseline, axis='index')


    df.columns=datetime_convert(df.columns, return_as='seconds')
    

    #df=boxcar(df, 2.0)
    dfsliced=wavelength_slices(df, ranges=((350.0,370.0), (450.0,500.0), (550.0,570.0), (650.0,680.0), (680.0,700.0)),\
                               apply_fcn='simps')
                             #  apply_fcn=np.histogram, bins=3)

    dfarea=wavelength_slices(df, ranges=(min(df.index), max(df.index)), apply_fcn='simps')
                             
    df=df.ix[400.0:700.0]
   # colormapper=_df_colormapper(df, axis=0, vmin=300.0, vmax=700.0, cmap=cm.gist_heat)
    #specplot(df, colors=colormapper)
    #plt.show()

#    timeplot(df, colors=_df_colormapper(df, axis=1,cmap=cm.autumn))
    range_timeplot(dfsliced)
    plt.show()
    df=boxcar(df, 10.0, axis=1)


    df=df.ix[400.0:800.0] 
    #df=df.ix[500.0:600.0]
   
    #spec_surface3d(df, kind='contourf', xlabel='Time (s)', ylabel='Wavelength (nm)')
  

    #plt.title('9/5/12 NPSam')
    #plt.show()
              
    #spec_surface3d(df, kind='contourf', xlabel='Time (s)', ylabel='Wavelength (nm)')
    #spec_surface3d(df)



    #mlab.surf(np.asarray(list(df.columns)), np.asarray(list(df.index)) , np.asarray(df), warp_scale='auto')
    spec_poly3d(df)
    plt.show()

    #transfer_attr(df, df2)     
    #specax=specplot(df2)

    #dftime=df.transpose()  ### Store a custom axis.
    #dftime.runname='Spec test name'
    #timeax=timeplot(dftime)
    #fig = plt.figure()
    #fig.axes.append(timeax)

    hz=spectral_convert(df.index)
    print 'hi'
    #df=df.transpose()
    #plt.figure()
    #df.plot()
    #plt.leged=False
    #plt.show()
