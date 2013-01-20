from types import MethodType
import copy
import functools
import cPickle

from pandas import DataFrame, DatetimeIndex, Index, Series

## for testing
from numpy.random import randn


#----------------------------------------------------------------------
# Loading (perhaps change name?) ... Doesn't work correctly as instance methods

def load(inname):
    ''' Load MetaDataframe from file'''
    if isinstance(inname, basestring):
        inname=open(inname, 'r')
    return cPickle.load(inname)

def loads(string):
    ''' Load a MetaDataframe from string stored in memory.'''
    ### BUG WHY DOESNT THIS WORK
    return cPickle.loads(string)   


class MetaDataframe(object):
    ''' Provides composition class that is essentially stores a DataFrame; however, all methods/attributes of the dataframe
    are directly accessible by the user.  As such, this object "quacks" like a dataframe, but is merely a Python object.  Thus,
    it can be subclassed easily and also has persistent custom attributes.'''

    def __init__(self, *dfargs, **dfkwargs):
        ''' Stores a dataframe under reserved attribute name, self._df'''
        self._df=DataFrame(*dfargs, **dfkwargs)
        self.a=50


    ### Save /Load methods    
    def save(self, outname):
        ''' Takes in str or opened file and saves. cPickle.dump wrapper.'''
        if isinstance(outname, basestring):
            outname=open(outname, 'w')
        cPickle.dump(self, outname)


    def dumps(self):
        ''' Output TimeSpectra into a pickled string in memory.'''
        return cPickle.dumps(self)

    def deepcopy(self):
        ''' Make a deepcopy of self, including the dataframe.'''
        return copy.deepcopy(self)   

    def as_dataframe(self):
        ''' Convience method to return a raw dataframe, self._df'''
        return self._df    

    #----------------------------------------------------------------------
    # Overwrite Dataframe methods and operators

    def __getitem__(self, key):
        ''' Item lookup'''
        return self._df.__getitem__(key)    

    def __setitem__(self, key, value):
        self._df.__setitem__(key, value)    

    ### These tell python to ignore __getattr__ when pickling; hence, treat this like a normal class    
    def __getstate__(self): return self.__dict__
    def __setstate__(self, d): self.__dict__.update(d)    

    def __getattr__(self, attr, *fcnargs, **fcnkwargs):
        ''' Tells python how to handle all attributes that are not found.  Basic attributes 
        are directly referenced to self._df; however, instance methods (like df.corr() ) are
        handled specially using a special private parsing method, _dfgetattr().'''

        ### Return basic attribute
        refout=getattr(self._df, attr)
        if not isinstance(refout, MethodType):
            return refout

        ### Handle instance methods using _dfgetattr().
        ### see http://stackoverflow.com/questions/3434938/python-allowing-methods-not-specifically-defined-to-be-called-ala-getattr
        else:         
            return functools.partial(self._dfgetattr, attr, *fcnargs, **fcnkwargs)
            ### This is a reference to the fuction (aka a wrapper) not the function itself


    def _deepcopy(self, dfnew):
        ''' Copies all attribtues into a new object except has to store current dataframe
        in memory as this can't be copied correctly using copy.deepcopy.  Probably a quicker way...

        dfnew is used if one wants to pass a new dataframe in.  This is used primarily in calls from __getattr__.'''
        ### Store old value of df and remove current df to copy operation will take
        olddf=self._df.copy(deep=True)
        self._df=None

        ### Create new object and apply new df 
        newobj=copy.deepcopy(self)
        newobj.df=dfnew

        ### Restore old value of df and return new object
        self._df=olddf
        return newobj


    def _dfgetattr(self, attr, *fcnargs, **fcnkwargs):
        ''' Called by __getattr__ as a wrapper, this private method is used to ensure that any
        DataFrame method that returns a new DataFrame will actually return a TimeSpectra object
        instead.  It does so by typechecking the return of attr().

        **kwargs: use_base - If true, program attempts to call attribute on the baseline.  Baseline ought
        to be maintained as a series, and Series/Dataframe API's must be same.

        *fcnargs and **fcnkwargs are passed to the dataframe method.

        Note: tried to ad an as_new keyword to do this operation in place, but doing self=dfout instead of return dfout
        didn't work.  Could try to add this at the __getattr__ level; however, may not be worth it.'''

        out=getattr(self._df, attr)(*fcnargs, **fcnkwargs)

        ### If operation returns a dataframe, return new TimeSpectra
        if isinstance(out, DataFrame):
            dfout=self._deepcopy(out)
            return dfout

        ### Otherwise return whatever the method return would be
        else:
            return out

    def __repr__(self):
        ''' Can be customized, but by default, reutrns the output of a standard Dataframe.'''
        return self._df.__repr__()


    @property
    def ix(self):    
        return self._deepcopy(self._df.ix)

    ### Operator overloading ####
    ### In place operations need to overwrite self._df
    def __add__(self, x):
        return self._deepcopy(self._df.__add__(x))

    def __sub__(self, x):
        return self._deepcopy(self._df.__sub__(x))

    def __mul__(self, x):
        return self._deepcopy(self._df.__mul__(x))

    def __div__(self, x):
        return self._deepcopy(self._df.__div__(x))

    def __truediv__(self, x):
        return self._deepcopy(self._df.__truediv__(x))

    ### From what I can tell, __pos__(), __abs__() builtin to df, just __neg__()    
    def __neg__(self):  
        return self._deepcopy(self._df.__neg__() )

    ### Object comparison operators
    def __lt__(self, x):
        return self._deepcopy(self._df.__lt__(x))

    def __le__(self, x):
        return self._deepcopy(self._df.__le__(x))

    def __eq__(self, x):
        return self._deepcopy(self._df.__eq__(x))

    def __ne__(self, x):
        return self._deepcopy(self._df.__ne__(x))

    def __ge__(self, x):
        return self._deepcopy(self._df.__ge__(x))

    def __gt__(self, x):
        return self._deepcopy(self._df.__gt__(x))     

    def __len__(self):
        return self._df.__len__()

    def __nonzero__(self):
        return self._df.__nonzero__()

    def __contains__(self, x):
        return self._df.__contains__(x)

    def __iter__(self):
        return self._df.__iter__()


class SubFoo(MetaDataframe):
    ''' Shows an example of how to subclass MetaDataframe with custom attributes, a and b.'''

    def __init__(self, *args, **kwargs):
        self.a = kwargs.pop('a', None)
        self.b = kwargs.pop('b', None)        

        super(SubFoo, self).__init__(*args, **kwargs)
        
#### TESTING ###
if __name__ == '__main__':

    df=MetaDataframe(abs(randn(3,3)), index=['A','B','C'], columns=['c11','c22', 'c33'])    
    df.rank()
    df.deepcopy()
    df.save('hi')
    f=open('hi', 'r')
    df2=load(f)

    ### Add some attributes
    df.a=50

    ### Perform an operation
    df2=df*50
    print df2.a

    subclass=SubFoo(abs(randn(3,3)), index=['A','B','C'], columns=['c11','c22', 'c33'], a=50, b=2)    

    print df