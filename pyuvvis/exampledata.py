import os, sys

from pkgutil import get_loader
from pandas import read_csv

from pyuvvis.pandas_utils.dataframeserial import df_load

def get_data_smart(package, resource, as_stream=True):
    """Rewrite of pkgutil.get_data() that actually lets the user determine if data should
    be returned read into memory (aka as_stream=True) or just return the file path.
    """

    loader = get_loader(package)
    if loader is None or not hasattr(loader, 'get_data'):
        return None
    mod = sys.modules.get(package) or loader.load_module(package)
    if mod is None or not hasattr(mod, '__file__'):
        return None

    # Modify the resource name to be compatible with the loader.get_data
    # signature - an os.path format "filename" starting with the dirname of
    # the package's __file__
    parts = resource.split('/')
    parts.insert(0, os.path.dirname(mod.__file__))
    resource_name = os.path.join(*parts)
    if as_stream:
        return loader.get_data(resource_name)
    else:
        return resource_name

def get_exampledata(filename='spectra.csv', as_stream=False):
    '''Import for reading pyuvvis example data.  Sort of like pkgutil.get_data without forcing
    you to read into memory.
    
    filename- File in data/example_data/ to import.
    
    as_stream- If true, file is read into memory using open(filename, 'rb').read().  Otherwise,
               filepath is returned.'''

    package='pyuvvis'
    pathtodata='example_data/'
    
    filepath=os.path.join(pathtodata, filename)
    return get_data_smart(package, filepath, as_stream)

def get_csvdataframe(filename='spectra.csv', **csvargs):
    ''' Takes in spectral data, either .pickle or .csv, returns dataframe.  Files must be in same path as
    called by get_exampledata.  If csv file, one can pass csvargs throught the **csvargs dictionary.'''
    filepath=get_exampledata(filename, as_stream=False)
    ext=os.path.splitext(filepath)[1]
    if ext == '.csv':
        return read_csv(filepath, **csvargs)
    elif ext == '.pickle':
        return df_load(filepath)
    else:
        raise AttributeError('%s must have file extension .csv or .pickle, not %s' %(filename, ext))
        
        
    
if __name__=='__main__':
    data=get_csvdataframe(filename='spectra.pickle')  #csv args are required, like index column and shit
