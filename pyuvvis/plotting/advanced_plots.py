""" 2d and 3d wrappers for plotting 2d and 3d data in dataframes """
__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"


import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import matplotlib.colorbar as mplcbar
import matplotlib.cm as cm
from matplotlib.collections import PolyCollection
from matplotlib.colors import colorConverter, Normalize
from basic_plots import PlotError

import plot_utils as pu

### USE LOCAL VERSION USE
#import sys
#sys.path.append('../')
#from custom_errors import badvalue_error

from pyuvvis.exceptions import badvalue_error

# Smart float to int conversion
_ir=lambda(x): int(round(x))

def _gen2d(xx, yy, zz, contours=6, label=None, fill=False, colorbar=None, 
           background=None, **pltkwargs):
    """ Abstract layout for 2d plot.
    For convienence, a few special labels, colorbar and background keywords 
    have been implemented.  If these are not adequate, it one can add 
    custom colorbars, linelabels background images etc... easily just by 
    using respecitve calls to plot (plt.colorbar(), plt.imshow(), 
    plt.clabel() ); my implementations are only for convienences and
    some predefined, cool styles.
        
    countours: Number of desired contours from output.
    
    label: Predefined label types.  For now, only integer values 1,2.  Use plt.clabel to add a custom label.
    
    background: Integers 1,2 will add gray or autumn colormap under contour plot.  Use plt.imgshow() to generate
                custom background, or pass a PIL-opened image (note, proper image scaling not yet implemented).
                
    fill: bool (False)
        Fill between contour lines.

    **pltkwargs: Will be passed directly to plt.contour().
    
    """
             
    # Boilerplate from basic_plots._genplot(); could refactor as decorator
    xlabel = pltkwargs.pop('xlabel', '')
    ylabel = pltkwargs.pop('ylabel', '')
    title = pltkwargs.pop('title', '')
    
    pltkwargs.setdefault('legend', False)
    pltkwargs.setdefault('linewidth', 1)    
    cbar = pltkwargs.pop('cbar', False)
    
    fig = pltkwargs.pop('fig', plt.gcf())
    ax = pltkwargs.pop('ax', None)  
    
    # Overwrites fig (desireable?)
    if not ax:
        fig, ax = plt.subplots(1)

    labelsize = pltkwargs.pop('labelsize', 'medium') #Can also be ints
    titlesize = pltkwargs.pop('titlesize', 'large')
    ticksize = pltkwargs.pop('ticksize', '') #Put in default and remove bool gate
    
    
    ### BUG, PLT.CONTOUR() doesn't take 'color'; rather, takes 'colors' for now
    ### This is only for solid colors.  contour takes cmap argument by default.  
    if 'color' in pltkwargs:        
        pltkwargs['colors']=pltkwargs.pop('color')
        
    ### Convienence method to pass in string colors
    if 'cmap' in pltkwargs and isinstance(pltkwargs['cmap'], basestring):
        pltkwargs['cmap']=pu.cmget(pltkwargs['cmap'])
    
    ### I CAN MAKE THIS GENERAL TO ANY PLOT, ADDITION OF IMAGES TO A BACKGROUND MAKE IT A GENERAL ROUTINE TO ALL MY PLOTS ###
    ### More here http://matplotlib.org/examples/pylab_examples/image_demo3.html ###
    # Refactored with xx, yy instead of df.columns/index UNTESTED
    if background:
        xmin, xmax, ymin, ymax = xx.min(), xx.max(), yy.min(), yy.max()
        if background==1:
            im = plt.imshow(zz, interpolation='bilinear', origin='lower',
                        cmap=cm.gray, extent=(xmin, xmax, ymin, ymax))     
            
        elif background==2:
            im = plt.imshow(zz, interpolation='bilinear', origin='lower',
                       cmap=cm.autumn, extent=(xmin, xmax, ymin, ymax))            

    ### This will take a custom image opened in PIL or it will take plt.imshow() returned from somewhere else
        else:
            try:
                im = plt.imshow(background) 
            ### Perhaps image was not correctly opened    
            except Exception:
                raise badvalue_error(background, 'integer 1,2 or a PIL-opened image')
    else:
        im=None
        
    if fill:
        contours = ax.contourf(xx, yy, zz, contours, **pltkwargs)    #linewidths is a pltkwargs arg
    else:
        contours = ax.contour(xx, yy, zz, contours, **pltkwargs)    

    if cbar:
        fig.colorbar(contours)
 
    ### Pick a few label styles to choose from.
    if label:
        if label==1:
            ax.clabel(inline=1, fontsize=10)
        elif label==2:
            ax.clabel(levels[1::2], inline=1, fontsize=10)   #label every second line      
        else:
            raise PlotError(label, 'integer of value 1 or 2')
               
    ax.set_xlabel(xlabel, fontsize=labelsize)
    ax.set_ylabel(ylabel, fontsize=labelsize)
    ax.set_title(title, fontsize=titlesize)         
        
    return (ax, contours)    

# Refactor to be more of a skeleton with xx, yy, zz like in _gen2d
def plot3d(df, kind='contour', elev=0, azim=0, proj_xy=True, proj_zy=True, proj_xz=True,
               contour_color=None, contour_cmap=None, c_iso=10, r_iso=10,*args, **pltkwargs):
    """ Matplotlib Axes3d wrapper for dataframe. Made to handle surface plots, so pure contour plots,
    polygon plots etc... these need their own classes.
    parameters:
     kind
      contour: Based on Axes3d.contour(x,y,z,*args,**kwargs), returns a plot_surface() with
               relevant spectral projections.
      contourf: Filled contour plot based on Axes3D.conourf(x,y,z,*args,**kwargs).  Same a contour
                except contours are filled.
                
    pltwargs can be any Axes3d keywords, with the following extra keywords being germane to this class.
      xlabel, ylabel, zlabel: Axis labels.  Defaults are provided here.  If none are provided, the 
                              attributes df.index.name and df.columns.name will be examined, aftwards, 
                              defaults are used (see below).
                              
      xlim, ylim, zlim:  These can be passed, but if not, the are inferred from the data.  It's smarter
                         to manipulate the df input than to mess with these.  For now, I'm keeping them
                         because they are relevant to proj_padding, but otherwise, probably not too essential.
                              
      proj_padding: Padding percentage if one does not want contour projections right on the wall of the grid.
                    This actually needs fixed.  It is intended to work as in the user says... 1.1 and this means 
                    that the projections should be 10% outside of the axes grid.  0.9 would be 10% in.  
                    The operation to computes the new limit is actually not correct, and if a minimum axis 
                    value is 0, it won't move it beyond.  
                    If this ever becomes useful again, I think it would be wise to first set the x,y,z lims
                    on the plot, then after that, compute the paddings and set the offset to these values.
                    Something like 
                      ax.set(xlim)
                      newxlim=xlim*padding correction
                      contour(offset=newxlim)
                      
      A note on strides: Strides are step sizes.  Say you have 100 curves, then a stride of 5 would give you 20 
                         isolines over your surface.  As such, a smart keyword (c_iso and r_iso) will make sure
                         that a fixed number of contours are drawn when the user passes in a dataframe.  
                        
                        
      c_iso, r_iso:  See above.  These control how man column and row iso lines will be projected onto the 3d plot.
                    For example, if c_iso=10, then 10 isolines will be plotted as columns, despite the actual length of the
                    columns.  Alternatively, one can pass in c_stride directly, which is a column step size rather than
                    an absolute number, and c_iso will be disregarded.
                    
     contour_color/contour_cmap:  
           Either a solid color, or colormap, passed to the contour projections (proj_xy etc...).
           For now, will be passed to all contour projections (xy, zy, xz).

      """
    
    ### Error raised by cfunc() is not very clear so here's an easier one
    if contour_cmap and contour_color:
        raise AttributeError('plot3d can have non-null values for attributes contour_cmap and contour_color, but not both.')

    zlabel_def=''     
    zlabel=pltkwargs.pop('zlabel', zlabel_def)                    
    
    xlabel = pltkwargs.pop('xlabel', '')
    ylabel = pltkwargs.pop('ylabel', '')
    title = pltkwargs.pop('title', '')
    
    ### If plane (xy) is input backwards (yx), still works    
    proj_xy=pltkwargs.pop('proj_yx', proj_xy)
    proj_zy=pltkwargs.pop('proj_yz', proj_zy)
    proj_xz=pltkwargs.pop('proj_zx', proj_xz)
    
                    
    ### Make mesh grid based on dataframe indicies ###
    fig = plt.figure()
    ax = fig.gca(projection='3d')    
    xx,yy=np.meshgrid(df.columns, df.index)

    ### Set axis limits explicitly from padding and data.
    ### PLOT PADDING NEEDS FIXED AS OF NOW IT IS NOT CORRECT.  FOR EXAMPLE, IF MIN IS 0, NEED AN OPERATION
    ### THAT WILL STILL REDUCE IT TO LESS THAN ZERO.  ONLY WORTH FIGURING OUT IF NEED PROJECTIONS OUTSIDE OF THE GRID.
    ### ALSO BUGS IF THE AXIS VALUES AREN'T NUMBERS.  FOR EXAMPLE, IF THEY ARE NAMED COLUMNS.  FIX WITH TRY EXCEPT
    proj_padding=pltkwargs.pop('projpad', 0.0)
    
    xlim=pltkwargs.pop('xlim', (min(df.columns)*(1.0-proj_padding), max(df.columns)*(1.0+proj_padding)) )
    ylim=pltkwargs.pop('ylim', (min(df.index)*(1.0-proj_padding), max(df.index)*(1.0+proj_padding)) )
    
    ### Min/max of total data (only works if the data is 2d)
    zlim=pltkwargs.pop('zlim',  ((1.0-proj_padding)*(df.min()).min(), (1.0+proj_padding)*(df.max().max())) )  
    
    cstride= _ir( len(df.columns)/float(c_iso) ) 
    rstride= _ir( len(df.index)/float(r_iso) )   
    
    ### This occurs if the 
    if cstride==0:
        print "Warning, dataset is too small to accomodate c_iso of %i, setting to 1."%c_iso
        cstride=1
    if rstride==0:
        print "Warning, dataset is too small to accomodate r_iso of %i, setting to 1."%r_iso        
        rstride=1 #to prevent errors
    
    ### If these values are already passed in, they won't be overwritten.  Cmap here is for surface, not countour
    _surface_defaults={'alpha':0.2, 'rstride':rstride, 'cstride':cstride, 'cmap':pu.cmget('autumn')} #Don't have any special
    _surface_defaults.update(pltkwargs)
    pltkwargs=_surface_defaults #Need to do this in two steps or it errors

    ax.plot_surface(xx,yy,df, *args, **pltkwargs)   

    if kind=='contourf' or kind=='contour':           
        if kind=='contourf':
            cfunc=ax.contourf
        else:
            cfunc=ax.contour
            
        if proj_xy:
            cset = cfunc(xx, yy, df, zdir='z', colors=contour_color, cmap=contour_cmap, offset=zlim[0])   #project z onto xy (zmid to bottom)
    
        if proj_zy:
            cset = cfunc(xx, yy, df, zdir='x',colors=contour_color, cmap=contour_cmap, offset=xlim[0]) #project x onto zy (timestart)  (negative half time interval)

        if proj_xz:
            cset = cfunc(xx, yy, df, zdir='y',colors=contour_color, cmap=contour_cmap, offset=ylim[1]) #project y onto xz (ymid to 0)  (negative mid wavelength)

    else:    
        raise badvalue_error(kind, 'contour, contourf')
   
    ax.set_xlabel(xlabel)        #x 
    ax.set_ylabel(ylabel)  #Y
    ax.set_zlabel(zlabel)   #data     
    ax.set_title(title)       
    
    ax.view_init(elev, azim) 
    
    return ax


def spec_surface3d(df, **pltkwargs):
    """ Wrapper for plot3d, using basic spectral label and view as default parameters."""

    pltkwargs['elev']=pltkwargs.pop('elev', 14)
    pltkwargs['azim']=pltkwargs.pop('azim', -21)
    pltkwargs['zlabel']=pltkwargs.pop('zlabel', 'Intensity')  #No df attribute, so leave like this    


    pltkwargs['ylabel_def']='Wavelength'
    pltkwargs['xlabel_def']='Time'
    
    return plot3d(df, **pltkwargs)

### Should I just merge spec-surface and spec-poly?  
def spec_poly3d(df, **pltkwargs):
    """ Wrapper for poly, using basic spectral label and view as default parameters."""
    pltkwargs['elev']=pltkwargs.pop('elev', 23)
    pltkwargs['azim']=pltkwargs.pop('azim', 26)
    pltkwargs['zlabel']=pltkwargs.pop('zlabel', 'Intensity')      
    
    
    pltkwargs['ylabel_def']='Wavelength'
    pltkwargs['xlabel_def']='Time'    
    return poly3d(df, **pltkwargs)


### OTHER MATPLOTLIB 3d PLOT TYPES
def poly3d(df, elev=0, azim=0, **pltkwargs):
    """ Written by evelyn, updated by Adam 12/1/12."""

    xlabel = pltkwargs.pop('xlabel', '')
    ylabel = pltkwargs.pop('ylabel', '')
    title = pltkwargs.pop('title', '')
    
    zlabel_def=''         
    zlabel=pltkwargs.pop('zlabel', zlabel_def)   
    zs=df.columns

    verts=[zip(df.index, df[col]) for col in df]  #don't have to say df.columns
    
    fig = plt.figure()
    ax = fig.gca(projection='3d')
       
 ### Convert verts(type:list) to poly(type:mpl_toolkits.mplot3d.art3d.Poly3DCollection)  
 ### poly used in plotting function ax.add_collection3d to do polygon plot    
    cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.6)
    poly = PolyCollection((verts), facecolors = [cc('b'), cc('g'), cc('r'),
                        cc('y'),cc('m'), cc('c'), cc('b'),cc('g'),cc('r'), cc('y')])
    poly.set_alpha(0.2)  
    
 ### zdir is the direction used to plot,here we use time so y axis
    ax.add_collection3d(poly, zs=zs, zdir='x')        
    ax.set_xlabel(xlabel) 
    ax.set_ylabel(ylabel)  #Y
    ax.set_zlabel(zlabel)   #data     
    ax.set_title(title)       

    ax.set_ylim3d(min(df.index), max(df.index))
    ax.set_xlim3d(min(df.columns), max(df.columns))    #x 
    ax.set_zlim3d(min(df.min()), max(df.max()))  #How to get absolute min/max of df values
    
    ax.view_init(elev, azim) 

    return ax

def surf3d(df, **surfargs):
    """ Mayavi mlab surf plot from a dataframe.  For now, just posting here because it works, not sure
    how necessary it will be."""
    from mayavi import mlab

    warp_scale=surfargs.pop('warp_scale', 'auto')

    ### So this is how I need to overcome glitches to pass x,y in if they are needed.  If no axis needed,
    ### see below.
    #mlab.surf(np.asarray(list(df.columns)), np.asarray(list(df.index)) , np.asarray(df), warp_scale='auto')

    mlab.surf(np.asarray(df), warp_scale=warp_scale, **surfargs)
    mlab.show()    
   
def _gencorr2d(xx, yy, zz, a1_label=r'$\bar{A}(\nu_1)$', 
               a2_label=r'$\bar{A}(\nu_2)$', **contourkwds): 
    """ Abstract layout for 2d correlation analysis plot.  
    
    **contourkwds
        Passed directly to _gen2d; includes keywords like xlabel, ylabel
        and so forth.
    """

    # Maybe this should take X, Y, Z not ts

    #fig, ax #how to handle these in general 2d
    # Maybe it's helpful to have args for top plots (ie ax1,2,3)
    
    title = contourkwds.pop('title', '')
    cbar = contourkwds.pop('cbar', False)
    grid = contourkwds.pop('grid', False) #Adds grid to plot and side plots
    cbar_nticks = contourkwds.pop('cbar_nticks', 5) #Number ticks in colorbar
  
    contourkwds.setdefault('contours', 20)        
    contourkwds.setdefault('fill', True)        
    
    
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
    
    ax4, contours = _gen2d(xx, yy, zz, ax=ax4, **contourkwds)
    
 #   plt.colorbar(ax4)  #oesn't work http://matplotlib.org/examples/pylab_examples/contourf_demo.html
    
    # Bisecting line
    ax4.plot(ax4.get_xlim(), ax4.get_ylim(), ls = '--', color='black', linewidth=1)  
    
    fig = plt.gcf()

    if grid:
        ax2.grid()
        ax3.grid()
        ax4.grid()
        
    # Hide axis labels 
    for ax in [ax2, ax3]:
        if grid:
            pu.hide_axis(ax, axis='both', axislabel=True, ticklabels=True)
        else:
            pu.hide_axis(ax, axis='both', hide_everything = True)
            
    pu.hide_axis(ax1, axis='both', hide_everything=True)
  
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
        cb.update_ticks()


    fig.suptitle(title, fontsize='large') # Still overpads
        
        
    return (ax1, ax2, ax3, ax4)

if __name__ == '__main__':

    from matplotlib import rc
    from pyuvvis.data import aunps_glass
    
    ts = aunps_glass().as_interval('s')
    xx,yy = np.meshgrid(ts.columns, ts.index)

    _gencorr2d(xx, yy, ts, 
               fill=True,
               title='My baller plot',
               xlabel=ts.full_timeunit,
               ylabel=ts.full_specunit,
               contours=20,
               cbar = True,
               background=False)
 
#    _gen2d(xx, yy, ts, cbar=True, fill=True, contours=20)
    
    

    rc('text', usetex=True)    
    print ts.shape
    plt.show()
