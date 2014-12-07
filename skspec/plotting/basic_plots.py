import plot_utils as put
import skspec.core.utilities as pvutils
import skspec.config as pvcnfg
import logging
import numpy as np
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

class PlotError(Exception):
    """ """

#XXX UPDATE DOCSTRING (HOW TO REFERENCE SPECPLOT TO THIS ONE)
def _genplot(ts, *args, **pltkwargs):
    """ Generic wrapper to ts._frame.plot(), that takes in x/y/title as parsed
    from various calling functions:
    NEW KEYWORDS:
        grid
        color
        labelsize
        titlesize
        ticksize 
        xlim/ylabel
        cbar
        ax
        fig
        xlabel
        ylabel
        title
    """
             
    # Add custom legend interface.  Keyword legstyle does custom ones, if pltkwrd legend==True
    # For now this could use improvement  
    xlabel = pltkwargs.pop('xlabel', '')
    ylabel = pltkwargs.pop('ylabel', '')
    title = pltkwargs.pop('title', '')

    pltkwargs.setdefault('legend', False)
    pltkwargs.setdefault('linewidth', 1)
    legstyle = pltkwargs.pop('legstyle', None)   
        
    # Adhere to cananoical "cmap" 
    if 'cmap' in pltkwargs:
        pltkwargs['colormap'] = pltkwargs.pop('cmap')    
    
    fig = pltkwargs.pop('fig', None)
    ax = pltkwargs.pop('ax', None)
    cbar = pltkwargs.pop('cbar', False)
    _barlabels = 5 #Number of ticks/labels in colorbar

    xlim = pltkwargs.pop('xlim', None)
    ylim = pltkwargs.pop('ylim', None)
    custompadding = pltkwargs.pop('custompadding', 0.05)
            
            
    if not ax:
        f, ax = plt.subplots(1)
        if not fig:
            fig = f
        
   
    # Grid (add support for minor grids later)
    grid = pltkwargs.pop('grid', 'black')
    
    labelsize = pltkwargs.pop('labelsize', pvcnfg.LABELSIZE) #Can also be ints
    titlesize = pltkwargs.pop('titlesize', pvcnfg.TITLESIZE)
    ticksize = pltkwargs.pop('ticksize', '') #Put in default and remove bool gate below

    pltkwargs['ax'] = ax            
    ax = ts._frame.plot(**pltkwargs)
    
    if cbar:
        if pltkwargs.get('color', None):
            raise PlotError('Colorbar requires cmap; solid color \
            "%s" found.' % pltkwargs['color'])

        c_rotation, c_reverse = 90, False
        if cbar in ['r', 'reverse']:
            c_rotation, c_reverse = 270, True
        if not fig:
            raise PlotError("Color bar requries access to Figure.  Either pass fig"
                            " keyword or do not pass custom AxesSubplot.")

        # Need a colormap if you have a colorbar!
        try:
            pcmap = pltkwargs['colormap']
        except KeyError:
            raise PlotError('Cannot plot a colorbar without a colormap!')

        mappable, vmin, vmax = put._annotate_mappable(ts, pcmap, axis=0)
        cbar = fig.colorbar(mappable, ticks=np.linspace(vmin, vmax, _barlabels))
        
        tunit = pvutils.safe_lookup(ts, 'full_varunit')
        
        cbar.set_label(r'%s$\rightarrow$' % tunit, rotation=c_rotation)
        
        if len(ts.columns) > _barlabels -1:
            label_indices = np.linspace(0, len(ts.columns), _barlabels)
            label_indices = [int(round(x)) for x in label_indices]
            if label_indices[-1] > len(ts.columns)-1:
                label_indices[-1] = len(ts.columns)-1 #Rounds over max
            
            labels = [ts.columns[x] for x in label_indices]

            # IF LABELS ARE FLOATS (NEED A BETTER CONDITION THAN THIS)
            try:
                labels = [round(float(x),put.float_display_units) for x in label_indices]
            except Exception:
                pass
        
        # Don't add custom labels if aren't at least 5 columns if DF        
        else:
            labels = []
            
        cbar.ax.set_yticklabels(labels)
            
        if c_reverse:
            cbar.ax.invert_yaxis()
        
    # Add minor ticks through tick parameters  
    ax.minorticks_on()
        
    ax.set_xlabel(xlabel, fontsize=labelsize)
    ax.set_ylabel(ylabel, fontsize=labelsize)
    ax.set_title(title, fontsize=titlesize)         
    
    # Not normazling padding correctly!
    
    def _correct_padding(xi,xf):
        """ Note, when making multiplots, this can be an issue and users
        will want to do padding=None
        """
        dlt_x = xf-xi
        boundary = abs(dlt_x *custompadding)
        low_bound = xi-boundary
        high_bound = xf+boundary
        return (low_bound, high_bound)
    
    
    if not xlim and custompadding is not None:
        try:
            xlim = _correct_padding(min(ts.index), max(ts.index))
            ax.set_xlim(xlim)
        # Padding not inferrable from string indicies like in time plots 
        except Exception:
            pass
                 
    if not ylim and custompadding is not None:
        try:
            ylim = _correct_padding(ts.min().min(), ts.max().max())
            ax.set_ylim(ylim)
        except Exception:
            pass
        
    
    if legstyle and pltkwargs['legend'] == True:  #Defaults to False
        if legstyle == 0:
            ax.legend(loc='upper center', ncol=8, shadow=True, fancybox=True)
        elif legstyle == 1:
            ax.legend(loc='upper left', ncol=2, shadow=True, fancybox=True)  
        elif legstyle == 2:
            ax=put.easy_legend(ax, position='top', fancy=True)

    # http://matplotlib.org/api/axis_api.html           
    # Other grid args like linestyle should be set directly with calls
    # to ax.grid(**linekwds)
    if grid:
        if grid == True:
            ax.grid()
        else:
            ax.grid(color=grid) #Let's any supported color in
        
    if ticksize:
        logger.info('Adjusting ticksize to "%s"' % ticksize)
        # Get all x and y ticks in a list
        allticks = ax.xaxis.get_majorticklabels()
        allticks.extend(  ax.yaxis.get_majorticklabels() )

        for label in allticks:
            label.set_fontsize(ticksize)
         #  label.set_fontname('courier')        

    return ax    


# Requires ranged dataframe used wavelength slices method
def range_timeplot(ranged_ts, **pltkwds):
    ''' Makes plots based on ranged time intervals from spec_utilities.wavelength_slices().
    Uses a special function, put._uvvis_colorss() to map the visible spectrum.  Changes default legend
    behavior to true.'''

    pltkwds['cmap'] = pltkwds.pop('cmap', 'jet')
    pltkwds['legend'] = pltkwds.pop('legend', True)
    pltkwds['linewidth'] = pltkwds.pop('linewidth', 2.0 )  
          
    tunit = pvutils.safe_lookup(ranged_ts, 'full_varunit')    
          
    pltkwds.setdefault('xlabel', tunit)     
    pltkwds.setdefault('ylabel', '$\int$ %s (sliced)' % ranged_ts.full_iunit)    
    pltkwds.setdefault('title', 'Area Ranges: '+ ranged_ts.name )       
                
    # Needs to be more robust and check specunit is index etc...
    return _genplot(ranged_ts.transpose(), **pltkwds)   #ts TRANSPOSE


def areaplot(ranged_ts, **pltkwds):
    """
    Makes plots based on ranged time intervals from spec_utilities.wavelength_slices().
    Uses a special function, put._uvvis_colorss() to map the visible spectrum.  
    Changes default legend behavior to true.
    
    Parameters:
    -----------
    ranged_ts: Spectra or Spectrum.  If n x m spectra, ts.area() will be called,
    and transposed().  If Spectrum, passed directlyt hrough.
    
    Notes:
    ------
    Added some extra functionality on 2/13/13, to make it ok if user passed in 
    transposed() or non-transposed(). Additionally, if user passes non Mx1
    dimensional plot, it recomputes the area.  Hence, user can just do areaplot(ts)
    """
    
    # If not M x 1 shape, recompute area
    if ranged_ts.ndim > 1:
        rows, cols = ranged_ts.shape
        if cols != 1 and rows != 1:
            try:
                ranged_ts = ranged_ts.area()
            except Exception:
                # Often error is if someone passed in transposed area using datetime index
                raise IOError('Could not successfully run .area() on %s object.' % 
                              type(ranged_ts))
            else:
                logger.warn('Recomputing area from shape (%s, %s) to %s' % 
                            (rows, cols, str(ranged_ts.shape)))

    # Replace w/ set defaults
    pltkwds.setdefault('legend', False)
    pltkwds.setdefault('linewidth', 3.0)
    pltkwds.setdefault('color', 'black') # If removing, colormap default in _genplot
                                         # Will cause bug

    tunit = pvutils.safe_lookup(ranged_ts, 'full_varunit')

    pltkwds.setdefault('xlabel', tunit)  
    pltkwds.setdefault('ylabel', '$\int$ %s d$\lambda$'%ranged_ts.full_iunit)    
    pltkwds.setdefault('title', 'Area: '+ ranged_ts.name )      


    # If shape is wrong, take transpose    
    if ranged_ts.ndim > 1:
        rows, cols = ranged_ts.shape    
        if cols == 1 and rows != 1:
            out = ranged_ts
        else:
            logger.warn("areaplot() forcing transpose on %s for plotting" 
                        % ranged_ts.name)
            # _df.transpose() causes error now because specunit is being transferred!
            out = ranged_ts.transpose()

    # If series, just pass in directly
    else:
        out = ranged_ts
                    
    # Pass in df.tranpose() as hack until I fix specunit (otherwise it tries to
    # assign specunit to the index, which is a time index (this causes error in new pandas)
    return _genplot(out, **pltkwds)   #ts TRANSPOSE
    
if __name__ == '__main__':
    from skspec.data import aunps_glass
    ts = aunps_glass()
    print ts.full_iunit
    ts.plot(kind='area')
#    areaplot(ts)
    plt.show()
