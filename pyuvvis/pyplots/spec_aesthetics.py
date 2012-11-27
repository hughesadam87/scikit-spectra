''' Defines simple/static matplotlib plots.  These are mostly for convienence/aesthetics, like for saving or
for putting into quick scripts.  These only define aesthetics attributes, which can be overwritten.  Actual data
manipulation must be handled separately by some other controller'''

from matplotlib.colors import cnames, Normalize
import matplotlib.cm as cm



### Reminder of dataframe plot attributes from df.plot() definition
#def plot_frame(frame=None, x=None, y=None, subplots=False, sharex=True,
               #sharey=False, use_index=True, figsize=None, grid=False,
               #legend=True, rot=None, ax=None, style=None, title=None, xlim=None,
               #ylim=None, logy=False, xticks=None, yticks=None, kind='line',
               #sort_columns=False, fontsize=None, secondary_y=False, **kwds)
               
def _df_colormapper(df, axis=0, cmap=cm.autumn, style='mean', vmin=None, vmax=None):
    ''' Maps matplotlibcolors to a dataframe based on the mean value of each curve along that
    axis.  '''
    
    
    if axis != 0 and axis != 1:
        raise AttributeError('In _df_colormapper, axis must be 0 or 1')\

    if not vmin:
        vmin=min(df.min(axis=axis))
    if not vmax:
        vmax=max(df.max(axis=axis))
        
    cNorm=Normalize(vmin=vmin, vmax=vmax)
    scalarmap=cm.ScalarMappable(norm=cNorm, cmap=cmap)    
    if axis==0:
        colors=[scalarmap.to_rgba(df[x].mean()) for x in df.columns]
    elif axis==1:
        colors=[scalarmap.to_rgba(df.ix[x].mean()) for x in df.index]        
    return colors
    
def _uvvis_colors(df, delim=':'):
    '''    From a dataframe with indicies of ranged wavelengths (eg 450.0:400.0), and builds colormap
    with fixed uv_vis limits (for now 400, 700).  Here are some builtin ones:
    http://dept.astro.lsa.umich.edu/~msshin/science/code/matplotlib_cm/'''
    colors=[]
    cNorm=Normalize(vmin=350.0, vmax=700.0)
    scalarmap=cm.ScalarMappable(norm=cNorm, cmap=cm.jet)  

    for rng in df.index:
        start,stop=rng.split(delim)
        colors.append(scalarmap.to_rgba(0.5 * (float(stop)+float(start) ) ) )
    return colors

def _genplot(df, title_def, xlabel_def, ylabel_def, **pltkwds):
    ''' Generic wrapper to df.plot().  It operates a heirachy of input of sorts.  The user can
    pass plotkwords that df.plot() would take, (see above) and it will make that first priority.  
    If not found, it will probe the dataframe for special attributes.  For example, df.index.name 
    is reserved for the xlabel.  df.columns.name I usually use for the ylabel.  If these are not found,
    then defaults arguments title_Def, xlabel_def, ylabel_def are used.
    Returns matplotlib AxesSubplot.  '''
    
    
    defaultkwds={'legend':False}#, 'style':cnames.keys()}  #STYLE ERRORS IF 145 CURVES
    
    ### Get xaxis label from direct user keyword argument
    if pltkwds.has_key('xlabel'):  
        xlabel=pltkwds.pop('xlabel') #Should I change to pltkwds.pop('xlabel')
    else:
        ### Get from df.index.name
        try:
            xlabel=df.index.name
        ### Get from default value    
        except AttributeError:
            xlabel=xlabel_def
            
        ### Attribute error not tripped if the index.name is None    
        if xlabel==None:
            xlabel=xlabel_def  
            
            
    if pltkwds.has_key('ylabel'):
        ylabel=pltkwds.pop('ylabel')
    else:
        ylabel=ylabel_def    
        
    ### Get title from user input
    if pltkwds.has_key('title'):
        pass  #this will get passed to DF automaticallyu
    ### Otherwise try to get runname, if none, use default title.
    else:
        try:
            defaultkwds['title']=title_def + ':  '+ df.runname
        except AttributeError:
            defaultkwds['title']=title_def
            
 
    defaultkwds.update(pltkwds)  
    ax=df.plot(**defaultkwds)
        
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    
    return ax    

	
### The following three plots are simply wrappers to genplot.  Up to the user to pass
### the correct dataframes to fill these plots.
def specplot(df, **pltkwds):
    ''' Basically a call to gen plot with special attributes, and a default color mapper.'''
    pltkwds['colors']=pltkwds.pop('colors', _df_colormapper(df, cmap=cm.jet) )   
    pltkwds['linewidth']=pltkwds.pop('linewidth', 1.0 )    
    
    ### TEMPORARY WAY TO REMOVE COLOR BEHAVIOR REMOVE LATER ###
    if pltkwds['colors']==None:
        pltkwds.pop('colors')
    
    return _genplot(df, 'Spectral Plot', 'Wavelength', 'Intensity', **pltkwds)
    
def timeplot(df, **pltkwds):
    ''' Sends transposed dataframe into _genplot(); however, this is only useful if one wants to plot
    every single row in a dataframe.  For ranges of rows, see spec_utilities.wavelegnth_slices and
    range_timeplot() below.'''
    pltkwds['colors']=pltkwds.pop('colors', _df_colormapper(df, axis=1) )       
    
    ### TEMPORARY WAY TO REMOVE COLOR BEHAVIOR REMOVE LATER ###
    if pltkwds['colors']==None:
        pltkwds.pop('colors')    
    
    return _genplot(df.transpose(), 'Temporal Plot', 'Time', 'Intensity', **pltkwds)

def range_timeplot(df, **pltkwds):
    ''' Makes plots based on ranged time intervals from spec_utilities.wavelength_slices().
    Uses a special function, _uvvis_colors() to map the visible spectrum.  Changes default legend
    behavior to true.'''

    pltkwds['colors']=pltkwds.pop('colors', _uvvis_colors(df))
    pltkwds['legend']=pltkwds.pop('legend', True)
    pltkwds['linewidth']=pltkwds.pop('linewidth', 3.0 )    
    
    ### TEMPORARY WAY TO REMOVE COLOR BEHAVIOR REMOVE LATER ###
    if pltkwds['colors']==None:
        pltkwds.pop('colors')    
    
    return _genplot(df.transpose(), 'Temporal Plot', 'Time', 'Intensity', **pltkwds)    

def absplot(df, **pltkwds):
    return _genplot(df, 'Absorbance Plot', 'Wavelength', 'Relative Intensity', **pltkwds)

def area(df, **pltkwds):
    return _genplot(df, 'Area Plot', 'Time', 'Area', **pltkwds)

### Xlabel needs units, especially when time.  Need to pass runname into title.

    
