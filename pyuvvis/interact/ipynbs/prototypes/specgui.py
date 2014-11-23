from pyuvvis.plotting.advanced_plots import PLOTPARSER

from IPython.html.widgets import (
    FlexBox, VBox, HBox, HTML, Box, RadioButtons,
    Text, Dropdown, Checkbox, Image, 
    IntSlider, Button, Text, FloatSlider, IntText, ContainerWidget
)

from IPython.utils.traitlets import link

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


class SpectralGUI(Box):
    """
    An example GUI for a spectroscopy application.
    
    Note that `self.model` is the owner of all of the "real" data, while this
    class handles creating all of the GUI controls and links. This ensures
    that the model itself remains embeddable and rem
    """
    
    
    def __init__(self, model=None, model_config=None, *args, **kwargs):
        self.model = model or Spectrogram(**(model_config or {}))  #Need to access spectrogram if defaulting...
        # Create a GUI
        kwargs["orientation"] = 'horizontal'
        kwargs["children"] = [
            HBox([self.model,
                  VBox([self.save_load_panel(), self.load_panel(), self.unit_panel()]),
                ]),
            self._controls()
        ]
        super(SpectralGUI, self).__init__(*args, **kwargs)
        self._dom_classes += ("spectroscopy row",)
    
    def _controls(self):
        panels = HBox([
            self.plot_panel(),
            self.slicing_panel()
  	         ],
        _dom_classes=["col-xs-3"])
        
        return panels
    
    def load_panel(self):
        # create correlation controls. NOTE: should only be called once.
        loadbutton = Button(description = 'Load')
        
        loaddata = Checkbox(description="NB Variable")
        link((self.model, "load_spec"), (loaddata, "value"))
        specname = Text(description = "Spec Name")
        link((self.model, "specname"), (specname, "value"))
        specbox = VBox([specname,loadbutton])
        link((self.model, "load_spec"), (specbox, "visible"))
        
        loadfile = Checkbox(description="Test Data")
        link((self.model, "load_file"), (loadfile, "value"))
        filename = Text(description = "Name")
        link((self.model, "file_name"), (filename, "value"))
        filebox = VBox([filename,loadbutton])
        link((self.model, "load_file"), (filebox, "visible"))
        
        return ControlPanel(title="Load Dataset", children=[HBox(children=[loaddata,loadfile]),specbox,filebox])

    def plot_panel(self):
        # create draw mode controls.  NOTE: should only be called once.
        cbar = Checkbox(description="Colorbar")
        link((self.model, "colorbar"), (cbar, "value"))

        interact = Checkbox(description="Interactive")
        link((self.model, "interactive"), (interact, "value"))

	select = Checkbox(description="Line Selection")
	link((self.model, 'selectlines'), (select, 'value'))
        
        autoupdate = Checkbox(description="Auto Update")
        link((self.model, "autoupdate"), (autoupdate, "value"))
        
        
        cmap = Dropdown(description="Colormap",values=self.model.COLORMAPS)
        link((self.model,"colormap"),(cmap,"value"))
             
        color = Dropdown(description="Color",values=self.model.COLORS)
        link((self.model, "color"), (color, "value"))
        
        kind = Dropdown(description="Kind", values=PLOTPARSER.keys())
        link((self.model, "kind"), (kind, "value"))

             
        return ControlPanel(title="Plot Settings", 
                children=[
                    HBox([autoupdate, interact, select]),
                    HBox([cmap,cbar]),
	            HBox([color, kind])
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
		iunit
            ]
        )
    
    def slicing_panel(self):
        """ create spectrum controls.  NOTE: should only be called once."""

        model = self.model #For readability
        
        # ALL WIDGETS ARE CAPITALIZED. 
        AXIS = RadioButtons(values=[0,1],description="Axis")
        link((model, "slice_axis"), (AXIS, "value"))
        
        START = FloatSlider(description="Slice Start",
                            min=model.slice_position_start) #Will not try to update
       
        link((model,"slice_position_start"),(START,"value"))
        link((model,"step_spec"),(START,"step"))
        link((model,"slider_start"),(START,"min")) # Start end values (IE slider_min / slider_max)
        link((model,"slider_end"),(START,"max"))
        
        END = FloatSlider(description="Slice End",
                          max=model.slice_position_end) # Will not try to update
        
        link((model,"slice_position_end"),(END,"value"))
        link((model,"step_spec"),(END,"step"))
        link((model,"slider_start"),(END,"min"))
        link((model,"slider_end"),(END,"max"))
        
        # SPACING WIDGET
        SPACING = IntText(description="Sample by",value=1)
        link((model,"spacing"),(SPACING,"value"))

        RANGED = VBox([START,END,SPACING])
        
        
        return ControlPanel(title="Slicing/Sampling",
              children=[
                  AXIS,
                  RANGED
                  ]
              )
    
    def save_load_panel(self):
        
        saveplot = Button(description='Save Plot')
        
        savets = Button(description='Save New Spectra')
        #link((self.model,"save_spec"),(savets,'value'))
        savets.on_click(lambda x: self.model.save_to_ns())
        savetsas = Text(description='Save as:')
        link((self.model,"save_spec_as"),(savetsas,'value'))
        #redraw = Button(description="Redraw")
        #redraw.on_click(lambda x: self.model.draw())
        return ControlPanel(title='Save Dataset (combine w/ load)',children=[saveplot,savets,savetsas])
        #return ToolBar(redraw)      
