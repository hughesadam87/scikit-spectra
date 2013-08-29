''' 2d and 3d wrappers for plotting 2d and 3d data in dataframes '''
__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"


import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import matplotlib.cm as cm
from matplotlib.collections import PolyCollection
from matplotlib.colors import colorConverter, Normalize

from plot_utils import smart_label, _df_colormapper, cmget

### USE LOCAL VERSION USE
#import sys
#sys.path.append('../')
#from custom_errors import badvalue_error

from pyuvvis.exceptions import badvalue_error

# Smart float to int conversion
_ir=lambda(x): int(round(x))

def plot2d(df, contours=6, label=None, colorbar=None, background=None, **pltkwds):
    ''' Wrapper for plt.contour that uses np.meshgrid to generate curves.  For convienence, a few special labels, colorbar and background
    keywords have been implemented.  If these are not adequate, it one can add custom colorbars, linelabels background images etc... easily
    just by using respecitve calls to plot (plt.colorbar(), plt.imshow(), plt.clabel() ); my implementations are only for convienences and
    some predefined, cool styles.
    
    df: Dataframe.
    
    countours: Number of desired contours from output.
    
    label: Predefined label types.  For now, only integer values 1,2.  Use plt.clabel to add a custom label.
    
    background: Integers 1,2 will add gray or autumn colormap under contour plot.  Use plt.imgshow() to generate
                custom background, or pass a PIL-opened image (note, proper image scaling not yet implemented).
                
    **pltkwds: Will be passed directly to plt.contour().'''
             
    xlabel, ylabel, title, pltkwds=smart_label(df, pltkwds)

    ### BUG, PLT.CONTOUR() doesn't take 'color'; rather, takes 'colors' for now
    ### This is only for solid colors.  contour takes cmap argument by default.  
    if 'color' in pltkwds:        
        pltkwds['colors']=pltkwds.pop('color')
        
    ### Convienence method to pass in string colors
    if 'cmap' in pltkwds and isinstance(pltkwds['cmap'], basestring):
        pltkwds['cmap']=cmget(pltkwds['cmap'])
    
    ### I CAN MAKE THIS GENERAL TO ANY PLOT, ADDITION OF IMAGES TO A BACKGROUND MAKE IT A GENERAL ROUTINE TO ALL MY PLOTS ###
    ### More here http://matplotlib.org/examples/pylab_examples/image_demo3.html ###
    if background:
        xmin, xmax, ymin, ymax=min(df.columns), max(df.columns), min(df.index), max(df.index)
        if background==1:
            im = plt.imshow(df, interpolation='bilinear', origin='lower',
                        cmap=cm.gray, extent=(xmin, xmax, ymin, ymax))     
            
        elif background==2:
            im = plt.imshow(df, interpolation='bilinear', origin='lower',
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
        
    xx,yy=np.meshgrid(df.columns, df.index)
    ax=plt.contour(xx, yy, df, contours, **pltkwds)    #linewidths is a pltkwds arg
 
    ### Pick a few label styles to choose from.
    if label:
        if label==1:
            ax.clabel(inline=1, fontsize=10)
        elif label==2:
            ax.clabel(levels[1::2], inline=1, fontsize=10)   #label every second line      
        else:
            raise badvalue_error(label, 'integer of value 1 or 2')
        
            
    ### Add colorbar, for some reason need to do plt.colorbar() even though can do ax.clabel...
    if colorbar:
        if colorbar==1:  ### WHAT OTHER COLORBAR OPTIONS ARETHERE
            CB=plt.colorbar(ax, shrink=0.8) #shringk is heigh of colorbar relative ot height of plot
    
            if im:
                IMCB=plt.colorbar(im, orientation='horizontal', shrink=0.8)

                ### Move original colorbar to more natural to make room for image colorbar
                l,b,w,h = plt.gca().get_position().bounds
                ll,bb,ww,hh = CB.ax.get_position().bounds
                CB.ax.set_position([ll, b+0.1*h, ww, h*0.8])
                
        else:
            raise badvalue_error(colorbar, 'integer of value 1 is only supported for now')
                
         

    plt.xlabel(xlabel)      
    plt.ylabel(ylabel)                  
    plt.title(title)
    return ax    

def plot3d(df, kind='contour', elev=0, azim=0, proj_xy=True, proj_zy=True, proj_xz=True,
               contour_color=None, contour_cmap=None, c_iso=10, r_iso=10,*args, **pltkwds):
    ''' Matplotlib Axes3d wrapper for dataframe. Made to handle surface plots, so pure contour plots,
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

      '''
    
    ### Error raised by cfunc() is not very clear so here's an easier one
    if contour_cmap and contour_color:
        raise AttributeError('plot3d can have non-null values for attributes contour_cmap and contour_color, but not both.')

    zlabel_def=''     
    zlabel=pltkwds.pop('zlabel', zlabel_def)                    
    
    xlabel, ylabel, title, pltkwds=smart_label(df, pltkwds)    
        
    ### If plane (xy) is input backwards (yx), still works    
    proj_xy=pltkwds.pop('proj_yx', proj_xy)
    proj_zy=pltkwds.pop('proj_yz', proj_zy)
    proj_xz=pltkwds.pop('proj_zx', proj_xz)
    
                    
    ### Make mesh grid based on dataframe indicies ###
    fig = plt.figure()
    ax = fig.gca(projection='3d')    
    xx,yy=np.meshgrid(df.columns, df.index)

    ### Set axis limits explicitly from padding and data.
    ### PLOT PADDING NEEDS FIXED AS OF NOW IT IS NOT CORRECT.  FOR EXAMPLE, IF MIN IS 0, NEED AN OPERATION
    ### THAT WILL STILL REDUCE IT TO LESS THAN ZERO.  ONLY WORTH FIGURING OUT IF NEED PROJECTIONS OUTSIDE OF THE GRID.
    ### ALSO BUGS IF THE AXIS VALUES AREN'T NUMBERS.  FOR EXAMPLE, IF THEY ARE NAMED COLUMNS.  FIX WITH TRY EXCEPT
    proj_padding=pltkwds.pop('projpad', 0.0)
    
    xlim=pltkwds.pop('xlim', (min(df.columns)*(1.0-proj_padding), max(df.columns)*(1.0+proj_padding)) )
    ylim=pltkwds.pop('ylim', (min(df.index)*(1.0-proj_padding), max(df.index)*(1.0+proj_padding)) )
    
    ### Min/max of total data (only works if the data is 2d)
    zlim=pltkwds.pop('zlim',  ((1.0-proj_padding)*(df.min()).min(), (1.0+proj_padding)*(df.max().max())) )  
    
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
    _surface_defaults={'alpha':0.2, 'rstride':rstride, 'cstride':cstride, 'cmap':cmget('autumn')} #Don't have any special
    _surface_defaults.update(pltkwds)
    pltkwds=_surface_defaults #Need to do this in two steps or it errors

    ax.plot_surface(xx,yy,df, *args, **pltkwds)   

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

def spec_surface3d(df, **pltkwds):
    ''' Wrapper for plot3d, using basic spectral label and view as default parameters.'''

    pltkwds['elev']=pltkwds.pop('elev', 14)
    pltkwds['azim']=pltkwds.pop('azim', -21)
    pltkwds['zlabel']=pltkwds.pop('zlabel', 'Intensity')  #No df attribute, so leave like this    


    pltkwds['ylabel_def']='Wavelength'
    pltkwds['xlabel_def']='Time'
    
    return plot3d(df, **pltkwds)

### Should I just merge spec-surface and spec-poly?  
def spec_poly3d(df, **pltkwds):
    ''' Wrapper for poly, using basic spectral label and view as default parameters.'''
    pltkwds['elev']=pltkwds.pop('elev', 23)
    pltkwds['azim']=pltkwds.pop('azim', 26)
    pltkwds['zlabel']=pltkwds.pop('zlabel', 'Intensity')      
    
    
    pltkwds['ylabel_def']='Wavelength'
    pltkwds['xlabel_def']='Time'    
    return poly3d(df, **pltkwds)


### OTHER MATPLOTLIB 3d PLOT TYPES
def poly3d(df, elev=0, azim=0, **pltkwds):
    ''' Written by evelyn, updated by Adam 12/1/12.'''

    xlabel, ylabel, title, pltkwds=smart_label(df, pltkwds)    

    zlabel_def=''         
    zlabel=pltkwds.pop('zlabel', zlabel_def)   
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
    ''' Mayavi mlab surf plot from a dataframe.  For now, just posting here because it works, not sure
    how necessary it will be.'''
    from mayavi import mlab

    warp_scale=surfargs.pop('warp_scale', 'auto')

    ### So this is how I need to overcome glitches to pass x,y in if they are needed.  If no axis needed,
    ### see below.
    #mlab.surf(np.asarray(list(df.columns)), np.asarray(list(df.index)) , np.asarray(df), warp_scale='auto')

    mlab.surf(np.asarray(df), warp_scale=warp_scale, **surfargs)
    mlab.show()    
   
