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

class PopOvers(HTML):
    template = Template("""
        <p id="x"
        class="{{classname}}"
        title="{{ title|escape }}"
        data-toggle="popover"
        data-content="{{ content|escape }}">{{description}}</p>
        <script>
        $('#x').popover();
        </script>
        """)
    description = Unicode(sync=True)
    classname = Unicode(sync=True)
    title = Unicode(sync=True)
    content = Unicode(sync=True)


    def __init__(self, *args, **kwargs):
        super(PopOvers, self).__init__(*args, **kwargs)

    def _title_changed(self, old, new):
        self.value = self.template.render(**self._trait_values)


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
    more = Checkbox(description="Advanced")

    def __init__(self, model=None, model_config=None, *args, **kwargs):
	# RUN HTML
        self.model = model or Spectrogram(**(model_config or {}))  #Need to access spectrogram if defaulting...
        # Create alert widget (refactor into its own function?)
        alert = Alert(description = "Alert or something")
        link((self.model, "message"), (alert, "value"))

        # Create a GUI
        kwargs["orientation"] = 'horizontal'
        kwargs["children"] = [
            HBox([VBox([alert, self.model]),
                  VBox([self.save_load_panel(), 
                        self.load_panel(),
                        self.unit_panel()]),
                       ]),
            self._controls(),
        ]
        super(SpectraGui, self).__init__(*args, **kwargs)
        self._dom_classes += ("spectroscopy row",)

    def _controls(self):
        panels = VBox([
            HBox([self.plot_panel(),self.slicing_panel()]),
            HBox([self.plot_plugin_panel(),self.user_function_panel()])],
                      _dom_classes=["col-xs-3"])

        return panels

    def set_layout(self):
	return ipdisplay.HTML(open('style1.html','r').read())

    def load_panel(self):
        # create correlation controls. NOTE: should only be called once.
        loadbutton = Button(description = 'Load')

        loaddata = Checkbox(description="Testdata")
        link((self.model, "load_spec"), (loaddata, "value"))
        testdataset = Text(description = "") 
        link((self.model, "testdataset"), (testdataset, "value"))
     
        specbox = HBox([loadbutton, testdataset])
        link((self.model, "load_spec"), (specbox, "visible"))

        loadfile = Checkbox(description="NB Variable") #Test Data
        link((self.model, "load_file"), (loadfile, "value"))
        filename = Text(description = "")

        link((self.model, "file_name"), (filename, "value"))
        filebox = HBox([loadbutton, filename])
        link((self.model, "load_file"), (filebox, "visible"))

        reset = Button(color='white',background_color='violet',
                       escription='Reset Defaults')
        #reset.on_click(lambda x: self.model.)

        return ControlPanel(title="Load Dataset", children=[HBox(children=[loaddata,loadfile]),specbox,filebox,reset])

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

        plugin2= Checkbox(description='plugin2')
        plugin3= Checkbox(description='plugin3')
        fwidth = FloatText(description='Plot width')
        fheight = FloatText(description='Plot height')
        link((self.model, "figwidth"), (fwidth, "value"))
        link((self.model, "figheight"), (fheight, "value"))
        
        
        f = Text(description="Function:")
        link((self.model,"user_f"),(f,"value"))
        fapp = Button(description = "Apply")
        fapp.on_click(lambda x: self.model.apply_userf(name='apply clicked'))

        #plugins = HBox([plugin1,plugin2,plugin3])
        #more = Checkbox(description="More Options")### LINK IT
        #link((self, "moreopt"), (more, "value"))
        popmore = Popup(children=[VBox([HBox([plug_select,plugin2,plugin3]),
                                        HBox([f,fapp]),
                                        VBox([fwidth, fheight])
                                      ])],
                        description='Advanced', button_text='Advanced')

        cmap = Dropdown(description="Colormap",values=self.model.COLORMAPS)
        link((self.model,"colormap"),(cmap,"value"))

        color = Dropdown(description="Color",values=self.model.COLORS)
        link((self.model, "color"), (color, "value"))

        kind = Dropdown(description="Kind", values=PLOTPARSER.keys())
        link((self.model, "kind"), (kind, "value"))


        return ControlPanel(title="Plot Settings", 
                            children=[
                                HBox([autoupdate, interact, self.more]),
                                HBox([cmap,cbar]),
                                HBox([color, kind]),
                                popmore
                                ]
                            )

    def unit_panel(self):
        # create spectrum controls.  NOTE: should only be called once.
        specunit = Text(description="Specunit",values=self.model.spec_unit)
        link((self.model,"spec_unit"),(specunit,"value"))

        varunit = Text(description="Varunit",values=self.model.var_unit)
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
                                iunit]
                            )

    def slicing_panel(self):
        """ create spectrum controls.  NOTE: should only be called once."""

        model = self.model #For readability

        # ALL WIDGETS ARE CAPITALIZED. 
        #AXIS = RadioButtons(values=[0,1],description="Axis")
        #link((model, "slice_axis"), (AXIS, "value"))

        SPECSTART = FloatSlider(description="Spec Slice Start",
                                min=model.specslice_position_start) #Will not try to update

        link((model,"specslice_position_start"),(SPECSTART,"value"))
        link((model,"specstep"),(SPECSTART,"step"))
        link((model,"specslider_start"),(SPECSTART,"min")) # Start end values (IE slider_min / slider_max)
        link((model,"specslider_end"),(SPECSTART,"max"))

        SPECEND = FloatSlider(description="Spec Slice End",
                              max=model.specslice_position_end) # Will not try to update

        link((model,"specslice_position_end"),(SPECEND,"value"))
        link((model,"specstep"),(SPECEND,"step"))
        link((model,"specslider_start"),(SPECEND,"min"))
        link((model,"specslider_end"),(SPECEND,"max"))

        # SPACING WIDGET
        SPECSPACING = IntText(description="Spec Sample by",value=1)
        link((model,"specspacing"),(SPECSPACING,"value"))

        TIMESTART = FloatSlider(description="Time Slice Start",
                                min=model.timeslice_position_start)

        link((model,"timeslice_position_start"),(TIMESTART,"value"))
        link((model,"timestep"),(TIMESTART,"step"))
        link((model,"timeslider_start"),(TIMESTART,"min"))
        link((model,"timeslider_end"),(TIMESTART,"max"))

        TIMEEND = FloatSlider(description="Time Slice End",
                              max=model.timeslice_position_end)
        link((model,"timeslice_position_end"),(TIMEEND,"value"))
        link((model,"timestep"),(TIMEEND,"step"))
        link((model,"timeslider_start"),(TIMEEND,"min"))
        link((model,"timeslider_end"),(TIMEEND,"max"))

        TIMESPACING = IntText(description="Time Sample by",value=1)
        link((model,"timespacing"),(TIMESPACING,"value"))

        RANGED = VBox([SPECSTART,SPECEND,SPECSPACING, TIMESTART, TIMEEND, TIMESPACING])


        return ControlPanel(title="Slicing/Sampling",
                            children=[
                                #AXIS,
                                RANGED
                            ]
                            )

    def save_load_panel(self):
        """ All Save/Load IO of GUI in this panel. """
        saveplot = Button(description='Save Plot')
        savets = Button(description='Export as NB Variable')
        #link((self.model,"save_spec"),(savets,'value'))
        savets.on_click(lambda x: self.model.save_to_ns())
        savetsas = Text(description='Save as:')
        link((self.model,"save_spec_as"),(savetsas,"value"))

        po= PopOvers(description='Click for Popover')
        link((self.model,"CONTENT"),(po,"content"))
        link((self.model,"classname"),(po,"classname"))
        link((self.model,"title"),(po,"title"))
        #redraw = Button(description="Redraw")
        #redraw.on_click(lambda x: self.model.draw())
        return ControlPanel(title='Save Dataset (combine w/ load)',
                            children=[saveplot,
                                      savets,
                                      savetsas,
                                      po])
        #return ToolBar(redraw)


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
