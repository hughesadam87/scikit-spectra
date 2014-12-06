''' Plotting wrappers for dataframes, for implementation in skspec.  Basically calls df.plot()
with some extra bells and whistles like trying to extract column labels and dataframe names,
as well as some exploration into custom labels and color mapping.'''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

import numpy as np

import matplotlib.colors as mplcolors
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import skspec.config as cnfg

from skspec.exceptions import badvalue_error

DEFCOLOR = (1.0, 0.0, 0.0)

_rgb_from_string = mplcolors.ColorConverter().to_rgb

class ColorError(Exception):
    """ """

def cmget(color):
    ''' Return colormap from string (eg 'jet')'''
    try:
        cmap=getattr(cm, color)
    except AttributeError:
        raise badvalue_error(color, 'a custom LInearSegmentedColormap or a string matching \
        the default colormaps available to matplotlib (http://dept.astro.lsa.umich.edu/~msshin/science/code/matplotlib_cm/)') 
    return cmap


def diag_line(ax, **linekwds):
    """ Draw a diagonal line x=y"""
    linekwds.setdefault('ls', ':')   #Dotted ... 
    linekwds.setdefault('color', 'k') #black
    linekwds.setdefault('linewidth', 1)

    # Bisecting line
    ax.plot(ax.get_xlim(), 
            ax.get_ylim(), 
            **linekwds)    
    return ax

def multi_axes(count, **kwargs):
    """ """
    figsize = kwargs.pop('figsize', None)#, rcParams['figure.figsize'])
    ncols = kwargs.pop('ncols', cnfg.multicols)

    if count <= ncols:
        nrows = 1
        ncols = count

    else:  
#       ncols = _mod_closest(count)
        nrows = int(count/ncols)         
        if count % ncols: #If not perfect division
            nrows += 1

    if figsize:
        fig, axes = splot(nrows, ncols, figsize=figsize, fig=True)
    else:
        fig, axes = splot(nrows, ncols,fig=True)


    while len(fig.axes) > count:
        fig.delaxes(fig.axes[-1])
    return fig, fig.axes, kwargs



def _parse_names(names, default_names):
    """ Boilerplate: user enters *names to overwrite X default names.  
    For example, if user enters 2 names but 5 unique labels in an image 
    are found, and vice versa."""

    default_names = list(default_names)
    names = list(names)

    # Handle various cases of names/values not being the same
    if names:
        if len(names) == len(default_names):
            pass

        elif len(names) < len(default_names):
            logger.warn("length : %s names provided but %s unique "
                        "labels were found" % (len(names), len(default_names)) )              
            default_names[0:len(names)] = names[:]
            return default_names

        else: #len(names) >= len(default_names)
            logger.warn("length : %s names provided but %s unique "
                        "labels were found" % (len(names), len(default_names)) )     
            return names[0:len(default_names)] 

    else:
        names[:] = default_names[:]

    return names

def _annotate_mappable(df, cmap, axis=0, vmin=None, vmax=None):

    if isinstance(cmap, basestring): 
        cmap=cmget(cmap)

    if axis != 0 and axis != 1:
        raise badvalue_error(axis, 'integers 0 or 1')

    # Min and max values of color map must be min and max of dataframe
    if not vmin:
        vmin=min(df.min(axis=axis))
    if not vmax:        
        vmax=max(df.max(axis=axis))

    cNorm = mplcolors.Normalize(vmin=vmin, vmax=vmax)
    scalarmap = cm.ScalarMappable(norm=cNorm, cmap=cmap)    
#   http://stackoverflow.com/questions/6600579/colorbar-for-matplotlib-plot-surface-command
    scalarmap.set_array(np.arange(0,1)) #Thsi can be anything, arbitrary
    return scalarmap, vmin, vmax


def _df_colormapper(df, cmap, axis=0, colorbymax=False, vmin=None, vmax=None):
    ''' Maps matplotlibcolors to a dataframe based on the mean value of each curve along that
    axis.  

    Parameters
    ----------
    colorbymax : bool (False)
        If true, curves are colored based on their maxima value (ie largest
        curve is max color regardless of where it appears in time). Otherwise,
        curves are colored chornologically.

    Notes
    -----
    Useful for df.plot() which doesn't take a normalized colormap natively. 
    cmap can be an instance of an RGB color map, or a string which such that 
    cm.string will produce one.
    '''

    if isinstance(cmap, basestring): 
        cmap=cmget(cmap)

    if axis != 0 and axis != 1:
        raise badvalue_error(axis, 'integers 0 or 1')

    # Min and max values of color map must be min and max of dataframe
    if not vmin:
        try:
            vmin = min(df.min(axis=axis)) 
        except TypeError: #If df only is one column...
            vmin = df.min(axis=axis)
    if not vmax:   
        try:
            vmax = max(df.max(axis=axis))
        except TypeError:
            vmax = df.max(axis=axis)

    cNorm = mplcolors.Normalize(vmin=vmin, vmax=vmax)
    scalarmap = cm.ScalarMappable(norm=cNorm, cmap=cmap)    

    if axis == 0:
        if colorbymax:
            colors=[scalarmap.to_rgba(df[x].max()) for x in df.columns]
        else:
            colors = [scalarmap.to_rgba(x) for x in 
                      np.linspace(vmin, vmax, len(df.columns))]

    elif axis == 1:
        if colorbymax:
            colors=[scalarmap.to_rgba(df.ix[x].max()) for x in df.index]                
        else:
            colors = [scalarmap.to_rgba(x) for x in 
                      np.linspace(vmin, vmax, len(df.index))]

    return colors

def to_normrgb(color):
    """ Returns an rgb len(3) tuple on range 0.0-1.0 with several input styles; 
        wraps matplotlib.color.ColorConvert.  If None, returns config.PCOLOR by
        default."""

    if color is None:
        color = DEFCOLOR 

    # If iterable, assume 3-channel RGB
    if hasattr(color, '__iter__'):
        if len(color) != 3:
            if len(color) == 4:
                color = color[0:3]
                #   logger.warn("4-channel RGBA recieved; ignoring A channel")
            else:
                raise ColorError("Multi-channel color must be 3-channel;"
                                 " recieved %s" % len(color))
        r, g, b = color
        if r <= 1 and g <= 1 and b <= 1:
            return (r, g, b)

        # Any thing like (0, 255, 30) ... uses 255 as upper limit!
        else:
            r, g, b = map(_pix_norm, (r, g, b) )        
            return (r, g, b)


    if isinstance(color, basestring):
        if color == 'random':
            raise NotImplementedError("random color generation not supported")
#            color = rand_color(style='hex')            
        return _rgb_from_string(color)

    # If single channel --> map accross channels EG 22 --> (22, 22, 22)
    if isinstance(color, int):
        color = float(color)

    if isinstance(color, float):
        if color > 1:
            color = _pix_norm(color)
        return (color, color, color)

    if isinstance(color, bool):
        if color:
            return (1.,1.,1.)
        return (0.,0.,0.)

    raise ColorError(ERRORMESSAGE)        

def _uvvis_colors(df, delim=':'):
    '''    From a dataframe with indicies of ranged wavelengths (eg 450.0:400.0), and builds colormap
    with fixed uv_vis limits (for now 400, 700).  Here are some builtin ones:
    http://dept.astro.lsa.umich.edu/~msshin/science/code/matplotlib_cm/.  

    Colors each curve based on the mid value in range. '''
    colors=[]
    cNorm=mplcolors.Normalize(vmin=350.0, vmax=700.0)
    scalarmap=cm.ScalarMappable(norm=cNorm, cmap=cm.jet)  

    for rng in df.index:
        start,stop=rng.split(delim)
        colors.append(scalarmap.to_rgba(0.5 * (float(stop)+float(start) ) ) )
    return colors


def splot(*args, **kwds):
    """ Wrapper to plt.subplots(r, c).  Will return flattened axes and discard
    figure.  'flatten' keyword will not flatten if the plt.subplots() return
    is not itself flat.  If flatten=False and fig=True, standard plt.subplots
    behavior is recovered."""

    flatten = kwds.pop('flatten', True)
    _return_fig = kwds.pop('fig', False)

    fig, args = plt.subplots(*args, **kwds)

    # Seems like sometimes returns flat, sometimes returns list of lists
    # so either way I flatten    
    if not hasattr(args, '__iter__'):
        args = [args]

    try:
        args = [ax.axes for ax in args] 
    except Exception:
        if flatten:
            args = [ax.axes for row in args for ax in row]
        else:
            args = [tuple(ax.axes for ax in row) for row in args]

    if _return_fig:
        return (fig, args)
    else:
        return args


def hide_axis(ax, axis='x', axislabel=True, ticklabels=True, ticks=False,
              hide_everything=False):
    """ Hide axis features on an axes instance, including axis label, tick
    labels, tick marks themselves and everything.  Careful: hiding the ticks
    will also hide grid lines if a grid is on!

    Parameters
    ----------

    axis : 'x' or 'y' 'both'

    axislabel : True
        Hide the axis label

    ticklabels : True
        Hide the tick labels

    ticks : True
        Hide the tick markers

    hide_everything : False
        Hides labels, tick labels and axis labels.

    """
    if axis not in ['x','y','both']:
        raise AttributeError('axis must be "x" or "y" or both')

    axis_to_modify = []

    if hide_everything:
        ticks = True; axislabel=True; ticklabels=True

    # Set axis labels
    if axis == 'x' or axis == 'both':
        axis_to_modify.append(ax.get_xaxis())

        if axislabel: 
            ax.set_xlabel('')

    if axis == 'y' or axis == 'both': #not elif becuase "both" stipulation
        axis_to_modify.append(ax.get_yaxis())

        if axislabel:
            ax.set_ylabel('')

    for an_axis in axis_to_modify:
        if ticklabels:
            an_axis.set_ticklabels([])
        if ticks:
            an_axis.set_ticks([])

    return ax 


def invert_ax(ax):
    """ Inverts x and y data on a plot axis, and flips limits.  Most useful for
    having an oriented axes in correlation side plots.
    """
    for line in ax.lines:
        xd = line.get_xdata()
        yd = line.get_ydata()
        line.set_xdata(yd)
        line.set_ydata(xd)

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    ylim = (ylim[-1], ylim[0])
    ax.set_xlim(ylim)
    ax.set_ylim(xlim)
    return ax


def easy_legend(ax, fancy=True, position='top', **legendkwds):
    ''' Wrapper around ax.legend to make it easy to move a legend around the edges of the plot.  Made for sensible
    numbers of lines (1-15) and tries to choose smart placement to avoid conflict with lines, labels etc...

    BROKEN!!!

    This is a bust, since plotting legend is easy enough.  See guide, especially with the 'loc'      
    http://matplotlib.org/users/legend_guide.html

    If coming back to this, here are the issues to resolve:
       legend['loc'] must be enabled for the bounding box to work correctly/consistently.
       bbox coordinates are (left edge, bottom edge) of legend.  
         -controlling bottom edge is really dumb because want the top edge to clear the xlabel for example, and bottom
           edge depends on thickness of plot.  Putting the legend on top actually works nicely for this.

       If plotting outside left/right of plot, need to squeeze the plot in afterall, it will not accommadate my legend.
       Had this code, but deleted it.  Basically, need to squeeze left/right width of the axes.bounding width by 20%
       per column of legend.  
       (see second reply here http://stackoverflow.com/questions/4700614/how-to-put-the-legend-out-of-the-plot)


    '''

    ir=lambda x: int(round(x))
    position=position.lower() 
    legendkwds['loc']=3 #MUST BE SET TO SOMETHING, 2 or 3 doesn't matter, or lower left is no longer start point    

    if position not in ['top', 'bottom', 'left', 'right']:
        raise badvalue_error(position, 'top, bottom, left, or right')

    ################################################################
    ### Choose skinny legend for top bottom, long for left/right ###
    ################################################################
    if 'ncol' not in legendkwds:
        if position=='top' or position=='bottom':

            if len(ax.lines) < 4:
                ncol=len(ax.lines)
            else:
                ncol=4           
        else:
            ncol=ir( len(ax.lines)/20.0) #For left right, nice if columns have large vertical extent (10 lines is good)
            if ncol==0:
                ncol=1
        legendkwds['ncol']=ncol

    ###################################################
    ### Choose legend position around plot elements ###
    ###################################################

    box=ax.get_position()   #Can do box.x0 and stuff when resetting ax.set_position()

    if 'bbox_to_anchor' not in legendkwds:  #Don't use has_key(), gone in 3.x

        if position=='top':     
            ''' Legend slightly inside the upper bound of plot'''
            if ax.get_title() == '':
                bbox_to_anchor=(0.2, 1.025)  #0.25 will only center plot if plot is 0.5 units long, then
            else:                             #other end at 0.75.  0.2 looks nice for 8 column uv-vis plot. 
                bbox_to_anchor=(0.2, 1.05)   #Also depends on size of monitor!! so either way, screwed


        elif position=='bottom':
            ''' Centered legend under the label'''

            if ax.get_xlabel()=='':
                bbox_to_anchor=(0.25, -0.025)
            else:
                bbox_to_anchor=(0.25, -0.05)


        elif position=='right':
            ''' Squeeze 20% width inward per column in legend to make room'''
            bbox_to_anchor=(1.05, 0.0) #WHY DOESNT 1,1 work

        elif position=='left':
            ''' Squeeze 20% width inward per column in legend to make room'''
            if ax.get_ylabel()=='':
                bbox_to_anchor=(-0.07, 1.0)   
            else:
                bbox_to_anchor=(-0.12, 1.0)


        legendkwds['bbox_to_anchor']=bbox_to_anchor

    if fancy and 'fancybox' not in legendkwds and 'shadow' not in legendkwds:
        legendkwds['fancybox']=True
        legendkwds['shadow']=True

    if 'borderaxespad' not in legendkwds:
        legendkwds['borderaxespad']=0.0  #Havne't played with this

        ### WHY IS MODE BROKEN (comes up garbled on plot)  
#    if 'mode' not in legendkwds:
    #       legendkwds['mode']='expand'


    ax.legend(**legendkwds)
    return ax