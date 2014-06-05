''' Plotting wrappers for dataframes, for implementation in pyuvvis.  See plot_utils
for most of the real work.  Recently updated to work on timespectra and not dataframes.'''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

import plot_utils as put
import logging
import numpy as np
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

class PlotError(Exception):
    """ """

#XXX UPDATE DOCSTRING
def _genplot(ts, xlabel, ylabel, title, **pltkwargs):
    ''' Generic wrapper to ts.plot(), that takes in x/y/title as parsed
    from various calling functions:
    NEW KEYWORDS:
        grid
        color
        labelsize
        titlesize
        ticksize 
    '''
             
    # Add custom legend interface.  Keyword legstyle does custom ones, if pltkwrd legend==True
    # For now this could use improvement  
    pltkwargs.setdefault('legend', False)
    pltkwargs.setdefault('linewidth', 2)
    legstyle = pltkwargs.pop('legstyle', None)   

    fig = pltkwargs.pop('fig', None)
    ax = pltkwargs.pop('ax', None)
    cbar = pltkwargs.pop('cbar', None)
    _barlabels = 5 #Number of ticks/labels in colorbar
    
    if not ax:
        f, ax = plt.subplots(1)
        if not fig:
            fig = f
        
    pltkwargs['ax'] = ax
    
    # Grid (add support for minor grids later)
    grid = pltkwargs.pop('grid', True)
    
    labelsize = pltkwargs.pop('labelsize', 'medium') #Can also be ints
    titlesize = pltkwargs.pop('titlesize', 'large')
    ticksize = pltkwargs.pop('ticksize', '') #Put in default and remove bool gate below
            
    # Make sure don't have "colors" instead of "color"   
    if 'colors' in pltkwargs:
        pltkwargs['color'] = pltkwargs.pop('colors')    
        logger.warn('_genplot(): overwriting kwarg "colors" to "color"')
        
    # Axis = 0, assumes timeplot has passed transposed array for example
    pltcolor = pltkwargs.setdefault('color', put._df_colormapper(ts, 'jet', axis=0) )         
    if isinstance(pltcolor, basestring):
        # Try color mapping; if none found, retain string (eg 'red')
        try:
            put.cmget(pltcolor) #Validate color map
        except AttributeError:
            pass
        else:
            pltkwargs['color'] = put._df_colormapper(ts, pltcolor, axis=0)#put.cmget(pltkwargs['color'])

    # Since df.plot takes ax, multi axes inherently supported.
    ax = ts.plot(**pltkwargs)
    
    if cbar:
        if not fig:
            raise PlotError("Color bar requries access to Figure.  Either pass fig"
                            " keyword or do not pass custom AxesSubplot.")
        mappable, vmin, vmax = put._annotate_mappable(ts, pltcolor, axis=0)
        cbar = fig.colorbar(mappable, ticks=np.linspace(vmin, vmax, _barlabels))
        label_indices = np.linspace(0, len(ts.columns), _barlabels)
        label_indices = [int(round(x)) for x in label_indices]
        if label_indices[-1] > len(ts.columns)-1:
            label_indices[-1] = len(ts.columns)-1 #Rounds over max
        cbar.ax.set_yticklabels([ts.columns[x] for x in label_indices])
        
    # Add minor ticks through tick parameters  
    ax.minorticks_on()
        
    ax.set_xlabel(xlabel, fontsize=labelsize)
    ax.set_ylabel(ylabel, fontsize=labelsize)
    ax.set_title(title, fontsize=titlesize)         
    
    if legstyle and pltkwargs['legend'] == True:  #Defaults to False
        if legstyle == 0:
            ax.legend(loc='upper center', ncol=8, shadow=True, fancybox=True)
        elif legstyle == 1:
            ax.legend(loc='upper left', ncol=2, shadow=True, fancybox=True)  
        elif legstyle == 2:
            ax=put.easy_legend(ax, position='top', fancy=True)
            
    if grid:
        ax.grid(True)
        
    if ticksize:
        logger.info('Adjusting ticksize to "%s"' % ticksize)
        # Get all x and y ticks in a list
        allticks = ax.xaxis.get_majorticklabels()
        allticks.extend(  ax.yaxis.get_majorticklabels() )

        for label in allticks:
            label.set_fontsize(ticksize)
         #  label.set_fontname('courier')        

    return ax    

	
# The following three plots are simply wrappers to genplot.  Up to the user to pass
# the correct dataframes to fill these plots.
def specplot(ts, **pltkwds):
    ''' Basically a call to gen plot with special attributes, and a default color mapper.'''

    pltkwds['linewidth'] = pltkwds.pop('linewidth', 1.0 )    
#    pltkwds['color'] = pltkwds.pop('color', put._df_colormapper(ts, 'jet', axis=0) )         
           
    xlabel = pltkwds.pop('xlabel', ts.full_specunit)  
    ylabel = pltkwds.pop('ylabel', ts.full_iunit+' (Counts)')    
#    title = pltkwds.pop('title', '(%s) %s' % (ts.full_iunit, ts.name) )    
    title=pltkwds.pop('title', ts.name )    

        
    return _genplot(ts, xlabel, ylabel, title, **pltkwds)
    
    
def timeplot(ts, **pltkwds):
    ''' Sends transposed dataframe into _genplot(); however, this is only useful if one wants to plot
    every single row in a dataframe.  For ranges of rows, see spec_utilities.wavelegnth_slices and
    range_timeplot() below.'''
    
    pltkwds['legend']=pltkwds.pop('legend', True) #Turn legend on
        
    xlabel=pltkwds.pop('xlabel', ts.full_timeunit)  
    ylabel=pltkwds.pop('ylabel', ts.full_iunit)    
    title=pltkwds.pop('title', ts.name )    
        
    return _genplot(ts.transpose(), xlabel, ylabel, title, **pltkwds)

# Is this worth having? 
def absplot(ts, default='a', **pltkwds):    
    ''' Absorbance plot.  Note: This will autoconvert data.  This is a convienence method
    but if data is already in absorbance mode, then it's redundant to have this as specplot()
    will produce same plot.'''
    # Make sure ts is absorbance, or readily convertable
    if ts.full_iunit not in ['a', 'a(ln)']:
        ts = ts.as_iunit(default)
                    
    pltkwds.setdefault('linewidth', 1.0)
 
    xlabel = pltkwds.pop('xlabel', ts.full_specunit)  
    ylabel = pltkwds.pop('ylabel', ts.full_iunit)    
    title = pltkwds.pop('title', 'Absorbance: '+ ts.name )    
        
    return _genplot(ts, xlabel, ylabel, title, **pltkwds)

# Requires ranged dataframe used wavelength slices method
def range_timeplot(ranged_ts, **pltkwds):
    ''' Makes plots based on ranged time intervals from spec_utilities.wavelength_slices().
    Uses a special function, put._uvvis_colorss() to map the visible spectrum.  Changes default legend
    behavior to true.'''

    pltkwds['color'] = pltkwds.pop('color', put._uvvis_colors(ranged_ts))
    pltkwds['legend'] = pltkwds.pop('legend', True)
    pltkwds['linewidth'] = pltkwds.pop('linewidth', 3.0 )  
          
    xlabel = pltkwds.pop('xlabel', ranged_ts.full_timeunit)  
    ylabel = pltkwds.pop('ylabel', ranged_ts.full_iunit)    
    title = pltkwds.pop('title', 'Ranged Time Plot: '+ ranged_ts.name )       
                
    # Needs to be more robust and check specunit is index etc...
    return _genplot(ranged_ts.transpose(), xlabel, ylabel, title,**pltkwds)   #ts TRANSPOSE


def areaplot(ranged_ts, **pltkwds):
    """
    Makes plots based on ranged time intervals from spec_utilities.wavelength_slices().
    Uses a special function, put._uvvis_colorss() to map the visible spectrum.  
    Changes default legend behavior to true.
    
    Notes:
    ------
    Added some extra functionality on 2/13/13, to make it ok if user passed in 
    transposed() or non-transposed(). Additionally, if user passes non Mx1
    dimensional plot, it recomputes the area.  Hence, user can just do areaplot(ts)
    """
    
    # If not M x 1 shape, recompute area
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

    xlabel = pltkwds.pop('xlabel', ranged_ts.full_timeunit)  
    ylabel = pltkwds.pop('ylabel', ranged_ts.full_iunit)    
    title = pltkwds.pop('title', 'Area Plot: '+ ranged_ts.name )      


    # If shape is wrong, take transpose    
    rows, cols = ranged_ts.shape    
    if cols == 1 and rows != 1:
        out = ranged_ts
    else:
        logger.warn("areaplot() forcing transpose on %s for plotting" 
                    % ranged_ts.name)
        # _df.transpose() causes error now because specunit is being transferred!
        out = ranged_ts._df.transpose()
                    
    # Pass in df.tranpose() as hack until I fix specunit (otherwise it tries to
    # assign specunit to the index, which is a time index (this causes error in new pandas)
    return _genplot(out, xlabel, ylabel, title, **pltkwds)   #ts TRANSPOSE
    
if __name__ == '__main__':
    from pyuvvis.data import test_spectra
    ts = test_spectra()
#    specplot(ts)
    areaplot(ts)
    plt.show()