import os.path as op

__docformat__ = 'restructuredtext' #What's this actually do

### Core classes
from skspec.core.spectra import Spectra
from skspec.core.timespectra import TimeSpectra
from skspec.core.anyspectra import AnyFrame
from skspec.core.specstack import SpecStack

from skspec.units.abcunits import Unit

#  Borrowing API from skimage
pkg_dir = op.abspath(op.dirname(__file__))
data_dir = op.join(pkg_dir, 'data')
bundled_dir = op.join(pkg_dir, 'bundled')

#Abspath will merge the .. and go up and into examples
examples_dir = op.abspath(op.join(pkg_dir, '../examples/Notebooks'))
