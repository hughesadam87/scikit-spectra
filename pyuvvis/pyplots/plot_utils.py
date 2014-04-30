''' Plotting wrappers for dataframes, for implementation in pyuvvis.  Basically calls df.plot()
with some extra bells and whistles like trying to extract column labels and dataframe names,
as well as some exploration into custom labels and color mapping.'''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

from matplotlib.colors import cnames, Normalize
import matplotlib.cm as cm
import numpy as np

### For local use
#import sys
#sys.path.append('../')
#from custom_errors import badvalue_error

from pyuvvis.exceptions import badvalue_error

def cmget(color):
    ''' Return colormap from string (eg 'jet')'''
    try:
        cmap=getattr(cm, color)
    except AttributeError:
        raise badvalue_error(color, 'a custom LInearSegmentedColormap or a string matching \
        the default colormaps available to matplotlib (http://dept.astro.lsa.umich.edu/~msshin/science/code/matplotlib_cm/)') 
    return cmap

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
        vmin=min(df.min(axis=axis))
    if not vmax:        
        vmax=max(df.max(axis=axis))
        
    cNorm=Normalize(vmin=vmin, vmax=vmax)
    scalarmap=cm.ScalarMappable(norm=cNorm, cmap=cmap)              

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
    
def _uvvis_colors(df, delim=':'):
    '''    From a dataframe with indicies of ranged wavelengths (eg 450.0:400.0), and builds colormap
    with fixed uv_vis limits (for now 400, 700).  Here are some builtin ones:
    http://dept.astro.lsa.umich.edu/~msshin/science/code/matplotlib_cm/.  
    
    Colors each curve based on the mid value in range. '''
    colors=[]
    cNorm=Normalize(vmin=350.0, vmax=700.0)
    scalarmap=cm.ScalarMappable(norm=cNorm, cmap=cm.jet)  

    for rng in df.index:
        start,stop=rng.split(delim)
        colors.append(scalarmap.to_rgba(0.5 * (float(stop)+float(start) ) ) )
    return colors

               
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

def smart_label(df, pltkwargs):
    '''Infers title, xlabel and ylabel either from dictionary or dataframe attributes index.name, columns.name
    and df.name.  Used by plotting functions to assign labels and title.  All defaults are set to blank.
    
    Note: xlabel, ylabel, zlabel are popped out of the dictionary, so will be gone upon return.'''
    
    ### If no pltkwards or df attributes found, these are assigned to axis.  Blank probably not necessary,
    ### but wanted to leave this here incase it's ever useful to alter the default label.
    xlabel_def=pltkwargs.pop('xlabel_def', '')
    ylabel_def=pltkwargs.pop('ylabel_def', '')
    zlabel_def=pltkwargs.pop('zlabel_def', '')
    title_def=pltkwargs.pop('title_def', '')        
        
    if 'xlabel' in pltkwargs:
        xlabel=pltkwargs.pop('xlabel')
    else:
        ### Get from df.index.name
        try:
            xlabel=df.columns.name  #YES THIS IS PRIMARILY COLUMN IN THIS CASE
        ### Get from default value    
        except AttributeError:
            xlabel=xlabel_def
            
        ### Attribute error not tripped if the index.name is None    
        if not xlabel:
            xlabel=xlabel_def  
                       
    if 'ylabel' in pltkwargs:
        ylabel=pltkwargs.pop('ylabel')
    else:
        try:
            ylabel=df.index.name
        ### Get from default value    
        except AttributeError:
            ylabel=ylabel_def

        ### Attribute error not tripped if the column.name is None    
        if not ylabel:
            ylabel=ylabel_def          

    if 'title' in pltkwargs:
        title=pltkwargs.pop('title')
    else:
        try:
            title=df.name
        except AttributeError:
            title=title_def
        
       ### Attribute error not tripped if the column.name is None    
        if not title:
            title=title_def             

    return xlabel, ylabel, title, pltkwargs   