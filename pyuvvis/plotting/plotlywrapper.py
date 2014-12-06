# skspec intefrace to plotly:
# http://nbviewer.ipython.org/github/plotly/python-user-guide/blob/master/s00_homepage/s00_homepage.ipyn

import plotly.graph_objs as grobs
import numpy as np
import plot_utils as put

def make_linetrace(x, y, **tracekwargs):#, linecolor):  
    """Trace-generating function (returns a Scatter object) from timespectra"""
    # good example of trace options http://plot.ly/python/bubblecharts
    
    name = tracekwargs.pop('name', '')
    tracekwargs.setdefault('color', 'rgb(255,0,0)') #markercolor
    #tracekwargs.setdefault('opacity', 1.0) 
    #tracekwargs.setdefault('width', 1.0) 
        
    return grobs.Scatter(x=x,
                         y=y,          
                         mode='lines',          
                         name=name,          
                         marker= grobs.Line(**tracekwargs) 
                         )


def make_pointtrace(x, y, **tracekwargs):  
    """Trace-generating function (returns a Scatter object) from timespectra"""
    # good example of trace options http://plot.ly/python/bubblecharts
    
    name = tracekwargs.pop('name', '')    
    tracekwargs.setdefault('color', 'rgb(255,0,0)') #markercolor
    tracekwargs.setdefault('symbol', 'circle')
    #tracekwargs.setdefault('opacity', 1.0)
    tracekwargs.setdefault('size', 10)


    return grobs.Scatter(x=x,
                         y=y,
                         mode='markers',
                         marker=grobs.Marker(**tracekwargs)
                         )


def _parsenull(value):
    """ 1.0.22 plotly will error if gets axis titles of None (turns into null)
    in the json.  Therefore, this replaced values of None with an empty string.
    This may be fixed in later version of plotly."""
    if not value:
        value = ''
    return value


def layout(ts, *args, **kwargs):
    """ Make a plotly layout from timespectra attributes """    
    
    kwargs.setdefault('title', _parsenull(ts.name))
    kwargs.setdefault('plot_bgcolor', '#EFECEA') #gray
    kwargs.setdefault('showlegend', False)

    # Map x,y title into grobs.XAxis and grobs.YAxis
    xtitle = _parsenull(kwargs.pop('xtitle', ts.specunit))
    ytitle = _parsenull(kwargs.pop('ytitle', ts.iunit))    

   
    kwargs['xaxis'] = grobs.XAxis(title=xtitle)
    kwargs['yaxis'] = grobs.YAxis(title=ytitle)
    
    layout = grobs.Layout(**kwargs)

    axis_style = dict(zeroline=False,       # remove thick zero line
                     gridcolor='#FFFFFF',  # white grid lines
                     ticks='outside',      # draw ticks outside axes 
                     ticklen=8,            # tick length
                     tickwidth=1.5)        #   and width

    # Can I just set these in XAxis and YAxis __init__?
    layout['xaxis'].update(axis_style)
    layout['yaxis'].update(axis_style)
    return layout
    

def ply_fig(ts, points=False, color='jet', **kwds):
    """ Convert a timespectra to plotly Figure.  Figures can be then directly
    plotted with plotly.iplot(figure) in the notebook.  Use the layout keyword
    to specify layout parameters; all other keywords are interpreted as line style
    keywords (color
    
    Parameters
    ----------
    
    points: bool
        If true, scatter plot; else, lineplots
        
    color: str
        Any valid matplotlib color or colormap.
    
    layout: dict
        Dictionary of keywords that go into layout.  
        
    """
    
    data = grobs.Data()
    layoutkwds = kwds.pop('layout', {})
    lout = layout(ts, **layoutkwds)    
    
    # List of colors, either single color or color map
    try:
        cmapper = put.cmget(color) #Validate color map
    except AttributeError:
        cmapper = [color for i in range(len(ts.columns))]
    else:
        cmapper = put._df_colormapper(ts, color, axis=0)        
        
    # Map colors to rgb
    cmapper = map(put.to_normrgb, cmapper)    
    
    # Scale by 255 and string format for plotly
    def _rgbplotlycolor(rgb):
        r,g,b = rgb
        return 'rgb(%s, %s, %s)' % (255.0*r, 255.0*g, 255.0*b)
    
    cmapper = map(_rgbplotlycolor, cmapper)

    if points:
        tracefcn = make_pointtrace
    else:
        tracefcn = make_linetrace

    for idx, clabel in enumerate(ts):            
        trace = tracefcn(
            x = np.array(ts.index),               # Not necessary to force to np.array.dtype(float)
            y = np.array(ts[ts.columns[idx]]),
            name=clabel,
            color=cmapper[idx], #marker color
            **kwds
            ) 
        data.append(trace)

    return grobs.Figure(data=data, layout=lout)


#def ply_multifig(*figargs):
    #""" """
    #for fig in figargs:
        #ts,  
    
    
if __name__ == '__main__':
    from skspec.data import test_spectra
    ts = test_spectra()
    out = ply_figure(ts)

    print tls.get_subplots(rows=3, columns=2, print_grid=True)

    
    import plotly.plotly as py
    py.sign_in('reeveslab', 'hfpi35mejw')
    
    fig = ply_figure(ts, color='black', points=True)
    py.iplot(fig, filename='foo', fileopt='new')    
    print 'FINISHED PLOT 1'
