# Import sample data.  This import structure was taken directly from skimages
# data import style:
    # https://github.com/scikit-image/scikit-image

import os.path as op
from pyuvvis import data_dir
from pandas import read_csv
from pyuvvis.pandas_utils.dataframeserial import df_load

__all__ = ['spectra']

class DataError(Exception):
    """ """

def load(filepath, *args, **kwargs):
    """
    Parameters
    ----------
    f : string
        File name of .csv or .pickle spectrum.

    Returns
    -------
    img : ndarray
        Image loaded from skimage.data_dir.
    """
    
    filepath = op.join(data_dir, filepath)
    ext = op.splitext(filepath)[1]

  
    if ext == '.csv':
        return read_csv(filepath, **kwargs)

    # Is this deprecated/useful?
    elif ext == '.pickle':
        return df_load(filepath)

    else:
        raise DataError('%s must have file extension .csv or .pickle, not '
                             '%s' %(filepath, ext))
#    return _get_data_smart(PACKAGE, filepath, as_stream)

def spectra(*args, **kwargs):
    return load('spectra.csv', *args, **kwargs)