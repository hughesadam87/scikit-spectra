__docformat__ = 'restructuredtext' #What's this actually do

### Core classes
from pyuvvis.core.timespectra import TimeSpectra, mload, mloads
from pyuvvis.core.specindex import SpecIndex

### Plotting
from pyuvvis.pyplots.advanced_plots import spec_surface3d, surf3d, spec_poly3d, plot2d, plot3d 
from pyuvvis.pyplots.basic_plots import specplot, timeplot, absplot, range_timeplot, areaplot, _genplot    
from pyuvvis.pyplots.plot_utils import _df_colormapper, cmget  #???

### Pandas utilities
#---------------- Deprecated
#from pyuvvis.pandas_utils.dataframeserial import df_load, df_dump
#from pyuvvis.pandas_utils.df_attrhandler import transfer_attr

### Spectral utilities
from pyuvvis.core.spec_labeltools import spec_slice, datetime_convert, spectral_convert, spec_slice
from pyuvvis.core.baseline import dynamic_baseline #leave as function.

###IO (most common GWU imports)
from pyuvvis.IO.gwu_interfaces import from_timefile_datafile, get_files_in_dir, from_spec_files

### Correlation analysis (had to put in corr folder cuz of ****ing glitch!)
from pyuvvis.core.corr import ca2d, make_ref, sync_3d, async_3d  #Think these should stay as functions since not many people would use

### Running example data
from pyuvvis.exampledata import get_csvdataframe, get_exampledata
