#!/usr/bin/env python
''' Serialization interface for custom DataFrame objects.  Allows to save/load 
 for memory streams or files.  Because one cannot serialize DataFrames with
 custom attributes, this uses an intermediate object for that process.'''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__version__ = "1.0.1"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

import cPickle

class TempDump(object):
    ''' Temporary class to dump DataFrame object with custom attributes.
    Can't cPickle DataFrame and retain custom attributes so this is an intermediate.'''
    def __init__(self, dataframe):
        self.dataframe=dataframe
        self.filedict=dataframe.filedict
        self.metadata=dataframe.metadata
        self.baseline=dataframe.baseline

def save_specdata_stream(specdf):
    ''' Save spectral data as a stream into memory.'''
    return cPickle.dumps(TempDump(specdf)) #Dumps writes the object to memory
    
def save_specdata_file(specdf, outfile):
    ''' Save spectral data as a file.'''
    f=open(outfile, 'w')
    outstream=cPickle.dump(temp, f)
    f.close()
    return outstream    
    
def load_specdata_fromfile(infile):
    '''Returns spectral data object from a serialized file '''
    f=open(infile, 'r')
    tempobj=cPickle.load(f)
    df.filedict=tempobj.filedict
    df.metadata=tempobj.metadata
    df.baseline=tempobj.baseline
    return tempobj
    
def load_specdata_fromstream(stream):
    ''' Returns spectral data object from a serialized stream'''
    tempobj=cPickle.loads(stream) #loads not load
    df=tempobj.dataframe
    df.filedict=tempobj.filedict
    df.metadata=tempobj.metadata
    df.baseline=tempobj.baseline
    return df
    
    
    
    
    

