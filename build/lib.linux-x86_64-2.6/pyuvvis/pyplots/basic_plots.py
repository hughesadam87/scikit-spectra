''' Plotting wrappers for dataframes, for implementation in pyuvvis.  See plot_utils
for most of the real work.'''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

from plot_utils import _df_colormapper, _uvvis_colors, easy_legend, smart_label

def _genplot(df, **pltkwargs):
    ''' Generic wrapper to df.plot().    '''
       
    ### Pop xlabel, ylabel, title from direct user keyword argument       
    xlabel, ylabel, title, pltkwargs=smart_label(df, pltkwargs)                       
     
    ### Add custom legend interface.  Keyword legstyle does custom ones, if pltkwrd legend==True
    ### For now this could use improvement  
    pltkwargs['legend']=pltkwargs.pop('legend', False)
    legstyle=pltkwargs.pop('legstyle', None)          
    
    ### Special keyword to remove pre-set defaults from methods that call this one ###
   
        
    ### Make sure don't have "colors", or that 'colors' is not set to default    
    if 'colors' in pltkwargs:
        if pltkwargs['color'].lower()=='default':
            pltkwargs.pop('color')      
    
    if 'colors' in pltkwargs:
        pltkwargs['color']=pltkwargs.pop('colors')    
        print 'Warning: in _genplot, overwriting kwarg "colors" to "color"'
    
    ax=df.plot(**pltkwargs)
        
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)       
        
    if legstyle and pltkwargs['legend']==True:  #Defaults to false
        if legstyle==0:
            ax.legend(loc='upper center', ncol=8, shadow=True, fancybox=True)  #If l
        if legstyle==1:
            ax.legend(loc='upper left', ncol=2, shadow=True, fancybox=True)  #If l
        if legstyle==2:
            ax=easy_legend(ax, position='top', fancy=True)
    return ax    

	
### The following three plots are simply wrappers to genplot.  Up to the user to pass
### the correct dataframes to fill these plots.
def specplot(df, **pltkwds):
    ''' Basically a call to gen plot with special attributes, and a default color mapper.'''
    pltkwds['linewidth']=pltkwds.pop('linewidth', 1.0 )    
           
    pltkwds['ylabel']=pltkwds.pop('ylabel', 'Intensity')
    pltkwds['xlabel']=pltkwds.pop('xlabel', 'Wavelength')
    pltkwds['title']=pltkwds.pop('title', 'Spectral Plot')   
    
    return _genplot(df, **pltkwds)
    
def timeplot(df, **pltkwds):
    ''' Sends transposed dataframe into _genplot(); however, this is only useful if one wants to plot
    every single row in a dataframe.  For ranges of rows, see spec_utilities.wavelegnth_slices and
    range_timeplot() below.'''
    pltkwds['color']=pltkwds.pop('color', _df_colormapper(df, 'jet', axis=1) )         
        
    pltkwds['ylabel']=pltkwds.pop('ylabel', 'Intensity')
    pltkwds['xlabel']=pltkwds.pop('xlabel', 'Time')
    pltkwds['title']=pltkwds.pop('title', 'Temporal Plot')    
    pltkwds['legend']=pltkwds.pop('legend', True) #Turn legend on
    
    return _genplot(df.transpose(),  **pltkwds)

def range_timeplot(df, **pltkwds):
    ''' Makes plots based on ranged time intervals from spec_utilities.wavelength_slices().
    Uses a special function, _uvvis_colorss() to map the visible spectrum.  Changes default legend
    behavior to true.'''

    pltkwds['color']=pltkwds.pop('color', _uvvis_colors(df))
    pltkwds['legend']=pltkwds.pop('legend', True)
    pltkwds['linewidth']=pltkwds.pop('linewidth', 3.0 )  
          
    pltkwds['ylabel']=pltkwds.pop('ylabel', 'Intensity')
    pltkwds['xlabel']=pltkwds.pop('xlabel', 'Time')
    pltkwds['title']=pltkwds.pop('title', 'Ranged Time Plot')   
    pltkwds['legend']=pltkwds.pop('legend', True) #Turn legend on    
            
    return _genplot(df.transpose(), **pltkwds)   #DF TRANSPOSE
 
def absplot(df, **pltkwds):
    pltkwds['ylabel']=pltkwds.pop('ylabel', 'Relative Intensity')
    pltkwds['xlabel']=pltkwds.pop('xlabel', 'Wavelength')
    pltkwds['title']=pltkwds.pop('title', 'Absorbance Plot')   
    
    return _genplot(df, **pltkwds)    
    

    
