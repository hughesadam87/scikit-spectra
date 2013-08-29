""" SpecStack: Similar to pandas Panel but built to 
    store TimeSpectra classes."""

from pandas.core.panel import Panel
from pyuvvis.core.timespectra import TimeSpectra
from pyuvvis.core.utilities import boxcar
from pandas.core.generic import PandasObject


class SpecStack(Panel):
    
    _constructor_sliced = TimeSpectra    
    
    def __init__(self, data=None, items=None, spectral=None, temporal=None,
                     copy=False, dtype=None, name=None):
        '''Initialize with same arguments as panel, with special keywords
           for the SpecStack object.
           
        Parameters:
        -----------
            See Panel API for Panel__init__() arguments.
            name: name of the SpecStack object.'''
            
        super(SpecStack, self).__init__(data=data, items=items, major_axis=
                             spectral, minor_axis=temporal, copy=copy,
                             dtype=dtype)      
       
        self.name=name
                
    def _get_unique(self, attr):
        ''' Inspects SpecStack itemwise for an attribute for unique values.
            If non-unique value for the attributes are found, returns
            "mixed". '''
        unique=set(self.inspect(attr).values())
        if len(unique) > 1:
            return 'mixed'
        else:
            return tuple(unique)[0] #set doesn't support indexing        
        
    def _set_attr(self, attr, val):
        ''' Set attributes itemwise.'''
        for item in self:
            setattr(self[item], attr, val)
            
    def inspect(self, attr):
        '''Returns a dictionary of items:attribute for a given attribute.'''
        return dict((item, getattr(self[item], attr)) for item in self.items)
    
    @property
    def specunit(self):
        return self._get_unique('specunit')
                
    ### Do I want to make as a _set method to avoid accidental overwrite?
    @specunit.setter
    def specunit(self, unit):
        ''' Sets specunit for every stored TimeSpectra.'''
        self._set_attr('specunit', unit)
    
    @property
    def iunit(self):
        return self._get_unique('iunit')    
    

    ### This shouldn't have a setter
    @property
    def timeunit(self):
        return self._get_unique('timeunit')
    
    def applynew(self, func, *args, **kwargs):
        for item in self:
            self[item]=getattr(self[item], func)(*args, **kwargs)

SpecStack._setup_axes(axes      = ['items', 'spectral', 'temporal'], 
                  info_axis = 0,
                  stat_axis = 1,
                  aliases   = { 0: 'index',
                                1: 'columns' },
                  slicers   = { 'spectral': 'index',
                                'temporal': 'columns' })
                                              
                       
    
if __name__=='__main__':
    ### For testing.
    from pyuvvis.core.specindex import SpecIndex
    from pandas import date_range, DataFrame, Index
    import numpy as np       

    
    spec=SpecIndex(np.arange(400, 700,10), unit='nm' )
    spec2=SpecIndex(np.arange(400, 700,10), unit='m' )
    
    testdates=date_range(start='3/3/12',periods=30,freq='h')
    testdates2=date_range(start='3/3/12',periods=30,freq='h')
    
    ts=TimeSpectra(abs(np.random.randn(30,30)), columns=testdates, index=spec)  
    t2=TimeSpectra(abs(np.random.randn(30,30)), columns=testdates2, index=spec2) 
    d={'d1':ts, 'd2':t2}
     
    ts._df.name='n1'
    t2._df.name='n2'
   
#    dfs={'d1':ts._df, 'd2':t2._df}   
 #   ps2=Panel(dfs)
  #  print ps2
    
   
    #print d['d1'].specunit, 'too'
    ##x=Panel(d)
    y=SpecStack(d)
    y['d1']
    
    print y
    y.applynew('area')

    x=y.apply(np.sqrt, axis='items')
    #y.applynew('boxcar', binwidth=10)
    #y.applynew(boxcar, binwidth=10)
    ##print y.specunit
    ##y.specunit='f'
    #print 'hi'