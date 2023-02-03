""" Various utilities used for manipultating custom spectral dataframe objects.
    Some of these may work for any dataframe, but others require special attributes
    such as "baseline" and "filedict".  For serialization operations, import 
    from spec_serial.py 
    """

from pandas import Series, DataFrame
import numpy as np
from scipy import integrate
from types import GeneratorType

from skspec.pandas_utils.dataframeserial import _get_metadict
from skspec.exceptions import badvalue_error
import skspec.config as pvconfig

import logging
logger = logging.getLogger(__name__) 


class UtilsError(Exception):
    """ """

def _compute_span(index, with_unit=False):
   """ Format the first, last entries in an index for string output
   like (start - final).  Doesn't include the unit
   """
   imin, imax = index.min(), index.max()
   try:
      span = '%.2f - %.2f' % (imin, imax)

   except TypeError:
      try: #hack for datetimeindex
         span = '%s - %s' % (
               str(imin).split()[1], #Cut out year
               str(imax).split()[1]
           )
         # Just string format if all else fails
      except Exception:
         span = '%s - %s' % (imin, imax)

   if with_unit:
      span = '%s %s' % (span, index._unit.short)
   return span


def hasgetattr(obj, attr, default=None):
    """ Combines hasattr/getattr to return a default if hasattr fail."""
    if not hasattr(obj, attr):
        return default
    return getattr(obj, attr)


def safe_lookup(obj, attr, missing=pvconfig.MISSING):
    """ Look up attribute on object.  If not found, or set to None,
    will return a missing value defaulting to pvconfig.MISSING.
    """
    return hasgetattr(obj, attr, missing)


def countNaN(obj):
    ''' Returns counts of nans in an object'''
    return np.isnan(obj.sum()).sum()   

def _parse_generator(generator, astype=tuple):
    """ Convert generator as tuple, list, dict or generator.
        
    Parameters
    ----------
    astype : container type (tuple, list, dict) or None
        Return expression as tuple, list... if None, return as generator. 

    Notes
    -----
    Mostly useful for operations that in some cases return a dictionary, 
    but also might be useful as a list of kv pairs etc...
    """        
    if not isinstance(generator, GeneratorType):
        raise UtilsError("Generator required; got %s" % type(generator))
    
    if isinstance(astype, str):
        astype = eval(astype)        

    if astype:
        return astype(generator)

    else:
        return generator   

### Rather deprecated due to TimeSpectra.reference/iunit
def divby(df, divisor=0, axis=0, sameshape=True):
    ''' Small wrapper around pandas.divide() that takes in either column integers, names,
    or entire arrays as the divisor.  Note, pandas.divide by default is rowwise, but here
    it defaults to column-wise.
    
    Parameters:
    -----------
      df:  Dataframe object.
      divisor: (See notes below)
      axis: Division axis. 0=column-wise division. 1=row-wise
      sameshape: If true, function will check that the divisor as the same shape as
        the data along that axis.  For example, is an array of 2000 units, 
        and axis=0, then the row dimension must be 2000 for the dataframe.
        AFAIK df.div does not enforce this stringency, which sometimes can lead
        to hard-to-find bugs.
    
    Notes:
    ------
      This program first checks if divisor is an integer.  If not, it attempts
      to lookup by rowname or columnname.  Finally, it tries to divide by the divisor itself,
      if the divisor is an array/series.  This seemed like a flexible way to do this 
      without too much type checking.'''

    ### Column-wise division
    if axis==0:        
        if isinstance(divisor, int):
            divisor=df.columns[divisor]
        
        else:
            try:
                divisor=df[divisor]
            except Exception:
                pass #divisor=divisor
            
        divlen=df.shape[0] #Store length of a single column


    ### Rowwise division    
    elif axis==1:
        if isinstance(divisor, int):
            divisor=df.ix[divisor]
        
        else:
            try:
                divisor=df.xs(divisor)
            except KeyError:
                pass
            
        divlen=df.shape[1]
        
    else:
        raise badvalue_error('axis', '0,1')
    
    ### Enforce strict shapetype
    if sameshape:
        if len(divisor) != divlen:
            raise TypeError('Divisor dimensions %s do not match dividend' 
            ' dimension %s along axis = %s'%(divlen, len(divisor), axis))
    
    return df.divide(divisor, axis=axis)
    
            

def boxcar(df, binwidth, axis=0):
    ''' Only works on boxcar for now.  Also, want binwidth and/or binnumber
    to be inputs but not both. '''
    if axis==1:
        binnumber=len(df.columns)/binwidth    
        counts, binarray=np.histogram(df.columns, bins=binnumber)
        digiarray=np.digitize(np.asarray(df.columns, dtype=float), binarray)          
        mapped_series=Series(digiarray, index=df.columns)       
        dfout=df.groupby(mapped_series, axis=1).mean()
        dfout.columns=binarray
    
    elif axis==0:
        binnumber=len(df.index)/binwidth  #Converted to int when np.histogram called
        counts, binarray=np.histogram(df.index, bins=binnumber)
        digiarray=np.digitize(np.asarray(df.index, dtype=float), binarray)    
        
        mapped_series=Series(digiarray, index=df.index)
        
        dfout=df.groupby(mapped_series, axis=0).mean()
        dfout.index=binarray   
        
    else:
        raise AttributeError('Axis must be 0 (column binning) or 1 (index/row) binning.  You entered %s'%axis)
    
    return dfout

                    
                                

def digitize_by(df, digitized_bins, binarray, axis=0, avg_fcn='mean', weight_max=None):
    ''' Takes in an array of digitized bins, and then restructures a dataframe
    based on the bin array'''
    
    ### Map the digitized bins to series data with axis same as one that will be collapsed ###
    if axis == 0:
        mapped_series=Series(digitized_bins, index=df.index) #No, this isn't wrong, just weird
    else:
        #mapped_series=Series(digitized_bins, index=df.columns)
        mapped_series=Series(digitized_bins, index=df.index)
    
    if len(df.shape)==1:
        if avg_fcn.lower() == 'mean':
            dfout=df.groupby(mapped_series).mean()  #// is importanmt
    
        elif avg_fcn.lower() == 'sum':
            dfout=df.groupby(mapped_series).sum()
    
        ### Rebins according to the sum, and then divides axis or rows by their maxes.
        ### If I want a normalized array, can call this with bindwidth=1.0
        elif avg_fcn.lower() == 'weighted':
            dfout=df.groupby(mapped_series).mean()
            if weight_max:
                dfout= dfout.apply(lambda x: x / weight_max)  #These should be float division
            else:
                dfout= dfout.apply(lambda x: x/ x.max())
            
        else:
            raise NotImplementedError('%s is not a valid key to df_rebin, must \
                                     be mean, sum or weighted'%avg_fcn)        
    
    elif len(df.shape)==2:
        if avg_fcn.lower() == 'mean':
            dfout=df.groupby(mapped_series, axis=axis).mean()
            dfout.index=binarray
            
    
        elif avg_fcn.lower() == 'sum':
            dfout=df.groupby(mapped_series, axis=axis).sum()
    
        ### Rebins according to the sum, and then divides axis or rows by their maxes.
        ### If I want a normalized array, can call this with bindwidth=1.0
        elif avg_fcn.lower() == 'weighted':
            dfout=df.groupby(mapped_series, axis=axis).mean()
            if weight_max:                
                dfout=dfout.apply(lambda x:x / weight_max, axis=axis)
            else:
                dfout=dfout.apply(lambda x: x / x.max(), axis=axis)            
            
        else:
            raise NotImplementedError('%s is not a valid key to df_rebin, must \
                                     be mean, sum or weighted'%avg_fcn)

    else:
        raise NotImplementedError('df_rebin only works with 1-d or 2-d arrays')        
        
    return dfout   


def split_by(df, n, axis=1, astype=list):
    """ Returns a list of dataframes sampled by n.  For example, a datframe
    of 20 columns, sampled by n=4, will return 5 evenly spaced dataframes.
    If uneven samples, will raise warning.  axis=1 for column sampling, axis=0
    for row sampling.
    """
    
    if n > df.shape[1]:
        raise UtilsError("Requested samplesize (n=%s) exceeds size along axis %s"
                         % (n,axis))
    
    # Integery guarantees rounding down
    m = int(float(df.shape[axis]) / n)
    df_out=[]
    for i in range(n):
        if i==n-1:
            df_out.append(df[df.columns[i*m::]])
        else:
            df_out.append(df[df.columns[i*m:(i+1)*m]])

    if n % df.shape[axis]:
        logger.warn("Returning uneven sampling for (n=%s) along axis %s"
                    "of size %s" % (n, axis, df.shape[axis]))
                    
    return df_out     
    

def rebin(df, binwidth, axis=0, avg_fcn='weighted', weight_max=None):
    ''' Pass in an array, this slices and averages it along some spacing increment (bins).
    Axis=0 means averages are computed along row.  axis=1 means averages are computed along column.
    Dataframe already handles most issues, such as if binning in unequal and/or binning is larger than 
    actual length of data along axis.  Aka bin 100 rows by 200 rows/bin.
    Binwidth is the spacing as in every X entries, take an average.  Width of 3 would be
    every 3 entries, take an average.
    
    Redundant because if series is passed in, the axis keyword causes errors.
    
    If using avg_fcn='weighted', one can pass an upper limmit into the "weight_max" category
    so that weighting is to a fixed value and not to the max of the dataset.  This is
    useful when comparing datasets objectively.  For dataframes, weight_max may be a 1d
    array of the normalization constant to each column in the dataframe.  If a single value
    is entered, or for a series, that value will be divided through to every row.
    
    Note: avg_fct='weighted' and weight_max=None will find a max after binning the data, 
    and divide all other column(or row values) by the max.  
    This is not the statistical normaization, which should be added later (X-u / sigma).'''


    if len(df.shape)==1:
        if avg_fcn.lower() == 'mean':
            dfout=df.groupby(lambda x:x//binwidth).mean()  #// is importanmt
    
        elif avg_fcn.lower() == 'sum':
            dfout=df.groupby(lambda x:x//binwidth).sum()
    
        ### Rebins according to the sum, and then divides axis or rows by their maxes.
        ### If I want a normalized array, can call this with bindwidth=1.0
        elif avg_fcn.lower() == 'weighted':
            dfout=df.groupby(lambda x:x//binwidth).mean()  #Groupby uses int division
            if weight_max:
                dfout=dfout.apply(lambda x: x / weight_max)      #Apply uses float division
            else:
                dfout=dfout.apply(lambda x: x/ x.max())
            
        else:
            raise NotImplementedError('%s is not a valid key to df_rebin, must \
                                     be mean, sum or weighted'%avg_fcn)        
    
    elif len(df.shape)==2:
        if avg_fcn.lower() == 'mean':
            dfout=df.groupby(lambda x:x//binwidth, axis=axis).mean()
    
        elif avg_fcn.lower() == 'sum':
            dfout=df.groupby(lambda x:x//binwidth, axis=axis).sum()
    
        ### Rebins according to the sum, and then divides axis or rows by their maxes.
        ### If I want a normalized array, can call this with bindwidth=1.0
        elif avg_fcn.lower() == 'weighted':
            dfout=df.groupby(lambda x:x//binwidth, axis=axis).mean()
            if weight_max:                
                dfout=dfout.apply(lambda x:x / weight_max, axis=axis)
            else:
                dfout=dfout.apply(lambda x: x / x.max(), axis=axis)            
            
        else:
            raise NotImplementedError('%s is not a valid key to df_rebin, must \
                                     be mean, sum or weighted'%avg_fcn)

    else:
        raise NotImplementedError('df_rebin only works with 1-d or 2-d arrays')        
        
    return dfout   

def maxmin_xy(obj, style='max', arg=False, idx=True, val=True):
    ''' Return arg (eg integer index position), index val, and object val
        at the data maximum.  Works on series or dataframes.
        
        Params:
        -------
          obj: 1 or 2-d array type.
          style: return 'max' or 'min' vals along the dataset.
          arg: Index position at maximum.
          idx: Index val at maximum.
          val: Return the data val at this point.'''
    
    if obj.ndim == 1:
        return _maxmin_xy(obj, style=style, arg=arg, idx=idx, val=val)

    elif obj.ndim == 2:
        return obj.apply(_maxmin_xy, style=style, arg=arg, idx=idx, val=val)

    else:
        raise badval_error('ndim', '1,2')
        

def _maxmin_xy(array, style='max', arg=False, idx=True, val=True):
    ''' Return index and val at maximum in a series.  For index position (eg 6) at max,
        use argmax()'''    
    
    if style not in ['max', 'min']:
        raise badval_error('style', 'max, min')        
    
    if not arg and not idx and not val:
        raise AttributeError('max_xy requires at least one of the following boolean arguments: arg, idx, val')    
    
    out=[]    

    if style=='max':               #X: idxmax/idxmin no longger array attributes
        fidx=array.argmax(); farg=array[array.idxmax()]; fval=array.max() 
    else:
        fidx=array.argmin(); farg=array[array.idxmin()]; fval=array.min()
        
    
    if arg:
        out.append(farg)

    if idx:
        out.append(fidx)

    if val:
        out.append(fval)
    
    if len(out) > 1:
        out=tuple(out)
    else:
        out=out[0]
    
    return out

def find_nearest(obj, value, arg=False, idx=True, val=True):
    if obj.ndim == 1:
        return _find_nearest(obj, value=value, arg=arg, idx=idx, val=val)  #Positional args still passed as kwargs

    elif obj.ndim == 2:
        return obj.apply(_find_nearest, value=value, arg=arg, idx=idx, val=val)

    else:
        raise badval_error('ndim', '1,2')    
    
    
def _find_nearest(array, value, arg=False, idx=True, val=True):
    '''Find nearest val in an array, return index and array val.
      Parameters:
      ---------
         array: Actually think this is set up for series/dataframe?

      Notes:
      ------
         This works by computing the absolute difference array of the value and looking
         for minimums along this array as seen in stack overflow discussions.
         http://stackoverflow.com/questions/2566412/find-nearest-value-in-numpy-array
    '''

    ### Get index and arg from diff array
    diff_array=np.abs(array-value)
    arg, idx=_maxmin_xy(diff_array, style='min', arg=arg, idx=idx, val=val)
    
    ### Find corresponding value from original array
    val=array[idx]
    
    out=[]
    if arg:
        out.append(arg)
        
    if idx:
        out.append(idx)
        
    if val:
        out.append(val)
    
    if len(out) > 1:
        out=tuple(out)
    else:
        out=out[0]
    
    return out    