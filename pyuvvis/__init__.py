__docformat__ = 'restructuredtext' #What's this actually do

### Core classes
from pyuvvis.core.timespectra import TimeSpectra, mload, mloads
from pyuvvis.core.specindex import SpecIndex

### Plotting
from pyuvvis.pyplots.advanced_plots import spec_surface3d, surf3d, spec_poly3d, plot2d, plot3d   #Make instance methods
from pyuvvis.pyplots.basic_plots import specplot, timeplot, absplot, range_timeplot, _genplot    #Make instance methods (cept _genplot)
from pyuvvis.pyplots.plot_utils import _df_colormapper, cmget  #???

### Pandas utilities
#---------------- Deprecated
#from pyuvvis.pandas_utils.dataframeserial import df_load, df_dump
#from pyuvvis.pandas_utils.df_attrhandler import transfer_attr

### Spectral utilities
from pyuvvis.core.spec_labeltools import spec_slice, datetime_convert, spectral_convert, spec_slice
from pyuvvis.core.spec_utilities import boxcar, wavelength_slices, divby  #Make instance methods? (remove divby since timespec can do that?)
#I think instance method version of boxcar should be sure to smooth baseline (how to do this non-generically?)
#and for that matter, IX should probably cut baseline too.
from pyuvvis.core.baseline import dynamic_baseline #leave as function.
from pyuvvis.core.imk_utils import make_root_dir, get_files_in_dir, get_shortname

###IO
from pyuvvis.IO.gwu_interfaces import from_timefile_datafile, get_files_in_dir, from_spec_files

### Correlation analysis (had to put in corr folder cuz of ****ing glitch!)
from pyuvvis.core.corr import ca2d, make_ref, sync_3d, async_3d  #Think these should stay as functions since not many people would use

### Running example data
from pyuvvis.exampledata import get_csvdataframe, get_exampledata
from pyuvvis.custom_errors import badvalue_error
