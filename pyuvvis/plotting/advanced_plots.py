""" 2d and 3d wrappers for plotting 2d and 3d data in dataframes """
__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"


import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
from mpl_toolkits.mplot3d import Axes3D, axes3d, art3d #Need Axes3d for 3d projection!

import numpy as np
import matplotlib.colorbar as mplcbar
import matplotlib.cm as cm
from matplotlib.collections import PolyCollection
from basic_plots import PlotError

import plot_utils as pu

from pyuvvis.exceptions import badvalue_error

# Smart float to int conversion
_ir=lambda(x): int(round(x))


# ALL HANDLED BY GENMESH_2D
KINDS2D = ['contour']
KINDS3D = ['contour3d', 'wire', 'surf', 'waterfall'] 


def wire_cmap(wires, ax, cmap='hsv'):
    """ Add a colormap to a set of wires (returned form ax.plot_wireframe)"""
    # Retrive data from internal storage of plot_wireframe, then delete it
    print wires._segments3d.shape, 'segments shape'
#    nx, ny, _  = np.shape(wires._segments3d)
    


    #try:
        #nx, ny, _  = np.shape(wires._segments3d)
    #except ValueError:
        #raise PlotError("WireCmap only supported for 2d mesh mesh.")

    nx = len(wires._segments3d)
    ny = len(wires._segments3d[0])

    allx = []
    for i in range(nx):
        allx.append(wires._segments3d[i])


    wire_y = np.array([wires._segments3d[i][:,1] for i in range(nx)]).ravel()
    wire_z = np.array([wires._segments3d[i][:,2] for i in range(nx)]).ravel()
                
#    wire_x = np.array(wires._segments3d)[:, :, 0].ravel()
#    wire_y = np.array(wires._segments3d)[:, :, 1].ravel()
#    wire_z = np.array(wires._segments3d)[:, :, 2].ravel()
    wires.remove()
        
    
    # create data for a LineCollection
    wire_x1 = np.vstack([wire_x, np.roll(wire_x, 1)])
    wire_y1 = np.vstack([wire_y, np.roll(wire_y, 1)])
    wire_z1 = np.vstack([wire_z, np.roll(wire_z, 1)])
    to_delete = np.arange(0, nx*ny, ny)
    wire_x1 = np.delete(wire_x1, to_delete, axis=1)
    wire_y1 = np.delete(wire_y1, to_delete, axis=1)
    wire_z1 = np.delete(wire_z1, to_delete, axis=1)
    scalars = np.delete(wire_z, to_delete)
    
    print scalars, 'scalars'
    print wire_x.shape
    
    segs = [list(zip(xl, yl, zl)) for xl, yl, zl in \
                     zip(wire_x1.T, wire_y1.T, wire_z1.T)]
    
    # Plots the wireframe by a  a line3DCollection
    new_wires = art3d.Line3DCollection(segs, cmap=cmap)
    new_wires.set_array(scalars)
    ax.add_collection(new_wires)
    return new_wires

def overload_plot_wireframe(ax, X, Y, Z, *args, **kwargs):
    '''
    Overoad matplotlib's plot_wireframe for a special use-case.  
    In future versions, this may be incorporated into matplotlib natively.
    This would still be required for backwards compatibility.
    '''

    rstride = kwargs.pop("rstride", 1)
    cstride = kwargs.pop("cstride", 1)

    ts = Z

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

    # Row lines from rowstrides
    lines = [list(zip(xl, yl, zl)) for xl, yl, zl in \
             zip(xlines, ylines, zlines)]

    # Col lines form colstrides
    lines += [list(zip(xl, yl, zl)) for xl, yl, zl in \
              zip(txlines, tylines, tzlines)]


    #allzlines = np.concatenate([np.array(zlines).ravel(), 
                                #np.array(tzlines).ravel()])
    #allxlines = np.concatenate([np.array(xlines).ravel(), 
                                #np.array(txlines).ravel()])
    #allylines = np.concatenate([np.array(ylines).ravel(), 
                                #np.array(tylines).ravel()])    

    #ALL = np.concatenate([allzlines, allxlines, allylines])

    #test = np.array(list(ts.columns.values.ravel()) +
                    #list(ts.index.values.ravel().ravel()))

#    kwargs = {} #REMOVE ME HACK
    linec = art3d.Line3DCollection(lines, *args, **kwargs)

    #linec.set_array(test) 
    #linec.set_cmap('jet_r')
    #linec.set_clim(0,2500)


    ax.add_collection(linec)
    ax.auto_scale_xyz(X, Y, Z, had_data)

    return linec

# Rename
def _gen2d3d(*args, **pltkwargs):
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

    Returns
    -------
    tuple: (Axes, SurfaceFunction)
        Returns axes object and the surface function (e.g. contours for
        contour plot.  Surface for surface plot.
    
    """
    
    if len(args) == 1:
        ts = args[0]
        xx, yy = ts.meshgrid()

    elif len(args) == 3:
        xx, yy, ts = args
        
    else:
        raise PlotError("Please pass a single spectra, or xx, yy, zz.  Got %s args" % len(args))
             
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
    
    xlim = pltkwargs.pop('xlim', None)
    ylim = pltkwargs.pop('ylim', None)
    zlim = pltkwargs.pop('zlim', None)
    
    #Private attributes
    _modifyax = pltkwargs.pop('_modifyax', True)
    contours = pltkwargs.pop('contours', 6)
    label = pltkwargs.pop('label', None)
    
    if kind in KINDS2D:
        projection = None

        
    elif kind in KINDS3D:
        projection = '3d'

        elev = pltkwargs.pop('elev', 35)
        azim = pltkwargs.pop('azim', -135)        
        
        view = pltkwargs.pop('view', None)
        if view:
            if view == 1:
                elev, azim = 35, -135
            elif view == 2:
                elev, azim = 35, -45 
            elif view == 3:
                elev, azim = 20, -10  # Side view
            elif view == 4:
                elev, azim = 20, -170
            elif view == 5:
                elev, azim = 0,-90          
            elif view == 6:
                elev, azim = 65, -90
            else:
                raise PlotError('View must be between 1 and 6; otherwise set'
                                ' "elev" and "azim" keywords.')

        # Orientation of zlabel (doesn't work...)
        _zlabel_rotation = 0.0
        if azim < 0:
            _zlabel_rotation = 90.0

        c_iso = pltkwargs.pop('c_iso', 10)
        r_iso = pltkwargs.pop('r_iso', 10)
        
        if c_iso > ts.shape[1] or c_iso < 0:
            raise PlotError('"c_iso" must be between 0 and %s, got "%s"' %
                            (ts.shape[1], c_iso))

        if r_iso > ts.shape[0] or r_iso < 0:
            raise PlotError('"r_iso" must be between 0 and %s, got "%s"' % 
                            (ts.shape[0], r_iso))
        

        if c_iso == 0:
            cstride = 0
        else:
            cstride = _ir(ts.shape[1]/float(c_iso) ) 
            
        if r_iso == 0:
            rstride = 0
        else:
            rstride = _ir(ts.shape[0]/float(r_iso) )   
    
                        
        pltkwargs.setdefault('cstride', cstride)
        pltkwargs.setdefault('rstride', rstride)

    else:
        raise PlotError('Invalid plot kind: "%s".  '
               'Choose from %s' % (kind, KINDS2D+KINDS3D))

    # Is this the best logic for 2d/3d fig?
    if not ax:
        f = plt.figure()
#        ax = f.gca(projection=projection)       
        ax = f.add_subplot(111, projection=projection)
        if not fig:
            fig = f
        

    labelsize = pltkwargs.pop('labelsize', 'medium') #Can also be ints
    titlesize = pltkwargs.pop('titlesize', 'large')
    ticksize = pltkwargs.pop('ticksize', '') #Put in default and remove bool gate
    
    
    # PLT.CONTOUR() doesn't take 'color'; rather, takes 'colors' for now
    if 'color' in pltkwargs:       
        if kind == 'contour':
            pltkwargs['colors'] = pltkwargs.pop('color')
        
    # Convienence method to pass in string colors
    if 'colormap' in pltkwargs:
        pltkwargs['cmap'] = pltkwargs.pop('colormap')

    if 'cmap' in pltkwargs:
        if isinstance(pltkwargs['cmap'], basestring):
            pltkwargs['cmap'] = pu.cmget(pltkwargs['cmap'])
    
    # Contour Plots    
    # -------------

        # Broken background image
        ### More here http://matplotlib.org/examples/pylab_examples/image_demo3.html ###
        # Refactored with xx, yy instead of df.columns/index UNTESTED
        #if background:
            #xmin, xmax, ymin, ymax = xx.min(), xx.max(), yy.min(), yy.max()
            
            ## Could try rescaling contour rather than image:
            ##http://stackoverflow.com/questions/10850882/pyqt-matplotlib-plot-contour-data-on-top-of-picture-scaling-issue
            #if background==1:
                #im = ax.imshow(ts, interpolation='bilinear', origin='lower',
                            #cmap=cm.gray, extent=(xmin, xmax, ymin, ymax))             
    
        #### This will take a custom image opened in PIL or it will take plt.imshow() returned from somewhere else
            #else:
                #try:
                    #im = ax.imshow(background) 
                #### Perhaps image was not correctly opened    
                #except Exception:
                    #raise badvalue_error(background, 'integer 1,2 or a PIL-opened image')


    # Note this overwrites the 'contours' variable from an int to array
    if kind == 'contour' or kind == 'contour3d':
        if fill:
            mappable = ax.contourf(xx, yy, ts, contours, **pltkwargs)    #linewidths is a pltkwargs arg
        else:
            mappable = ax.contour(xx, yy, ts, contours, **pltkwargs)    


        ### Pick a few label styles to choose from.
        if label:
            if label==1:
                ax.clabel(inline=1, fontsize=10)
            elif label==2:
                ax.clabel(levels[1::2], inline=1, fontsize=10)   #label every second line      
            else:
                raise PlotError(label, 'integer of value 1 or 2')

 
    elif kind == 'surf': 
        mappable = ax.plot_surface(xx, yy, ts, **pltkwargs)
#        pltkwargs.pop('edgecolors')
        wires = overload_plot_wireframe(ax, xx, yy, ts, **pltkwargs)
#        print np.shape(wires._segments3d)
        wires = wire_cmap(wires, ax, cmap='jet')
        
    elif kind == 'wire':
        pltkwargs.setdefault('color', 'black')
        mappable = overload_plot_wireframe(ax, xx, yy, ts, **pltkwargs)

    elif kind == 'waterfall':
        
        edgecolors = pltkwargs.setdefault('edgecolors', None)
        pltkwargs.setdefault('closed', False)
        alpha = pltkwargs.setdefault('alpha', None)

        # Need to handle cmap/colors a bit differently for PolyCollection API
        if 'color' in pltkwargs:
            pltkwargs['facecolors']=pltkwargs.pop('color')
        cmap = pltkwargs.setdefault('cmap', None)
        
        if alpha is None: #as opposed to 0
            alpha = 0.6 * (13.0/ts.shape[1])
            if alpha > 0.6:
                alpha = 0.6        
        
        #Delete stride keywords
        for key in ['cstride', 'rstride']:
            try:
                del pltkwargs[key]
            except KeyError:
                pass
        
        # Verts are index dotted with data
        verts = []
        for col in ts.columns:  
            values = ts[col]
            values[0], values[-1] = values.min().min(), values.min().min()
            verts.append(list(zip(ts.index, values)))
    
        mappable = PolyCollection(verts, **pltkwargs)
        
        if cmap:
            mappable.set_array(ts.columns.values), #If set array in __init__, autogens a cmap!
            mappable.set_cmap(pltkwargs['cmap'])

        mappable.set_alpha(alpha)      
                    
        #zdir is the direction used to plot; dont' fully understand
        ax.add_collection3d(mappable, zs=ts.columns, zdir='x' )      

        # custom limits/labels polygon plot (reverse x,y)
        if not ylim:
            ylim = (max(ts.index), min(ts.index))  #REVERSE AXIS FOR VIEWING PURPOSES

        if not xlim:
            xlim = (min(ts.columns), max(ts.columns))    #x 

        if not zlim:
            zlim = (min(ts.min()), max(ts.max()))  #How to get absolute min/max of ts values
            
        xlabel, ylabel = ylabel, xlabel        

    # General Features
    # ----------------
    
    # Some applications (like add_projection) shouldn't alther axes features
    if not _modifyax:
        return (ax, mappable)

    if cbar:
        # Do I want colorbar outside of fig?  Wouldn't be better on axes?
        try:
            fig.colorbar(mappable, ax=ax)
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
        ax.set_zlabel(zlabel, fontsize=labelsize, rotation= _zlabel_rotation)     
    
    if xlim:
        ax.set_xlim3d(xlim)

    if ylim:
        ax.set_ylim3d(ylim)        
     
    if zlim:
        ax.set_zlim3d(zlim)    
                
        
    # Return Ax, contours/surface/polygons etc...
    return (ax, mappable)  


# Support images or any other 2d plot besides contours?
def add_projection(ts, plane='xz', flip=False, fill=False, **contourkwds):
    """ Add a contour plot/projection onto the xy, xz, or yz plane of a 3d
    plot.
    
    args: 2D Arrays or Contour Set
        xx, yy, zz : 2D mesh arrays, or contour set.
    
        
    plane: str ('xz')
        'xz', 'yz', 'xy', choose the plane on which to project the contours.
        
    flip : bool (False)
        The 3d plot is a square of 6 sides.  Flip will change the projeciton
        from the left wall to right wall, or from floor to ceiling in the 
        same plane.
        
    fill : bool (False)
        Fill the contours

    **contourkwds
        Keywords passed directly to ax.contour.  

    Returns
    -------
    tuple: Axes
        Returns axes object.
    """
                
    plane = plane.lower()

    if plane == 'zx': plane = 'xz'
    if plane == 'zy': plane = 'yz'
    if plane == 'yx': plane = 'xy'
    
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

    ax, cset = _gen2d3d(ts, 
                        zdir=zdir, 
                        kind='contour', 
                        offset=offset, 
                        _modifyax=False,
                        **contourkwds)  
   
    # Return axes only as this is public
    return ax 
   
   
def spec3d(ts, projection=True, samples=5, **pltkwargs):
    """ Wireframe plot with no connected clines.  By default, adds an xz 
    projection. 
    
    Parameters
    ----------
    projection : color/colormap
        Valid colormap or solid color of contour projection.
        
    samples : int
        Number of samples to take from dataset.  Defaults to 5.  Must
        be within 0 and the number of columns in Spectra.
    
    Returns
    -------
    tuple: (Axes, SurfaceFunction)
        Returns axes object and the surface function (e.g. contours for
        contour plot.  Surface for surface plot.)
    
    Notes
    -----
    Mostly a shortcut for a very useful 3d look at data. Thus, did not add
    much customizability as this plot can be assembled from _gen2d3d2d and
    add_projeciton.
    """

    for invalid in ['c_iso', 'r_iso', 'cstride', 'rstride']:
        if invalid in pltkwargs:
            raise PlotError('Unsupported Keyword %s.'
                            'Please use the samples argument' % invalid)
        
    pltkwargs['kind'] = 'wire'
    pltkwargs['r_iso'] = 0
    pltkwargs['c_iso'] = samples
    ax, mappable = _gen2d3d(ts, **pltkwargs)
    
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
            
        ax = add_projection(ts, ax=ax, fill=True, **contourkwds)
   
    return ax, mappable
    
   
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
    
    ax4, contours = _gen2d3d(xx, yy, zz, ax=ax4, **contourkwds)
    
 #   plt.colorbar(ax4)  #oesn't work http://matplotlib.org/examples/pylab_examples/contourf_demo.html
    
    # Bisecting line
    ax4.plot(ax4.get_xlim(), 
             ax4.get_ylim(), 
             ls = '--', 
             color='black', 
             linewidth=1)  
    
    # Fig is created by _gen2d in ax4 _gen2d3d
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
    from pyuvvis.data import aunps_glass, aunps_water, solvent_evap
    
    ts = solvent_evap().as_varunit('m')#.as_iunit('a')
#    ts = ts.nearby[400:700]
#    ts = ts.nearby[1520:1320]
#    ts=ts.iloc[450:500, 50:100]
    xx,yy = ts.meshgrid()
    
    
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
               
    
 
 
    ax2, contours = _gen2d3d(ts,
                kind='contour',
#                cmap='jet_r',
#                edgecolors='jet',
                linewidth=2,
                alpha=.1,
                fill=False,
#                cbar=True,
#                c_iso=20,
#                r_iso=20,
#                contours=9,
#                linewidth=50,
                xlabel = ts.full_specunit,
                ylabel = ts.full_varunit,
                zlabel = ts.full_iunit) 
    if ts.index[0] > ts.index[-1]:
       ax2.set_xlim(ax2.get_xlim()[::-1]) 
    

    add_projection(ts, ax=ax2, cmap='cool')

    rc('text', usetex=True)    
    
    print ts.shape
    plt.show()
