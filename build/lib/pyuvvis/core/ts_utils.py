''' Utilities particular to TimeSpectra.  Had to separate these from files in utilities module because
of circular imports.  EG, TimeSpectra imports utilities like divby so I can't impot TimeSpectra in utilities.py'''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

### slicing with pandas is so easy, might not even be worth writing my own methods.

from pyuvvis.pandas_utils.dr_reader import df_from_directory
from pyuvvis.core.utilties import df_wavelength_slices    

def wavelength_slices(df, ranges, apply_fcn='mean', **applyfcn_kwds):
    '''See df_wavelength_slices in utilities.py '''    
    return TimeSpectra(df_wavelength_slices)
            
            

### Wrapper for df_from_directory
def spec_from_dir(directory, csvargs, sortnames=False, concat_axis=1, shortname=True, cut_extension=False):
    ''' Takes files from a directory, presuming they are identically formatted, and reads them into
    a dataframe by iterating over read_csv().  All arguments that read_csv() would take are passed
    in.  These kwargs are in regard the files themselves, for example, skiprows, skipfooter and header.
        
    For now, no support for glob to take only files of a certain file extension.
    For now, conctaentation occurs along

    Args:
       directory- Path to directory where files are stored.
       csvargs- Dictionary of arguments that are passed directly to the read_csv() function. For example
                skiprows, header, na_values etc... see pandas API for read_csv()
        
    Kwds:
       sortnames- Will attempt to autosort the filelist. Otherwise, files are ordered by the module
                  os.path.listdir().
                  
       concat_axis- How to merge datafiles into a dataframe.  Default is axis=1, which means all files 
                    should share the same index values.  I use this for spectral data where the wavelength
                    column is my dataframe index.
                  
       shortname- If false, full file path is used as the column name.  If true, only the filename is used. 
       
       cut_extension- If kwd shortname is True, this will determine if the file extension is saved or cut from the data.'''
    
    return TimeSpectra(df_from_directory(directory, csvargs, sortnames=sortnames, concat_axis=concat_axis, shortname=shortname, cut_extension=cut_extension))