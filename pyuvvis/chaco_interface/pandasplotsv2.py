### Enthought tool suite imports 
from traits.api import Instance, Str, Enum, Range, HasTraits, Button, Enum, Property, Bool, Any
from traitsui.api import Item, View, HGroup, VGroup, Group, Include, ShellEditor
from enable.api import ComponentEditor
from chaco.api import LabelAxis, Plot, ToolbarPlot
from chaco.tools.api import BetterSelectingZoom, PanTool
from random import randint
from copy import deepcopy
from pandas import DataFrame

from chaco.tools.api import RangeSelection, RangeSelectionOverlay

### For testing 
import numpy as np
from time import sleep

### For pyuvvis imports
#from pyuvvis import get_csvdf
#from pyuvvis import wavelength_slices
#from pyuvvis import datetime_convert
from pandas.stats.moments import rolling_mean

### Local import 
from pandasplotdatav3 import PandasPlotData
   
    

### Add a method to relable rows/columns in place?
class PandasPlot(HasTraits):
    '''Plot to interface a pandas df'''
    ### Actually   
    _dffull=Instance(DataFrame)  #Any?
    df=Instance(DataFrame)  
    indexname=Str('Index')
    columnname=Str('Column')

    ### Traits of the actual plot and plotdatasource handler ###
    plot=Instance(Plot)  
    plotdata=Instance(PandasPlotData) #Data stored at any given time in the plot

    ### Aesthetic traits
    plot_title=Str('') #Defaults from df name
    linecolor=Str('black')
    pointcolor=Str('red')
    linestyle=Enum('line', 'scatter', 'both')
    markersize=Range(low=1, high=5)

    def _df_changed(self, old, new):
        ''' Handles how updates occur when df changes.  Evaluates if columns or columnlabels
        have been changed.  Provides entry condition as well.

        Note: New automatically sets self.df, so when I refer to new, I am actually
        referring to self.df.  Using "new" instead of self.df is just for readability'''

        ### Initialize plot first time df is passed into the class.  Boolean listeners
        ### for df behave oddly, so uses self.plotdata for entry condition.

        if not self.plotdata:
            self.plotdata=PandasPlotData(df=new)
            
            self._dffull=new

            ### Try to infer plot title from df name ###	    
            try: 
                self.plot_title=new.name   #Turn into a "transfer" method where I pass list of attributes i want look for
            except AttributeError:
                pass

            ### Draw barebones of plot
            self.draw_plot()
            self._update_lines()           
       
        
        ### Decide to update columns or completely redraw df.  
        else:
            self.plotdata.set_df(new)
            self._update_lines()

        self.plot.request_redraw()

    def _update_lines(self):
        ''' Recasts plotdata and ties it to the plot object.'''

        print 'updatelines called'
        
        oldplots=self.plot.plots.keys()
        newplots=[name for name in self.plotdata.list_data(as_strings=True)]
        
        to_remove=[p for p in oldplots if p not in newplots]
        to_add=[p for p in newplots if p not in oldplots]

        if to_remove:
            for p in to_remove:
                self.plot.delplot(p)
        
        if to_add:
            for p in to_add:
                self.plot.plot(('index',name), name=name)
            
        print 'listing', self.plotdata.list_data()
            
        if self.plot.plots:
            mycomp=self.plot.plots.itervalues().next()[0] #Quick wayt to get first value in dictionary
            self.plot.active_tool = RangeSelection(mycomp)
            self.plot.overlays.append(RangeSelectionOverlay(component=mycomp)) 
            
        self.plot.request_redraw()

    def draw_plot(self, toolbar=True, **pltkws):
        ''' Draw bare plot, including main plotting area, toolbar, etc...
         either at initialization or global redo'''
        if toolbar:
            plot=ToolbarPlot(self.plotdata, **pltkws)
        else:
            plot=Plot(self.plotdata, **pltkws)
            
 #       plot.active_tool = RangeSelection(plot)
 #       plot.overlays.append(RangeSelectionOverlay(component=plot))    
        
        plot.title = self.plot_title
        plot.padding = 50
        plot.legend.visible=False

        plot.tools.append(PanTool(plot))
        zoom=BetterSelectingZoom(component=plot, tool_mode="box", always_on=False)
        plot.overlays.append(zoom)
        
        #indexlabels=[str(round(i,1)) for i in self.df.index]

        #### If I do plot.index_axis, it actually removes the default values.
    
        #index_axis=LabelAxis(plot, orientation='top', 
                    ##              positions=range(int(float(indexlabels[0])),
                     ##                             int(float(indexlabels[-1]))), 
                                   #positions=range(0,1000,100),
                                #labels=indexlabels,#, resizable='hv',
                                #title=self.indexname)
        #plot.underlays.append(index_axis)

        #plot.value_axis= LabelAxis(plot, orientation='left',  positions=range(self.t_axis_samples),
                                    #mainlabels=['t1', 't2', 't3', 't4','t5', 't6'], resizable='hv', 
                                    #title=self.t_axis_title)
        self.plot=plot

    def _overwrite_plotdata(self):
        '''When a new instance of PandasPlotData is created, this overwrites the
        data source and updates the axis values.'''
        self.plotdata=PandasPlotData(df=self.df)
        self.draw_plot() #CAN THIS JUST DRAW LINES
        #self.plot.index_axis=LabelAxis(self.plot, orientation='bottom', positions=[0,4,42], 
                                #labels=self.plotdata._rowmasks.keys(), resizable='hv',
                                #title=self.indexname)

        #plot.value_axis= LabelAxis(plot, orientation='left',  positions=range(self.t_axis_samples),
                                    #mainlabels=['t1', 't2', 't3', 't4','t5', 't6'], resizable='hv', 
                                    #title=self.t_axis_title)	


    #axis_traits_group=VGroup(
                            #HGroup(
                                    #Item('x_axis_title'), Item('t_axis_title'), Item('plot_title'), 
                                    #),
                            #HGroup(
                                    #Item('markersize'),Item('linestyle'),
                                    #),
                            #)

    #sample_group=Group(
                        #HGroup(Item('spacing'), Item('samp_style') )
                        #)

    main_group=Group(
        Item('plot', editor=ComponentEditor(), show_label=False),
     #   Item('df_new'), Item('df_change'), 
        #Include('sample_group'),
        #Include('axis_traits_group')
    )

    traits_view=View( Include('main_group') , height=600, width=800)
    
    

class WithShell(HasTraits):
    df=Instance(DataFrame)
    shell=Any()
    pandasplot=Instance(PandasPlot)
    
    def __init__(self):
        self.df=DataFrame([1,2,3])
        self.pandasplot=PandasPlot()
        self.pandasplot.df=self.df
        
    def _df_changed(self):
        if self.pandasplot:
            self.pandasplot.df=self.df
        
        
    main_group=Group(
        Item('pandasplot', show_label=False, style='custom'),
     #   Item('df_new'), Item('df_change'), 
        Item('shell', editor=ShellEditor(), style='simple'),
        #Include('sample_group'),
        #Include('axis_traits_group')
    )

    traits_view=View( Include('main_group'), resizable=True, height=600, width=800)

if __name__=='__main__':
    
  #  df=get_csvdf('spectra.pickle')
    df=DataFrame([1,2,3,4,5], index=[400,500,600,700,760])


    ### THIS WILL INDUCE A FAILURE IN THE PLOT.PLOT call
 #   df=wavelength_slices(df, ranges=((350.0,370.0), (450.0,500.0), (550.0,570.0), (650.0,680.0), (680.0,700.0)),\
 #                           apply_fcn='simps')

    ### resample df to be a bit less dense, makes plot changes more fluid ###
    
#    df=df.ix[300.0:800.0:5.0, 0:150:5]
 
#    theplot=PandasPlot()   
#    theplot.df=df   
#    theplot.configure_traits()
    
    test=WithShell()
    test.df=df
    idx=list('abcdefghij')
    test.df=DataFrame((np.random.rand(10,10)), index=idx)
    test.configure_traits()
    

