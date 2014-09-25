import os.path as op

__docformat__ = 'restructuredtext' #What's this actually do

### Core classes
from pyuvvis.core.spectra import Spectra
from pyuvvis.core.timespectra import TimeSpectra
from pyuvvis.core.specstack import SpecStack

### Correlation analysis
from pyuvvis.core.corr import Corr2d

#from pyuvvis.core.specindex import SpecIndex
#from pyuvvis.core.utilities import maxmin_xy


#### MetaDataframe utilities
#from pyuvvis.pandas_utils.metadframe import mload as tsload
#from pyuvvis.pandas_utils.metadframe import mloads as tsloads

#### Spectral utilities
#from pyuvvis.core.spec_labeltools import spec_slice, datetime_convert, \
    #spectral_convert, spec_slice
#from pyuvvis.core.baseline import dynamic_baseline #leave as function.

####IO (most common GWU imports)
#from pyuvvis.IO.gwu_interfaces import from_timefile_datafile, get_files_in_dir, \
    #from_spec_files

#### Correlation analysis (had to put in corr folder cuz of ****ing glitch!)
#from pyuvvis.core.corr import ca2d, make_ref, sync_3d, async_3d  #Think these should stay as functions since not many people would use


#  Borrowing API from skimage
pkg_dir = op.abspath(op.dirname(__file__))
data_dir = op.join(pkg_dir, 'data')
bundled_dir = op.join(pkg_dir, 'bundled')

#Abspath will merge the .. and go up and into examples
examples_dir = op.abspath(op.join(pkg_dir, '../examples/Notebooks'))
