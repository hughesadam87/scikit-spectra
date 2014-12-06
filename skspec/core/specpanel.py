''' Interface to make a panel-type object for storing timespectra.  Allows for
    axis aliases like "spectral" and "temporal" slicers.'''

from pandas.core.panel import Panel
from skspec.core.timespectra import TimeSpectra

class SpecPanel(Panel):
    
    _constructor_sliced = TimeSpectra
    
    def __init__(self, data=None, items=None, spectral=None, temporal=None,
                        copy=False, dtype=None, name=None):
    
        '''Initialize with same arguments as panel, with special keywords
          for the SpecStack object.
          
         Parameters:
        -----------
           See Panel API for Panel__init__() arguments.
           name: name of the SpecStack object.'''    
          
        super(SpecPanel, self).__init__(data=data, items=items, major_axis=
                           spectral, minor_axis=temporal, copy=copy,
                           dtype=dtype)      
       

SpecPanel._setup_axes(axes      = ['items', 'spectral', 'temporal'], 
                  info_axis = 0,
                  stat_axis = 1,
                  aliases   = { 0: 'index',
                                1: 'columns' },
                  slicers   = { 'spectral': 'index',
                                'temporal': 'columns' })