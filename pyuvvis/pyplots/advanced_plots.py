import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import matplotlib.cm as cm
from matplotlib.collections import PolyCollection
from matplotlib.colors import colorConverter, Normalize

def spec_surface3d(df, kind='contour', elev=0, azim=0, proj_xy=True, proj_zy=True, proj_xz=True,
                   c_iso=10, r_iso=10,*args, **pltkwargs):
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
                              attributes df.index.name and df.column.name will be examined, aftwards, 
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
                

      '''
    xlabel_def='Time'
    ylabel_def='Wavelength'
    zlabel_def='Intensity'
    
    
    
    if not pltkwargs:
        pltkwargs={}
        
    ### If plane (xy) is input backwards (yx), still works    
    proj_xy=pltkwargs.pop('proj_yx', proj_xy)
    proj_zy=pltkwargs.pop('proj_yz', proj_zy)
    proj_xz=pltkwargs.pop('proj_zx', proj_xz)
    
    
    zlabel=pltkwargs.pop('zlabel', zlabel_def)
    
    if pltkwargs.has_key('xlabel'):
        xlabel=pltkwargs.pop('xlabel')
    else:
        ### Get from df.index.name
        try:
            xlabel=df.column.name  #YES THIS IS PRIMARILY COLUMN IN THIS CASE
        ### Get from default value    
        except AttributeError:
            xlabel=xlabel_def
            
        ### Attribute error not tripped if the index.name is None    
        if not xlabel:
            xlabel=xlabel_def  
            
            
    if pltkwargs.has_key('ylabel'):
        ylabel=pltkwargs.pop('ylabel')
    else:
        try:
            ylabel=df.index.name
        ### Get from default value    
        except AttributeError:
            ylabel=ylabel_def

        if not ylabel:
            ylabel=ylabel_def          
                
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
    
    cstride=int(round( len(df.columns)/float(c_iso) ) )
    rstride=int(round( len(df.index)/float(r_iso) )  ) 
    
    ### This occurs if the 
    if cstride==0:
        print "Warning, dataset is too small to accomodate c_iso of %i, setting to 1."%c_iso
        cstride=1
    if rstride==0:
        print "Warning, dataset is too small to accomodate r_iso of %i, setting to 1."%r_iso        
        rstride=1 #to prevent errors
    
    ### If these values are already passed in, they won't be overwritten
    # rstride are equitime lines, cstride is equispectral lines.  Low number, more lines
    _surface_defaults={'alpha':0.2, 'rstride':rstride, 'cstride':cstride, 'color':'pink'} #Don't have any special
    _surface_defaults.update(pltkwargs)
    pltkwargs=_surface_defaults #Need to do this in two steps or it errors

    ax.plot_surface(xx,yy,df, *args, **pltkwargs)   

    if kind=='contourf' or kind=='contour':           
        if kind=='contourf':
            cfunc=ax.contourf
        else:
            cfunc=ax.contour
            
        if proj_xy:
            cset = cfunc(xx, yy, df, zdir='z', offset=zlim[0])   #project z onto xy (zmid to bottom)
    
        if proj_zy:
            cset = cfunc(xx, yy, df, zdir='x', offset=xlim[0]) #project x onto zy (timestart)  (negative half time interval)

        if proj_xz:
            cset = ax.contour(xx, yy, df, zdir='y', offset=ylim[1]) #project y onto xz (ymid to 0)  (negative mid wavelength)

    else:
        raise AttributeError('spec_surface3d attribute "kind" must be\
        contour or contourf.\nYou entered %s'%kind)

    ax.set_xlabel(xlabel)        #x 
    ax.set_ylabel(ylabel)  #Y
    ax.set_zlabel(zlabel)   #data      
    
    ax.view_init(elev, azim) 
    
    return ax


### Add other methods for polyplot?

def spec_poly3d(df):
    ''' Written by evelyn.  Needs touched up with our axis stuff like spec_surface3d.'''

    xs = df.index   
    verts = []
### verts is a sequence of ( verts0, verts1, ...) 
### where verts_i is a sequence of xy tuples of vertices, 
### or an equivalent numpy array of shape (nv, 2).



### Make a sequence of wavelength-intensity(x-z) of shape (n,2) ,n=len(df.index)###
### An easy way converting df to list is  verts=list(df.T.itertuples()), but cannot be applied here
    for item in df.columns:
        ys = df[item]
        verts.append(zip(xs,ys))
    
    fig = plt.figure()
    ax = fig.gca(projection='3d')
       
 ### Convert verts(type:list) to poly(type:mpl_toolkits.mplot3d.art3d.Poly3DCollection)  
 ### poly used in plotting function ax.add_collection3d to do polygon plot    
    cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.6)
    poly = PolyCollection(verts, facecolors = [cc('b'), cc('g'), cc('r'),
                        cc('y'),cc('m'), cc('c'), cc('b'),cc('g'),cc('r'), cc('y')])
    poly.set_alpha(0.7)  
    
 ### zdir is the direction used to plot,here we use time so y axis
    zs=np.array(df.columns)
    ax.add_collection3d(poly, zs=zs, zdir='y')        
    ax.set_xlabel('Wavelength(nm)')
    ax.set_xlim3d(350., 800.)
    ax.set_ylabel('Time(s)')
    ax.set_ylim3d(0, 40)
    ax.set_zlabel('Intensity')
    ax.set_zlim3d(0, 1600)  

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
   