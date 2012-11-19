''' Various utilities used for manipultating custom spectral dataframe objects.
    Some of these may work for any dataframe, but others require special attributes
    such as "darkseries" and "filedict".  For serialization operations, import 
    from spec_serial.py '''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

### slicing with pandas is so easy, might not even be worth writing my own methods.

from pandas import Series, DataFrame
from pyuvvis.pandas_utils.dataframeserial import _get_metadict
import numpy as np
from scipy import integrate

def divby(df, divisor=0, axis=0):
    ''' Small wrapper around pandas.divide() that takes in either column integers, names,
    or entire arrays as the divisor.  Note, pandas.divide by default is rowwise, but here
    it defaults to column-wise.
    
    Note that this program first checks if divisor is an integer.  If not, it attempts
    to lookup by rowname or columnname.  Finally, it tries to divide by the divisor itself,
    if the divisor is an array/series.  This seemed like a flexible way to do this 
    without too much type checking.'''
    if axis==0:
        if isinstance(divisor, int):
            return df.divide(df[df.columns[divisor]], axis=0) #Default axis is actually 1/rows
        
        else:
            try:
                return df.divide(df[divisor], axis=0) #Default axis is actually 1/rows
            except KeyError:
                return df.divide(divisor, axis=0)
        
    elif axis==1:
        if isinstance(divisor, int):
            return df.divide(df.ix[divisor], axis=1) #Default axis is actually 1/row        
        
        else:
            try:
                return df.divide(df.xs(divisor), axis=1) #Default axis is actually 1/rows
            except KeyError:
                return df.divide(divisor, axis=0)        
    else:
        raise AttributeError('Axis must be 0 (column binning) or 1 (index/row) binning.  You entered %s'%axis)
    

def wavelength_slices(df, ranges, apply_fcn='mean', **applyfcn_kwds):
    '''Takes in a dataframe with a list of start/end ranges.  Slices df into these various ranges,
    then returns a composite dataframe with these slices.  Composite dataframe will nicely
    plot when piped into spec aesthetics timeplot.
    
    Note: By default, this operation slices rows/index, and then averages by columns.  Therefore,
          the default operations is df.ix[], followed by mean(axis=0).  Note that this is not axis=1!
          The can be confusing, so I chose to force the user to use this method (didn't give keyword options).
          It is best for users to pass a transposed array.  
          
         
          If ever deciding to change this, I should merely change the following:
           df.ix  ---> df.columns[]
           mean(axis=0) to mean(axis=1)
           
    
    kwds:
     apply_fcn: Chooses the way to collapse data.  Special/useful functions have special string designations.
        Can be mean, sum, or a variety of integration methods (simps, trapz etc..)
        Any vectorized function (like np.histogram) can be passed in with keyword arguments and it will be
        applied chunk by chunk to the slices.
        
     **apply_fcn_kdws:  If user is passing a function to apply_fcn that requires keywords, the get passed 
      in to dfcut.apply() '''

    ### Probably could do this all at once using groupby... ###
    
    dflist=[]; snames=[]

    ### If single range is passed in, want to make sure it can still be iterated over...
    if len(ranges)==2:
        ranges=[ranges]

    for rng in ranges:
        if len(rng)!=2:
            raise AttributeError("In slices function, all ranges passed in must be len 2, aka a start and stop \
            pair.  %s of length %s was entered"%rng, len(rng))
        else:
            dfcut=df.ix[rng[0]:rng[1]]
            snames.append('%s:%s'%(rng[0],rng[1]))
            
            if isinstance(apply_fcn, str):

                ### Pandas cython operations ###
                if apply_fcn.lower() == 'mean': 
                    series=dfcut.mean(axis=0)
                elif apply_fcn.lower() == 'sum':
                    series=dfcut.sum(axis=0)
                
                    
                ### Integration isn't the same as sum because it takes the units of the x-axis into account through x
                ### parameter.  If interval is odd, last interval is used w/ trapezoidal rule
                elif apply_fcn.lower() == 'simps':
                    series=dfcut.apply(integrate.simps, x=dfcut.index, even='last')
                    
                elif apply_fcn.lower() == 'trapz':
                    series=dfcut.apply(integrate.trapz, x=dfcut.index)     
                    
                elif apply_fcn.lower() == 'romb':
                    series=dfcut.apply(integrate.romb, x=dfcut.index)
                    
                elif apply_fcn.lower() == 'cumtrapz':
                    series=dfcut.apply(integrate.trapz, x=dfcut.index, ititial=None)           
                    
                else:
                    raise AttributeError('apply_fcn in wavelength slices, as a string, must be one of the following: \
                    (mean, sum, simps, trapz, romb, cumtrapz) but %s was entered.  Alternatively, you can pass \
                    a function to apply_fcn, with any relevant **kwds')

            ### Try to apply arbirtrary function.  Note, function can't depend on dfcut, since 
            ### that is created in here
            else:
                series=dfcut.apply(apply_fcn, **applyfcn_kwds)
                
                
            ### OK
            dflist.append(series)
            
    dataframe=DataFrame(dflist, index=snames)
    
            ### THESE ACTUALLY YIELD SERIES
                ###APPLY INTEGRAL, NORMALIZED SUM, NORMALIZED AREA?    
                
            
    return dataframe
            
            

def boxcar(df, binwidth, axis=0):
    ''' Only works on boxcar for now.  Also, want binwidth and/or binnumber to be inputs but not both. '''
    if axis==0:
        binnumber=len(df.columns)/binwidth    
        counts, binarray=np.histogram(df.columns, bins=binnumber)
        digiarray=np.digitize(np.asarray(df.columns, dtype=float), binarray)          
        mapped_series=Series(digiarray, index=df.columns)       
        dfout=df.groupby(mapped_series, axis=1).mean()
        dfout.columns=binarray
    
    elif axis==1:
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
