''' Serialization interface for custom DataFrame objects.  Allows to save/load 
 for memory streams or files.  Because one cannot serialize DataFrames with
 custom attributes, this uses an intermediate object for that process.  Plan
 it implement pickling saved methods later (requires more work).  These are meant to 
 supplant the DataFrame's save() and load() methods when custom attributes must persist.
 
 Note, this program assesses custom attributes by inspecting your DataFrame's
 attributes using Python's builting function, dir().  It compares these to the
 attributes of an empty DataFrame.  This adds a bit of overhead, but should allow
 this program to work with new versions of pandas, as Dataframe's methods and attributes
 are likely to change.  Is there are better way to do this?
 
 The following four functions are defined:
   df_dumps:  Serialize a DataFrame into memory.  Returns serialized stream.
   df_dump:  Serialize a DataFrame into a file.  Returns None.
   df_loads: Return a DataFrame from a serialized stream.
   df_load: Return a Dataframe from a serialized file.
 
 See bottom of file for test cases:  '''

__author__ = "Adam Hughes"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Prototype"

import cPickle
from operator import attrgetter
from pandas import DataFrame

### For testing ###
from numpy.random import randn


class TempDump(object):
    ''' Temporary class to dump DataFrame object with custom attributes.  Custom attrubutes are
    passed in as a dictionary and then temporarily stored upon serialization as _metadict.  Upon
    deserialization, the attributes and values are re-appended to the DataFrame automatically.'''
    def __init__(self, dataframe, metadict):
        self.dataframe=dataframe
        self._metadict=metadict

dfempty=DataFrame() 
defattrs=dir(dfempty)

def print_customattr(df):
    '''Formatted output of all custom attributes found in a DataFrame.  For all
    attributes and methods, use dir(df).'''
    metadict=_get_metadict(df)
    if len(metadict) > 0:
        print '\nFound %s custom attributes:\n'%len(metadict)        
        print '\n'.join([(k+'\t'+v) for k,v in sorted(metadict.items())])

    else:
        print 'No custom attributes found'

def _get_metadict(df):
    ''' Returns dictionary of attributes in a dataframe not found in the default frame.'''
    attrs=dir(df)
    newattr=[att for att in attrs if att not in defattrs] #if not is type(instancemethod?)
    if len(newattr) > 1:
        fget=attrgetter(*newattr)
        return dict(zip(newattr, fget(df)))
    else:
        return {}

def df_dumps(df):
    ''' Save dataframe as a stream into memory.'''
    metadict=_get_metadict(df)
    return cPickle.dumps(TempDump(df, metadict )) #Dumps writes the object to memory
    
def df_dump(df, outfile):
    ''' Save dataframe as a file.'''
    outstream=df_dumps(df) #Dumps writes the object to memory    
    f=open(outfile, 'w') #Should this be 'wb'
    f.write(outstream)
    f.close()
    return None #Should I return none or stream?    
    
def df_load(infile):
    '''Returns dataframe from a serialized file '''
    f=open(infile, 'r')
    tempobj=cPickle.load(f)
    f.close()
    df=tempobj.dataframe    
    for attr, value in tempobj._metadict.items():
        setattr(df, attr, value)
    return df       

def df_loads(stream):
    ''' Returns dataframe from a serialized stream'''
    tempobj=cPickle.loads(stream) #loads not load
    df=tempobj.dataframe
    for attr, value in tempobj._metadict.items():
        setattr(df, attr, value)
    return df    

    
if __name__ == '__main__':
    ### Make a random dataframe, add some attributes
    df=DataFrame(((randn(3,3))), columns=['a','b','c'])
    print_customattr(df)
    print 'adding some attributes'
    df.name='Billy'
    df.junk='in the trunk'
    print_customattr(df)
    
    ### Serialize into memory
    stream=df_dumps(df)
    print 'wrote dataframe to memory'
    ### Restore from memory
    dfnew=df_loads(stream)
    print 'restored from memory'
    print_customattr(dfnew)
    
    
    ### Serialize into file
    outfile='dftest.df' #What file extension is commonly used for this?
    df_dump(df, outfile)  
    print 'wrote dataframe to file %s'%outfile
    ### Restore from file     
    dfnewnew=df_load(outfile)
    print 'Restored from file%s'%outfile
    print_customattr(dfnewnew)


