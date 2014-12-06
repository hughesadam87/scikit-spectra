#CITE BOOK, REWRITE

""" Suite for 2-dimensional correlation analysis.  Decided to put it in, despite already
seeing a numpy-based version in paper "2D-correlation analysis applied to in situ and operando Mossbauer spectroscopy".
This would not be pandas friendly, so it wouldn't intgerate into skspec and I also want to build some tools from 
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


2d Codistriubtion Spectroscopy[2] is a more recent development and is also included.

References
----------

[1] Scaling techniques to enhance two-dimensional correlation spectra, Isao Noda,
    Journal of Molecular Structure.  2008. Volume: 883-884, Issue: 1-3, (216-227) 
[2] Isao Nodal. Journal of Molectul Structure. 2014.  Two-dimensional codistriubtion spectroscopy to
    determine the sequential order of distributed presence of species.  1069. 2014 (50-59)

"""

#Copy these to notebooks?

from __future__ import division

import logging
import pandas
logger = logging.getLogger(__name__) 

from math import pi
import numpy as np

from skspec.core.anyspectra import AnyFrame 
from skspec.plotting.correlation_plot import corr2d, corr3d, corr_multi
import skspec.config as pvconfig
import skspec.core.utilities as pvutils
from skspec.pandas_utils.metadframe import MetaDataFrame
from pca_lite import PCA
#from pcakernel import PCA


# Original way to subtract ref spec:
#     data_trans = matrix.transpose()
#    return (data_trans - vector).transpose()

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


class CorrError(Exception):
    """ """
    
class Spec2dError(Exception):
    """ """

class Spec2d(AnyFrame):
    """ Frame to hold synchronous, asynchronous and other 2D spectra objects.
    Mostly just want to customize headers, and subclasses correspond to various
    corr2D object.  For example, synchronous spectra has spectral data on 
    index and columns.  Therefore, it is represented by Spec2D class.

    Also overwrites Spectra.norm for 3dPlotting purposes.

    Will update active/spectral unit based on index/columns, but original
    datarange (like how much time synchronous corresponds to) is stored
    permanently in self._span_string
    """

    def __init__(self, *args, **kwargs):
        """ Hack over norms for plotting API sake.  Stores metadata like
        scaling, spectral and variance range of spectra.  *args, **kwargs
        passed to AnyFrame constructor.

        kwargs
        ------

        _corr2d: Corr2D object

        _norm: ''
           norm to appear in 3dplots and on contour colorbar
        """


        # Mandatory, access to corr2d and hence original dataset 
        # (passed by reference)!
        self._corr2d = kwargs.pop('corr2d')

        #self._scalestring = kwargs.pop('scalestring', '??')
        #self._originadataindex

        # INDEX/COLUMNS are SET TO INDEX OF ORIGINAL DATA
        kwargs['index'] = self._corr2d.index
        kwargs['columns'] = self._corr2d.index

        super(Spec2d, self).__init__(*args, **kwargs)


    @classmethod
    def from_corr2d(cls, corr2d):
        return cls(scale_string=corr2d.scalestring, 
                   originaldatindex=corr2d.index)
        
    @property
    def _var_span(self):
        cols = self._corr2d.columns
        return pvutils._compute_span(cols, with_unit=True)
    
    # Header/output
    # -------------
    @property
    def _header(self):
        """ Header for string printout """
        delim = pvconfig.HEADERDELIM

        # Since correlation REQUIRES index units, this will probably just work
        
        # Certain methods aren't copying this correctly.  Delete later if fix
        name = pvutils.safe_lookup(self, 'name')
        ftunit = pvutils.safe_lookup(self, 'varunit')  
        spunit = pvutils.safe_lookup(self, 'specunit')


        header = "*%s*%sScaling:%s\n" % \
            (name, delim, self._corr2d._scale_string)

        return header


    @property
    def _header_html(self):
        """ Header for html printout """
        delim = pvconfig.HEADERHTMLDELIM

        # Should be same by virtue of index units being same, but don't
        # enforece it; up to user not to change it!
        ftunit = pvutils.safe_lookup(self, 'varunit')  
        spunit = pvutils.safe_lookup(self, 'specunit')

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
        span_string = 'Span:  <font color="#000000">%s</font>' % self._var_span

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

        pltkwargs.setdefault('title', '%s (%s)' % (self.name, self._var_span))        

        # Default to specplot
        if kind not in ['corr2d', 'corr3d']:
            return super(Spec2d, self).plot(kind=kind, **pltkwargs)

        pltkwargs.setdefault('xlabel', self.specunit)
        pltkwargs.setdefault('ylabel', self.specunit)         

        if kind == 'corr2d':
            # If user sets color/cmap, will overwrite
            if 'cmap' not in pltkwargs and 'color' not in pltkwargs and 'colors' not in pltkwargs:
                pltkwargs['cmap'] = pvconfig.CMAP_CONTOUR

            if self.index[0] > self.index[-1]:
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
    def __init__(self, spec, refspec=None):
        """ refspec is if you want custom centering.  """
        if spec.ndim != 2:
            raise CorrError('Data must be 2d!')

        if not isinstance(spec, MetaDataFrame):
            raise CorrError('Corr2d requires skspec data structures (Metadataframe,'
                            'Spectra, etc... got %s') % type(data)


        # MAKE AN ACTUAL COPY OF DATA, NOT PASSING BY REFERENCE
        self.spec = spec.deepcopy()


        self.index = spec.index   #Relax these maybe and just hide some sideplots...
        self.columns = spec.columns
        self.specunit = spec.specunit
        self.varunit = spec.varunit

        # Better to store than compute as a property over and over
        self._noda = noda_matrix(self.M)

        # Defaults
        self._scaled = False
        self.alpha = 0.8
        self.beta = 0.0
        self._PCA = None

        # Ref spectrum/dynamic spectrum/centering
        if refspec is not None:
            # QUICKEST VAILDATION OF REF_SPEC (WHY CLASS NOT WORKING WIT NP.NDARRAY)
            
            #INSTEAD OF TYPE CHECK, JUST FORCE CONVERT BY DOING array(REFSPEC)
            refspec = np.array(refspec)
            if refspec.shape != self.index.shape:
                raise CorrError('Shape mismatch: spectral data index %s and'
                                ' reference spec shape %.' % \
                                (self.index.shape, refspec.shape))

            # Ref spectrum must be stored as an array for subtraction to work 
            # as defined here!
            self.ref_spectrum = np.array(refspec)           
            self._center = 'Pre-centered'
            self.dyn_spec = self.spec.subtract(self.ref_spectrum, axis=0)

        else:
            self.set_center('mean')


    # Scaling and Centering
    # ---------------------

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
        if self.alpha > 1 or self.beta > 1:
            logger.warn('Alpha/Beta lose meaning off of range 0-1.')


    @property
    def center(self):
        return self._center
    

    def set_center(self, style, *args, **kwargs):
        """ User sets centering, this updates the  """

        try:

            if not style:
                self._center = None
                # Instead of np.zeros, I will just multiply 0 times a column
                # To get spectrum of 0's
                ref_spectrum = self.spec[0] * 0.0  

            elif style == 'mean':
                self._center = 'mean'
                ref_spectrum = self.spec.mean(axis=1)

            # style is understood as a function, but not inspected
            else:            
                self._center = 'custom fcn.'           
                ref_spectrum = style(self.spec, *args, **kwargs)

        except Exception:

            raise CorrError('Center requires style of "mean", None or a '
                            ' a function, got "%s".' % style)

        self.ref_spectrum = np.array(ref_spectrum)

        if len(self.ref_spectrum) != self.shape[0]:
            raise CorrError('ref. spectrum should be of spectral length (%s)'
                            ' got "%s".' % (self.shape[0], len(self.ref_spectrum)))

        # Set dynamic spectrum.  Should just be able to subtract but numpy messing up        
        self.dyn_spec = self.spec.subtract(self.ref_spectrum, axis=0)


    @property
    def shape(self):
        return self.spec.shape     

    @property
    def M(self):
        return self.shape[1]

    # Numpy Arrays
    # ------------

    @property
    def sync_noscale(self):
        """ Return unscaled, synchronous spectrum as a numpy array. """
        return np.dot(self.dyn_spec, self._dynconjtranspose) / (self.M - 1.0)  #ORDER OF OPERATIONS DEPENDENT (aka np.dot(t_dyn, dyn) doesn't work)


    @property
    def async_noscale(self):
        """ """
        return np.dot(self.dyn_spec, np.dot(self._noda, self._dynconjtranspose) ) / (self.M-1.0)


    @property
    def coeff_corr(self):
        """ Correlation coefficient (pg 78) """   
        return np.divide(self.sync_noscale, self.joint_var) 


    @property
    def coeff_disr(self):
        """ Disrelation coefficient (pg 79) """
        # Not the same as np.sqrt( 1 - coef_corr**2), only same in magnitude!
        return np.divide(self.async_noscale, self.joint_var)

    @property
    def joint_var(self):
        """ Product of standard devations of dynamic spectrum. 
        s1 * s2 or sqrt(siag(sync*sync)).
        """
        std = self.dyn_spec.std(axis=1) #sigma(lambda)
        return np.outer(std, std)
        #return Spec2d(np.outer(std, std),
                      #corr2d = self,
                      #name='Joint Variance',
                      #iunit='variance')


    # 11/10/14
    # I confirmed that these are equivalent to book definitions from 
    # diagonals of synchronous spectrum!  IE std = sqrt(diag(sync*sync))
    # and var = diag(sync * sync)
    # std is actually > var cuz var <1 so sqrt makes larger

    @property
    def _dynconjtranspose(self):
        """ Dynamic spectrum conjugate transpose; helpful to be cached"""
        return np.conj(self.dyn_spec).transpose()


    # 2D Correlation Spectra
    # ----------------------
    @property
    def sync(self):
        """ """
        if self._scaled:
            matrixout = self.sync_noscale * self.joint_var**(-1.0 * self.alpha) * \
                abs(self.coeff_corr)**(self.beta)
                    # ** faster than np.power but abs and np.abs same        
        else:
            matrixout = self.sync_noscale

        return Spec2d(matrixout, 
                      corr2d = self,
                      name='Synchronous Correlation',
                      iunit='synchronicity')   

    @property
    def async(self):
        """ """     
        if self._scaled:
            matrixout = self.async_noscale * self.joint_var**(-1.0 * self.alpha) * \
                abs(self.coeff_disr)**(self.beta)
        else:
            matrixout = self.async_noscale

        return Spec2d(matrixout, 
                      corr2d = self,
                      name='Asynchronous Correlation',
                      iunit='asynchronicity')   

    @property
    def phase(self):
        """ Global phase angle (pg 79).  This will use scaled data."""
        phase = np.arctan(self.async/self.sync)
        phase.name = 'Phase Map' 
        phase.iunit = 'phase angle'
        return phase    
    
    
    @property
    def modulous(self):
        """ Effective lengh the vector with components Sync/Async"""
        modulous = np.sqrt(self.sync**2 + self.async**2)
        modulous.name = 'Modulous'
        modulous.iunit = 'mod'
        return modulous
        

    @property
    def correlation(self):
        """ 2D Correlation Spectrum"""
        return Spec2d(self.coeff_corr, 
                      corr2d = self,
                      name = 'Correlation Coefficient',
                      iunit='corr. coefficient')                

    @property
    def disrelation(self):
        """ 2D Disrelation Spectrum"""
        return Spec2d(self.coeff_disr,
                      corr2d = self,
                      name = 'Disrelation Coefficient',
                      iunit='disr. coefficient')   


    # 2DCodistribution Spectroscopy
    # -----------------------------
    @property
    def char_index(self):
        """ Characteristic index.  In Ref. [2], this is the 
        characteristic time, and is equation 6.

        Returns: Spectrum of length equivalent to spectral index.
        """
        m = self.M

#        if self._center is None: #pre-center also has this case
        if np.count_nonzero(self.ref_spectrum) == 0:
            raise CorrError('CoDistribution divides by ref spectrum.  If'
                            ' not centring, the ref spec is 0 and you get infinities!')
        coeff = 1.0 / (m * self.ref_spectrum)

        summation = 0 
        k_matrix = np.empty(m)
        for k in range(1, m+1): #m+1 to include m in sum
            k_matrix.fill(k) # in place
            # df.mul is same as dotting:
                #http://stackoverflow.com/questions/15753916/dot-products-in-pandas
            summation += self.dyn_spec.dot(k_matrix) + ((m+1) / 2)
        return coeff * summation

    @property
    def char_perturb(self):
        """ Characteristic index.  In Ref. [2], this is the 
        characteristic time, and is equation 6.

        Returns: Spectrum of length equivalent to spectral index.
        """
        tm, t1 = self.columns[-1], self.columns[0]
        Kj = self.char_index
        
        return ((tm-t1) * ((Kj-1) / (self.M -1))) + t1


    # TO	VECTORIZE:
    
    @property
    def async_codist(self):
        """ Asynchronous codistribution """
        
        # Empty asyn matrix
        numrows = self.shape[0]        
        async = np.empty((numrows,numrows))

        tm, t1 = self.columns[-1], self.columns[0]
        
        # Numpy arrays to speed up loop/indexer?
        tbar = self.char_perturb.values
        var = self.joint_var
        
        # broadcast this?
        for i in range(numrows):
            for j in range(numrows):
                coeff = (tbar[j] - tbar[i]) / (tm -t1)
                # I believe std[i] std[j] is correct way
                async[i][j] = coeff * var[i,j]

        return Spec2d(async, 
                      corr2d=self, 
                      name='Asynchronous Codistribution', 
                      iunit='asynchronicity')
    
    @property
    def sync_codist(self):
        """ Syncrhonous codistribution.  Computed from asyn_codist"""
        numrows = self.shape[0]                    

        # Numpy arrays to speed up calculation
        var = self.joint_var
        async_cod = self.async_codist.values
        
        sync = np.empty((numrows,numrows))
        for i in range(numrows):
            for j in range(numrows):
                sync[i][j] = np.sqrt(var[i,j]**2 - async_cod[i,j]**2 )
                 
        return Spec2d(sync, 
                      corr2d=self, 
                      name='Synchronous Codistribution', 
                      iunit='synchronicity')
    

    def plot(self, **pltkwargs):
        """ Quad plot shows several kinds of correlation plots."""
        return corr_multi(self, **pltkwargs)
        

    def _pcagate(self, attr):
        """ Raise an error if use calls inaccessible PCA method."""
        if not self._PCA:
            raise CorrError('Please run .pca_fit() method before '
                            'calling %s.%s' % self.__class__.__name__, attr)    

    def pca_fit(self, n_components=None, fit_transform=True):# k=None, kernel=None, extern=False):           
        """         
        Adaptation of Alexis Mignon's pca.py script

        Adapted to fit skspec 5/6/2013.  
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
        
        # NOW USES DYNSPEC BUT DID NOT TEST BEFORE CHANGING
        if self.center:
            logger.warn('Builtin PCA will perform mean-centering on'
                        ' data.  Data is not mean centered yet.')
        self._PCA = PCA(n_components=n_components)                
        if fit_transform:
            return self._PCA.fit_transform(self.dyn_spec)#.transpose())
        else:    
            self._PCA.fit(self.dyn_spec)#.transpose())


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
        outstring += '%sCentering -->  %s\n' % (pad, self.center)

        #Scaling
        if self._scaled:
            outstring += '%sScaled    -->  %s\n' % (pad, self._scale_string)
        else:
            outstring += '%sScaled    -->  %s\n' % (pad, self._scaled)        

        outstring += '%sUnits     -->  [%s X %s]' % (pad, 
                                                     self.specunit.lower(), 
                                                     self.varunit.lower())
        return outstring


if __name__ == '__main__':
    from skspec.data import aunps_glass, solvent_evap, aunps_water
    import numpy as np
    import matplotlib.pyplot as plt 

#    ts=aunps_water().as_varunit('s')
    ts = solvent_evap()#.as_varunit('s').as_norm('r')

    cd = Corr2d(ts)#, refspec=ts.mean(axis=1) )
    cd.set_center('mean')
    print cd.sync
    cd.scale(alpha=0, beta=0)
    cd.sync.plot(contours=20, kind='corr3d')
    plt.show()
#    cd.scale(a=.5, b=.5)
    
#    cd.sync
#    cd.async_noscale
