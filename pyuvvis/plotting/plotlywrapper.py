# pyuvvis intefrace to plotly:
# http://nbviewer.ipython.org/github/plotly/python-user-guide/blob/master/s00_homepage/s00_homepage.ipyn

import plotly.graph_objs as grobs
import numpy as np
import pyuvvis.plotting.plot_utils as put

def make_linetrace(x, y, **tracekwargs):#, linecolor):  
    """Trace-generating function (returns a Scatter object) from timespectra"""
    # good example of trace options http://plot.ly/python/bubblecharts
    
    name = tracekwargs.pop('name', '')
    tracekwargs.setdefault('color', 'rgb(255,0,0)') #markercolor
    tracekwargs.setdefault('opacity', 1.0) 
    
    return grobs.Scatter(x=x,
                         y=y,          
                         mode='lines',          
                         name=name,          
                         marker= grobs.Line(**tracekwargs) 
                         )

def make_pointtrace(x, y, **tracekwargs):#, linecolor):  
    """Trace-generating function (returns a Scatter object) from timespectra"""
    # good example of trace options http://plot.ly/python/bubblecharts
    
    name = tracekwargs.pop('name', '')    
    tracekwargs.setdefault('color', 'rgb(255,0,0)') #markercolor
    tracekwargs.setdefault('symbol', 'circle')
    tracekwargs.setdefault('opacity', 1.0)
    tracekwargs.setdefault('size', 12)

    return grobs.Scatter(x=x,
                         y=y,
                         mode='markers',
                         marker=grobs.Marker(**tracekwargs)
                         )


def layout(ts, *args, **kwargs):
    """ Make a plotly layout from timespectra attributes """    
    
    kwargs.setdefault('title', ts.name)
    kwargs.setdefault('plot_bgcolor', '#EFECEA') #gray
    kwargs.setdefault('showlegend', False)

    # Map x,y title into grobs.XAxis and grobs.YAxis
    xtitle = kwargs.pop('xtitle', ts.specunit)
    ytitle = kwargs.pop('ytitle', ts.specunit)
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
    

def ply_figure(ts, color='jet', **layoutkwds):
    """ Convert a timespectra to plotly Figure.  Figures can be then directly
    plotted with plotly.iplot(figure) in the notebook.
    """
    
    data = grobs.Data()
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

    for idx, clabel in enumerate(ts):
        trace = make_linetrace(
            x = list(np.linspace(0,6.28)),
            y = list(np.sin(np.linspace(0,6.28))),
            #x = np.array(ts.index).astype(float), 
            #y = np.array(ts.index).astype(float),
#                           y = np.array(ts[clabel]), 
#                           name=clabel,
#                           color=cmapper[idx]
            ) #marker color
        data.append(trace)

    return grobs.Figure(data=data, layout=lout)
    
    
if __name__ == '__main__':
    from pyuvvis.data import test_spectra
    ts = test_spectra()
    out = ply_figure(ts)
    
    import plotly.plotly as py
    py.sign_in('reeveslab', 'pdtrwl7yjd')
    
    fig = ply_figure(ts, color='jet')
    py.iplot(fig, filename='foo', fileopt='new')    
    print 'FINISHED PLOT 1'
    
    fig = ply_figure(ts, color='bone')
    py.iplot(fig, filename='bar', fileopt='new')        
    print 'FINISHED PLOT 2'