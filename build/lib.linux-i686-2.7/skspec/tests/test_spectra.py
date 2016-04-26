""" Tests for skspec.core.Spectra class.  Much inspiration was taken from the pandas
amazing test suite, so thank you to the pandas team for such diligence.

https://github.com/pydata/pandas/blob/master/pandas/tests/test_frame.py
"""


from copy import deepcopy

import sys
import operator
import nose

from numpy import random, nan
from numpy.random import randn
import numpy as np
import numpy.ma as ma
from numpy.testing import assert_array_equal
import numpy.ma.mrecords as mrecords
