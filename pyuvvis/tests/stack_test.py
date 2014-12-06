""" SpecStack: Similar to pandas Panel but built to 
    store TimeSpectra classes."""

from pandas.core.panel import Panel
from skspec.core.timespectra import TimeSpectra
from skspec.core.utilities import boxcar


#class SpecStack(Panel):
    
    #_constructor_sliced = TimeSpectra    
    
    #def __init__(self, data=None, items=None, major_axis=None, minor_axis=None,
                     #copy=False, dtype=None, name=None):
        #'''Initialize with same arguments as panel, with special keywords
           #for the SpecStack object.
           
        #Parameters:
        #-----------
            #See Panel API for Panel__init__() arguments.
            #name: name of the SpecStack object.'''
            
        #super(SpecStack, self).__init__(data=data, items=items, major_axis=
                             #major_axis, minor_axis=minor_axis, copy=copy,
                             #dtype=dtype)      
       
        #self.name=name
                
    #def _get_unique(self, attr):
        #''' Inspects SpecStack itemwise for an attribute for unique values.
            #If non-unique value for the attributes are found, returns
            #"mixed". '''
        #unique=set(self.inspect(attr).values())
        #if len(unique) > 1:
            #return 'mixed'
        #else:
            #return tuple(unique)[0] #set doesn't support indexing        
        
    #def _set_attr(self, attr, val):
        #''' Set attributes itemwise.'''
        #for item in self:
            #setattr(self[item], attr, val)
            
    #def inspect(self, attr):
        #'''Returns a dictionary of items:attribute for a given attribute.'''
        #return dict((item, getattr(self[item], attr)) for item in self.items)
    
    #@property
    #def specunit(self):
        #return self._get_unique('specunit')
                
    #### Do I want to make as a _set method to avoid accidental overwrite?
    #@specunit.setter
    #def specunit(self, unit):
        #''' Sets specunit for every stored TimeSpectra.'''
        #self._set_attr('specunit', unit)
    
    #@property
    #def iunit(self):
        #return self._get_unique('iunit')    
    

    #### This shouldn't have a setter
    #@property
    #def timeunit(self):
        #return self._get_unique('timeunit')
    

    ##def apply(self, func, axis='major'):
        ##"""
        ##Apply

        ##Parameters
        ##----------
        ##func : numpy function
            ##Signature should match numpy.{sum, mean, var, std} etc.
        ##axis : {'major', 'minor', 'items'}
        ##fill_value : boolean, default True
            ##Replace NaN values with specified first

        ##Returns
        ##-------
        ##result : DataFrame or Panel
        ##"""
        ##i = self._get_axis_number(axis)
        ##result = np.apply_along_axis(func, i, self.values)
        ##return self._wrap_result(result, axis=axis)
    
    #def applynew(self, func, *args, **kwargs):
        #for item in self:
            #self[item]=getattr(self[item], func)(*args, **kwargs)

##SpecStack._setup_axes(axes      = ['items', 'major_axis', 'minor_axis'], 
                  ##info_axis = 0,
                  ##stat_axis = 1,
                  ##aliases   = { 'spectral': 'major_axis',
                                ##'temporal': 'minor_axis' },
                  ##slicers   = { 'major_axis': 'index',
                                #'minor_axis': 'columns' })

from pandas.core import panelnd
from pandas.core.generic import NDFrame
import numpy as np
from pandas import DataFrame

class PanelNew(NDFrame):

    @property
    def _constructor(self):
        return type(self)

    _constructor_sliced = DataFrame

PanelNew._setup_axes(axes      = ['items', 'spectral', 'temporal'], 
                  info_axis = 0,
                  stat_axis = 1,
                  aliases   = { 'spectral': 'major_axis',
                                'temporal': 'minor_axis' },
                  slicers   = { 'spectral': 'index',
                                'temporal': 'columns' })

if __name__=='__main__':
    ### For testing.
    #from skspec.core.specindex import SpecIndex
    #from pandas import date_range, DataFrame, Index
    #import numpy as np       

    x=TimeSpectra([1,1,1])
    y=PanelNew(x) 
    print y