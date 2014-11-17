import os.path as op

__docformat__ = 'restructuredtext' #What's this actually do

### Core classes
from pyuvvis.core.spectra import Spectra
from pyuvvis.core.timespectra import TimeSpectra
from pyuvvis.core.anyspectra import AnyFrame
from pyuvvis.core.specstack import SpecStack

from pyuvvis.units.abcunits import Unit

#  Borrowing API from skimage
pkg_dir = op.abspath(op.dirname(__file__))
data_dir = op.join(pkg_dir, 'data')
bundled_dir = op.join(pkg_dir, 'bundled')

#Abspath will merge the .. and go up and into examples
examples_dir = op.abspath(op.join(pkg_dir, '../examples/Notebooks'))
