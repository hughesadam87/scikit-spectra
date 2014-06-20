# Import sample data.  This import structure was taken directly from skimages
# data import style:
    # https://github.com/scikit-image/scikit-image

import os.path as op
from pyuvvis import data_dir, TimeSpectra
from pyuvvis.pandas_utils.dataframeserial import df_load

__all__ = ['aunps_glass', 'aunps_water']

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


def aunps_glass(*args, **kwargs):
    """ Reeveslab data obtained by Adam Hughes of gold nanoparticles (AuNPs)
    on a glass optical fiber; spectrum corresponds to the specular Reflectance.
    Please reference pyuvvis if citing.  

    Parameters
    ----------
    style : int (1,2,or 3
        represents three types of AuNPs on fibers.  style 1 is very homegenous
        coverage.  style 2 is fair coverage with early signs of aggregation.
        style=3 is poor coverage is many AuNP aggregates.
   
    Notes
    -----
    style 1 correponds to dataset 5/22/14, fiber 4.  style 2 from 9/11/13 fiber 1
    and style 3 from 10/1/DTSSP fiber 1.  All of these were cropped and resampled
    to have exatly 100 columns.  Such sampling may exagerate features of the 
    original dataset, such as the temporal gaps in the style=3 dataset.  They were
    there in original data, but sampling makes them seem more pronounced or intense.
    """
    style = kwargs.pop('style', 1)
    
    if style == 1:
        kwargs.setdefault('name', 'AuNPs Glass (good)')    
        return _load_gwuspec('aunps_glass_good.csv', *args, **kwargs)
        

    elif style == 2:
        kwargs.setdefault('name', 'AuNPs Glass (fair)')    
        return _load_gwuspec('aunps_glass_fair.csv', *args, **kwargs)


    elif style == 3:
        kwargs.setdefault('name', 'AuNPs Glass (poor)')   
        return _load_gwuspec('aunps_glass_bad.csv', *args, **kwargs)

    else:
        raise DataError("style argument must be '1' '2' or '3', instead got %s" % style)

    

def aunps_water(*args, **kwargs):
    """ Reeveslab data obtained by Adam Hughes of gold nanoparticles in water. 
    UV peak is due to residual citrates from citrate reduction in synthesizing
    the nanoparticles via the Turkevich method.
    Please reference pyuvvis if citing.  Added baseline = 234.0 array.
    """
    kwargs.setdefault('name', 'Gold Nanoparticles in Water')    
    ts = _load_gwuspec('aunps_water.csv', *args, **kwargs)
    ts.baseline = 234.0
    return ts
    
if __name__ == '__main__':
    ts = uvvis_spec1()
    print ts, type(ts)
    
