''' File IO and miscellaneous utilities'''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

import os
from pandas import DataFrame, read_csv, concat
from skspec.core.imk_utils import get_files_in_dir, get_shortname


def df_from_directory(directory, csvargs, sortnames=False, concat_axis=1, shortname=True, cut_extension=False):
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
       
       cut_extension- If kwd shortname is True, this will determine if the file extension is saved or cut from the data.
       '''

    filelist=get_files_in_dir(directory)

    if shortname:
        fget=lambda x:get_shortname(x, cut_extension=cut_extension)
    else:
        fget=lambda x: x
    
    ### Either full names or short names of filelist    
    working_names=[fget(afile) for afile in filelist]       

    ### This parameter can't be passed in, so if user does so, pull it out.
    try:
        csvargs.pop('names')
    except KeyError:
        pass
    else:
        raise Warning('Please do not enter a names keyword for csvargs, it gets inferred from the filenames in\
        the directory.')

    dflist=[read_csv(afile, names=[fget(afile)], **csvargs) for afile in filelist]
    
    ### THIS IS BUSTED, PUTTING NANS EVERYWHERE EXCEPT ONE FILE, but dflist itself ws nice.
    dataframe=concat(dflist, axis=1)
                        
    ### concat tries to sort these, so this will preserve the sort order
    if sortnames:
        dataframe=dataframe.reindex(columns=sorted(working_names))

    return dataframe
            

if __name__=='__main__':
    datadirectory='./NPConcentration'
    
    read_csv_args={'sep':',', 'header':2, 'index_col':0, 'skiprows':2, 'na_values':' \r'}
  
    df=df_from_directory(datadirectory, read_csv_args, sortnames=True)

