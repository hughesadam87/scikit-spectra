from skspec.plotting.advanced_plots import PLOTPARSER

from IPython.html.widgets import (
    FlexBox, VBox, HBox, HTML, Box, RadioButtons,
    Text, Dropdown, Checkbox, Image, Popup,
    IntSlider, Button, Text, FloatSlider, IntText, 
    ContainerWidget, FloatText
    )

import IPython.display as ipdisplay

from IPython.utils.traitlets import link, Unicode
from jinja2 import Template

LAYOUT_HTML_1 = '<style> \
.widget-area .spectroscopy .panel-body{padding: 0.5;} \
.widget-area .spectroscopy .widget-numeric-text{width: 2.5em;} \
.widget-area .spectroscopy .widget-box.start{margin-left: 0;} \
.widget-area .spectroscopy .widget-hslider{width: 10em;} \
.widget-area .spectroscopy .widget-text{width: 10em;} \
</style>'

class PanelTitle(HTML):
    def __init__(self, *args, **kwargs):
        super(PanelTitle, self).__init__(*args, **kwargs)
        self._dom_classes += ("panel-heading panel-title",)

class PanelBody(Box):
    def __init__(self, *args, **kwargs):
        super(PanelBody, self).__init__(*args, **kwargs)
        self._dom_classes += ("panel-body",)

class ControlPanel(Box):
    # A set of related controls, with an optional title, in a box (provided by CSS)
    def __init__(self, title=None, *args, **kwargs):
        super(ControlPanel, self).__init__(*args, **kwargs)
        self._dom_classes += ("panel panel-info",)

        # add an option title widget
        if title is not None:            
            self.children = [
                PanelTitle(value=title),
                PanelBody(children=self.children)
            ]


class Alert(HTML):
    """HTML widget that is used to store alerts.  For now,
    just a pure HTML class but put in in separate class to
    allow potential customaization in future."""


class SpectraGui(Box):
    """
    An example GUI for a spectroscopy application.

    Note that `self.model` is the owner of all of the "real" data, while this
    class handles creating all of the GUI controls and links. This ensures
    that the model itself remains embeddable and rem
    """

    def __init__(self, model=None, model_config=None, *args, **kwargs):
	# RUN HTML
        self.model = model or Spectrogram(**(model_config or {}))  #Need to access spectrogram if defaulting...
        # Create alert widget (refactor into its own function?)
        alert = Alert(description = "Alert or something")
        link((self.model, "message"), (alert, "value"))

        # Create a GUI
        kwargs["orientation"] = 'horizontal'
        kwargs["children"] = [HBox([
                                    VBox([self.INOUT_panel(), self.model, alert]),
                                    VBox([self.plot_panel(),self.slicing_panel(),self.unit_panel()]),
                                    ])
                              ]
        super(SpectraGui, self).__init__(*args, **kwargs)
        self._dom_classes += ("spectroscopy row",)

    def tight_layout(self):
	""" Tight layout for gui boxes/widgets """
        return ipdisplay.HTML(LAYOUT_HTML_1)

    def INOUT_panel(self):
        # create correlation controls. NOTE: should only be called once.
        incheck = Checkbox(description = 'Import')
        link((self.model, "inbox"), (incheck,"value"))
        outcheck = Checkbox(description = 'Export')
        link((self.model, "outbox"), (outcheck,"value"))
        
        #loaddata = Checkbox(description="Testdata")
        #link((self.model, "load_spec"), (loaddata, "value"))
        #testdataset = Text(description = "")
        #link((self.model, "testdataset"), (testdataset, "value"))
     
        filename = Text(description = "")
        link((self.model, "file_name"), (filename, "value"))
        loadbutton = Button(color='black',background_color='AliceBlue',description="Load")
        loadbutton.on_click(lambda x: self.model.load_from_ns())
        boxi = HBox([filename,loadbutton])
        #link((self.model, "load_spec"), (specbox, "visible"))

#        loadfile = Checkbox(description="NB Variable") #Test Data
#        link((self.model, "load_file"), (loadfile, "value"))

        
        #                filebox = HBox([loadbutton, filename])
        #link((self.model, "load_file"), (filebox, "visible"))
        
        #boxi = VBox([
                     #HBox([loaddata, loadfile]),
                     #loaddata,
                     #             specbox,
                     #filebox,
                     #            ])
        link((self.model, "inbox"), (boxi,"visible"))

        saveplot = Button(color='black',background_color='AliceBlue',description='Save Plot')
        saveplot.on_click(lambda x: self.model.save_plot())
        savespec = Button(color='black',background_color='AliceBlue',description='Export Dataset')
        savespec.on_click(lambda x: self.model.save_to_ns())
        savespecas = Text(description="")
        link((self.model,"save_spec_as"),(savespecas,"value"))
        
        boxo = VBox([
                    savespecas,
                    HBox([saveplot,savespec]),
                    ])
        link((self.model, "outbox"), (boxo,"visible"))
        
        #reset = Button(color='white',background_color='violet',description='Reset Defaults')
        #reset.on_click(lambda x: self.model.)
                       
        #redraw = Button(description="Redraw")
        #redraw.on_click(lambda x: self.model.draw())

        return ControlPanel(title="Import/Export Dataset",
                            children=[HBox([
                                            VBox([incheck,outcheck]),
                                            VBox([boxi,boxo])
                                            ])
                                     ]
                            )
                       
                       
                       
    def plot_panel(self):
        # create draw mode controls.  NOTE: should only be called once.
        cbar = Checkbox(description="Colorbar")
        link((self.model, "colorbar"), (cbar, "value"))

        interact = Checkbox(description="Interactive")
        link((self.model, "interactive"), (interact, "value"))

        plug_select = Checkbox(description="Line Selection")
        link((self.model, "selectlines"), (plug_select, "value"))

        autoupdate = Checkbox(description="Auto Update")
        link((self.model, "autoupdate"), (autoupdate, "value"))
        
        plugin2= Checkbox(description='Cursor')
        plugin3= Checkbox(description='plugin3')
        fwidth = FloatText(description='Plot width')
        fheight = FloatText(description='Plot height')
        link((self.model, "figwidth"), (fwidth, "value"))
        link((self.model, "figheight"), (fheight, "value"))
        
        
        f = Text(description="Function:")
        link((self.model,"user_f"),(f,"value"))
        fapp = Button(color='black',background_color='AliceBlue',description = "Apply")
        fapp.on_click(lambda x: self.model.apply_userf(name='apply clicked'))

        #plugins = HBox([plugin1,plugin2,plugin3])
        #more = Checkbox(description="More Options")### LINK IT
        #link((self, "moreopt"), (more, "value"))
        #popmore = Popup(children=[VBox([HBox([plug_select,plugin2,plugin3]),
        #                                HBox([f,fapp]),
        #                                VBox([fwidth, fheight])
        #                              ])],
        #                description='Advanced', button_text='Advanced')

        more = Checkbox(description="Advanced")
        link((self.model, "advancedbox"), (more, "value"))

        popmore = VBox([HBox([plug_select,
									plugin2,
							#		plugin3
									]),
                        HBox([f,fapp]),
                        HBox([fwidth, fheight])
                        ])
        link((self.model, "advancedbox"), (popmore,"visible"))

        cmapcheck = Checkbox(description="Colormap")
        link((self.model, "cmapbox"), (cmapcheck, "value"))

        cmap = Dropdown(description="Colormap",values=self.model.COLORMAPS)
        link((self.model,"colormap"),(cmap,"value"))
        link((self.model,"cmapbox"),(cmap,"visible"))
        
        colorcheck = Checkbox(description="Color")
        link((self.model, "colorbox"), (colorcheck, "value"))

        color = Dropdown(description="Color",values=self.model.COLORS)
        link((self.model, "color"), (color, "value"))
        link((self.model,"colorbox"),(color,"visible"))

        kind = Dropdown(description="Plot Type", values=PLOTPARSER.keys())
        link((self.model, "kind"), (kind, "value"))


        return ControlPanel(title="Plot Settings", 
                            children=[
                                VBox([autoupdate,kind]),
                                HBox([cbar, interact]),
                                HBox([colorcheck, cmapcheck]),
                                HBox([more]),
                                cmap,
                                color,
                                popmore
                                ]
                            )

    def unit_panel(self):
        # create spectrum controls.  NOTE: should only be called once.
        specunit = Dropdown(description="Specunit",values=self.model.SPECUNITS.values())
        link((self.model,"spec_unit"),(specunit,"value"))

        varunit = Dropdown(description="Varunit",values=self.model.VARUNITS.values())
        link((self.model,"var_unit"),(varunit,"value"))

        iunit = Text(description="I Unit",values=self.model.iunit)
        link((self.model,"iunit"),(iunit,"value"))

        normunit = Dropdown(description="Normunit",values=self.model.NORMUNITS.values())
        link((self.model,"norm_unit"),(normunit,"value"))

        return ControlPanel(title="Units",
                            children= [
                                normunit,
                                specunit,
                                varunit,
                                iunit
                            ])
                            

    def slicing_panel(self):
        """ create spectrum controls.  NOTE: should only be called once."""

        model = self.model #For readability

        # ALL WIDGETS ARE CAPITALIZED. 
        #AXIS = RadioButtons(values=[0,1],description="Axis")
        #link((model, "slice_axis"), (AXIS, "value"))

        SPECSTART = FloatSlider(description="Spec Start",
                                min=model.specslice_position_start) #Will not try to update

        link((model,"specslice_position_start"),(SPECSTART,"value"))
        link((model,"specstep"),(SPECSTART,"step"))
        link((model,"specslider_start"),(SPECSTART,"min")) # Start end values (IE slider_min / slider_max)
        link((model,"specslider_end"),(SPECSTART,"max"))

        SPECEND = FloatSlider(description="Spec End",
                              max=model.specslice_position_end) # Will not try to update

        link((model,"specslice_position_end"),(SPECEND,"value"))
        link((model,"specstep"),(SPECEND,"step"))
        link((model,"specslider_start"),(SPECEND,"min"))
        link((model,"specslider_end"),(SPECEND,"max"))

        # SPACING WIDGET
        SPECSPACING = IntText(description="Spec Sample by",value=1)
        link((model,"specspacing"),(SPECSPACING,"value"))

        TIMESTART = FloatSlider(description="Var Start",
                                min=model.timeslice_position_start)

        link((model,"timeslice_position_start"),(TIMESTART,"value"))
        link((model,"timestep"),(TIMESTART,"step"))
        link((model,"timeslider_start"),(TIMESTART,"min"))
        link((model,"timeslider_end"),(TIMESTART,"max"))

        TIMEEND = FloatSlider(description="Var End",
                              max=model.timeslice_position_end)
        link((model,"timeslice_position_end"),(TIMEEND,"value"))
        link((model,"timestep"),(TIMEEND,"step"))
        link((model,"timeslider_start"),(TIMEEND,"min"))
        link((model,"timeslider_end"),(TIMEEND,"max"))

        TIMESPACING = IntText(description="Var Sample by",value=1)
        link((model,"timespacing"),(TIMESPACING,"value"))

        speccheck = Checkbox(description="Spectral Axis")
        link((model,"specbox"),(speccheck,"value"))
        SPECRANGED = VBox([SPECSTART,SPECEND,SPECSPACING])
        link((model,"specbox"),(SPECRANGED,"visible"))
        
        timecheck = Checkbox(description="Variation Axis")
        link((model,"timebox"),(timecheck,"value"))
        TIMERANGED = VBox([TIMESTART, TIMEEND, TIMESPACING])
        link((model,"timebox"),(TIMERANGED,"visible"))

        return ControlPanel(title="Slicing/Sampling",
                            children=[
                                HBox([speccheck, timecheck]),
                                SPECRANGED,
                                TIMERANGED
                            ]
                            )




    def plot_plugin_panel(self):
        plugin1= Checkbox(description='plugin1')
        plugin2= Checkbox(description='plugin2')
        plugin3= Checkbox(description='plugin3')
        cp = ControlPanel(title='Choose Plot Plugins',children=[plugin1,plugin2,plugin3])
        link((self.more,"value"),(cp,"visible"))
        return cp

    def user_function_panel(self):
        f = Text(description="Function, Args:")
        link((self.model,"user_f"),(f,"value"))
        fapp = Button(description = "Apply")
        fapp.on_click(lambda x: self.model.apply_userf(name='Apply clicked'))
        cp2 = ControlPanel(title='User Defined Function',children=[f,fapp])
        link((self.more,"value"),(cp2,"visible"))
        return cp2
