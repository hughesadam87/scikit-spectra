import numpy as np

from chaco.api import AbstractPlotData, ArrayPlotData, Plot, ArrayDataSource
from traits.api import Dict, Instance, Str
from pandas import DataFrame

class PandasPlotData(AbstractPlotData):

    ''' Chaco requires a PlotData interface to manage plot/data mapping; however, pandas
    already is its own nice data handler, so this class mostly provides a wrapper that tries
    to be a hidden middle man.  As such, I try to make this PandasPlotData feel like a pandas
    dataframe.  It would be nice to have chaco communicate with a dataframe directly, but for now
    it must do so through this liason class.'''

    # The dataframe, column and row labels
    df = Instance(DataFrame)

    # Dict to store extra dataframes or series that aren't necessarily in the dataframe
    # Must pass
    extras=Dict()

    #Dictionary stores a string mapping of the data labels, which are not restricted to strings.
    #This allows users to get_data() with floats and chaco plots to access them with strings.

    # Dict mapping data series name to a mask array holding the selections
    selections = Dict()


    def __init__(self, dataframe, columnlabel='columns', indexlabel='index'):
        """PandasPlotData exposes a PlotData interface from a DataFrame.
        It is chosen that this object MUST be initialized with a dataframe.
           The intializer in ArrayPlotData will assign the names "seriesN" to
        any unlabeled selections passed into the program through the *data argument.
        Because dataframes are inherently labeled, this behavior is unnecessary 
        for basic use.

        indexlabel and columnlabel keywords let the user access the data stored in the rows/column
        labels in the dataframe when calling plot.  It is important that no columns or rows
        in the data share this name.

        Data is stored column-wise or row-wise depending on the choice of axis (0=column)."""
        
        super(AbstractPlotData, self).__init__() #AbstractPlotData has no __init__, but if that ever changes...        

        ### make traits or just leave as attributes? ###
        if len(dataframe.shape) > 2:
            raise NotImplementedError('Multidimensional dataframes of order 3 or higher \
	    are not supported by in PandasPlotData')
 
        self.columnlabel=columnlabel
        self.indexlabel=indexlabel
        
        event=self._add_dataframe(dataframe)
        self.data_changed = event        



    ### SHOULD JUST SUBCLASS ARRAY PLOT DATA
    def list_data(self, axis=0, as_strings=False):
        """ Returns a list of the names of the selections managed by this instance.  For convienence,
        axis can be 0,1 or the index label column label.
        """
        if axis==0 or axis==self.columnlabel:
            if as_strings:
                datalist=self._colmasks.keys()
            else:
                datalist=self._colmasks.values()

        elif axis==1 or axis==self.indexlabel:
            if as_strings:
                datalist=self._rowmasks.keys()
            else:
                datalist=self._rowmasks.values()

        return datalist



    def get_data(self, name):
        """ Attempts to return a name, which can be either from the dataframe, from the "extras" dict,
        or the column/index designators.  Trys them all systematically in the order dataframe, extras,
        column, row labels. """            
        try:
            return self.df[name].values
        except KeyError:
            try:
                return self.extras[name]
            except KeyError:
                try:
                    return self.df[self._colmasks[name]].values  #if name is str()
                except KeyError:
                    try:
                        self.extras[self._colmasks[name]].values
                    except KeyError: 
                        if name == self.columnlabel:
                            return self._colmasks.values()  
                        elif name == self.indexlabel:
                            return self._rowmasks.values()                                  

    def get_row_data(self, name):
        ''' Returns row data.  This is never used by plots, only a convienence method for users.'''
        return self.df.xs(name)

    def set_data(self, name, new_data):
        """ Sets the specified array as the value for either the specified
        name or a generated name.

        Implements AbstractPlotData.  
        THIS WILL ONLY SET ROW DATA IN A PANDA DATAFRAME OBJECT UNDER CURRENT SELECTION

        Parameters
        ----------
        name : string
            The name of the array whose value is to be set.
        new_data : array
            The array to set as the value of *name*.
        generate_name : Boolean
            I've eliminated this functionality for this datatype 

        Returns
        -------
        The name under which the array was set.
        """
        if not self.writable:
            return None

        if isinstance(new_data, list) or isinstance(new_data, tuple):
            new_data = np.array(new_data) #Convert to array data

        event = {}
        ### If entry is in data frame, change it
        try:
            self.df[name]=new_data
            event['changed']=[str(name)]
        except KeyError:
            self.df[self._colmasks[name]] = new_data    	    
            event['changed'] = [str(name)]  #Enforce strings, since DF names can be floats
                ### Else, add it to the "extras" array.
        self.data_changed = event       
        return name
    
    def update_dataframe(self, dataframe):
        ''' Changes dataframe in place assuming all new values are in here'''
        for column in dataframe.columns.values:
            self.set_data(column, dataframe[column])


    def set_dataframe(self, dataframe):
        ''' Completely reset plotdata with a new object.  This removes ALL 
        old data, does not cross check for overlapping keys.'''
        ### Remove old columns of dataframe ###
        removed={'removed':self._colmasks.keys()}
        ### Add new entries
        added=self._add_dataframe(dataframe)
        event=dict(added.items() + removed.items() )
        self.data_changed = event
               
    
    def _add_dataframe(self, dataframe):
        ''' Convienence function for set_dataframe to be called either by __init__
        or set_dataframe. Needed because can't evaluate self.df as a Bool() to 
        distinguish cases of initialization from overwriting dataframe.'''
        self.df=dataframe                
        self._colmasks=dict( ((str(val), val) for val in self.df.columns.values)) 
        self._rowmasks=dict( ((str(val), val) for val in self.df.index.values))
        return {'added':self._colmasks.keys()}
        

    ######## These are used by chaco to inform the plot that a certain region of data is selected

    def get_selection(self, name):
        """ Returns the selection for the given column name """
        return self.selections.get(name, None)

    def set_selection(self, name, selection):
        # Store the selection in a separate dict mapping name to its
        # selection array
        self.selections[name] = selection
        self.data_changed = True

if __name__=='__main__':
    df=DataFrame((np.random.randn(10,10)) ) 
    data=PandasPlotData(df)
    print data.df[0]
    df2=DataFrame((np.random.randn(10,10)) )
    data.set_dataframe(df2)
    print data.df[0]

