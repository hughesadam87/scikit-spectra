''' Provides composition class, MetaPandasObject, which is an ordinary python object that stores a Dataframe and 
attempts to promote attributes and methods to the instance level (eg self.x instead of self.df.x).  This object
can be subclassed and ensures persistence of custom attributes.  The goal of this MetaPandasObject is to provide a 
subclassing api beyond monkey patching (which currently fails in persisting attributes upon most method returns 
and upon derialization.'''

from types import MethodType
import copy
import functools
import cPickle
import collections

from pandas.core.indexing import _IXIndexer, _iLocIndexer, _LocIndexer

from pandas import DataFrame, Series

# for testing
from numpy.random import randn

# Logging functions
from skspec.logger import logclass
import logging
logger = logging.getLogger(__name__) 

#----------------------------------------------------------------------
# Store attributes/methods of dataframe for later inspection with __setattr__
# Note: This is preferred to a storing individual instances of self._frame with custom 
#       attr as if user tried self.a and self._frame.a existed, it would call this...
_dfattrs=[x for x in dir(DataFrame) if '__' not in x]

#----------------------------------------------------------------------
# Loading (perhaps change name?) ... Doesn't work correctly as instance methods

def mload(inname):
    ''' Load MetaPandasObject from file'''
    if isinstance(inname, basestring):
        inname=open(inname, 'r')
    return cPickle.load(inname)

def mloads(string):
    ''' Load a MetaPandasObject from string stored in memory.'''
    return cPickle.loads(string)        
        

# Log all public/private methods to debug
#@logclass(public_lvl='debug', log_name=__name__, skip=['_transfer'])
class MetaPandasObject(object):
    ''' Base composition for subclassing pandas DataFrame and Series.'''
    
    cousin = None #OVERWRITE
    
    def __init__(self, *dfargs, **dfkwargs):
        ''' Stores a dataframe under reserved attribute name, self._frame'''      
        self._frame = self.cousin(*dfargs, **dfkwargs)

    ### Save methods    
    def save(self, outname):
        ''' Takes in str or opened file and saves. cPickle.dump wrapper.'''
        if isinstance(outname, basestring):
            outname=open(outname, 'w')
        cPickle.dump(self, outname)

    def dumps(self):
        ''' Output TimeSpectra into a pickled string in memory.'''
        return cPickle.dumps(self)    

    #----------------------------------------------------------------------
    # Overwrite Dataframe methods and operators

    def __getitem__(self, keyslice):
        ''' Item lookup.  If output is an interable, _transfer is called.  
        Sometimes __getitem__ returns a float (indexing a series) at which 
        point we just want to return that.'''

        frameout=self._frame.__getitem__(keyslice)

        try:
            iter(frameout)  #Test if iterable without forcing user to have collections package.
        except TypeError:
            return frameout
        else:
            return self._transfer(self._frame.__getitem__(keyslice) )               

    def __setitem__(self, key, value):
        self._frame.__setitem__(key, value)    

    ### These tell python to ignore __getattr__ when pickling; hence, treat this like a normal class    
    def __getstate__(self): return self.__dict__
    def __setstate__(self, d): self.__dict__.update(d)    

    def __getattr__(self, attr, *fcnargs, **fcnkwargs):
        ''' Tells python how to handle all attributes that are not found.
        Basic attributes are directly referenced to self._frame; however, 
        instance methods (like df.corr() ) are handled specially using a
        special private parsing method, _framegetattr().'''

        # Return basic attribute        
        try:
            refout = getattr(self._frame, attr)
        except AttributeError:
            raise AttributeError('Either failed to find attribute "%s" in %s or '
             'its underlying pandas object, or it is found, but throwing an error'
             ' when accessed.'%(attr, self.__class__.__name__))           
           
        if not isinstance(refout, MethodType):
            return refout

        # Handle instance methods using _framegetattr().
        # see http://stackoverflow.com/questions/3434938/python-allowing-methods-not-specifically-defined-to-be-called-ala-getattr
        else:         
            return functools.partial(self._framegetattr, attr, *fcnargs, **fcnkwargs)
            # This is a reference to the fuction (aka a wrapper) not the function itself
            
    def __setattr__(self, name, value):
        ''' When user sets an attribute, this tries to intercept any name conflicts.  For example, if user attempts to set
        self.columns=50, this will actually try self._frame.columns=50, which throws an error.  The behavior is acheived by
        using dir() on the data frame created upon initialization, filtering __x__ type methods.   Not guaranteed to work 100%
        of the time due to implicit possible issues with dir() and inspection in Python.  Best practice is for users to avoid name
        conflicts when possible.'''
        
        super(MetaPandasObject, self).__setattr__(name, value)        
        if name in _dfattrs:
            setattr(self._frame, name, value)
        else:
            self.__dict__[name]=value


    def _transfer(self, dfnew):
        """ Copy current attributes into a new dataframe.  For methods that
        return a dataframe and need to append current attributes/columns/index.
        """
        newobj = copy.deepcopy(self)  #This looks like None, but is it type (MetaPandasObject, just __union__ prints None
        newobj._frame = dfnew
        
        # THESE ARE NEVER TRANSFERED AT DF LEVEL, JUST CREATED NEW.  TRY
        # df.loc
        # a = df*50
        # a._loc  ---> Will be None
        #newobj._loc = self._loc
        #newobj._iloc = self._iloc
        #newobj._ix = self._ix         
        return newobj


    def deepcopy(self):
        ''' Make a deepcopy of self, including the dataframe.'''
        return copy.deepcopy(self)  

    def _framegetattr(self, attr, *fcnargs, **fcnkwargs):
        ''' Called by __getattr__ as a wrapper, this private method is used 
        to ensure that output is MetaPandasObject.  For example, MetaDataFrame
        will return DataFrame, MetaSeries will return Series.  This is done
        through inspecting the output object type and comparing with self.cousin.

        **kwargs: use_base - If true, program attempts to call attribute on
        the reference.  reference ought to be maintained as a series, and 
        Series/Dataframe API's must be same.

        *fcnargs and **fcnkwargs are passed to the dataframe method.

        Note: tried to ad an as_new keyword to do this operation in place, 
        but doing self=dfout instead of return dfout didn't work.  Could 
        try to add this at the __getattr__ level; however, may not be worth it.
        '''

        out=getattr(self._frame, attr)(*fcnargs, **fcnkwargs)

        ### If operation returns a dataframe, return new TimeSpectra
        if isinstance(out, self.cousin): #metadataframe or won't have _transfer method
            dfout=self._transfer(out)
            return dfout

        ### Otherwise return whatever the method return would be
        else:
            return out

    def _repr_html_(self):
        """ Allows ipython notebook to display as default html"""
        return self._frame._repr_html_()

    def __repr__(self):
        return self._frame.__repr__()
    
    def _fast_xs(self, *args, **kwargs):
        print 'in fastxs'
        return self._frame._fast_xs(*args, **kwargs)  

    ### Operator overloading ####
    ### In place operations need to overwrite self._frame
    def __add__(self, x):
        return self._transfer(self._frame.__add__(x))

    def __sub__(self, x):
        return self._transfer(self._frame.__sub__(x))

    def __mul__(self, x):
        return self._transfer(self._frame.__mul__(x))

    def __div__(self, x):
        return self._transfer(self._frame.__div__(x))

    def __truediv__(self, x):
        return self._transfer(self._frame.__truediv__(x))

    ### From what I can tell, __pos__(), __abs__() builtin to df, just __neg__()    
    def __neg__(self):  
        return self._transfer(self._frame.__neg__() )

    ### Object comparison operators
    def __lt__(self, x):
        return self._transfer(self._frame.__lt__(x))

    def __le__(self, x):
        return self._transfer(self._frame.__le__(x))

    def __eq__(self, x):
        return self._transfer(self._frame.__eq__(x))

    def __ne__(self, x):
        return self._transfer(self._frame.__ne__(x))

    def __ge__(self, x):
        return self._transfer(self._frame.__ge__(x))

    def __gt__(self, x):
        return self._transfer(self._frame.__gt__(x))     

    def __len__(self):
        return self._frame.__len__()

    def __nonzero__(self):
        return self._frame.__nonzero__()

    def __contains__(self, x):
        return self._frame.__contains__(x)

    def __iter__(self):
        return self._frame.__iter__()
    
    def __pow__(self, exp):
        return self._transfer(self._frame.__pow__(exp))
    
    def __abs__(self):
        return self._transfer(self._frame.__abs__())     
    
    # Reflected operands (http://www.rafekettler.com/magicmethods.html)
    def __radd__(self, x):
        return self._transfer(self._frame.__radd__(x))

    def __rsub__(self, x):
        return self._transfer(self._frame.__rsub__(x))
    
    def __rmul__(self, x):
        return self._transfer(self._frame.__rmul__(x))    

    def __rdiv__(self, x):
        return self._transfer(self._frame.__rdiv__(x))
    
    def __rtruediv__(self, x):
        return self._transfer(self._frame.__rtruediv__(x))    
    
    def __rmod__(self, x):
        return self._transfer(self._frame.__rmod__(x))
    
    def __rdivmod__(self, x):
        return self._transfer(self._frame.__rdivmod__(x))    
    
    def subtract(self, *args, **kwargs):
        return self._transfer(self._frame.subtract(*args, **kwargs))

    @property
    def data(self):
        """ Accesses self._frame.  RETURNS COPY SO USER DOESNT OVERWRITE IN PLACE"""
        return self._frame.copy(deep=True)    

    @property
    def index(self):
        return self._frame.index
    
    #To avoid accidentally setting index ie ts.index()
    @index.setter
    def index(self, index):
        self._frame.index = index
        

    ## Fancy indexing
    _ix=None     
    _iloc=None
    _loc=None

        
    @property	  	
    def ix(self, *args, **kwargs):      	
        ''' Pandas Indexing.  Note, this has been modified to ensure that series returns (eg ix[3])
        still maintain attributes.  To remove this behavior, replace the following:
        
        self._ix = _MetaIXIndexer(self, _IXIndexer(self) ) --> self._ix=_IXIndexer(self)
        
        The above works because slicing preserved attributes because the _IXIndexer is a python object 
        subclass.'''
        if self._ix is None:
            try:
                self._ix=_IXIndexer(self)
            #New versions of _IXIndexer require "name" attribute.
            except TypeError as TE:
                self._ix=_IXIndexer(self, 'ix')
        return self._ix   

    @property	  	
    def iloc(self, *args, **kwargs):      	
        """ See pandas.Index.iloc; preserves metadata"""
        if self._iloc is None:
            try:
                self._iloc =_iLocIndexer(self)
            #New versions of _IXIndexer require "name" attribute.
            except TypeError as TE:
                self._iloc=_iLocIndexer(self, 'iloc')
        return self._iloc   
    

    @property	  	
    def loc(self, *args, **kwargs):      	
        """See pandas.Index.loc; preserves metadata"""
        if self._loc is None:
            try:
                self._loc = _LocIndexer(self)
            #New versions of _IXIndexer require "name" attribute.
            except TypeError as TE:
                self._loc= _LocIndexer(self, 'loc')
        return self._loc         
    
            


#@logclass(public_lvl='debug', log_name=__name__, skip=['_transfer'])
class MetaDataFrame(MetaPandasObject):

    # Repeated for clarity
    cousin = DataFrame

    @property
    def columns(self):
        return self._frame.columns

    @columns.setter
    def columns(self, columns):
        self._frame.columns = columns

        
#@logclass(public_lvl='debug', log_name=__name__, skip=['_transfer'])
class MetaSeries(MetaPandasObject):
    
    cousin = Series
        
	            
    

# Test Subclass
# -------------
class SubFoo(MetaDataFrame):
    ''' Shows an example of how to subclass MetaPandasObject with custom attributes, a and b.'''

    def __init__(self, a, b, *dfargs, **dfkwargs):
        self.a = a
        self.b = b    

        super(SubFoo, self).__init__(*dfargs, **dfkwargs)

    def __repr__(self):
        return "Hi I'm SubFoo. I'm not really a DataFrame, but I quack like one."


#### TESTING ###
if __name__ == '__main__':

    ### Create a MetaPandasObject
    meta_df=MetaDataFrame(abs(randn(3,3)), index=['A','B','C'], columns=['c11','c22', 'c33'])    
    
    meta_df.to_csv('deletejunkme')

    ### Add some new attributes
    meta_df.a=50
    meta_df.b='Pamela'
    print 'See the original metadataframe\n'
    print meta_df
    print '\nI can operate on it (+ - / *) and call dataframe methods like rank()'
    
    meta_df.ix[0]

    ### Perform some intrinsic DF operations
    new=meta_df*50.0
    new=new.rank()
    print '\nSee modified dataframe:\n'
    print new

    ### Verify attribute persistence
    print '\nAttributes a = %s and b = %s will persist when new metadataframes are returned.'%(new.a, new.b)

    ### Demonstrate subclassing by invoking SubFoo class
    print '\nI can subclass a dataframe an overwrite its __repr__() or more carefully __bytes__()/__unicode__() method(s)\n'
    subclass=SubFoo(50, 200, abs(randn(3,3)), index=['A','B','C'], columns=['c11','c22', 'c33'])    
    print subclass
    ### Access underlying dataframe
    print '\nMy underlying dataframe is stored in the "data" attribute.\n'
    print subclass.data

    ### Pickle
    print '\nSave me by using x.save() / x.dumps() and load using mload(x) / mloads(x).'
    
    # INDEX SLICING THROUGH LOC AND ILOC
    print '\nslicing one column \n'
    print meta_df.iloc[0]
    print meta_df._frame.iloc[0]

    print '\nslicing many columns\n'
    print  meta_df.iloc[0:1]
    print meta_df._frame.iloc[0:1]
    
    print '\nIndexing by label\n'
    print meta_df.loc['A':'B']

    #GOOD EXPLANATION OF WHY CANT STRING SLICE COLUMNS
    #http://stackoverflow.com/questions/11285613/selecting-columns    
    print '\nColumn slicing\n'
    print meta_df[['c11','c33']]
    print meta_df[['c11','c33']].a
    
#    df.save('outpath')
#    f=open('outpath', 'r')
#    df2=load(f)    

    print '\nCreating MetaSeries'
    s = MetaSeries(range(0,10))
    print s, type(s)
    print '\nSeries Slicing 0:5'
    print s[0:5]
