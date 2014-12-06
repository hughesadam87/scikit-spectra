import re
import skspec
import skspec.data
import matplotlib.pyplot as plt

from datetime import datetime
from collections import OrderedDict
from skspec import Spectra


from IPython.html.widgets import (
            FlexBox, VBox, HBox, HTML, Box, RadioButtons,
            FloatText, Dropdown, Checkbox, Image,
            IntSlider, Button, Text, FloatSlider, IntText, ContainerWidget
                                  )
from IPython.utils.traitlets import (
            link, Unicode, Float, Int, Enum, Bool, Instance, Any
                                     )


from specgui import Box, HTML
from nbtools import mpl2html, log_message

from skspec.core.spectra import _normdic as NUdic
import skspec.config as pvconf
from skspec.data import aunps_glass
from skspec.plotting.advanced_plots import PLOTPARSER

class SpectraModel(HTML, Box):
    """
    A notional "complex widget" that knows how to redraw itself when key
    properties change.
    """
    
    # CONSTANTS (These are not traits)
    classname = Unicode("btn btn-success",sync=True)
    title = Unicode("Popover Test",sync=True)
    CONTENT = Unicode("""Lovely popover :D. Color in green using class btn btn-success""",sync=True)
    html = Bool(sync=True)
    
    DONT_DRAW = re.compile(r'^(_.+|value|keys|comm|children|visible|parent|log|config|msg_throttle)$')
    NORMUNITS = NUdic
    NORMUNITS_REV = OrderedDict((v,k) for k,v in NORMUNITS.items())
    COLORS = ["b","g","r","y","k"]
    COLORMAPS = sorted(m for m in plt.cm.datad if not m.endswith("_r"))
    SLIDER_STEPS = Float(25)
    
    # IO traitlets
    load_spec = Bool(False,sync=True)
    load_file = Bool(True,sync=True) #
    file_name = Unicode("<Variable>", sync=True)
    save_spec = Bool(False,sync=True)
    save_spec_as = Unicode('Test',sync=True)
    
    # Spectra traits
    spec = Instance(Spectra)
    testdataset = Unicode('<Dataset>', sync=True) 
    spec_modified = Instance(Spectra)
    
    # Plotting Traits
    figwidth = Float(6.5)
    figheight = Float(6.5)
    interactive = Bool(False, sync=True)
    colorbar = Bool(False, sync=True)
    autoupdate = Bool(True, sync=True)
    colormap = Enum(COLORMAPS ,sync=True)
    color = Enum(COLORS, default_value = 'k', sync=True)
    kind = Enum(PLOTPARSER.keys(), default_value = 'spec', sync=True)
    
    # Units
    spec_unit = Unicode
    var_unit = Unicode
    iunit = Unicode
    norm_unit = Enum(NORMUNITS.values(),  sync=True)
    
    # Message/warnings
    message = Unicode
    
    # Sampling/slicing
    #specslice_axis = Enum([0,1], default_value=0, sync=True)
    specslice_position_start = Float(sync=True)
    specslice_position_end = Float(sync=True)
    specslider_start = Float(sync=True)
    specslider_end = Float(sync=True)
    specstep = Float(sync=True)
    specspacing = Int(1, sync=True)
    
    timeslice_position_start = Float(sync=True)
    timeslice_position_end = Float(sync=True)
    timeslider_start = Float(sync=True)
    timeslider_end = Float(sync=True)
    timestep = Float(sync=True)
    timespacing = Int(1, sync=True)
    
    selectlines = Bool(False, sync=True)
    
    # User Defined Function
    user_f = Unicode(sync=True)
    
    
    def __init__(self, *args, **kwargs):
        
        # Initialize traits (_spec_changed calls initial draw)
        super(SpectraModel, self).__init__(*args, **kwargs)
        self._dom_classes += ("col-xs-9",)
    
    
    # DEFAULTS
    # --------
    def _spec_default(self):
        return getattr(skspec.data, 'aunps_water')()
    
    def _colormap_default(self):
        return pvconf.CMAP_1DSPECPLOT #Use skspec config default (red/blue map)
    
    # Events
    # ------
    def _spec_changed(self, name, old, new):
        """Overall spectrum changes; triggers most events."""
        
        # Leave this at this position in loop
        self.spec_modified= self.spec
        # --------------
        
        self._FREEZE = True #pause draws/slicing
        
        # Units
        self.spec_unit = self.spec.full_specunit
        self.var_unit = self.spec.full_varunit
        self.norm_unit = self.spec.full_norm
        self.iunit = self.spec.full_iunit
        
        
        # Spec slicing
        self.specslice_position_start = self.spec.index[0]
        self.specslice_position_end = self.spec.index[-1]
        self.specslider_start = self.spec.index[0]
        self.specslider_end = self.spec.index[-1]
        self.specstep = (self.spec.index.max() - self.spec.index.min())/self.SLIDER_STEPS
        self.specspacing = 1
        
        self.timeslice_position_start = self.spec.columns[0]
        self.timeslice_position_end = self.spec.columns[-1]
        self.timeslider_start = self.spec.columns[0]
        self.timeslider_end = self.spec.columns[-1]
        self.timestep = 10#(self.spec.columns.max() - self.spec.columns.min())/self.SLIDER_STEPS
        self.timespacing = 1
        
        # Plot defaults to color map
        self._color_state = False
        
        self._FREEZE = False
        self.draw(name, old, new)
    
    def _norm_unit_changed(self, name, old, new):
        self.spec_modified = self.spec_modified.as_norm(self.NORMUNITS_REV[new])
        self.draw(name, old, new)
    
    def _iunit_changed(self, name, old, new):
        self.spec_modified.iunit = new
        self.draw(name, old, new)
    
    # Plotting events
    # ---------------    
    def _figwidth_changed(self, name, old, new):
        self.draw(name, old, new)

    def _figheight_changed(self, name, old, new):
        self.draw(name, old, new)
    
    def _colormap_changed(self, name, old, new):
        self._color_state = False
        self.draw(name, old, new)
    
    def _color_changed(self):
        """ Because this sets colorbar, might cause 2 redraws,
            so _FREEZE used to prevent this
            """
        self._FREEZE = True
        self.colorbar = False
        self._color_state = True
        self._FREEZE = False
        self.draw()
    
    def _colorbar_changed(self, name, old, new):
        self._color_state = False
        self.draw(name, old, new)
    
    def _interactive_changed(self, name, old, new):
        self.draw(name, old, new)
    
    # This should be phased out; plots should support colormap, area should handle accordingly
    def _kind_changed(self, name, old, new):
        self.draw(name, old, new)
    
    def _selectlines_changed(self, name, old, new):
        if self.interactive:
            self.draw(name, old, new)
    
    # IO Events
    # ---------
    # THIS SHOULD BE LOAD BUTTON CLICKED!!!!
    def _file_name_changed(self):
        try:
            self.spec = getattr(skspec.data, self.file_name)()
        except AttributeError:
            pass

    @log_message    
    def save_to_ns(self):
        get_ipython().user_ns[self.save_spec_as]=self.spec_modified
    
    @log_message
    def load_from_ns(self, var):
        self.spec = get_ipython().user_ns[var]            
        
    # Slicing events
    # --------------
    def _specslice_position_start_changed(self, name, old, new):       
        if not self._FREEZE:
            self.slice_spectrum(name)
            self.draw(name, old, new)
    
    def _specslice_position_end_changed(self, name, old, new):
        if not self._FREEZE:
            self.slice_spectrum(name)
            self.draw(name, old, new)
    
    def _timeslice_position_start_changed(self, name, old, new):
        if not self._FREEZE:
            self.slice_spectrum(name)
            self.draw(name, old, new)
    
    def _timeslice_position_end_changed(self, name, old, new):
        if not self._FREEZE:
            self.slice_spectrum(name)
            self.draw(name, old, new)
    
    
    def _timespacing_changed(self, name, old, new):
        """ Don't let user set less than 1 or more than dataset size"""
        # Will have to update when add var/spec slicing
        #axis = self.slice_axis
        if self.timespacing < 1:
            self.timespacing = 1
        elif self.timespacing > self.spec_modified.shape[1]:
            self.timespacing = self.spec_modified.shape[1]
        
        self.slice_spectrum(name)
        self.draw(name, old, new)
    
    def _specspacing_changed(self, name, old, new):
        """ Don't let user set less than 1 or more than dataset size"""
        # Will have to update when add var/spec slicing
        #axis = self.slice_axis
        if self.specspacing < 0:
            self.specspacing = 0
        elif self.specspacing > self.spec_modified.shape[0]:
            self.specspacing = self.spec_modified.shape[0]
        
        self.slice_spectrum(name)
        self.draw(name, old, new)
        
    # Draw/Slice updates
    # ------------------
    @log_message
    def slice_spectrum(self, name=None):
        """ Slice and resample spectra """
        self.spec_modified = self.spec.nearby[self.specslice_position_start:self.specslice_position_end:self.specspacing,
                                              self.timeslice_position_start:self.timeslice_position_end:self.timespacing]
    
    @log_message
    def apply_userf(self,name=None):
        import numpy as np
        self.spec_modified = self.spec_modified.apply(eval(self.user_f))
        self.draw(name)
    
    
    
    @log_message
    def draw(self, name=None, old=None, new=None):
        if name is not None and self.DONT_DRAW.match(name):
            return
        
        if self._FREEZE:
            return
        
        plot_and_message = ''
        
        # Better way would be a decorator or something that only goes into draw if not autoupdate
        if self.autoupdate:
            
            # Generate new figure object
            f = plt.figure(figsize=(self.figwidth, self.figheight))
            if PLOTPARSER.is_3d(self.kind):
                projection = '3d'
            else:
                projection = None
            ax = f.add_subplot(111, projection=projection)
            
            if self._color_state or self.kind not in ['spec', 'waterfall', 'contour', 'contour3d']:
                colorkwags = dict(color=self.color)
            else:
                colorkwags = dict(cmap=self.colormap, cbar=self.colorbar)
            
            self.spec_modified.plot(ax=ax,
                                    fig=f,
                                    kind=self.kind,
                                    norm=self.NORMUNITS_REV[self.norm_unit],
                                    **colorkwags
                                    )
            f.tight_layout() #Padding around plot
            lines = ax.get_lines()
            plt.close(f)
                                    
            #http://mpld3.github.io/modules/API.html
            if self.interactive:
                import mpld3
                if self.selectlines:
                    from line_plugin import HighlightLines
                    
                    for idx, col in enumerate(self.spec_modified.columns):
                        name = 'COLUMN(%s): %s' % (idx, col)
                        tooltip = mpld3.plugins.LineLabelTooltip(lines[idx], name)
                        #voffset=10, hoffset=10,  css=css)
                        mpld3.plugins.connect(f, tooltip)
                    
                    mpld3.plugins.connect(f, HighlightLines(lines))
                
                plot_and_message += mpld3.fig_to_html(f)
            else:
                plot_and_message += mpl2html(f)
            
            self.fig_old = f
        
        else:
            plot_and_message += html_figure(self.fig_old)
        
        # VALUE IS WHAT GUI LOOKS UP!!!
        self.value = plot_and_message
