""" 2d and 3d wrappers for plotting 2d and 3d data in dataframes """
__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"


import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
from mpl_toolkits.mplot3d import Axes3D, art3d #Need Axes3d for 3d projection!
import numpy as np
import matplotlib.colorbar as mplcbar
import matplotlib.cm as cm
from matplotlib.collections import PolyCollection
from matplotlib.colors import colorConverter, Normalize
from basic_plots import PlotError

import plot_utils as pu

from pyuvvis.exceptions import badvalue_error

# Smart float to int conversion
_ir=lambda(x): int(round(x))


# ALL HANDLED BY GENMESH_2D
KINDS2D = ['contour']
KINDS3D = ['scatter3d', 'contour3d', 'wire', 'surf', 'poly'] 


def overload_plot_wireframe(ax, X, Y, Z, *args, **kwargs):
    '''
    Overoad matplotlib's plot_wireframe for a special use-case.  
    In future versions, this may be incorporated into matplotlib natively.
    This would still be required for backwards compatibility.
    '''

    rstride = kwargs.pop("rstride", 1)
    cstride = kwargs.pop("cstride", 1)

    had_data = ax.has_data()
    Z = np.atleast_2d(Z)
    # FIXME: Support masked arrays
    X, Y, Z = np.broadcast_arrays(X, Y, Z)
    rows, cols = Z.shape

    # We want two sets of lines, one running along the "rows" of
    # Z and another set of lines running along the "columns" of Z.
    # This transpose will make it easy to obtain the columns.
    tX, tY, tZ = np.transpose(X), np.transpose(Y), np.transpose(Z)

    if rstride:
        rii = list(xrange(0, rows, rstride))
        # Add the last index only if needed
        if rows > 0 and rii[-1] != (rows - 1) :
            rii += [rows-1]        
    else:
        rii = []

    if cstride:                
        cii = list(xrange(0, cols, cstride))
        if cols > 0 and cii[-1] != (cols - 1) :
            cii += [cols-1]        
    else:
        cii = []

    # If the inputs were empty, then just
    # reset everything.
    if Z.size == 0 :
        rii = []
        cii = []

    xlines = [X[i] for i in rii]
    ylines = [Y[i] for i in rii]
    zlines = [Z[i] for i in rii]

    txlines = [tX[i] for i in cii]
    tylines = [tY[i] for i in cii]
    tzlines = [tZ[i] for i in cii]

    lines = [list(zip(xl, yl, zl)) for xl, yl, zl in \
             zip(xlines, ylines, zlines)]
    lines += [list(zip(xl, yl, zl)) for xl, yl, zl in \
              zip(txlines, tylines, tzlines)]

    linec = art3d.Line3DCollection(lines, *args, **kwargs)
    ax.add_collection(linec)
    ax.auto_scale_xyz(X, Y, Z, had_data)

    return linec

# Rename
def _genmesh(xx, yy, zz, **pltkwargs):
    # UPDATE
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

   c_iso, r_iso: These control how man column and row iso lines will be projected onto the 3d plot.
                    For example, if c_iso=10, then 10 isolines will be plotted as columns, despite the actual length of the
                    columns.  Alternatively, one can pass in c_stride directly, which is a column step size rather than
                    an absolute number, and c_iso will be disregarded.
                    
                
    fill: bool (False)
        Fill between contour lines.

    **pltkwargs: Will be passed directly to plt.contour().
    
    """
             
    # Boilerplate from basic_plots._genplot(); could refactor as decorator
    xlabel = pltkwargs.pop('xlabel', '')
    ylabel = pltkwargs.pop('ylabel', '')
    zlabel = pltkwargs.pop('zlabel', '')    
    title = pltkwargs.pop('title', '')

    # Choose plot kind
    kind = pltkwargs.pop('kind', 'contour')
    grid = pltkwargs.pop('grid', '')
#    pltkwargs.setdefault('legend', False) #(any purpose in 2d?)
#   LEGEND FOR 2D PLOT: http://stackoverflow.com/questions/10490302/how-do-you-create-a-legend-for-a-contour-plot-in-matplotlib
    pltkwargs.setdefault('linewidth', 1)    
    
    cbar = pltkwargs.pop('cbar', False)
    
    fig = pltkwargs.pop('fig', None)
    ax = pltkwargs.pop('ax', None)  
    fill = pltkwargs.pop('fill', False)            

    
    # Different logic than 1d, but I think necessary for sideplots

    if kind in KINDS2D:
        projection = None

        label = pltkwargs.pop('label', None)
        contours = pltkwargs.pop('contours', 6)
        
    elif kind in KINDS3D:
        projection = '3d'

        elev = pltkwargs.pop('elev', 35)
        azim = pltkwargs.pop('azim', -135)        

        c_iso = pltkwargs.pop('c_iso', 10)
        r_iso = pltkwargs.pop('r_iso', 10)

        

        if c_iso == 0:
            cstride = 0
        else:
            cstride = _ir(zz.shape[1]/float(c_iso) ) 
            
        if r_iso == 0:
            rstride = 0
        else:
            rstride = _ir(zz.shape[0]/float(r_iso) )   
    
                        
        pltkwargs.setdefault('cstride', cstride)
        pltkwargs.setdefault('rstride', rstride)

        

    else:
        raise PlotError('Invalid plot kind: "%s".  Choose from %s' % (kind,
                                                    KINDS2D+KINDS3D))

    # Is this the best logic for 2d/3d fig?
    if not ax:
        f = plt.figure()
        ax = f.gca(projection=projection)       
        if not fig:
            fig = f
        

    labelsize = pltkwargs.pop('labelsize', 'medium') #Can also be ints
    titlesize = pltkwargs.pop('titlesize', 'large')
    ticksize = pltkwargs.pop('ticksize', '') #Put in default and remove bool gate
    
    
    # PLT.CONTOUR() doesn't take 'color'; rather, takes 'colors' for now
    if 'color' in pltkwargs:        
        pltkwargs['colors']=pltkwargs.pop('color')
        
    # Convienence method to pass in string colors
    if 'cmap' in pltkwargs and isinstance(pltkwargs['cmap'], basestring):
        pltkwargs['cmap']=pu.cmget(pltkwargs['cmap'])
    
    # Contour Plots    
    # -------------

    if kind == 'contour' or kind == 'contourf':

        # Broken background image
        ### More here http://matplotlib.org/examples/pylab_examples/image_demo3.html ###
        # Refactored with xx, yy instead of df.columns/index UNTESTED
        #if background:
            #xmin, xmax, ymin, ymax = xx.min(), xx.max(), yy.min(), yy.max()
            
            ## Could try rescaling contour rather than image:
            ##http://stackoverflow.com/questions/10850882/pyqt-matplotlib-plot-contour-data-on-top-of-picture-scaling-issue
            #if background==1:
                #im = ax.imshow(zz, interpolation='bilinear', origin='lower',
                            #cmap=cm.gray, extent=(xmin, xmax, ymin, ymax))             
    
        ##### This will take a custom image opened in PIL or it will take plt.imshow() returned from somewhere else
            ##else:
                ##try:
                    ##im = ax.imshow(background) 
                ##### Perhaps image was not correctly opened    
                ##except Exception:
                    ##raise badvalue_error(background, 'integer 1,2 or a PIL-opened image')


        # Note this overwrites the 'contours' variable from an int to array
        if kind == 'contour' or kind == 'contour3d':
            if fill:
                mappable = ax.contourf(xx, yy, zz, contours, **pltkwargs)    #linewidths is a pltkwargs arg
            else:
                mappable = ax.contour(xx, yy, zz, contours, **pltkwargs)    


            ### Pick a few label styles to choose from.
            if label:
                if label==1:
                    ax.clabel(inline=1, fontsize=10)
                elif label==2:
                    ax.clabel(levels[1::2], inline=1, fontsize=10)   #label every second line      
                else:
                    raise PlotError(label, 'integer of value 1 or 2')
 
 
    elif kind == 'surf': 
        mappable = ax.plot_surface(xx, yy, zz, **pltkwargs)
        
    elif kind == 'wire':
        pltkwargs.setdefault('color', 'black')
        mappable = overload_plot_wireframe(ax, xx, yy, zz, **pltkwargs)

    # I THINK THIS IS ALSO A 1D TYPE PLOT!  
    elif kind == 'poly':
        raise NotImplementedError
        ## Convert verts(type:list) to poly(type:mpl_toolkits.mplot3d.art3d.Poly3DCollection)  
        ## poly used in plotting function ax.add_collection3d to do polygon plot    
        #cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.6)
        #verts=[zip(df.index, df[col]) for col in df]  #don't have to say df.columns        
        #poly = PolyCollection((verts), facecolors = [cc('b'), cc('g'), cc('r'),
                            #cc('y'),cc('m'), cc('c'), cc('b'),cc('g'),cc('r'), cc('y')])
        #poly.set_alpha(0.2)  
           
        #### zdir is the direction used to plot,here we use time so y axis
        #ax.add_collection3d(poly, zs=zs, zdir='x')              
 
    if cbar:
        # Do I want colorbar outside of fig?  Wouldn't be better on axes?
        try:
            fig.colorbar(mappable)
        except Exception:
            raise PlotError("Colorbar failed; did you pass a colormap?")
               

    ax.set_xlabel(xlabel, fontsize=labelsize)
    ax.set_ylabel(ylabel, fontsize=labelsize)
    ax.set_title(title, fontsize=titlesize)    

    if grid:
        ax.grid()
        
    # Set elevation/azimuth for 3d plots
    if projection:
        ax.view_init(elev, azim)                 
        ax.set_zlabel(zlabel, fontsize=labelsize, rotation=90) #Rotation doens't work      
        
        
    # NEEDS TO RETURN CONTOURS (Do other plots return anythign?)
    return ax #(ax, mappable)   WHERE MAPPABLE IS CONTOURS 


def add_projection(xx, yy, zz, plane='xz', ax=None, fill=False, flip=False, **contourkwds):
    """ Add a contour plot/projection onto the xy, xz, or yz plane of a 3d
    plot.
    
    xx, yy, zz : 2D Arrays
    
    fill : bool (False)
        Fill in contours (ax.contour vs. ax.contourf).
        
    flip : bool (False)
        The 3d plot is a square of 6 sides.  Flip will change the projeciton
        from the left wall to right wall, or from floor to ceiling in the 
        same plane.
        
    **contourkwds
        Keywords passed directly to ax.contour or ax.contourf.  
    """
    
    plane = plane.lower()

    if plane == 'zx': plane = 'xz'
    if plane == 'zy': plane = 'yz'
    if plane == 'yx': plane = 'xy'
    
    # Is this the best logic for 2d/3d fig?
    if not ax:
        f = plt.figure()
        ax = f.gca(projection='3d')          
    
    # MIGRATE THIS TO ITS OWN METHODS THAT TAKE IN AX
    if fill:
        cfunc=ax.contourf
    else:
        cfunc=ax.contour

    if plane == 'xy':
        offset=zz.min().min()
        if flip:
            offset=zz.max().max()
        zdir = 'z'

      
    elif plane == 'yz':
        offset=xx.min().min()
        if flip:
            offset=xx.max().max()
        zdir = 'x'        


    elif plane == 'xz':
        offset = yy.max().max()
        if flip:
            offset = yy.min().min()
        zdir = 'y'           
    
    else:
        raise PlotError('Invalid plane "%s": must be "xy, xz or yz".' % plane)

    # PLT.CONTOUR() doesn't take 'color'; rather, takes 'colors' for now
    if 'color' in contourkwds:        
        contourkwds['colors']=contourkwds.pop('color')

    cset = cfunc(xx, yy, zz, zdir=zdir, offset=offset, **contourkwds)  
   
    return ax #Return contours?
   
   
def spec3d(xx, yy, zz, projection=True, samples=5, **pltkwargs):
    """ Wireframe plot with no connected clines.  By default, adds an xz 
    projection. 
    
    Notes
    -----
    Mostly a shortcut for a very useful 3d look at data. Thus, did not add
    much customizability as this plot can be assembled from _genmesh2d and
    add_projeciton.
    """

    for invalid in ['c_iso', 'r_iso', 'cstride', 'rstride']:
        if invalid in pltkwargs:
            raise PlotError('Unsupported Keyword %s.'
                            'Please use the samples argument' % invalid)
        
    pltkwargs['kind'] = 'wire'
    pltkwargs['r_iso'] = 0
    pltkwargs['c_iso'] = samples
    pltkwargs.setdefault('linewidth', 2)
    ax = _genmesh(xx, yy, zz, **pltkwargs)
    
    if projection:
        if projection == True:
            projection = 'jet' 

        contourkwds = {}

        # Parse colormap vs. color for projection
        try: 
            contourkwds['cmap'] = pu.cmget(projection)
            contourkwds['alpha'] = 0.3 #     
            
        except AttributeError:
            contourkwds['colors'] = projection
            
        ax = add_projection(xx, yy, zz, ax=ax, fill=True, **contourkwds)
   
    return ax
    
   
def _gencorr2d(xx, yy, zz, a1_label=r'$\bar{A}(\nu_1)$', 
               a2_label=r'$\bar{A}(\nu_2)$', **contourkwds): 
    """ Abstract layout for 2d correlation analysis plot.  
    
    **contourkwds
        Passed directly to _gencontour; includes keywords like xlabel, ylabel
        and so forth.
    """

    # Maybe this should take X, Y, Z not ts

    #fig, ax #how to handle these in general 2d
    # Maybe it's helpful to have args for top plots (ie ax1,2,3)
    
    title = contourkwds.pop('title', '')
    cbar = contourkwds.pop('cbar', False)
    grid = contourkwds.pop('grid', True) #Adds grid to plot and side plots
    cbar_nticks = contourkwds.pop('cbar_nticks', 5) #Number ticks in colorbar
  
    contourkwds.setdefault('contours', 20)        
    contourkwds.setdefault('fill', True)        
    
    
    # This will create a fig
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
    
    ax4, contours = _gencontour(xx, yy, zz, ax=ax4, **contourkwds)
    
 #   plt.colorbar(ax4)  #oesn't work http://matplotlib.org/examples/pylab_examples/contourf_demo.html
    
    # Bisecting line
    ax4.plot(ax4.get_xlim(), 
             ax4.get_ylim(), 
             ls = '--', 
             color='black', 
             linewidth=1)  
    
    # Fig is created by _gen2d in ax4 _gencontour
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


def poly3d(ts, elev=0, azim=0, **pltkwargs):
    """ Written by evelyn, updated by Adam 12/1/12."""
    # Bugs: Facecolors must be exact length of number of columns
    # Requires closing (not a bug, just an issue; polygones need to be)
    #    closed.  Thus, what I really want is fill under a line plot.
    # Maybe want a path instead of poly?

    xlabel = pltkwargs.pop('xlabel', '')
    ylabel = pltkwargs.pop('ylabel', '')
    title = pltkwargs.pop('title', '')
    
    zlabel_def=''         
    zlabel=pltkwargs.pop('zlabel', zlabel_def)   

    # Verts are index dotted with data
    verts = []
    for col in ts.columns:
        values = ts[col]
#        values[0], values[-1] = 0, 0
        verts.append(list(zip(ts.index, values)))
    
    fig = plt.figure()
    ax = fig.gca(projection='3d')
       
 ### Convert verts(type:list) to poly(type:mpl_toolkits.mplot3d.art3d.Poly3DCollection)  
 ### poly used in plotting function ax.add_collection3d to do polygon plot    
    cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.6)

    poly = PolyCollection(verts, 
                          closed=False, # This is where closed should be
                          facecolors = [cc('y'), cc('r'), cc('g')])
    poly.set_alpha(0.2)  
    
    #zdir is the direction used to plot,here we use time so y axis
    ax.add_collection3d(poly, zs=ts.columns, zdir='x' )        
    ax.set_xlabel(xlabel) 
    ax.set_ylabel(ylabel)  #Y
    ax.set_zlabel(zlabel)   #data     
    ax.set_title(title)       

    ax.set_ylim3d(min(ts.index), max(ts.index))
    ax.set_xlim3d(min(ts.columns), max(ts.columns))    #x 
    ax.set_zlim3d(min(ts.min()), max(ts.max()))  #How to get absolute min/max of ts values
    
    ax.view_init(elev, azim) 

    return ax

if __name__ == '__main__':

    from matplotlib import rc
    from pyuvvis.data import aunps_glass, aunps_water, solvent_evap
    
    ts = aunps_glass().as_varunit('s')
    ts=ts.iloc[:, 65:68]
    xx,yy = ts.meshgrid()
    
    #fig = plt.figure(figsize=plt.figaspect(0.5))
    #ax1 = fig.add_subplot(1, 2, 2, projection='3d')
    
    ##---- First subplot
    #ax2 = fig.add_subplot(1, 2, 1, projection='3d')
    #_gencorr2d(xx, yy, ts, 
               #fill=True,
               #title='My baller plot',
               #xlabel=ts.full_varunit,
               #ylabel=ts.full_specunit,
               #contours=20,
               #cbar = True,
               #background=False)
               # Is this the best logic for 2d/3d fig?
               
    
 
 
    #ax2 = _genmesh(xx, yy, ts,
##                kind='contour3d',
                #cmap='autumn_r',
                #kind='wire',
                #cbar=False,
                #alpha=1,
                #linewidth=1,
                #fill=False,
                #c_iso=15,
                #r_iso = 0,
##                contours=9,
##                linewidth=50,
                #xlabel = ts.full_specunit,
                #ylabel = ts.full_varunit,
                #zlabel = ts.full_iunit)    
    
    #ax1 = add_projection(xx, yy, ts, ax=ax2, plane='xz', fill=True, flip=False, alpha=.8, cmap='cool')
    
#    spec3d(xx, yy, ts)
    poly3d(ts,                 xlabel = ts.full_specunit,
                ylabel = ts.full_varunit,
                zlabel = ts.full_iunit)
        
    

    rc('text', usetex=True)    
    
    print ts.shape
    plt.show()
