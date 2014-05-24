# pyuvvis intefrace to plotly:
# http://nbviewer.ipython.org/github/plotly/python-user-guide/blob/master/s00_homepage/s00_homepage.ipyn

import plotly.graph_objs as grobs

def make_trace(x, y, name):#, linecolor):  
    """Trace-generating function (returns a Scatter object) from timespectra"""

    return grobs.Scatter(x=x,        
                   y=y,        
                   mode='lines',          
                   name=name,          
#                   marker= Line(color=linecolor, width =0.0) 
                  )

def layout(ts, *args, **kwargs):
    """ Make a plotly layout from timespectra attributes """    
    
    kwargs.setdefault('title', ts.name)
    kwargs.setdefault('plot_bgcolor', '#EFECEA') #gray

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
    

def figure(ts, **layoutkwds):
    """ Convert a timespectra to plotly Figure.  Figures can be then directly
    plotted with plotly.iplot(figure) in the notebook.
    """
    
    data = grobs.Data()
    lout = layout(ts, **layoutkwds)
    
    for clabel in ts:
        trace = make_trace(ts.index, ts[clabel], clabel)
        data.append(trace)
        
    
    
if __name__ == '__main__':
    from pyuvvis.data import test_spectra
    ts = test_spectra()
    out = figure(ts)