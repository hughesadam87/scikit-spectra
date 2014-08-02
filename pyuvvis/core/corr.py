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

[1]
[2] Scaline techniques to enhance two-dimensional correlation spectra, Isao Noda,
    Journal of Molecular Structure.  2008. Volume: 883-884, Issue: 1-3, Pages: 216-227 

'''

#Copy these to notebooks?

import logging
logger = logging.getLogger(__name__) 

from math import pi
import numpy as np

from pyuvvis.plotting.advanced_plots import _gencorr2d, _gen2d
import pyuvvis.config as pvconfig
import pyuvvis.plotting.plot_utils as pvutil
from pca_lite import PCA
#from pcakernel import PCA

# pyuvvis imports
#from pyuvvis.plotting import spec_surface3d

class CorrError(Exception):
    """ """


# Keep this independt of TS; just numpy then more flexible
class Corr2d(object):
    """ Computed 2d correlation spectra, including synchronous and asynchronus,
    correlation, disrelation and other spectra given a 2d data matrix, index
    and columns.  Index and columns are necessary for plotting, so made them
    a mandatory requirement."""

    # Columns aren't used; should I eliminate
    def __init__(self, data, index, columns, idx_unit = 'index', col_unit='col',
                 centered=False):
        """  """
        if data.ndim != 2:
            raise CorrError('Data must be 2d Matrix.')

        # Array typecheck?
        self.data = data
        self.index = index   #Relax these maybe and just hide some sideplots...
        self.columns = columns
        self.idx_unit = idx_unit
        self.col_unit = col_unit

        # Defaults
        self._scaled = False
        self._alpha = 0.8
        self._beta = 0.0
        self._PCA = None

        self._centered = False
        if centered:
            if centered == True:
                self._centered = True
            else:
                self._centered = str(centered)  #User can say "max centered"


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

        self._alpha = kwargs.pop('alpha', self._alpha)
        self._beta = kwargs.pop('beta', self._beta)


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

    # Used internally; for example in calculation of coeff_corr, need unscaled
    @property
    def synchronous_noscale(self):
        """ """
        m = self.data.shape[1]  # columns        
        return np.dot(self.data, self._dynconjtranspose) / (m - 1.0)  #ORDER OF OPERATIONS DEPENDENT (aka np.dot(t_dyn, dyn) doesn't work)


    @property
    def asynchronous_noscale(self):
        """ """
        m = self.data.shape[1]  # columns                
        return np.dot(self.data, np.dot(self._noda, self._dynconjtranspose) ) / (m-1.0)
        

    @property
    def synchronous(self):
        """ """
        if self._scaled:
            return self.synchronous_noscale * self.data.var(axis=1)**(-1.0 * self._alpha) * \
                   abs(self.coeff_corr)**(self._beta)
                    # ** faster than np.power but abs and np.abs same        
        else:
            return self.synchronous_noscale

    @property
    def asynchronous(self):
        """ """     
        if self._scaled:
            return self.asynchronous_noscale * self.data.var(axis=1)**(-1.0 * self._alpha) * \
               abs(self.coeff_disr)**(self._beta)
        else:
            return self.asynchronous_noscale

    @property
    def coeff_corr(self):
        """ Correlation coefficient (pg 78) """   
        return np.divide(self.synchronous_noscale, self.data.std(axis=1))

    @property
    def coeff_disr(self):
        """ Disrelation coefficient (pg 79) """
        # Not the same as np.sqrt( 1 - coef_corr**2), only same in magnitude!
        return np.divide(self.asynchronous_noscale, self.data.std(axis=1))


    @property
    def phase_angle(self):
        """ Global phase angle (pg 79).  This will use scaled data."""
        return np.arctan(self.asynchronous/self.synchronous)
           

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


    # Do I want xx, yy in here?
    def plot(self, attr='synchronous', sideplots='mean', annotate=True,
             **plotkwargs):
        """ Visualize synchronous, asynchronous or phase angle spectra.
        
        Parameters
        ----------
        
        attr: str attribute (e.g. 'synchronous') or numpy 2d array
            Select which correlation spectra to plot.  Choose from 'sync', 
            'async' or 'phase' for synchronous, asynchronous and phase_angle
            matricies.  In addition, can pass a custom matrix.  This is
            mainly for use case of plotting arithmetic operaitons on sync, 
            asynch and other matricies.  For example, if one wants to plot
            the squared synchronous spectrum, they can square the matrix,
            pass it back into this plotting funciton, and the index, titles
            and so forth will all be preserved.  See examples/documention.

        contours: int (20)
            Number of contours to display.
            
        sideplots: str or bool ('mean')
            If True, sideplots will be put on side axis of cross plots.  Use
            'empty' to return blank sideplots.  mean', 'min', 'max', will 
            plot these respective spectra on the sideplots.
            
        annotate: bool (True)
            Adds some default title and x/y labels and text to plot.
            Setting false is shortcut to removing them all
        
        cbar : str or bool (False)
            Add a colorbar to the plot.  Set cbar to 'top', 'bottom', 'left'
            or 'right' to control position.
            
        colormap : str or bool ('jet')
            Color map to apply to the contour plot.
    
            
        grid : bool (True)
            Apply a grid to the contour and sideplots
            
        fill : bool (True)
            Contours are lines, or filled regions.
            
        **plotkwargs: dict
            Any valid matplotlib contour plot keyword, as well as xlabel, ylabel
            and title for convenience.            

        Returns
        -------
        
        tuple (matplotlib.Axes)
            If side plots, returns (ax1, ax2, ax3, ax4)
            If not side plots, returns ax4 only

        """

        # if user passes matrix instead of a string
        if not isinstance(attr, str):
            attr_title = 'Custom' 
            data = attr
            
        elif attr in ['sync', 'synchronous']:
            attr_title = 'Synchronous' #For plot
            data = getattr(self, 'synchronous')
            
        elif attr in ['async', 'asynchronous']:
            attr_title = 'Asynchronous' #For plot
            data = getattr(self, 'asynchronous')

        elif attr in ['phase', 'phase_angle']:
            data = getattr(self, 'phase_angle')
            attr_title = 'Phase Angle' #For plot

        else:
            # Make better
            raise Corr2d('Valid plots include "sync", "async", "phase".'
                         'Alternatively, pass a custom matrix.')
        
        linekwds = dict(linewidth=1, 
                         linestyle='-', 
                         color='black')

        # Only set defaults for labels/title if annotate        
        if annotate:
            plotkwargs.setdefault('xlabel', self.idx_unit)
            plotkwargs.setdefault('ylabel', self.idx_unit)       


            # Title
            cols = self.columns        
            try:
                plotkwargs.setdefault('title', '%s (%.2f - %.2f %s)' % 
                                  ( attr_title, cols.min(), cols.max(), self.col_unit.lower()))
    
            # Working with timestamps (leave in year?)
            except TypeError:
                if self.col_unit.lower() == 'timestamp': #Bit of a hack
                    plotkwargs.setdefault('title', '%s (%s - %s)' % 
                             ( attr_title, 
                               #str(cols.min()).split()[1],  #Cut out year
                               #str(cols.max()).split()[1])
                               cols.min(),
                               cols.max())
                             )           
    
                # Full string format, not alteration of timestamp values
                else:
                    plotkwargs.setdefault('title', '%s (%s - %s %s)' % 
                              ( attr_title, cols.min(), cols.max(), self.col_unit.lower()))   


        # MAKE A DICT THAT RENAMES THESE synchronous: Synchronous Spectrm
        # phase_angle or 'phase' or w/e to: "Phase Anlge" (sans spectrum)
        xx, yy = np.meshgrid(self.index, self.index)
        
        if sideplots:
            
            if sideplots == True:
                sideplots = 'mean'
            
            if self._centered:
                label1, label2 = r'$\bar{A}(\nu_1)$', r'$\bar{A}(\nu_1)$'
            else:
                label1, label2 = r'$A(\nu_1)$', r'$A(\nu_1)$'

            ax1, ax2, ax3, ax4 = _gencorr2d(xx, yy, data, 
                                            label1, label2, **plotkwargs )
            
            # Problem here: this is calling plot method of
            if sideplots == 'mean':
                ax2.plot(self.index, self.data.mean(axis=1), **linekwds)
                ax3.plot(self.index, self.data.mean(axis=1),  **linekwds)     
                
            elif sideplots == 'max':
                ax2.plot(self.index, self.data.max(axis=1), **linekwds)
                ax3.plot(self.index, self.data.max(axis=1),  **linekwds)    
                
            elif sideplots == 'min':
                ax2.plot(self.index, self.data.min(axis=1), **linekwds)
                ax3.plot(self.index, self.data.min(axis=1),  **linekwds)    
                
            
            elif sideplots == 'empty':
                pass
            
            else:
                raise Corr2d('sideplots keyword must be "mean", "max", "min",'
                    ' or "empty".')
        
            # Reorient ax3
            pvutil.invert_ax(ax3)

            if sideplots != 'empty':
                ax2.set_ylabel(sideplots)
                ax2.yaxis.set_label_position('right')
            
            return (ax1, ax2, ax3, ax4)


        else:
            return _gen2d(xx, yy, data, **plotkwargs)[0] #return axes, not contours

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
            

    # Alternate constructers
    @classmethod
    def from_spectra(cls, ts, **kwargs):
        kwargs.setdefault('idx_unit',ts.full_specunit), 
        kwargs.setdefault('col_unit',ts.full_timeunit),
        return cls(np.array(ts),   
                   ts.index, 
                   ts.columns, 
                   **kwargs)


    def __repr__(self):
        """ Aligned columns like pyparty.multicanvas """
        pad = pvconfig.PAD
        address = super(Corr2d, self).__repr__().split()[-1].strip("'").strip('>')
        
        outstring = '%s (%s X %s) at %s:\n' % (self.__class__.__name__,
             self.shape[0], self.shape[1], address)

        #Units
   #     outstring += '%sUnits -->  %s X %s\n' % (pad, self.idx_unit.lower(), self.col_unit.lower())

        #Centering
        outstring += '%sCentering -->  %s\n' % (pad, self._centered)

        #Scaling
        if self._scaled:
            outstring += '%sScaled    -->  %s (a=%s, b=%s)\n' % \
            (pad, self._scaled, self._alpha, self._beta)
        else:
            outstring += '%sScaled    -->  %s\n' % (pad, self._scaled)        

        outstring += '%sUnits     -->  [%s X %s]' % (pad, self.idx_unit.lower(), self.col_unit.lower())


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


if __name__ == '__main__':
    from pyuvvis.data import aunps_glass, solvent_evap
    import numpy as np
    import matplotlib.pyplot as plt 

    ts = solvent_evap()#.as_interval('s').as_iunit('r')
    
    cd = Corr2d.from_spectra(ts)
    cd.center()

    cd.plot(sideplots=False, fill=False, title="Blank sideplots", grid=False)
    plt.show()
    
#    cd.scale()
#    cd.scale(False)
 #   cd.scale(alpha=0.5)
#    ax1,ax2,ax3, ax4 = cd.plot(cmap='bone', 
 #                              fill=True, cbar=True, contours=20, grid=True)
 #   ts.plot(ax=ax2, padding=0.01, title='', xlabel='', ylabel='Full', 
 #           colormap='gray')
 #   ts.plot(ax=ax3, colormap='jet', padding=0.01, title='', xlabel='', ylabel='Full')

#    ts.plot(ax=ax3, padding=0)

#    import plotly.plotly as py
#    fig = plt.gcf()
#    py.iplot_mpl(fig)

    #ax1, ax2, ax3, ax4 = cd.plot(sideplots='empty', grid=True, annotate=False)
    #ts.plot(ax=ax2, padding=0.01, xlabel='', ylabel='', title='')
    #ts.plot(ax=ax3, padding=0.01, xlabel='', ylabel='', title='')
    #pvutil.invert_ax(ax3)

    #plt.show()

 #   print cd.coeff_corr**2 + cd.coeff_disr**2
 #   print cd.synchronous
 #   print cd.mean()
    cd.scale()
    print cd
    cd.pca_fit()