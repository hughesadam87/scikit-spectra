''' Various dataframe-compatible reference utilities. '''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

import numpy as np
from pandas import DataFrame, Series
import logging

logger = logging.getLogger(__name__)

        
def _find_nearest(array, value):
    '''Find nearest value in an array, return index and array value'''
    idx=(np.abs(array-value)).argmin()
    return idx, array[idx]      

def dynamic_baseline(df, slices, style='linear', weightstyle=None, axis=1):
    '''Applies a dynamically calculated reference correction to a dataframe.  User passes in index values, either ranges
    or points, then a linear fit is applied through these points.  Each column in the dataframe is scaled its corresponding
    curve, which is then subracted off.  Essentially, this subracts a reference that can be lopsided- useful for assymetric data, and
    is usually how crude ATR-IR reference correction is performed.  
    
    For now, program only works for index values as the reference.
    
    df- DataFrame.
    
    slice- List of points or ranges at which the reference data is sampled.  For example, 
           ( (300.0, 500.0), 900.0 ).  Curve will take all index values of the dataframe between
           300.0:500.0 (nanometers in my case), and also take the closest index value there is to 900.0. 
           A fit is then drawn between these points.
           
    style- Fitting style to connect the dots between slice regions.  For now, only linear fit is used.  Not sure if higher order
           will ever be useful, so I left this in here as a reminder.
           
    axis-  Axis overwhich to do this reference correction.  For now, ONLY INDEX IS IMPLEMENTED.
    
    weightstyle- Tries to account for idea that if I pass slices, and one slice contains more points, then the line of best fit will be weighted
                 more strongly to this region.  For now, I haven't implemented this, but would have to actually use poly1d to call more points to the
                 other regions, or some other solution?  This does have an option, mean, which will take the mean if each range so that each range gets 
                 a single fit point; however, I think this is useless as this can be passed in anyway.  And it's the mean of the x-values, not even the 
                 mean of the data along that axis anyway.
                 
    returns-
       DataFrame of fitted references.'''
        
    ### Test for proper input ###
    if style != 'linear' or axis != 1:
        raise NotImplementedError('reference correction only support linear fitting style and index axis iteration only.')
    
    if weightstyle:
        if weightstyle != 'midpoint':
            raise NotImplemented('weightstyle attribute in reference_correction must be either None or "midpoint" but %s was entered'%weightstyle)

    xp=[] #xpoints
    
    logger.info('Applying dynamic baseline (style=%s)' % style)
    
    for val in slices:
        ### If slice is a single point, find its nearest actual entry in df.index
        if len(val) == 1:
            xp.append(_find_nearest(df.index, val)[1])
        
        ### If slice is range, take all index values in that region
        elif len(val) == 2:
            xvals=np.asarray(df.ix[ val[0]: val[1] ].index)

            if weightstyle =='mean':
                xp.append(np.mean(xvals))

            else:
                xp=xp+list(xvals) #List necessary to get npdtype straight..
            
            
        else:
            raise AttributeError('In reference correction, slices must 1 or 2 items;'
                'received %s of len %s'%(val, len(val)))
    
    ### Apply 1-d connect the dots curvefit to each column, then subtract this from said column
    ### Still vectorized, despite loop.  Loop is necessary; too much to use df.apply.
    bout={}                      
    for col in df.columns:
        curve=df[col] #Series at this point
        z=np.polyfit(xp, curve[xp], 1)  
        p=np.poly1d(z)        
        array=p(np.asarray(list(curve.index) ) )   
        reference=Series(array, name=col, index=curve.index) #curve.index instead of df.index                            
        bout[col]=reference #incase index is getting recast for nans or some behavior I may not be aware of
    
    bout=DataFrame(bout)
    bout.reindex(columns=df.columns) #Columns are automatically if they are datetimes
    return bout        