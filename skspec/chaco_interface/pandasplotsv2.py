### Enthought tool suite imports 
from traits.api import Instance, Str, Enum, Range, HasTraits, Button, Enum, Property, Bool, Any, on_trait_change
from traitsui.api import Item, View, HGroup, VGroup, Group, Include, ShellEditor
from enable.api import ComponentEditor
from chaco.api import LabelAxis, Plot, ToolbarPlot, PlotAxis, LinearMapper, ArrayDataSource, DataRange1D
from chaco.tools.api import BetterSelectingZoom, PanTool
from random import randint
from copy import deepcopy
from pandas import DataFrame

from chaco.tools.api import RangeSelection, RangeSelectionOverlay

### For testing 
import numpy as np
from time import sleep

### For skspec imports
#from skspec import get_csvdf
#from skspec import wavelength_slices
#from skspec import datetime_convert
from pandas.stats.moments import rolling_mean

### Local import 
from pandasplotdatav3 import PandasPlotData


class DefaultEnum(Enum):
    ''' Enum trait with default value.'''
    def __init__(self, *args, **kwds):
        super(DefaultEnum, self).__init__(*args, **kwds)
        if 'default' in kwds:
            self.default_value = kwds['default']


### Add a method to relable rows/columns in place?
class PandasPlot(HasTraits):
    '''Plot to interface a pandas df'''


    ### For testing
    rnd_cols=Bool(False)
    samecols=Bool(False)
    transpose=Bool(False)

    ### Traits of the actual plot and plotdatasource handler ###
    _dffull=Instance(DataFrame)  #Any?    
    plot=Instance(Plot)  
    plotdata=Instance(PandasPlotData) #Data stored at any given time in the plot
    df=Instance(DataFrame)  


    ### Axis traits    
    idxname=Str('Index')
    colname=Str('Column')
    idxorient=DefaultEnum('top', 'bottom', 'left', 'right', default='bottom')
    colorient=DefaultEnum('top', 'bottom', 'left', 'right', default='top')
    selection_axis=DefaultEnum('index','value', default='index') #Which axis does selection tool sample

    ### Aesthetic traits
    title=Str('Title') #Defaults from df name
    linecolor=Str('yellow')
    pointcolor=Str('red')
    linestyle=Enum('line', 'scatter', 'both')
    markersize=Range(low=1, high=5)
    
    sampling=Range(low=0.0, high=100., value=100.0)
    _spacing=Property(depends_on='sampling')



    ### _Event Handlers
    
    def _rnd_cols_changed(self):

        x=np.linspace(0, 100, 100) #Index generator
        y=np.linspace(0, 100, 100) #Column generator

        scale=randint(1,1000)        

        self.df=DataFrame((np.random.rand(len(x),len(y))), columns=(scale/2.0)*y, index=scale*x)


    def _samecols_changed(self):    
        self.df=DataFrame((np.random.rand(100,100)))

    def _transpose_changed(self):
        self.df=self.df.transpose()

    ### Axis Aesthetics
    @on_trait_change('idxname','idxcolumn', 'idxorient', 'colorient')
    def _axis_changed(self, trait, new):
        '''Change plot axis name or orientation'''
        setattr(self, trait, new)
        self._update_axis()
        self.plot.request_redraw() #Necessary but how do I only call axis redraw?
        
    def _title_changed(self, old, new):
        if old != new:
            self.plot.title=new
            self.plot.request_redraw() #HOW TO PREVENT COLLISION WITH TOP OVERLAY
        
    def _selection_axis_changed(self, old, new):
        if old != new:
            self._update_lines()



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
                self.title=new.name   #Turn into a "transfer" method where I pass list of attributes i want look for
            except AttributeError:
                pass

            ### Draw barebones of plot
            self._plot_default()
            self._update_lines()           


        ### Decide to update columns or completely redraw df.  
        else:
            changed=self.plotdata.set_df(new)

            ### If 'event changed', don't bother updaing lines
            if not changed:
                self._update_lines()
    
    ### Plot spacing
    
    def _get__spacing(self):
        '''Integer spacing given % sampling'''
        samp=self.sampling/100.0
        colsize=df.shape[0]
        return colsize - int(round( colsize*samp, 0))
    
    def _sampling_changed(self, old, new):
        if old != new:                 
            self._update_samples()
                
    def _update_samples(self):
        '''Updates the list of line plots shown or hidden based on plot sampling.'''
        if self._spacing==0:
            return           

        ### Hide all plots
        to_hide=self.plot.plots.keys()
        self.plot.hideplot(*to_hide)   
        
        ### Show only plots in samples        
        to_show=self.plot.plots.keys()[::self._spacing]
        self.plot.showplot(*to_show)
        self.plot.request_redraw()
                
    def _update_rangeselect(self):
        ''' Overwrites range selection tool in current plot.'''
           
        #### Remove current overlay
        self.plot.overlays=[obj for obj in self.plot.overlays if not isinstance(obj, RangeSelectionOverlay)]
            
        mycomp=self.plot.plots.itervalues().next()[0] #Quick wayt to get first value in dictionary
        
        inds=range(len(self.df.index))
        idx=ArrayDataSource(inds)
        vals=ArrayDataSource(df.index.values)
        
        index_range = DataRange1D(idx)        
        val_range=DataRange1D(vals)
        imap=LinearMapper(range=index_range)#,stretch_data=self.index_mapper.stretch_data)     
        vmap=LinearMapper(range=val_range)
     #   mycomp.index_range.refresh()
        
        mycomp.index_mapper=imap        
        mycomp.value_mapper=vmap
        
        self.rangeselect=RangeSelection(mycomp, axis=self.selection_axis)
        self.plot.active_tool = self.rangeselect
        self.plot.overlays.append(RangeSelectionOverlay(component=mycomp)) 
        self.rangeselect.on_trait_change(self.on_selection_changed, "selection")
                

    def _update_lines(self):
        ''' Redraws lines, plots and reapplies line selection.'''


        oldplots=self.plot.plots.keys()
        newplots=[name for name in self.plotdata.list_data(as_strings=True)]

        to_remove=[p for p in oldplots if p not in newplots]
        to_add=[p for p in newplots if p not in oldplots]

        if to_remove:
            for p in to_remove:
                self.plot.delplot(p)
                
        if to_add:
            for name in to_add:
                self.plot.plot(('index', name), name=name, color=self.linecolor)
                                      
        self._update_axis()
        self._update_samples()
        self._update_rangeselect()

    def on_selection_changed(self, selection):
        if selection != None:
            self.rangeXMin, self.rangeXMax = selection    
            print selection


    def _update_axis(self):    
        ''' Forces a label axis onto the plot. '''

        print 'updaing axis', self.idxname

        indexlabels=[str(round(i,1)) for i in self.df.index]
        columnlabels=[str(round(i,1)) for i in self.df.columns]


        index_axis=LabelAxis(self.plot, orientation=self.idxorient, 
                             positions=range(int(float(indexlabels[0])),
                                             int(float(indexlabels[-1]))), 

                             labels=indexlabels,#, resizable='hv',
                             title=self.idxname)



        col_axis=LabelAxis(self.plot, orientation=self.colorient, 
                           positions=range(int(float(columnlabels[0])),
                                           int(float(columnlabels[-1]))), 


                           labels=columnlabels,#, resizable='hv',
                           title=self.colname)        

        ### Remove underlays              
        self.plot.underlays=[obj for obj in self.plot.underlays if not isinstance(obj, PlotAxis)]
        self.plot.underlays=[obj for obj in self.plot.underlays if not isinstance(obj, LabelAxis)]

        self.plot.underlays.append(index_axis)
        self.plot.underlays.append(col_axis)



    def _plot_default(self, toolbar=True, **pltkwds):
        ''' Draw bare plot, including main plotting area, toolbar, etc...
         either at initialization or global redo'''      
        
        if toolbar:
            self.plot=ToolbarPlot(self.plotdata, **pltkwds)
        else:
            self.plot=Plot(self.plotdata, **pltkwds)

        self.plot.title = self.title
        self.plot.padding = 50
        self.plot.legend.visible=False

        self.plot.tools.append(PanTool(self.plot))
        zoom=BetterSelectingZoom(component=self.plot, tool_mode="box", always_on=False)
        self.plot.overlays.append(zoom)
        
    def _overwrite_plotdata(self):
        '''When a new instance of PandasPlotData is created, this overwrites the
        data source and updates the axis values.'''
        self.plotdata=PandasPlotData(df=self.df)
        self._plot_default() #CAN THIS JUST DRAW LINES


    ### Traits View

    main_group=Group(
        HGroup(Item('rnd_cols'), Item('samecols'), Item('transpose'),),
        Item('plot', editor=ComponentEditor(), show_label=False),
        Item('idxname'), Item('idxorient'), Item('selection_axis'), Item('title'),
        Item('sampling'),
        
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
#        self.df=DataFrame([1,2,3])
        self.pandasplot=PandasPlot()
#        self.pandasplot.df=self.df

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

#    test=PandasPlot()   

    test=WithShell()
    test.df=DataFrame((np.random.rand(100,100)))

#    for i in range(1000):
#        test.df=df
    #idx=list('abcdefghij')
    #test.df=DataFrame((np.random.rand(10,10)), index=idx)
    test.configure_traits()

