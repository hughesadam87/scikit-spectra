#CITE BOOK, REWRITE

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
just throw out regions where not much is happening right?  Maybe call it a 2dcs filter.

References
----------

[1] Scaling techniques to enhance two-dimensional correlation spectra, Isao Noda,
[2] Journal of Molecular Structure.  2008. Volume: 883-884, Issue: 1-3, Pages: 216-227 

'''

#Copy these to notebooks?

import logging
import pandas
logger = logging.getLogger(__name__) 

from math import pi
import numpy as np

from pyuvvis.core.anyspectra import AnyFrame 
from pyuvvis.plotting.correlation_plot import corr2d, corr3d
import pyuvvis.config as pvconfig
import pyuvvis.core.utilities as pvutils
from pyuvvis.pandas_utils.metadframe import MetaDataFrame
from pca_lite import PCA
#from pcakernel import PCA


class CorrError(Exception):
    """ """
class Spec2dError(Exception):
    """ """

class Spec2d(AnyFrame):
    """ Frame to hold synchronous, asynchronous and other 2D spectra objects.
    Mostly just want to customize headers, and subclasses correspond to various
    corr2D object.  For example, synchronous spectra has spectral data on 
    index and columns.  Therefore, it is represented by Spec2D class.
    
    Also overwrites Spectra.iunit for 3dPlotting purposes.
    
    Will update active/spectral unit based on index/columns, but original
    datarange (like how much time synchronous corresponds to) is stored
    permanently in self._span_string
    """

    def __init__(self, *args, **kwargs):
        """ Hack over iunits for plotting API sake.  Stores metadata like
        scaling, spectral and variance range of spectra.  *args, **kwargs
        passed to AnyFrame constructor.
        
        kwargs
        ------

       _corr2d: Corr2D object
       
       _iunit: ''
           iunit to appear in 3dplots and on contour colorbar
        """


        # Mandatory, access to corr2d and hence original dataset 
        # (passed by reference)!
        self._corr2d = kwargs.pop('corr2d')

        # INDEX/COLUMNS are SET TO INDEX OF ORIGINAL DATA
        kwargs['index'] = self._corr2d.index
        kwargs['columns'] = self._corr2d.index
        
              
        iunit = kwargs.pop('iunit', '')        
        super(Spec2d, self).__init__(*args, **kwargs)
        self._itype = iunit
        

    @property
    def _span_string(self):
        """ Format span of the original data columns (used in header)"""
        cols = self._corr2d.data.columns
        
        try:
            span = '%.2f - %.2f' % (cols.min(), cols.max())
            
        except TypeError:
            if cols.unit == 'dti': #hack
                span = '%s - %s' % (
                    str(cols.min()).split()[1], #Cut out year
                    str(cols.max()).split()[1]
                   )

            # Interval or otherwise unkown
            else:
              span = '%s - %s' % (cols.min(), cols.max())

        span_string = '%s %s'  % (span, self._corr2d.varunit) #full varunit?        
        return span_string

    # Overwrite Spectra.iunit API 
    # ---------------------------
    @property
    def iunit(self):
        return self._itype  

    # No distinction full_iunit and iunit
    @property
    def full_iunit(self):
        return self._itype
  
    @iunit.setter
    def iunit(self, unit):     
        self._itype = unit 
        
        
    # Header/output
    # -------------
    @property
    def _header(self):
        """ Header for string printout """
        delim = pvconfig.HEADERDELIM

        # Certain methods aren't copying this correctly.  Delete later if fix
        name = pvutils.hasgetattr(self, 'name', '??')
        full_varunit = pvutils.hasgetattr(self, 'full_varunit', '??')
        specunit = pvutils.hasgetattr(self, 'specunit', '??')
        varunit = pvutils.hasgetattr(self, 'varunit', '??')


        header = "*%s*%sScaling:%s\n" % \
            (name, delim, self._corr2d._scale_string)

        return header


    @property
    def _header_html(self):
        """ Header for html printout """
        delim = pvconfig.HEADERHTMLDELIM

        # Should be same by virtue of index units being same, but don't
        # enforece it; up to user not to change it!
        ftunit = getattr(self, 'varunit', '??')  
        spunit = getattr(self, 'specunit', '??')

        if self.ndim > 1:
            s1, s2 = self.shape            
            colorshape = '<font color="#0000CD">(%s%s X %s%s)</font>' % (
                                                              s1,
                                                              spunit,
                                                              s2,
                                                              ftunit)

        #If user turns 2D Corr into a 1D spectrum (which they shouldn't...)
        else:
            colorshape = '<font color="#0000CD"> (%s)</font>' % (self.shape)

        # Green        
        scale_string = 'Scaling: <font color="#197519">%s</font>' % self._corr2d._scale_string
        
        # Black 
        span_string = 'Span:  <font color="#000000">%s</font>' % self._span_string

        header = "%s:&nbsp%s%s%s%s%s\n" % \
            (self.name, 
             colorshape,
             delim,
             scale_string,
             delim,
             span_string         
             )   

        return header
    
    
    def plot(self, kind='corr2d', **pltkwargs):
        """ """

        pltkwargs.setdefault('title', '%s (%s)' % (self.name, self._span_string))        

        # Default to specplot
        if kind not in ['corr2d', 'corr3d']:
            return super(Spec2d, self).plot(kind=kind, **pltkwargs)
                
        pltkwargs.setdefault('xlabel', self.specunit)
        pltkwargs.setdefault('ylabel', self.specunit)         
        
        if kind == 'corr2d':
            # If user sets color/cmap, will overwrite
            if 'cmap' not in pltkwargs and 'color' not in pltkwargs and 'colors' not in pltkwargs:
                pltkwargs['cmap'] = pvconfig.CMAP_CONTOUR
            
            if ts.index[0] > ts.index[-1]:
                pltkwargs['_reverse_axis'] = True


            return corr2d(self, **pltkwargs)

        elif kind == 'corr3d':
            return corr3d(self, **pltkwargs)
     
    


# Keep this independt of TS; just numpy then more flexible
class Corr2d(object):
    """ Computed 2d correlation spectra, including synchronous and asynchronus,
    correlation, disrelation and other spectra given a 2d data matrix, index
    and columns.  Index and columns are necessary for plotting, so made them
    a mandatory requirement."""

    # Columns aren't used; should I eliminate
    def __init__(self, data, centered=False, numpyreturn=False):
        """  """
        if data.ndim != 2:
            raise CorrError('Data must be 2d!')

        if not isinstance(data, MetaDataFrame):
            raise CorrError('Corr2d requires pyuvvis data structures (Metadataframe,'
                            'Spectra, etc... got %s') % type(data)


        # MAKE AN ACTUAL COPY OF DATA, NOT PASSING BY REFERENCE
        self.data = data.deepcopy()


        self.index = data.index   #Relax these maybe and just hide some sideplots...
        self.columns = data.columns
        self.specunit = data.specunit
        self.varunit = data.varunit

        # Defaults
        self._scaled = False
        self.alpha = 0.8
        self.beta = 0.0
        self._PCA = None

        self._centered = False
        if centered:
            if centered == True:
                self._centered = True
            else:
                self._centered = str(centered)  #User can say "max centered"


    @property
    def _scale_string(self):
        """ Current state of scalling, used in __repr__ and plot """
        if self._scaled:
            return '(a=%s, b=%s)' % (self.alpha, self.beta)
        return 'False'



    def scale(self, *args, **kwargs):
        """Scale the synchronous and asynchronous spectra via REF 2
        based on generalized exponential parameters.  Scaling alpha will enhance
        the fine detail of the correlations, but also the noise.  Enhancing beta
        can screen the fine details and enhance the primary correlations.  Alpha
        0.8 and beta 0.0 are suggested as optimal tradeoff between fine correlation
        enhancement and low noise.
        """
        if args:
            if len(args) > 1:
                raise CorrError('Please use keywords (alpha=..., beta=...) to'
                                'avoid ambiguity.') 
                # Make that a custom exception
            if args[0] == True:
                if self._scaled == True:
                    logger.warn("Data already scaled!")
                self._scaled = True
            elif args[0] == False:
                if self._scaled == False:
                    logger.warn("Data already unscaled!")
                self._scaled = False
            else:
                raise CorrError('Argument "%s" not understood; please use True or False.')

        else:
            self._scaled = True

        self.alpha = kwargs.pop('alpha', self.alpha)
        self.beta = kwargs.pop('beta', self.beta)


    def center(self, style='mean'):  #Just call mean centered?
        """ Mean centers data.  Mean centering is defined columnwise, and while
        this can be down by a call to dataframe.subtract(x.mean(axis=1), axis=0),
        that requries a pandas dataframe method.  Instead, we transpose the data,
        subtract the mean, then transpose again. (confirmed equivalent)"""
        if self._centered:
            logger.warn('Data is already centered.') #Better than a warning I think
                    #In case user sets centered ot 'max' or something in __init__
        else:
            if style == 'mean':
                # Alternate way, pandas dependent
                # self.data = self.data.subtract(self.data.mean(axis=1), axis=0)
                data_trans = self.data.transpose()
                self.data = (data_trans - data_trans.mean()).transpose()
                self._centered = True
            else:
                raise NotImplementedError('mean centering only supported')



    # Numpy Arrays
    # ------------

    @property
    def synchronous_noscale(self):
        """ Return unscaled, synchronous spectrum as a numpy array. """
        m = self.data.shape[1]  # columns        
        return np.dot(self.data, self._dynconjtranspose) / (m - 1.0)  #ORDER OF OPERATIONS DEPENDENT (aka np.dot(t_dyn, dyn) doesn't work)


    @property
    def asynchronous_noscale(self):
        """ """
        m = self.data.shape[1]  # columns                
        return np.dot(self.data, np.dot(self._noda, self._dynconjtranspose) ) / (m-1.0)


    @property
    def coeff_corr(self):
        """ Correlation coefficient (pg 78) """   
        return np.divide(self.synchronous_noscale, self.std) 


    @property
    def coeff_disr(self):
        """ Disrelation coefficient (pg 79) """
        # Not the same as np.sqrt( 1 - coef_corr**2), only same in magnitude!
        return np.divide(self.asynchronous_noscale, self.std)

    #If std/var aren't arrays, will get issues in computations like async/sync
    @property
    def std(self):
        """ Standard devation along axis=1 as numpy array"""
        return self.data.std(axis=1).values

    @property
    def var(self):
        """ Variance along axis=1 as numpy array"""
        return self.data.var(axis=1).values


    @property
    def _noda(self):
        """ Store noda matrix of data; depends of number of columns in 
        data.
        """
        return noda_matrix(self.shape[1])

    @property
    def _dynconjtranspose(self):
        """ Dynamic spectrum conjugate transpose; helpful to be cached"""
        return np.conj(self.data).transpose()


    # Correlation Spectra Objects
    @property
    def synchronous(self):
        """ """
        if self._scaled:
            matrixout = self.synchronous_noscale * self.var**(-1.0 * self.alpha) * \
                abs(self.coeff_corr)**(self.beta)
                    # ** faster than np.power but abs and np.abs same        
        else:
            matrixout = self.synchronous_noscale

        return Spec2d(matrixout, 
                      corr2d = self,
                      name='Synchronous Spectrum',
                      iunit='synchronicity')   

    @property
    def asynchronous(self):
        """ """     
        if self._scaled:
            matrixout = self.asynchronous_noscale * self.var**(-1.0 * self.alpha) * \
                abs(self.coeff_disr)**(self.beta)
        else:
            matrixout = self.asynchronous_noscale

        return Spec2d(matrixout, 
                      corr2d = self,
                      name='Asynchronous Spectrum',
                      iunit='asynchronicity')   

    @property
    def phase(self):
        """ Global phase angle (pg 79).  This will use scaled data."""
        phase = np.arctan(self.asynchronous/self.synchronous)
        phase.name = 'Phase Map' 
        phase.iunit = 'phase angle'
        return phase    


    @property
    def correlation(self):
        """ 2D Correlation Spectrum"""
        return Spec2d(self.coeff_corr, 
                      corr2d = self,
                      name = 'Correlation Spectrum',
                      iunit='corr. coefficient')                

    @property
    def disrelation(self):
        """ 2D Disrelation Spectrum"""
        return Spec2d(self.coeff_disr,
                      corr2d = self,
                      name = 'Disrelation Spectrum',
                      iunit='disr. coefficient')   


    @property
    def shape(self):
        return self.data.shape          


    def _pcagate(self, attr):
        """ Raise an error if use calls inaccessible PCA method."""
        if not self._PCA:
            raise CorrError('Please run .pca_fit() method before '
                            'calling %s.%s' % self.__class__.__name__, attr)    

    def pca_fit(self, n_components=None, fit_transform=True):# k=None, kernel=None, extern=False):           
        """         
        Adaptation of Alexis Mignon's pca.py script

        Adapted to fit PyUvVis 5/6/2013.  
        Original credit to Alexis Mignon:
        Module for Principal Component Analysis.

        Author: Alexis Mignon (c)
        Date: 10/01/2012
        e-mail: alexis.mignon@gmail.com
        (https://code.google.com/p/pypca/source/browse/trunk/PCA.py)

        Constructor arguments:
        * k: number of principal components to compute. 'None'
             (default) means that all components are computed.
        * kernel: perform PCA on kernel matrices (default is False)
        * extern: use extern product to perform PCA (default is 
               False). Use this option when the number of samples
               is much smaller than the number of features.            

        See pca.py constructor for more info.

        This will initialize PCA class and fit current values of timespectra.

        Notes:
        ------
        The pcakernel.py module is more modular.  These class methods
        make it easier to perform PCA on a timespectra, but are less 
        flexible than using the module functions directly.

        timespectra gets transposed as PCA module expects rows as 
        samples and columns as features.

        Changes to timespectra do not retrigger PCA refresh.  This 
        method should be called each time changes are made to the data.
        """
        if self._centered != True:
            logger.warn('Builtin PCA will perform mean-centering on'
                        ' data.  Data is not mean centered yet.')
        self._PCA = PCA(n_components=n_components)                
        if fit_transform:
            return self._PCA.fit_transform(self.data)#.transpose())
        else:    
            self._PCA.fit(self.data)#.transpose())


    @property
    def PCA(self):
        """ Return the full PCA class object"""
        self._pcagate('pca')
        return self._PCA 

    @property
    def pca_evals(self):
        self._pcagate('eigen values')
        # Index is not self.columns because eigenvalues are still computed with
        # all timepoints, not a subset of the columns        
        return self._PCA.eigen_values_

    @property
    def pca_evecs(self):
        self._pcagate('eigen vectors')
        return self._PCA.eigen_vectors_

    def load_vec(self, k):
        """ Return loading vector series for k.  If k > number of components
            computed with runpca(), this raises an error rather than 
            recomputing.
        """
        self._pcagate('load_vec')
        if k > len(self.shape[1]):
            raise CorrError('Principle components must be <= number'
                            'of samples %s'% self.shape[1])

        # Decided to put impetus on user to recompute when not using enough principle components
        # rather then trying to figure out logic of all use cases.
        # If k > currently stored eigenvectors, recomputes pca
        if self._PCA._k:
            if k > len(self.pca_evals):   
                logger.warn('Refitting, only %s components were computed'
                            'originally' % self._PCA._k)
                self.pca_fit(n_components=k, fit_transform=False)

        return self._PCA.eigen_vectors_[:,k]


    def __repr__(self):
        """ Aligned columns like pyparty.multicanvas """
        pad = pvconfig.PAD
        address = super(Corr2d, self).__repr__().split()[-1].strip("'").strip('>')

        outstring = '%s (%s X %s) at %s:\n' % (self.__class__.__name__,
                                               self.shape[0], self.shape[1], address)

        #Units
    #     outstring += '%sUnits -->  %s X %s\n' % (pad, self.specunit.lower(), self.varunit.lower())

        #Centering
        outstring += '%sCentering -->  %s\n' % (pad, self._centered)

        #Scaling
        if self._scaled:
            outstring += '%sScaled    -->  %s\n' % (pad, self._scale_string)
        else:
            outstring += '%sScaled    -->  %s\n' % (pad, self._scaled)        

        outstring += '%sUnits     -->  [%s X %s]' % (pad, 
                                                     self.specunit.lower(), 
                                                     self.varunit.lower())


        return outstring


def noda_matrix(length):
    ''' Length is the number of timepoints/columns in the dataframe. 
       Returns the hilbert noda Transformation matrix.'''

    # XXX: how to vectorize?
    Njk = np.empty( (length,length))
    for j in range(length):
        for k in range(length):
            if j==k:
                Njk[j,k]=0
            else:
                Njk[j, k]=1.0 /  ( pi * (k-j)  )  #DOUBLE CHECK j-i with old verison.    
    return Njk


if __name__ == '__main__':
    from pyuvvis.data import aunps_glass, solvent_evap
    import numpy as np
    import matplotlib.pyplot as plt 

#    ts = solvent_evap()#.as_varunit('s').as_iunit('r')
#    ts.plot(kind='contour')
    ts = aunps_glass().as_varunit('s')#.as_varunit('intvl')
#    print ts.varunits()

    cd = Corr2d(ts)
   # cd.scale()
    
#    print cd.coeff_corr
#    print cd.asynchronous
   # cd.center()
#    cd.plot()
#    cd.plot('async')

    s = cd.synchronous
#    s = s.nearby[3250.0:750, 3250:750]
#    s.plot(grid=True, fill=True, cbar=True)
#    s.plot(kind='corr3d')
    s.plot(kind='wire', mesh=50)
    plt.show()
