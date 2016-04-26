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

### For skspec imports
#from skspec import get_csvdataframe
#from skspec import wavelength_slices
#from skspec import datetime_convert
from pandas.stats.moments import rolling_mean

### Local import 
from pandasplotdatav2 import PandasPlotData
   
    

### Add a method to relable rows/columns in place?
class PandasPlot(HasTraits):
    '''Plot to interface a pandas dataframe'''
    ### Actually   
    originaldata=Instance(DataFrame)
    dataframe=Instance(DataFrame)  
    primaryaxis=Enum(0,1,'index','columns') #Integer or string, defaults to 0
    _primaryaxis=Property(Enum(0,1), depends_on='primaryaxis') #0,1
    indexname=Str('Index')
    columnname=Str('Column')

    ### Traits of the actual plot and plotdatasource handler ###
    plot=Instance(Plot)  
    plotdata=Instance(PandasPlotData) #Data stored at any given time in the plot

    ### Aesthetic traits
    plot_title=Str('') #Defaults from dataframe name
    linecolor=Str('black')
    pointcolor=Str('red')
    linestyle=Enum('line', 'scatter', 'both')
    markersize=Range(low=1, high=5)

    ### Traits for testing    
    df_new=Button
    df_change=Button    
    re_bin=Range(1,100)

    def _dataframe_changed(self, old, new):
        ''' Handles how updates occur when dataframe changes.  Evaluates if columns or columnlabels
        have been changed.  Provides entry condition as well.

        Note: New automatically sets self.dataframe, so when I refer to new, I am actually
        referring to self.dataframe.  Using "new" instead of self.dataframe is just for readability'''

        ### Initialize plot first time dataframe is passed into the class.  Boolean listeners
        ### for dataframe behave oddly, so uses self.plotdata for entry condition.
        if not self.plotdata:
            self.plotdata=PandasPlotData(df=new)
            
            self.originaldata=new

            ### Try to infer plot title from dataframe name ###	    
            try: 
                self.plot_title=new.name
            except AttributeError:
                pass

            ### Draw barebones of plot
            self.draw_plot()
            ### Draw lines
            self._draw_lines() 

            return
        
        
        ### Decide to update columns or completely redraw dataframe.  
        else:
            labelold=self._getlabelarray(old)	    
            labelnew=self._getlabelarray(new)

            ### Have columns been added or removed?	    
            if len(labelold) != len(labelnew):
                self._overwrite_plotdata

            ### Has index along primaryaxis changed any?
            ### Pandas index comparison is a bit tricky so just list conver
            elif list(labelold) != list(labelnew):
                self._overwrite_plotdata
            else:
                print 'updating frame'
                self.plotdata.set_df(new)

    ### Properties ###	
    def _get__primaryaxis(self):
        ''' Converts 'columns' or 'index' to 0,1.  Mask basically'''
        if self.primaryaxis=='columns' or self.primaryaxis==0:
            return 0
        else:
            return 1

    def _getlabelarray(self, dataframe):
        ''' Conveience method to get label along working dimension of a dataframe.'''
        if self._primaryaxis==0:
            return np.asarray(dataframe.columns)
        else:
            return np.asarray(dataframe.index)

    def _df_change_fired(self):
        ''' set data iteratively column by column'''
        self.dataframe=DataFrame((np.random.randn(100,100)))

    def _df_new_fired(self):
        df2=DataFrame((np.random.randn(100,100)), columns=[i*5 for i in range(10)], index=[i*50 for i in range(10)])
        self.dataframe=df2
        self._draw_lines()
        
    def _re_bin_changed(self):
        ## Fix, squashing indicies
        #self.dataframe=rebin(self.dataframe, self.re_bin, axis=0, avg_fcn='mean')
        self.dataframe=rolling_mean(self.originaldata, self.re_bin)

    def _draw_lines(self):
        ''' Recasts plotdata and ties it to the plot object.'''
        for idx, name in enumerate(self.plotdata.list_data(as_strings=True)):
#            if idx % 50==0:
            self.plot.plot((self.indexname, name))        

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
        
        #indexlabels=[str(round(i,1)) for i in self.dataframe.index]

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
        return

    def _overwrite_plotdata(self):
        '''When a new instance of PandasPlotData is created, this overwrites the
        data source and updates the axis values.'''
        self.plotdata=PandasPlotData(dataframe=self.dataframe)
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
        Item('re_bin', style='simple'),
        #Include('sample_group'),
        #Include('axis_traits_group')
    )

    traits_view=View( Include('main_group') )
    
    

class WithShell(HasTraits):
    df=Instance(DataFrame)
    shell=Any()
    plot=Instance(PandasPlot)
    
    def __init__(self):
        self.df=DataFrame([1,2,3])
        self.plot=PandasPlot()
        self.plot.df=self.df
        
    def _df_changed(self):
        self.plot.df=self.df
        
        
    main_group=Group(
        Item('plot', show_label=False, style='custom'),
     #   Item('df_new'), Item('df_change'), 
        Item('shell', editor=ShellEditor(), style='simple'),
        #Include('sample_group'),
        #Include('axis_traits_group')
    )

    traits_view=View( Include('main_group'), resizable=True)

if __name__=='__main__':
    
  #  df=get_csvdataframe('spectra.pickle')
    df=DataFrame([1,2,3,4,5])


    ### THIS WILL INDUCE A FAILURE IN THE PLOT.PLOT call
 #   df=wavelength_slices(df, ranges=((350.0,370.0), (450.0,500.0), (550.0,570.0), (650.0,680.0), (680.0,700.0)),\
 #                           apply_fcn='simps')

    ### resample dataframe to be a bit less dense, makes plot changes more fluid ###
    
#    df=df.ix[300.0:800.0:5.0, 0:150:5]
 
    theplot=PandasPlot()   
    theplot.df=df   
    theplot.configure_traits()
    
#    test=WithShell()
#    test.df=df
#    test.configure_traits()
    

