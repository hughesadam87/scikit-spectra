''' Storage class for sets of pandas object.  Similar to a panel, 
    but does inherently store 3d data.  Data can be converted to 3d through
    methods, but otherwise is just a container.'''

from collections import OrderedDict, Iterable
from types import FunctionType
from copy import deepcopy

class AbstractStack(object):
    ''' Abstract base class to store pandas objects, with special operations to
        return as 3d data (eg panel) and to apply functions itemwise.  Items are
        stored in an ordered dict.'''
    
    itemlabel='Item'
    _magic=['__len__', '__iter__', '__reversed__', '__contains__']
    
    def __init__(self, data, items=None, name=None, sort_items=False):
        ## do stuff
        self.name=name
                                
        ### Dictionary input
        if isinstance(data, dict):
            if sort_items:
                self._data=OrderedDict(sorted(data.items(), key=lambda t: t[0]))

            else:
                self._data=OrderedDict(data)

        else:
            
            ### If data is not iterable
            if not isinstance(data, Iterable):
                data=[data]
            if items:
                if not isinstance(items, Iterable):
                    items=[items]

                if len(items) != len(data):
                    raise ValueError('Length mistmatch: items and data (%s,%s)'\
                    %(len(items), len(data)))
                
            ### If items not passed, generate them    
            else:
                items=self._gen_items(len(data))
 
            self._data=OrderedDict([(items[i],data[i]) for i in range(len(items))]) 
     
        self.__assign_magic()
      
    def _gen_items(self, lenght):
        ''' Return a list of itemlables (item0, item1 etc...) using
            self.itemlabel and a length'''
        return [self.itemlabel+str(i) for i in range(length)]                  
                
    #### Dictionary Interface ###
    def __getitem__(self, item):
        return self._data[item]
    
    def __delitem__(self, item):
        del self._data[item]
        
    #### Do I want to allow overwrite without restriction?    
    def __setitem__(self, item, value):
        ''' Changes item while preserving sort order.  If new item, 
            appended to end.'''
        self._data[item]=value     
                
    def __getattr__(self, attr):
        ''' If attribute not found, try attribute lookup in dictionary.  If
            that is not found, try finding attribute on self._data.
            
            For example, self.keys() will first look for self['keys'].  Since
            this isn't found, it calls self._data.keys().  But if I do 
            self.Item1, then it returns self['Item1'].  The very rare conflict
            case that a user has named the items a method that may already exist
            in the dictionary (eg items=['a','b','keys'] is addressed.'''
        if attr in self._data.keys():
            if hasattr(self._data, attr):
                raise AttributeError('"%s attribute" found in both the items\
                and as a method of the underlying dictionary object.'%(attr))
            else:
                return self[attr]
        return getattr(self._data, attr)
        

    def __assign_magic(self):
        for meth in self._magic:
            setattr(self, meth, getattr(self._data, meth))

    
 #   def __len__(self):
  #      return self._data.__len__()
    
    def __iter__(self):
        return self._data.__iter__()
    
    #def __reversed__(self):
        #return self._data.__reversed__
    
    #def __contains__(self, item):
        #return self._data.__contains__(item)
    
    #def __missing__(self, key):
        #return self._data.__missing__(key)
        
        
    
    def as_3d(self):
        ''' Return 3d structure of data.  Default is panel.'''
        raise Panel(data=self._data)
                 
        ### Data types without labels    
    
    def get_all(self, attr, ordered=False):
        '''Returns a tuple of (item, attribute) pairs for a given attribute.'''
        gen=((item[0], getattr(item[1], attr)) for item in self.items())
        if ordered:
            return OrderedDict(gen)
        return dict((item[0], getattr(item[1], attr)) for item in self.items())     
    
                
    def _get_unique(self, attr):
        ''' Inspects Stack itemwise for an attribute for unique values.
            If non-unique value for the attributes are found, returns
            "mixed". '''
        unique=set(self.get_all(attr).values())
        if len(unique) > 1:
            return 'mixed'
        else:
            return tuple(unique)[0] #set doesn't support indexing         
        
        
    def set_all(self, attr, val, inplace=False):
        ''' Set attributes itemwise.  
            If not inplace, returns new instance of self'''
        if inplace:
            for item in self:
                try:           
                    setattr(self[item], attr, val)    
                except Exception as E:
                    raise Exception('Could not set %s in %s.  Received the following \
                     exception:\n "%s"'%(attr, item, E))
        else:
            out=deepcopy(self._data) #DEEPCOPY            
            for item in out:
                setattr(out[item], attr, val)
                
            return self.__class__(out)

    def apply(self, func, *args, **kwargs):
        ''' Applies a user-passed function, or calls an instance method itemwise.
        
        
        Parameters:
        -----------
            func: If string, must correspond to a method on the object stored 
                  itemwise in the stack.  If a function, appliked itemwise to
                  objects stored.  
                  
           inplace:  Special kwarg.  If true, self._data modified inplace, 
                     otherwise new specstack is returned.
                             
           *args, **kwargs: 
                  Passed into the function directly if it requries additional
                  arguments.
          
        Returns:
        -----
            If not inplace, returns SpecStack after itemwise application.
            
            '''   

        inplace=kwargs.pop('inplace', False)
        
        if isinstance(func, basestring):
            if inplace:
                for item in self:
                    self[item]=getattr(self[item], func)(*args, **kwargs)      

            else:                
                return self.__class__(OrderedDict([(k, getattr(v, func)(*args, \
                                 **kwargs)) for k,v in self.items()]))                
                
        elif isinstance(func, FunctionType):
            if inplace:
                for item in self:
                    self[item]=self[item].apply(func)(*args, **kwargs)
                    
            else:
                return self.__class__(OrderedDict([(k, v.apply(func, *args, \
                                 **kwargs)) for k,v in self.items()]))                  
                
        else:
            raise AttributeError('func must be a basestring corresponding to\
            an instance method or a function.  %s is invalid.'%type(func))
          
               
class SpecStack(AbstractStack):
    ''' Stack for just storing timespectra objects.'''

    def as_3d(self, **kwargs):
        ''' Returns a 3d stack (SpecPanel) of the currently stored items.
            Additional kwargs can be passed directly to SpecPanel constructor.'''
        from specpanel import SpecPanel      
        return SpecPanel(data=self._data, **kwargs)        
    
    
    ### Special properties for swift, in-place attribute overwrites of most 
    ### common itemwise operation.  Getter only tests for uniqueness
    
    @property
    def specunit(self):
        return self._get_unique('specunit')
                
    ### Do I want to make as a _set method to avoid accidental overwrite?
    @specunit.setter
    def specunit(self, unit):
        ''' Sets specunit for every stored TimeSpectra.'''
        self.set_all('specunit', unit, inplace=True)
    
    @property
    def iunit(self):
        return self._get_unique('iunit')    
    
    @iunit.setter
    def iunit(self, unit):
        ''' Sets iunit for every stored TimeSpectra.'''
        self.set_all('iunit', unit, inplace=True)    
        
    @property
    def reference(self):
        return self._get_unique('reference')
    
    @reference.setter
    def reference(self, ref):
        ''' Set reference itemwise.  No getter, use get_all() instead.'''
        self.set_all('reference', ref, inplace=True)

    ### This shouldn't have a setter
    @property
    def timeunit(self):
        return self._get_unique('timeunit')   
    

if __name__=='__main__':
    ### For testing.
    from pyuvvis import specplot
    from pyuvvis.core.specindex import SpecIndex
    from pyuvvis.core.timespectra import TimeSpectra
    from pandas import date_range, DataFrame, Index

    import numpy as np       
    import matplotlib.pyplot as plt

    
    spec=SpecIndex(np.arange(400, 700,10), unit='nm' )
    spec2=SpecIndex(np.arange(400, 700,10), unit='m' )
    
    testdates=date_range(start='3/3/12',periods=30,freq='h')
    testdates2=date_range(start='3/3/12',periods=30,freq='h')
    
    ts=TimeSpectra(abs(np.random.randn(30,30)), columns=testdates, index=spec)  
    t2=TimeSpectra(abs(np.random.randn(30,30)), columns=testdates2, index=spec2) 
    d={'d1':ts, 'd2':t2}

    ##x=Panel(d)
    y=SpecStack(d)
    x=y.set_all('specunit', 'cm')
    y._get_unique('specunit')
    y.apply('wavelength_slices', 8)
    y['d1']
    
    x=y.apply(np.sqrt, axis='items')
    #y.applynew('boxcar', binwidth=10)
    #y.applynew(boxcar, binwidth=10)
    ##print y.specunit
    ##y.specunit='f'
    #print 'hi'