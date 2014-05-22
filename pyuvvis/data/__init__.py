# Import sample data.  This import structure was taken directly from skimages
# data import style:
    # https://github.com/scikit-image/scikit-image

import os.path as op
from pyuvvis import data_dir, TimeSpectra
from pandas import read_csv
from pyuvvis.pandas_utils.dataframeserial import df_load

__all__ = ['spectra']

class DataError(Exception):
    """ """

def load_ts(filepath, *args, **kwargs):
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
        df = read_csv(filepath)

    # THIS HAS BUGS
    elif ext == '.pickle':
        df = df_load(filepath)

    else:
        raise DataError('%s must have file extension .csv or .pickle, not '
                             '%s' %(filepath, ext))
 
    # Custom error handle here?  Do I want to relax to allow for dataframe imports?
    return TimeSpectra(df, *args, **kwargs)

def _load_gwuspec(filepath, *args, **kwargs):
    """ Loads GWU data from csv, assigns baseline and crops accordingly.
    This is a wrapper to let author use his own data for the example data."""
    
    # Refactor this to a "_loadgwu sv method"
    kwargs.setdefault('baseline', 0)
    kwargs.setdefault('reference', 1)
    kwargs.setdefault('specunit', 'nm')
    ts = load_ts(filepath, *args, **kwargs)

    # CSV baseline is in dataset, so subtract and then pop
    ts.sub_base()
    ts.pop(ts.columns[0])
    return ts


def test_spectra(*args, **kwargs):

    kwargs.setdefault('name', 'TestSpectra_1')    
    return _load_gwuspec('test_spectra1.csv', *args, **kwargs)

if __name__ == '__main__':
    ts = test_spectra()
    print ts, type(ts)
    