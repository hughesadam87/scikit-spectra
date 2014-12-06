# Import sample data.  This import structure was taken directly from skimages
# data import style:
    # https://github.com/scikit-image/scikit-image

import os.path as op
from skspec import data_dir, TimeSpectra, Spectra
from skspec.core.specindex import SpecIndex
from skspec.units import Unit
from skspec.pandas_utils.dataframeserial import df_load
from pandas import read_csv

__all__ = ['aunps_glass', 'aunps_water', 'solvent_evap', 'trip_peaks']

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
    TimeSpectra
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
    kwargs.setdefault('header_datetime', "%Y-%m-%d %H:%M:%S")    

    # TimeSpec KWARGS
    kwargs.setdefault('reference', 0) #Index col will be removed.
    kwargs.setdefault('specunit', 'nm')
        
    ts = load_ts(filepath, *args, **kwargs)

    # Baselines removed apriori with dynamic_baseline
    return ts


def trip_peaks(*args, **kwargs):
    """ Sample data packaged from 2d Shiege:
        (http://sci-tech.ksc.kwansei.ac.jp/~ozaki/2D-shige.htm)
    Data depicts three changing peaks.  Perturbation units is genera
    """
    
    filepath = op.join(data_dir, 'triple_peaks.csv')
    trips = Spectra.from_csv(filepath,
                             header=None, #Just use intindex, overwrite anyway
                             name='Three Peaks',
                             index_col=0,
                             skiprows=1)   
    trips.reference = 0
   
    # Hack because can't do floating point on SpecIndex (should change csv file)
    trips.index = SpecIndex(trips.index+50, unit='ev')
    # Generalized perturbation Unit, making it up
    trips.varunit = Unit(short='pz', full='Polarization', symbol=r'\phi')
    
    return trips
    


def solvent_evap(*args, **kwargs):
    """ Model solvent evaporation dataset graciously shared by Dr. Isao Noda;
    used in his 2004 book Two-Dimensional Correlation Spectroscopy.  From 
    page 47:
    
    'The system described here is a three-component solution mixture of 
    polystyrene (PS) dissolved in a 50:50 blblend of metyl etyl ketone (MEK) and
    perdeuterated tolune.  The initial concentration of PS is about 1.0wt%.
    Once the solution mixture is exposed to the open atmosphere, the solvents 
    start evaporating, and the PS concentraiton increases with time.  However,
    due to the substantial difference in the volatility of MEK and toluene 
    coupled with their slightly dissimilar affinity to PS, the composition of
    the solution mixture changes as a function of time in a rather complex 
    manner during hte spontaneous evaporation process.  
    
    The transient IR spectra were collected as the two solvents evaporated, 
    eventually leaving a PS film behind, as shown schematically in Figure 4.1
    (A).  The measurement was actually made using a horizontal attenuated total 
    reflectance (ATR) prism.  
    
    ...
    
    As expected, the intensities of bands at 2980 and 1720 cm-1 due to violatile
    MEK and those of bands at 2275 and 820cm-1 assigned to perdeuterated toluene
    gradually decrease, while those of PS bands at 3020 and 1450cm-1 increase 
    with time.'
    
    """
    
    # CSV KWARGS
    kwargs.setdefault('index_col', 0)

    # TimeSpec KWARGS
    kwargs.setdefault('reference', 0) #Index col will be removed.
    kwargs.setdefault('specunit', 'cm-1')
    kwargs.setdefault('name', 'Polystyrene Evaporation')    
    kwargs.setdefault('varunit', 'm')

#    kwargs.setdefault('dtype', 'float64') #For parser (data not labels)

    ts = load_ts('pskdt.csv', *args, **kwargs)    
    return ts


def aunps_glass(*args, **kwargs):
    """ Reeveslab data obtained by Adam Hughes of gold nanoparticles (AuNPs)
    on a glass optical fiber; spectrum corresponds to the specular Reflectance.
    Please reference skspec if citing.  

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
    
    if style == 1 or style == 'good':
        kwargs.setdefault('name', 'AuNPs Glass (good)')    
        return _load_gwuspec('aunps_glass_good.csv', *args, **kwargs)
        

    elif style == 2 or style == 'fair':
        kwargs.setdefault('name', 'AuNPs Glass (fair)')    
        return _load_gwuspec('aunps_glass_fair.csv', *args, **kwargs)


    elif style == 3 or style == 'poor':
        kwargs.setdefault('name', 'AuNPs Glass (poor)')   
        return _load_gwuspec('aunps_glass_bad.csv', *args, **kwargs)
    
    elif style == 4 or style == 'full':
        kwargs.setdefault('name', 'AuNPs Glass (full)')   
        return _load_gwuspec('aunps_glass_full.csv', *args, **kwargs)

    else:
        raise DataError("style argument must be '1' or 'good'; '2' or 'fair';"
            " '3' or 'poor'; '4' or 'full'; instead got '%s'" % style)

    

def aunps_water(*args, **kwargs):
    """ Reeveslab data obtained by Adam Hughes of gold nanoparticles in water. 
    UV peak is due to residual citrates from citrate reduction in synthesizing
    the nanoparticles via the Turkevich method.
    Please reference skspec if citing.  Added baseline = 234.0 array.
    """
    kwargs.setdefault('name', 'Gold Nanoparticles in Water')    
    ts = _load_gwuspec('aunps_water.csv', *args, **kwargs)
    ts.baseline = 234.0
    return ts
    
if __name__ == '__main__':
    ts = aunps_water()
    print ts, type(ts)
    
