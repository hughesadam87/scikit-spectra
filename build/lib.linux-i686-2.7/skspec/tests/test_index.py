""" Tests for skspec.core.index module.  Much inspiration was taken from the pandas
amazing test suite, so thank you to the pandas team for such diligence.

https://github.com/pydata/pandas/blob/master/pandas/tests/testindex.py
"""
import sys
import operator
import nose
import unittest
import warnings
import numpy as np
import pandas.util.testing as tm
from nose.tools import *
from copy import deepcopy
from numpy.testing import *
from pandas import DatetimeIndex
from skspec import AnyFrame, Spectra, TimeSpectra, SpecStack
from skspec.core.abcindex import ConversionIndex, CustomIndex, ConversionFloat64Index
from skspec.core.specindex import SpecIndex
from skspec.core.timeindex import TimeIndex
from skspec.data import aunps_glass


class TestIndex(tm.TestCase):
    def test_timeindex(self):
        ts = aunps_glass().iloc[0:3,0:3]
        sindex = SpecIndex([430.1, 430.47, 430.85])
        tindex = TimeIndex(DatetimeIndex(['2014-05-22 15:38:23', '2014-05-22 15:38:26', ' 2014-05-22 15:38:30']))
        self.assertTrue(ts.columns.equals(tindex))
        
    def test_specindex(self):
        sindex = SpecIndex(['430.0','431.0','432.0'])
        data = [[257,258,259],[267,268,269],[278,279,280]]
        s = Spectra(data, index = sindex)
        self.assertTrue(s.index.equals(sindex))    
        
    def test_timetype(self):
        tindex1 = TimeIndex(['2014-05-22 15:38:23', '2014-05-22 15:38:26', ' 2014-05-22 15:38:30'])
        tindex2 = DatetimeIndex(['2014-05-22 15:38:23', '2014-05-22 15:38:26', ' 2014-05-22 15:38:30'])
        self.assertFalse(tindex1.identical(tindex2))



class TestIndexing(tm.TestCase):        
    def test_nearby(self):
        ts = aunps_glass()
        start = 500
        end = 600
        values = np.array(ts.index)
        sstart = (np.abs(values - start)).argmin()
        send = (np.abs(values - end)).argmin()
        ts1 = ts.nearby[start:end]
        ind1 = ts1.index
        ind2 = ts.index[sstart:send+1]
        self.assertTrue(ind1.equals(ind2))    
    
    
