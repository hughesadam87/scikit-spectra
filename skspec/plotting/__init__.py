from skspec.plotting.plot_utils import splot

# Advanced plots has to create plotparser because its plot methods depend on it
# Surely just bad design
from skspec.plotting.advanced_plots import _gen2d3d, spec3d, PLOTPARSER, \
         add_projection

from skspec.plotting.basic_plots import range_timeplot, areaplot, _genplot    

from skspec.plotting.multiplots import quad_plot, six_plot

