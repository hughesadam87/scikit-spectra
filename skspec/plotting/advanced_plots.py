""" 2d and 3d wrappers for plotting 2d and 3d data in dataframes """
__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

import datetime

import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
import matplotlib.dates as dates
from mpl_toolkits.mplot3d import Axes3D, axes3d, art3d #Need Axes3d for 3d projection!

import numpy as np
import matplotlib.cm as cm
from matplotlib.collections import PolyCollection
from basic_plots import PlotError
from skspec.core.abcspectra import SpecError

import plot_utils as pu
import skspec.config as pvconfig

from skspec.exceptions import badvalue_error

# Smart float to int conversion
_ir=lambda(x): int(round(x))

from skspec.plotting.basic_plots import range_timeplot, areaplot, _genplot    
from skspec.plotting.plot_registry import PlotRegister

_TIMESTAMPPADDING = 2.9 #Padding for timestamp labels
_TIMESTAMPFORMAT = '%H:%M:%S'

# Colormap of wire plot: hack and only works on a square mesh (eg 100x100)
# https://github.com/matplotlib/matplotlib/issues/3562
def wire_cmap(wires, ax, cmap='hsv'):
    """ Add a colormap to a set of wires (returned form ax.plot_wireframe)"""
    # Retrive data from internal storage of plot_wireframe, then delete it

    if wires._segments3d.ndim != 3:
        raise PlotError('Wireframe colormapping for non-squre data (ie same '
                        'number rows and columns) is not supported.')

    nx, ny, _  = np.shape(wires._segments3d)
               
    wire_x = np.array(wires._segments3d)[:, :, 0].ravel()
    wire_y = np.array(wires._segments3d)[:, :, 1].ravel()
    wire_z = np.array(wires._segments3d)[:, :, 2].ravel()
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
        
    segs = [list(zip(xl, yl, zl)) for xl, yl, zl in \
                     zip(wire_x1.T, wire_y1.T, wire_z1.T)]
    
    # Plots the wireframe by a  a line3DCollection
    new_wires = art3d.Line3DCollection(segs, cmap=cmap)
    new_wires.set_array(scalars)
    ax.add_collection(new_wires)
    return new_wires

def custom_wireframe(ax, X, Y, Z, *args, **kwargs):
    """
    Overoad matplotlib's plot_wireframe for a special use case that we want
    to plot a wireframe over a surface with customizability of those
    lines.
    In future versions, this may be incorporated into matplotlib natively.
    This would still be required for backwards compatibility.
    """

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

    linec = art3d.Line3DCollection(lines, *args, **kwargs)

    ax.add_collection(linec)
    ax.auto_scale_xyz(X, Y, Z, had_data)

    if 'cmap' in kwargs:
        linec = wire_cmap(linec, ax, cmap=kwargs['cmap'])    
    
    return linec


def format_date(x, pos=None):
    return dates.num2date(x).strftime(_TIMESTAMPFORMAT) 


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

    c_mesh, r_mesh: These control how man column and row iso lines will be projected onto the 3d plot.
                    For example, if c_mesh=10, then 10 isolines will be plotted as columns, despite the actual length of the
                    columns.  Alternatively, one can pass in c_stride directly, which is a column step size rather than
                    an absolute number, and c_mesh will be disregarded.
                    
                
    fill: bool (False)
        Fill between contour lines.

    **pltkwargs: Will be passed directly to plt.contour().

    Returns
    -------
    tuple: (Axes, SurfaceFunction)
        Returns axes object and the surface function (e.g. contours for
        contour plot.  Surface for surface plot.
    
    """
    
    # Use a label mapper to allow for datetimes in any plot x/y axis
    _x_dti = _ = _y_dti = False

    # Passed Spectra
    if len(args) == 1:
        ts = args[0]

        try:
            index = np.array([dates.date2num(x) for x in ts.index])
            _x_dti = True
        except AttributeError:
            index = ts.index.values #VALUES NECESSARY FOR POLY CMAP
            
        try:
            cols = np.array([dates.date2num(x) for x in ts.columns])
            _y_dti = True
        except AttributeError:
            cols = ts.columns.values #VALUES NECESSARY FOR POLY CMAP
                
        yy, xx = np.meshgrid(cols, index)

    # Passed xx, yy, ts/zz
    elif len(args) == 3:
        xx, yy, ts = args
        cols, index = ts.columns.values, ts.index.values
        
    else:
        raise PlotError("Please pass a single spectra, or xx, yy, zz.  Got %s args"
                        % len(args))
             
    # Boilerplate from basic_plots._genplot(); could refactor as decorator
    xlabel = pltkwargs.pop('xlabel', '')
    ylabel = pltkwargs.pop('ylabel', '')
    zlabel = pltkwargs.pop('zlabel', '')    
    title = pltkwargs.pop('title', '')

    labelsize = pltkwargs.pop('labelsize', pvconfig.LABELSIZE) #Can also be ints
    titlesize = pltkwargs.pop('titlesize', pvconfig.TITLESIZE)

    # Choose plot kind
    kind = pltkwargs.pop('kind', 'contour')
    grid = pltkwargs.pop('grid', True)
#    pltkwargs.setdefault('legend', False) #(any purpose in 2d?)
#   LEGEND FOR 2D PLOT: http://stackoverflow.com/questions/10490302/how-do-you-create-a-legend-for-a-contour-plot-in-matplotlib
    pltkwargs.setdefault('linewidth', 1)    
    
    cbar = pltkwargs.pop('cbar', False)
    
    outline = pltkwargs.pop('outline', None)
    if outline:
        if kind != 'surf' and kind != 'waterfall':
            raise PlotError('"outline" is only valid for "surf" and "waterfall"'
                        ' plots.  Please use color/cmap for all other color'
                        ' designations.')
    
    fig = pltkwargs.pop('fig', None)
    ax = pltkwargs.pop('ax', None)  
    fill = pltkwargs.pop('fill', pvconfig.FILL_CONTOUR)  
    
    xlim = pltkwargs.pop('xlim', None)
    ylim = pltkwargs.pop('ylim', None)
    zlim = pltkwargs.pop('zlim', None)
    
    #Private attributes
    _modifyax = pltkwargs.pop('_modifyax', True)
    contours = pltkwargs.pop('contours', pvconfig.NUM_CONTOURS)
    label = pltkwargs.pop('label', None)
    
    projection = None
        
    if kind in PLOTPARSER.plots_3d:
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

        if 'mesh' in pltkwargs:
            pltkwargs['c_mesh'] = pltkwargs['r_mesh'] = pltkwargs.pop('mesh')


        # Defaults will be ignored if mesh or ciso in kwargs
        ciso_default = pvconfig.C_MESH
        if len(ts.columns) < ciso_default:
            ciso_default = len(ts.columns)
            
        riso_default = pvconfig.R_MESH  
        if len(ts.index) < riso_default:
            riso_default = len(ts.index)       
        
        
        c_mesh = pltkwargs.pop('c_mesh', ciso_default)
        r_mesh = pltkwargs.pop('r_mesh', riso_default)
        
        if c_mesh > ts.shape[1] or c_mesh < 0:
            raise PlotError('"c_mesh/column mesh" must be between 0 and %s, got "%s"' %
                            (ts.shape[1], c_mesh))

        if r_mesh > ts.shape[0] or r_mesh < 0:
            raise PlotError('"r_mesh/row mesh" must be between 0 and %s, got "%s"' % 
                            (ts.shape[0], r_mesh))
        

        if c_mesh == 0:
            cstride = 0
        else:
            cstride = _ir(ts.shape[1]/float(c_mesh) ) 
            
        if r_mesh == 0:
            rstride = 0
        else:
            rstride = _ir(ts.shape[0]/float(r_mesh) )   
    
                        
        pltkwargs.setdefault('cstride', cstride)
        pltkwargs.setdefault('rstride', rstride)

    elif kind == 'contour':
        pass

    else:
        raise PlotError('_gen2d3d invalid kind: "%s".  '
               'Choose from %s' % (kind, PLOTPARSER.plots_2d_3d))

    # Is this the best logic for 2d/3d fig?
    if not ax:
        f = plt.figure()
#        ax = f.gca(projection=projection)       
        ax = f.add_subplot(111, projection=projection)
        if not fig:
            fig = f
        
    
    
    # PLT.CONTOUR() doesn't take 'color'; rather, takes 'colors' for now
    if 'color' in pltkwargs:       
        if kind == 'contour' or kind == 'contour3d':
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

        # Cornercase datetimeindex and offest from add projection hack
        try:
            pltkwargs['offset'] = dates.date2num(pltkwargs['offset'])
        except Exception:
            pass

        if fill:                           #Values of DTI doesn't work
            mappable = ax.contourf(xx, yy, ts.values, contours, **pltkwargs)    #linewidths is a pltkwargs arg
        else:
            mappable = ax.contour(xx, yy, ts.values, contours, **pltkwargs)    


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

        if outline:
            try:
                pltkwargs['cmap'] = pu.cmget(outline)
            except Exception: #Don't change; attribute error fails when outline=None
                pltkwargs['color'] = outline     
                pltkwargs.pop('cmap') 

        custom_wireframe(ax, xx, yy, ts, **pltkwargs)
        # Wires are thrown out, since mappable is the surface, and only mappable returned

    elif kind == 'wire':
        pltkwargs.setdefault('color', 'black')        
        mappable = custom_wireframe(ax, xx, yy, ts, **pltkwargs)

    elif kind == 'waterfall':
        
        # Parse outline color (if colormap, error!)
        try:
            pu.cmget(outline) 
        except Exception:
            pltkwargs['edgecolors'] = outline
        else:
            raise PlotError('Waterfall "outline" must be a solid color, not colormap.')
        
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
        
        #Delete stride keywords (waterfall doesn't have strides: not a surface!)
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
            mappable.set_array(cols) #If set array in __init__, autogens a cmap!
            mappable.set_cmap(pltkwargs['cmap'])

        mappable.set_alpha(alpha)      
                    
        #zdir is the direction used to plot; dont' fully understand
        ax.add_collection3d(mappable, zs=cols, zdir='x' )      

        # custom limits/labels polygon plot (reverse x,y)
        if not ylim:
            ylim = (max(index), min(index))  #REVERSE AXIS FOR VIEWING PURPOSES

        if not xlim:
            xlim = (min(cols), max(cols))    #x 

        if not zlim:
            zlim = (min(ts.min()), max(ts.max()))  #How to get absolute min/max of ts values
            
        # Reverse labels/DTI call for correct orientaion HACK HACK HACK
        xlabel, ylabel = ylabel, xlabel    
        _x_dti, _y_dti = _y_dti, _x_dti
        azim = -1 * azim

    # General Features
    # ----------------
    
    # Some applications (like add_projection) shouldn't alther axes features
    if not _modifyax:
        return (ax, mappable)

    if cbar:
        # Do I want colorbar outside of fig?  Wouldn't be better on axes?
        try:
            cb = fig.colorbar(mappable, ax=ax)
            # Label colorbar on contour since no 3d-zlabel
            if kind == 'contour':
                cb.set_label(zlabel)
        except Exception:
            raise PlotError("Colorbar failed; did you pass a colormap?")
               
    if grid:
        if grid == True:
            ax.grid()
        else:
            ax.grid(color=grid) #Let's any supported color in     
          

    # Format datetime axis
    # -------------------
    if _x_dti:
        ax.xaxis.set_major_formatter(mplticker.FuncFormatter(format_date))
            
        # Uncomment for custom 3d timestamp orientation
 #       if projection:
 #           for t1 in ax.yaxis.get_ticklabels():
 #               t1.set_ha('right')
 #               t1.set_rotation(30)        
 #           ax.yaxis._axinfo['label']['space_factor'] = _TIMESTAMPPADDING

    if _y_dti:
        ax.yaxis.set_major_formatter(mplticker.FuncFormatter(format_date))

        # Uncomment for custom 3d timestamp orientation
  #      if projection:
  #          for t1 in ax.yaxis.get_ticklabels():
  #              t1.set_ha('right')
  #              t1.set_rotation(30)        
  #          ax.yaxis._axinfo['label']['space_factor'] = _TIMESTAMPPADDING

    if xlim:
        ax.set_xlim3d(xlim)

    if ylim:
        ax.set_ylim3d(ylim)        
     
    if zlim:
        ax.set_zlim3d(zlim)    
                
    # Set elevation/azimuth for 3d plots
    if projection:        
        ax.view_init(elev, azim)                 
        ax.set_zlabel(zlabel, fontsize=labelsize, rotation= _zlabel_rotation)  
    
    ax.set_xlabel(xlabel, fontsize=labelsize)
    ax.set_ylabel(ylabel, fontsize=labelsize)
    ax.set_title(title, fontsize=titlesize) 
        
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
        offset=ts.min().min()
        if flip:
            offset=ts.max().max()
        zdir = 'z'
      
    elif plane == 'yz':
        offset=ts.index.min()
        if flip:
            offset=ts.index.max()
        zdir = 'x'        

    elif plane == 'xz':
        offset = ts.columns.max()
        if flip:
            offset = ts.columns.min()
        zdir = 'y'           
    
    else:
        raise PlotError('Invalid plane "%s": must be "xy, xz or yz".' % plane)
    
          
    ax, cset = _gen2d3d(ts, 
                        zdir=zdir, 
                        kind='contour', 
                        offset=offset, 
                        fill=fill,
                        _modifyax=False,
                        **contourkwds)  
   
    # Return axes only as this is public
    return ax 
   
   
def spec3d(ts, projection=True, fill=True, samples=5, contourkwds={}, **pltkwargs):
    """ Wireframe plot with no connected clines.  By default, adds an xz 
    projection. 
    
    Parameters
    ----------
    projection : color/colormap
        Valid colormap or solid color of contour projection.
        
    samples : int
        Number of samples to take from dataset.  Defaults to 5.  Must
        be within 0 and the number of columns in Spectra.
        
    contourkwds: {}
        Dictionary that holds arguments specific to the projection.
    
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


    for invalid in ['c_mesh', 'r_mesh', 'cstride', 'rstride']:
        if invalid in pltkwargs:
            raise PlotError('Unsupported Keyword %s.'
                            'Please use the samples argument' % invalid)
    #3d Plot
    pltkwargs['kind'] = 'wire'
    pltkwargs['r_mesh'] = 0
    pltkwargs['c_mesh'] = samples
    ax, mappable = _gen2d3d(ts, **pltkwargs)
    
    # Projection
    if 'alpha' not in contourkwds:
        contourkwds['alpha'] = 0.3
        
    if projection:
        if projection == True:
            projection = pvconfig.PROJECTION_CMAP

        ax = add_projection(ts, ax=ax, fill=fill, **contourkwds)
   
    return ax, mappable
    
   
# SET REGISTER HERE!  HAS TO BE HERE BECAUSE GEN2D USES IT, SO GET CIRCULAR IMPORT ISSUES
# IF PUT THIS IN A SEPARATE MODULE.  STRICTLY SPEAKING, GEND2D IS MANY PLOTS SO IT HAS
# TO INSPECT ITS OWN KIND ARGUMENT.  THIS IS ONE HEADACHE OF SUCH A DESIGN PATTERN!
PLOTPARSER = PlotRegister()

#Basic plots
PLOTPARSER.add('spec', _genplot, False, 'Spec vs. Variation' )
PLOTPARSER.add('area', areaplot, False, 'Area vs. Variation' )
PLOTPARSER.add('range_timeplot', range_timeplot, False, 'Slice Ranges vs. Variation' )

#Advanced plots
PLOTPARSER.add('contour', _gen2d3d, False, 'Contour Plot' )
PLOTPARSER.add('contour3d',_gen2d3d, True, '3D Contour Plot')
PLOTPARSER.add('wire', _gen2d3d, True, '3D Wireframe')
PLOTPARSER.add('surf', _gen2d3d, True, '3D Surface' )
PLOTPARSER.add('waterfall', _gen2d3d, True, '3D Waterfall' )
PLOTPARSER.add('spec3d', spec3d, True, '3D Wire + Projection' )

if __name__ == '__main__':

    from matplotlib import rc
    from skspec.data import aunps_glass, aunps_water, solvent_evap
    
    ts = aunps_glass()
#    ts = ts.nearby[400:700]
#    ts = ts.nearby[1520:1320]
#    ts=ts.iloc[450:500, 50:100]
#    xx,yy = ts.meshgrid()
    
    
    print PLOTPARSER
    
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
               
     
    ts = ts.iloc[0:100, :]#.as_varunit('m')

    ts.plot(kind='spec3d', fill=False)    
        
        
        
    ax = ts.plot(
                kind='spec3d',
                cmap = 'hot',
                outline='cool',
    
#                outline='je',
#                outline = 'r',
                
#                cmap='jet',
                cbar=False,
#                c_mesh=5,
#                r_mesh=5,
#                edgecolors='r',
    
#edgecolors='jet',
                linewidth=2,
                alpha=.5,
                contours=5,
                xlabel = ts.full_specunit,
                ylabel = ts.full_varunit,
                zlabel = ts.full_iunit) 
    
    ## Done automatically by spec.plot
#    if ts.index[0] > ts.index[-1]:
#       ax2.set_xlim(ax2.get_xlim()[::-1]) 
    


#    add_projection(ts, ax=ax2, cmap='cool')

    rc('text', usetex=True)    
    
    print ts.shape
    plt.show()
