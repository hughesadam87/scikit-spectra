# Import sample data.  This import structure was taken directly from skimages
# data import style:
    # https://github.com/scikit-image/scikit-image

import os.path as op
from pyuvvis import data_dir, TimeSpectra
from pyuvvis.pandas_utils.dataframeserial import df_load

__all__ = ['uvvis_spec1', 'uvvis_spec2']

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
        return TimeSpectra.from_csv(filepath, *args, **kwargs)

    #  XXX INCOMPLETE FUNCTIONALITY
    elif ext == '.pickle':
        df = df_load(filepath)
        logger.critical("LOADING FROM PICKLE NOT COMPLETE YET")

    else:
        raise DataError('%s must have file extension .csv or .pickle, not '
                             '%s' %(filepath, ext))
 

def _load_gwuspec(filepath, *args, **kwargs):
    """ Loads GWU data from csv, assigns baseline and crops accordingly.
    This is a wrapper to let author use his own data for the example data."""
    
    # CSV KWARGS
    kwargs.setdefault('index_col', 0)

    # TimeSpec KWARGS
    kwargs.setdefault('reference', 0) #Index col will be removed.
    kwargs.setdefault('specunit', 'nm')
    ts = load_ts(filepath, *args, **kwargs)

    # Baselines removed apriori with dynamic_baseline
    return ts


def uvvis_spec1(*args, **kwargs):
    """ Reeveslab data obtained by Adam Hughes of gold nanoparticles on a 
    glass optical fiber; spectrum corresponds to the specular Reflectance.
    Please reference pyuvvis if citing.
    """
    kwargs.setdefault('name', 'Nanoparticles on Glass')    
    return _load_gwuspec('uvvis_spec1.csv', *args, **kwargs)


def uvvis_spec2(*args, **kwargs):
    """ Reeveslab data obtained by Adam Hughes of gold nanoparticles in water. 
    UV peak is due to residual citrates from citrate reduction in synthesizing
    the nanoparticles via the Turkevich method.
    Please reference pyuvvis if citing.
    """
    kwargs.setdefault('name', 'Nanoparticles in Water')    
    return _load_gwuspec('uvvis_spec2.csv', *args, **kwargs)

if __name__ == '__main__':
    ts = uvvis_spec1()
    print ts, type(ts)
    
