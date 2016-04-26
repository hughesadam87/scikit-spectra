import sys
import operator
import nose
import unittest
import numpy as np
import pandas.util.testing as tm
from nose.tools import *
from copy import deepcopy
from numpy.testing import *
from skspec import AnyFrame, Spectra, TimeSpectra, SpecStack
from skspec.core.abcindex import ConversionIndex, CustomIndex, ConversionFloat64Index
from skspec.core.specindex import SpecIndex
from skspec.core.timeindex import TimeIndex
from skspec.data import aunps_glass
from skspec.units import SPECUNITS


ts = aunps_glass()

class test_timespectra(tm.TestCase):
    def test_specunits(self):
        k1 = ts.specunits().keys()
        k2 = SPECUNITS.keys()
        self.assertListEqual(sorted(k1),sorted(k2))
        
    def test_specindex(self):
        h=float(6.626068*10**-34)          
        eVtoJ=float(1.60217646 * 10**-19)
        c=float(299792458)        
        ts1 = ts.as_specunit('nm')
        index1 = np.array(ts1.index)*.000000001
        ts2 = ts.as_specunit('ev')
        index2 = (h*c)/(eVtoJ*np.array(ts2.index))
        assert_array_almost_equal(index1,index2)
    
    #def test_varunits(self):
        #ts = aunps_glass()
        #var1 = ts.varunits().keys()
        #var2 = VARUNITS.keys()
        #self.assertListEqual(sorted(var1),sorted(var2)) 
        
    #def test_baseline(self):
        
    def test_timeindex(self):
        ts1 = ts.as_varunit('s')
        time1 = np.array(ts1.columns)
        ts2 = ts.as_varunit('m')
        time2 = np.array(ts2.columns)*60
        assert_array_almost_equal(time1,time2)
        

    def test_subbase(self):
        AMP = 100
        ts.baseline = AMP * np.random.randn(ts.shape[0])
        ts.sub_base()        
        ts1 = aunps_glass()
        for item in ts1.columns:
            ts1[item] -= ts.baseline
            assert_array_almost_equal(ts[item],ts1[item])
        
    def test_addbase(self):
        AMP = 100
        ts.baseline = AMP * np.random.randn(ts.shape[0])
        ts.sub_base() 
        ts.add_base()
        ts1 = aunps_glass()
        for item in ts1.columns:
            assert_array_almost_equal(ts[item],ts1[item])        
        
        
    def test_numeric(self):
        tsquared = ts**2
        for item in ts.columns:
            assert_array_almost_equal(ts[item]**2,tsquared[item])        