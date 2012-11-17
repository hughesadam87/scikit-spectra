#Utilities for dataframe manipulations, in particular useful for spectral analysis.

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