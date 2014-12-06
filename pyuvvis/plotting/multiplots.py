import plot_utils as put
import matplotlib.pyplot as plt
from skspec.core.utilities import split_by
from basic_plots import areaplot, range_timeplot

# Used by SpecStack.plot()
def slice_plot(ts_list, names=[], n=4, *plotargs, **plotkwds):
    """ Pass in a container of timespectra; outputs is subplot for reach. """

    default_names = ['' for i in range(len(ts_list))]
    names = put._parse_names(names, default_names)
    
    figtitle = plotkwds.pop('title', '')

    # CURRENTLY, DOES NOT TAKE AXIS
    fig, axes, plotkwds = put.multi_axes(len(ts_list), **plotkwds)
    
    for (idx, tspec) in enumerate(ts_list):
        tspec.plot(ax=axes[idx], fig=fig, title=names[idx], *plotargs, **plotkwds)
        
    fig.suptitle(figtitle, fontsize=20)        
    return axes
    

def quad_plot(ts, *plotargs, **plotkwds):
    """ Output a matplotlib figure with full spectra, absorbance, area and 
    stripchart.  Figure should be plotly convertable through py.iplot_mpl(fig)
    assuming one is signed in to plotly through py.sign_in(user, apikey).
    
    Parameters
    -----------
    title : str
        Title of the overall figure
        
    striplegend : bool (False)
        Add a legend to the strip chart
        
    colormap : string ('jet')
        Colormap applied to full and absorbance spectra.
        'Jet' is applid to strip chart regardless.
        
    tight_layout: bool (False)
        Calls mpl.fig.tight_layout()
    """

    title = plotkwds.pop('title', '')
    tight_layout = plotkwds.pop('tight_layout', False)
    figsize = plotkwds.pop('figsize', (8,8))


    f, axes = put.splot(2,2, fig=True, figsize=figsize)
    f.suptitle(title, fontsize=20)
    if tight_layout:
        f.tight_layout()
    
    cmap = plotkwds.pop('colormap', 'jet')
    strip_cmap = 'spectral'
    
    striplegend = plotkwds.pop('striplegend', False)
    
    ts.plot(*plotargs, 
             ax=axes[0], 
             title='Spectra', 
             colormap = cmap,
             fig=f, #for colorbar
             **plotkwds)


    range_timeplot(ts.wavelength_slices(8), 
                   ax=axes[1], 
                   legend=False,
                   colormap = strip_cmap,
                   title='Spectral Slices',
                   **plotkwds)    
    
    
    ts.plot(*plotargs,
             norm='r',
            ax=axes[2], 
            colormap=cmap, 
            title='Normalized',
            **plotkwds)


    areaplot(ts, *plotargs,
             ax=axes[3], 
             title='Area', 
             fig=f,
             **plotkwds)

    # Custom legend to strip chart (http://matplotlib.org/users/legend_guide.html#multicolumn-legend)
    if striplegend:
        axes[1].legend(loc='lower center',
                       ncol=4, 
                       fontsize=5, 
#                       mode='expand',
                       bbox_to_anchor=(0.5,-0.1))

 
    for a in (axes[1], axes[3]):
        a.yaxis.tick_right()      
        a.yaxis.set_label_position("right")

    # Remove y-axis of area/stripchart
    put.hide_axis(axes[0], axis='x')
    put.hide_axis(axes[1], axis='x')

    #axes[1].get_yaxis().set_ticklabels([])#set_visible(False)
    #axes[3].get_yaxis().set_ticklabels([])
    #axes[0].get_xaxis().set_ticklabels([])
    #axes[1].get_xaxis().set_ticklabels([])
    
    return f


def six_plot(ts, *plotargs, **plotkwds):
    """ Output a matplotlib figure with full spectra, absorbance, area and 
    stripchart.  Figure should be plotly convertable through py.iplot_mpl(fig)
    assuming one is signed in to plotly through py.sign_in(user, apikey).
    
    Parameters
    -----------
    title : str
        Title of the overall figure
        
    striplegend : bool (False)
        Add a legend to the strip chart
        
    colormap : string ('jet')
        Colormap applied to full and absorbance spectra.
        'Jet' is applid to strip chart regardless.
        
    tight_layout: bool (False)
        Calls mpl.fig.tight_layout()
    """

    title = plotkwds.pop('title', '')
    tight_layout = plotkwds.pop('tight_layout', False)
    figsize = plotkwds.pop('figsize', (10,8))
    
    f, axes = put.splot(3,2, fig=True, figsize=figsize)
    f.suptitle(title, fontsize=20)
    if tight_layout:
        f.tight_layout()
    
    cmap = plotkwds.pop('colormap', 'jet')
    strip_cmap = 'spectral'
    
    striplegend = plotkwds.pop('striplegend', False)
    
    ts.plot(*plotargs, 
             ax=axes[0], 
             title='Spectra', 
             colormap = cmap,
             fig=f, #for colorbar
             **plotkwds)


    range_timeplot(ts.wavelength_slices(8), 
                   ax=axes[1], 
                   legend=False,
                   colormap = strip_cmap,
                   title='Slices (Full)',
                   **plotkwds)    
    
    ts.plot(*plotargs,
            ax=axes[2], 
            colormap=cmap, 
            norm = 'r',
            title='Normalized (r)',
            **plotkwds)

    range_timeplot(ts.as_norm('r').wavelength_slices(8), *plotargs,
             ax=axes[3], 
             legend=False,
             title='Slices (r)',
             fig=f,
             **plotkwds)

    ts.plot(*plotargs,
            ax=axes[4], 
            norm='a',
            colormap=cmap, 
            title='Normalized (a)',
            **plotkwds)

    areaplot(ts, *plotargs,
             ax=axes[5], 
             title='Area', 
             fig=f,
             **plotkwds)

    # Custom legend to strip chars (http://matplotlib.org/users/legend_guide.html#multicolumn-legend)
    if striplegend:
        for ax in [axes[1]]: #axes[5] 
            ax.legend(loc='lower center',
                       ncol=4, 
                       fontsize=5, 
#                       mode='expand',
                       bbox_to_anchor=(0.5,-0.1))

    # Right axes to y-axis
    for a in (axes[1], axes[3], axes[5]):
        a.yaxis.tick_right()      
        a.yaxis.set_label_position("right")

    # Remove x-axis of area/stripchart
    for ax in (axes[0:4]):
        put.hide_axis(ax, axis='x')
    
    return f    
    
if __name__ == '__main__':
    from skspec.data import aunps_water
    import matplotlib.pyplot as plt
    ts = aunps_water()
    six_plot(ts, striplegend=True)
    plt.show()