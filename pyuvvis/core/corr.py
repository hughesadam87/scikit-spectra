''' Suite for 2-dimensional correlation analysis based on pandas dataframes.  Decided to put it in, despite already
seeing a numpy-based version in paper "2D-correlation analysis applied to in situ and operando Mossbauer spectroscopy".
This would not be pandas friendly, so it wouldn't intgerate into pyuvvis and I also want to build some tools from 
scratch to refamiliarize myself with the topic.

To remember/writeup eventually:

From page 32 Noda book,
Classical statistical cross correlation measures the dot product between spectral variables at different times.
For example, a pulse at t=0 and again at t=3, then the cross correlation would be max at tau=3.  If this experiment
went on for 50 minutes, then we average and integrate over all time.  If this pulse happed every 3 seconds, this correlation
would be 100% for exmaple.  If the pulse happed like only 5 times, the correlation would be diluted by the normalization factor.

The synchronous spectrum is the cross correlation at tau=0, summed and averaged over all times.  Basically, it measures the instantaneous
correlation of all spectral variables.  The asynchronous spectrum is the instantaneous orthogonal spectrum basically.  So whenever two things
are moving together at one instant, weight goes into the sync.  If not, weight goes into the async  Makes me think of an easy filter!  Can
just throw out regions where not much is happening right?  Maybe call it a 2dcs filter.'''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

from pandas import Series, DataFrame
from numpy import dot, empty, asarray, conj
from math import pi

# pyuvvis imports
from pyuvvis.pyplots.advanced_plots import spec_surface3d
from pyuvvis.exceptions import badvalue_error


def make_ref(df, method='mean'):
    ''' Get a reference spectrum, requried for computing the dynamic spectrum (y-ref).  Usually this is this is set
    to the time-wise mean of the dataset, to 0, or to an external, pre-saved spectrum.  This will generate mean or empy
    reference spectra.  External spectra are easy enough to generate.
    
    Assumes spectral information is along the index of the dataframe!  No attempt to acommadate other styles is made.
    
    df: DataFrame with spectral data along index/row axis (=1) and temporal/physical variable along columns (axis=0)
    
    Method: Style to generate reference spectrum from dataframe.
       "mean" - Columnwise-mean of the dataframe
       "empty" - Fills series with 0.0's to length of spectral index
    
    returns: series of length of df.index'''

    method=method.lower()
    
    if method=='mean':
        refspec=df.mean(axis=1)

    elif method=='empty':
        refspec=Series( [0.0 for i in range(len(df.index))], index=df.index)  #builtin way to do this?
               
        
    else:
        raise badvalue_error(method, 'mean, empty')
        
    refspec.name='refspec' #Not sure if this will be useful
    return refspec

### PUT IN SPACING METHOD FOR NON-EVENLY SPACED DATA!

def noda_matrix(length):
    ''' Length is the number of timepoints/columns in the dataframe. 
       Returns the hilbert noda Transformation matrix.'''

    # XXX: how to vectorize?
    Njk=empty( (length,length))
    for j in range(length):
        for k in range(length):
            if j==k:
                Njk[j,k]=0
            else:
                Njk[j, k]=1.0 /  ( pi * (k-j)  )  #DOUBLE CHECK j-i with old verison.    
    return Njk

def ca2d(df, reference):
    '''This actually compuates 2d correlation analysis'''
    dyn=df.sub(reference, axis=0) #Need to subtract along index this way (WHAT IS THIS)?
    T_dyn=conj(dyn).transpose()  #Conjugate transpose matrix
    m=len(df.columns)  #confirmed columns
    
    ### Synchronous spectrum is simply the normalized covariance matrix.
    S=dot(dyn, T_dyn) / (m - 1.0)  #ORDER OF OPERATIONS DEPENDENT (aka dot(t_dyn, dyn) doesn't work)
    
    ### Generate Noda Matrix 
    Njk=noda_matrix(m)
    
    ### Asynchronous spectrum using Hilbert Transformation
    A=dot(dyn, dot(Njk, T_dyn) ) / (m-1.0)
    
    ### Convert and return as dataframes
    S=DataFrame(S, index=df.index, columns=df.index)
    A=DataFrame(A, index=df.index, columns=df.index)
    
    return S, A    


def corr_3d(df, **pltkwds):
    ''' 3d plot suited for correlation analysis.  If special "speclabel" keyword is passed, it will
        add the "spectral label" to both the x and y-axis.  Otherwise, x,y,z labels can be set through 
        their own keywords.'''

    if 'speclabel' in pltkwds:
        pltkwds['xlabel']=pltkwds['speclabel']
        pltkwds['ylabel']=pltkwds['speclabel']
                
    pltkwds['elev']=pltkwds.pop('elev', 31)
    pltkwds['azim']=pltkwds.pop('azim', -52)    
    return spec_surface3d(df, **pltkwds)    

def sync_3d(df, checkdata=False,  **pltkwds):
    ''' Label and title set for synchronous correlation 3d spectrum.  Wrapper for corr_3d.  Has extra keywords for checking 2dcs data for errors.
    
        Checkdata: To be added.  Should check a few entries to make sure matrix is symmetric, to make sure not passing asynchronous spectrum, and also that
        data is evenly shaped (eg 30 by 30).'''
    
    if checkdata == True:
        ### Test for even shape
        s0,s1=df.shape
        if s0 != s1:
            raise Exception('Checkdata failed in sync_3d.  Synchronous spectra must have equal row and column dimensions. \
            Df dimensions were: %i,%i'%(s0, s1))
        
        ### IMPLEMENT TEST FOR SYMMETRY, NOT SURE HOW

    pltkwds['zlabel']=pltkwds.pop('zlabel', 'Synchronicity')      

    pltkwds['title_def']='Synchronous Spectrum'   
    corr_3d(df, **pltkwds)
    
def async_3d(df, checkdata=False,  **pltkwds):
    ''' Label and title set for synchronous correlation 3d spectrum.  Wrapper for corr_3d. '''
    
    if checkdata == True:
        ### Test for even shape
        s0,s1=df.shape
        if s0 != s1:
            raise Exception('Checkdata failed in sync_3d.  Aynchronous spectra must have equal row and column dimensions.\
            Df dimensions were: %i,%i'%(s0, s1))
        
        ### IMPLEMENT TEST FOR ANTI-SYMMETRY, NOT SURE HOW    
    
    pltkwds['zlabel']=pltkwds.pop('zlabel', 'Asynchronicity')      
    
    pltkwds['title_def']='Asynchronous Spectrum'
    corr_3d(df, **pltkwds)    
