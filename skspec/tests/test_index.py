""" Tests for skspec.core.index module.  Much inspiration was taken from the pandas
amazing test suite, so thank you to the pandas team for such diligence.

https://github.com/pydata/pandas/blob/master/pandas/tests/testindex.py
"""

from copy import deepcopy

import sys
import operator
import nose

