from basic_plots import specplot, absplot, areaplot, range_timeplot
from plot_utils import splot, multi_axes
import matplotlib.pyplot as plt
from pyuvvis.core.utilities import sample_by

def slice_plot(ts, n=4, *plotargs, **plotkwds):
    """ """

    ts_list = sample_by(ts, n)
    axes, kwargs = multi_axes(len(ts_list), **plotkwds)

    #if len(axes) < len(ts_list ):
        #logger.warn("MultiCanvas has %s canvas, but only %s axes recieved"
                    #" in show()" % (len(self), len(axes)))
        #upperlim = len(axes)

    #else:
        #upperlim = len(ts_list )
        
    #pcolors = self._request_plotcolors()
    
    for (idx, tspec) in enumerate(ts_list):
        tspec.plot(ax=axes[idx])
        
    return axes
    

def quad_plot(ts, *plotargs, **plotkwds):
    """ Output a matplotlib figure with full spectra, absorbance, area and 
    stripchart.  Figure should be plotly convertable through py.iplot_mpl(fig)
    assuming one is signed in to plotly through py.sign_in(user, apikey).
    
    Parameters
    -----------
    figtitle : str
        Title of the overall figure
        
    striplegend : bool (False)
        Add a legend to the strip chart
        
    color : string ('jet')
        Colormap applied to full and absorbance spectra.
        'Jet' is applid to strip chart regardless.
    """

    figtitle = plotkwds.pop('figtitle', '')
    f, axes = splot(2,2, fig=True, figsize=(8,8))
    f.suptitle(figtitle, fontsize=20)
    
    cmap = plotkwds.pop('color', 'jet')
    
    striplegend = plotkwds.pop('striplegend', False)
    
    specplot(ts, *plotargs, 
             ax=axes[0], 
             title='Spectra', 
             color = cmap,
             **plotkwds)
    
    areaplot(ts, *plotargs,
             ax=axes[1], 
             title='Area', 
             xlabel='seconds', 
             **plotkwds)

    absplot(ts, *plotargs,
            ax=axes[2], 
            color=cmap, 
            title='Absorbance',
            **plotkwds)

    range_timeplot(ts.wavelength_slices(8), 
                   ax=axes[3], 
                   xlabel='seconds',  
                   legend=False,
                   color = 'jet',
                   **plotkwds)

    if striplegend:
        axes[3].legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)

    # Remove y-axis of area/stripchart
    axes[1].get_yaxis().set_visible(False)
    axes[3].get_yaxis().set_visible(False)
    
    return f
        

if __name__ == '__main__':
    from pyuvvis.data import test_spectra
    quad_plot(test_spectra().ix[420.0:700.0], 
              figtitle='Quad Plot Title', 
              striplegend=True)
    plt.show()