""" Plots for correlation analysis. Designed for SPEC2D OBJECTS """

import numpy as np
from skspec.plotting.advanced_plots import _gen2d3d, add_projection
import matplotlib.pyplot as plt
import skspec.plotting.plot_utils as pvutil
import matplotlib.colorbar as mplcbar
import matplotlib.ticker as mplticker
from mpl_toolkits.mplot3d import Axes3D, axes3d, art3d #Need Axes3d for 3d projection!

class CorrPlotError(Exception):
    """ """

def _corr2d4fig(spec, a1_label=r'$\bar{A}(\nu_1)$', 
               a2_label=r'$\bar{A}(\nu_2)$', **contourkwds): 
    """ Abstract layout for 2d correlation analysis plot.  
    
    **contourkwds
        Passed directly to _gencontour; includes keywords like xlabel, ylabel
        and so forth.
    """

    # Maybe this should take X, Y, Z not ts

    #fig, ax #how to handle these in general 2d
    # Maybe it's helpful to have args for top plots (ie ax1,2,3)
    
    title = contourkwds.pop('title', '')
    cbar = contourkwds.pop('cbar', False)
    grid = contourkwds.setdefault('grid', True) #Adds grid to plot and side plots
    
    # REFACTOR THIS
    cbar_nticks = 5
  
    
    # This will create a fig
    ax1 = plt.subplot2grid((5,5), (0,0), colspan=1) # top left
    plt.subplots_adjust(hspace = 0, wspace=0)    # Remove whitespace
    
    ax1.plot([0,-1], color='black')    

    ax1.text(.18, -.78, a1_label, size=12) 
    ax1.text(.55, -.35, a2_label, size=12)    

    ax2 = plt.subplot2grid((5,5), (0,1), colspan=4) # top
    ax3 = plt.subplot2grid((5,5), (1,0), colspan=1, rowspan=4) #left
    ax4 = plt.subplot2grid((5,5), (1, 1), colspan=4, rowspan=4) #main contour
    ax3.invert_xaxis()
    ax4.yaxis.tick_right()
    ax4.xaxis.tick_bottom() #remove top xticks
    ax4.yaxis.set_label_position('right')
    
    ax4, contours = _gen2d3d(spec, ax=ax4, **contourkwds)
        
    # Bisecting line
    pvutil.diag_line(ax4)  
    
    # Fig is created by _gen2d in ax4 _gen2d3d
    fig = plt.gcf()
      
    # Hide axis labels 
    for ax in [ax2, ax3]:
        if grid:
            pvutil.hide_axis(ax, axis='both', axislabel=True, ticklabels=True)
        else:
            pvutil.hide_axis(ax, axis='both', hide_everything = True)
            
    pvutil.hide_axis(ax1, axis='both', hide_everything=True)
  
    #plt.colorbar() doesn't work
    # Handles its own colorbar (See links below; important)
   # http://stackoverflow.com/questions/13784201/matplotlib-2-subplots-1-colorbar
   # http://matplotlib.org/api/colorbar_api.html#matplotlib.colorbar.make_axes
    if cbar:
        if cbar in ['left', 'right', 'top', 'bottom']:
        # if bottom or right, should repad this
            location = cbar
        else:
            location = 'top'
        cax,kw = mplcbar.make_axes([ax1, ax2, ax3, ax4], 
                                   location=location,
                                   pad = 0.05,
                                   aspect = 30, #make skinnier
                                   shrink=0.75) 
        
        cb = fig.colorbar(contours, cax=cax,**kw)# ticks=[0,zz.max().max()], **kw)
        cb.locator = mplticker.MaxNLocator(nbins=cbar_nticks+1) #Cuts off one usually
        cb.set_label(spec.iunit)        
        cb.update_ticks()


    #ax1 will take care of itself in contour
    if grid:
        if grid == True:
            ax2.grid()
            ax3.grid()
  
        else:
            ax2.grid(color=grid)
            ax3.grid(color=grid)

    fig.suptitle(title, fontsize='large') # Still overpads
    return (ax1, ax2, ax3, ax4)



def corr2d(spec, sideplots='mean', **pltkwargs):
    """ Visualize synchronous, asynchronous or phase angle spectra.

    Parameters
    ----------
    
    sideplots: str or bool ('mean')
        If True, sideplots will be put on side axis of cross plots.  Use
        'empty' to return blank sideplots.  mean', 'min', 'max', will 
        plot these respective spectra on the sideplots.


    fill : bool (True)
        Contours are lines, or filled regions.

    **pltkwargs: dict
        Any valid matplotlib contour plot keyword, or skspec general
        plotting keyword (grid, title etc...)

    Returns
    -------

    tuple (matplotlib.Axes)
        If side plots, returns (ax1, ax2, ax3, ax4)
        If not side plots, returns ax4 only

    """
 
    SIDEPAD = 1.10
 
    _reverse_axis = pltkwargs.pop('_reverse_axis', False)

    #Side plot line kwds (passed to Spectrum())
    linekwds = dict(linewidth=1, 
                    linestyle='-', 
                    color='k',  #black
                    custompadding=0,
                    )
       
    if sideplots:
        if sideplots == True:
            sideplots = 'mean'

        # Should be identical, but maybe not when do heterspectral corr...
        try:
            symbol1 = spec.index._unit.symbol
            symbol2 = spec.columns._unit.symbol
        except Exception:
            symbol1 = symbol2 = r'\lambda'
                
        if spec._corr2d.center is not None:
            label1 = r'$\bar{A}(%s_1)$' % symbol1
            label2 = r'$\bar{A}(%s_2)$' % symbol2

        else:
            label1, label2 = r'$A(%s_1)$' % symbol1, r'$A(%s_2)$' % symbol2

        # BASED ON SELF, NOT BASED ON THE OBJECT ITSELF!
        ax1, ax2, ax3, ax4 = _corr2d4fig(spec, label1, label2, **pltkwargs )

        # Side plots    
        data_orig_top = spec._corr2d.spec.loc[spec.index[0]:spec.index[-1], :]
        data_orig_side = spec._corr2d.spec.loc[spec.columns[0]:spec.columns[-1], :]

        top =  None

        if sideplots == 'mean':
            top = data_orig_top.mean(axis=1)
            side = data_orig_side.mean(axis=1)

        elif sideplots == 'max':
            top = data_orig_top.max(axis=1)
            side = data_orig_side.max(axis=1)
            
        elif sideplots == 'min':
            top = data_orig_top.min(axis=1)
            side = data_orig_side.min(axis=1)
            
        elif sideplots == 'all':
            top = data_orig_top
            side = data_orig_side

        elif sideplots == 'empty':
            pass

        else:
            raise CorrPlotError('sideplots keyword must be "mean", "max", "min",'
                         ' "all", or "empty".')

        if top is not None:
            top.plot(ax=ax2, **linekwds)
            side.plot(ax=ax3, **linekwds) 
            for ax in (ax2, ax3):
                pvutil.hide_axis(ax, axis='both')
                ax.set_title('')

        # Reorient ax3
        pvutil.invert_ax(ax3)

        #Set sideplot labels    
        if sideplots != 'empty':
            ax2.set_ylabel(sideplots)
            ax2.yaxis.set_label_position('right')
            
        #Scale x/y padding just a hair 
        y1, y2 = ax2.get_ylim()
        ax2.set_ylim(y1, SIDEPAD*y2)

        x1, x2 = ax3.get_xlim()
        ax3.set_xlim(SIDEPAD*x1, x2)
        
        if _reverse_axis:
            ax4.set_ylim(ax4.get_ylim()[::-1]) 
            ax4.set_xlim(ax4.get_xlim()[::-1]) 
            
            #sideplots
            ax2.set_xlim(ax2.get_xlim()[::-1])
            ax3.set_ylim(ax3.get_ylim()[::-1]) 

        return (ax1, ax2, ax3, ax4)

    else:
        # If no sideplots, can allow for 3d plots
        pltkwargs.setdefault('kind', 'contour')
        ax = pltkwargs.pop('ax', _gen2d3d(spec, **pltkwargs)[0]) #return axes, not contours
        if _reverse_axis:
            ax.set_ylim(ax.get_ylim()[::-1]) 
            ax.set_xlim(ax.get_xlim()[::-1]) 
        return ax

    
def corr3d(spec, projection='xy', **pltkwargs):
    """ pltkwargs are passed to wire plot.  Special keyword 'contourkwargs'
    can pass arguments directly to contour plot.
    """

    contourkwargs = pltkwargs.pop('contourkwargs', {})

    # Like this view better
    pltkwargs.setdefault('elev', 45)
    pltkwargs.setdefault('azim', -135)            
        
    ax = spec.plot(kind='wire', **pltkwargs)    

    # if fill, will will draw over 3d (bug)
    if projection:
        # Pass contourkwargs, not plotkwards
        ax = add_projection(spec, ax=ax, plane=projection, **contourkwargs) 
    
    return ax


# How to mix multiplot:
#http://matplotlib.org/examples/mplot3d/mixed_subplots_demo.html
def corr_multi(corr2d, **pltkwargs):
    """ """
    
    sync = corr2d.sync #Used to look up some span attributes for now
    
    # Boilerplate multiplot

    _title_default = '%s (%s)  scale: %s' \
        % (corr2d.spec.name, sync._var_span, corr2d._scale_string)
    
    title = pltkwargs.pop('title', _title_default)
    grid = pltkwargs.pop('grid', True)
    tight_layout = pltkwargs.pop('tight_layout', False)
    figsize = pltkwargs.pop('figsize', (8,8))

    f, (ax1, ax2, ax3, ax4) = pvutil.splot(2,2, fig=True, figsize=figsize)
    f.suptitle(title) #, fontsize=20)
    if tight_layout:
        f.tight_layout()
        
    if 'cbar' in pltkwargs:
        raise NotImplementedError('Colorbar not supported.')
        
 
    ax1 = corr2d.dyn_spec.plot(ax=ax1,
                           title='Dynamic Spectra',
                           color='k')    


    pltkwargs['sideplots'] = None #Necessary
    pltkwargs['kind'] = 'corr2d'


    ax2 = corr2d.async_codist.plot(ax=ax2,
                                   title='Async. Codistribution ($\Delta$)', 
                                   **pltkwargs)

    ax3 = sync.plot(ax=ax3, 
                           title='Sync. Correlation ($\Phi$)',
                            **pltkwargs)

    ax4 = corr2d.async.plot(ax=ax4,
                            title='Async. Correlation ($\Psi$)',
                            **pltkwargs)


    # Hide axis labels
    for ax in (ax1, ax2, ax3, ax4):
        if grid:
            pvutil.hide_axis(ax, axis='both', axislabel=True, ticklabels=True)
        else:
            pvutil.hide_axis(ax, axis='both', hide_everything = True)    

    # Soft diagonal line
    for ax in (ax2, ax3, ax4):
        pvutil.diag_line(ax)     

    return (ax1, ax2, ax3, ax4)
    