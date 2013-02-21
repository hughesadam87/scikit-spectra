import numpy as np
from chaco.api import AbstractPlotData
from traits.api import Dict, Instance, Str, Array, Enum
from collections import OrderedDict #Req python 2.7
from operator import itemgetter

### Imports for testing ###
from pandas import DataFrame

### ADD A MODIFYING FUNCTION THAT DISTINGUISHES BETWEEN DATAFRAME AND SERIES COLUMN GETTERS ###
class PandasPlotData(AbstractPlotData):

    ''' Chaco requires a PlotData interface to manage plot/data mapping; however, pandas
    already is its own nice data handler, so this class mostly provides a wrapper that tries
    to be a hidden middle man.  As such, I try to make this PandasPlotData feel like a pandas
    dataframe.  It would be nice to have chaco communicate with a dataframe directly, but for now
    it must do so through this liason class.'''

    # Dict to store extra dataframes or series that aren't necessarily in the dataframe
    # Must pass
    arrays=OrderedDict()  #Str(name): name, index, data
    
    #Define a dictionary called extras which stores array data that is not belonging to the dataframe 
    #But compliments it.  Helps separate dataframe data from additional data used in plot.  
    #Useful to put here, instead of its own arrayplotdata class because then a single plot can
    #access both types of data
    extras=OrderedDict()

    #Itemgetters for easier access to nested data in the arrays/extras dictionaries
    nameget=itemgetter(0)
    idxget=itemgetter(1)
    dataget=itemgetter(2)       
    
    #Stores labels in their own, special arrays, unmodified.  More useful in subclasses.
    primaryaxis=Enum(0, 1)
    primaryname=Str('columns')
    secondaryname=Str('index')
    _primarylabel=Array()   #Don't forget to convert list--array to remove Index object functioality
    _secondarylabel=Array()

    # Dict mapping data series name to a mask array holding the selections. (Untested)
    selections = Dict()

    def __init__(self, dataframe, extras=None, add_labels_to_extras=False, **kwtraits):
        """PandasPlotData exposes a PlotData interface from a DataFrame.
        It is chosen that this object MUST be initialized with a dataframe.

        This class is intentionally constructed to imitate a dataframe.  Therefore,
        it is built to accept new dataframes instead of adding or removing columns.
        If a dataframe is modified in place such that its primary axis label is unchanged,
        then changes are overwritten with set_data.
        
        An additional trait called "extras" behaves more like an arrayplotdata container, meaning
        data can be added at will.  Therefore, persistence between the actual dataframe and the
        psuedo dataframe (arrays) maintained by this class is emulated.
        
        This class allows users to call get_data using non-sring names, but ensures that plotting
        programs can call by strings without any problem.  
        
        Once the primary data axis is passed in instantiation, the orientation if fixed and can't be 
        flipped at another time.
        
        If **add_labels_to_extras, this will automatically store row/column labels as data arrays.
        This is useful if these axis contain numerical data that needs to be plotted.
        """

        super(PandasPlotData, self).__init__(**kwtraits) #Trait initialization 
        if len(dataframe.shape) > 2:
            raise NotImplementedError('Multidimensional dataframes of order 3 or higher \
	    are not supported by in PandasPlotData')
        
        if extras:
            if len(extras.shape) > 2:
                raise NotImplementedError('Multidimensional dataframes of order 3 or higher \
                are not supported by in PandasPlotData')            
        
        if self.primaryaxis == 0:
            pass
        elif self.primaryaxis == 1:
            dataframe=dataframe.transpose()
            if extras:
                extras.transpose()
        else:
            raise(AttributeError('Attribute "primaryaxis" must be 0, 1 but %s was passed'%axis))
              
        self.arrays=self._set_arrays(dataframe)
        event={'added':self.arrays.keys()}  
        if extras:
            self.extras=self._set_arrays(extras)
            event['added'].extend(self.extras.keys())
            
        self.data_changed = event        

        ### Store label array separately and write to extras if desired
        self._primarylabel=np.asarray(list(dataframe.columns))  
        self._secondarylabel=np.asarray(list(dataframe.index))
        if add_labels_to_extras:
            self.set_extra(self.primaryname, self._primarylabel)
            self.set_extra(self.secondaryname, self._secondarylabel)


    #------------------------------------------------------------------------
    # Dictionary Interface that lets me treat the PandasPlotData object like
    # a dictionary.  Aka can do print pandasplotdata['array1'] instead of 
    # pandasplotdata.get_data('array1')
    #------------------------------------------------------------------------

    def __getitem__(self, name):
        return self.get_data(name)

    #Not sure I want to use the set/del in the dictionary interface until I 
    #know the best way to distinguish between extras and arrays in these respects.
    def __setitem__(self, name, value):
        raise NotImplemented
        #return self.set_extra(name, value)

    def __delitem__(self, name):
        raise NotImplemented        
        #return self.del_data(name)
    

    def list_data(self, as_strings=False):
        """ Returns a list of the names of the selections managed by this instance.  For convienence,
        axis can be 0,1 or the index label column label.
        """
        if as_strings:
            return self.arrays.keys()
        else:
            return [self.nameget(val) for val in self.arrays.values()]


    def get_data(self, name):
        """ Returns the array associated with *name*.  First checks self.arrays,
        then checks self.extras.  """
        try:
            value=self.arrays[str(name)]
        except KeyError:
            try:
                value=self.extras[str(name)]            
            except KeyError:
                return None
                
        return self.dataget(value) #Return array data

    def del_data(self, name):
        """ Deletes the array specified by *name*, or raises a KeyError if
        the named array does not exist.
        """
        raise NotImplementedError('Do I want to delete data from a dataframe?')
        #try:
            #del self.arrays[str(name)]
        #except KeyError:
            #raise KeyError("Data series '%s' does not exist." % name)
                                

    def set_data(self, name, new_data):
        """ Takes in name/array data similar to arrayplotdata.  Unlike arrayplotdata,
        this never adds values to the self.arrays.  Unlike arrayplotdata, this is not
        willing to accept new entries.  It is up to the Plot object pass in the correct
        data.
        """
        if not self.writable:
            return None

        if isinstance(new_data, list) or isinstance(new_data, tuple):
            new_data = np.array(new_data) #Convert to array data

        event = {}
        
        ### If entry is in data frame, change it.  Doesn not allow for addition 
        ### to mimic behavior of dataframe (eg user should change dataframe and replot).

        try:
            self.arrays[str(name)]=(name, len(self.extras)+1, new_data)  #Overwrite whole entry
            event['changed']=[str(name)]
        except KeyError:
            raise KeyError('%s does not exist in PandasPlotData dataframe.  Add to extras if you \
            do not wish to modify the dataframe.'%name)
                   
        self.data_changed = event       
        return name
    
    def set_extra(self, name, new_data):
        """ Works like arrayplotdata.  Lets the user set extra data, which can be changed or added,
        unlike set_data which maintains the data in the dataframe at all times.
        """
        if not self.writable:
            return None

        if isinstance(new_data, list) or isinstance(new_data, tuple):
            new_data = np.array(new_data) #Convert to array data

        event = {}
        ### If entry is in data frame, change it
        try:
            self.arrays[str(name)][2]=new_data
            event['changed']=[str(name)]
        except KeyError:
            self.extras[str(name)]=(name, len(self.extras)+1, new_data) 	    
            event['added'] = [str(name)]  

        self.data_changed = event       
        return name    
    
    def update_dataframe(self, dataframe):
        ''' Wrapper for set_data to take in an entire dataframe.'''
        for column in np.asarray(dataframe.columns):
            self.set_data(column, np.asarray(dataframe[column]) )
            
    def update_extras(self, dataframe):
        ''' Wrapper for set_data to take in an entire dataframe.'''
        for column in np.asarray(dataframe.columns):
            self.set_extra(column, np.asarray(dataframe[column]))    


    #### Deprecated method that updates the dataframe in place.  For usecases, it is better to
    #### just rerun this object than overwrite the whole dataframe.
    #def set_dataframe(self, dataframe):
        #''' Completely reset plotdata with a new object.  This removes ALL 
        #old data, does not cross check for overlapping keys.'''
        #### Remove old columns of dataframe ###
        #removed={'removed':self.arrays.keys()}
        #### Add new entries
        #self._set_arrays(dataframe)
        #added={'added':self.arrays.keys()}        
        #event=dict(added.items() + removed.items() )
        #self.data_changed = event
               
    
    def _set_arrays(self, dataframe):
        ''' Sets the array dictionary, preserving sort order.'''
        return OrderedDict( (str(name),(name, idx, np.asarray(dataframe[name]) ))\
                               for idx, name in enumerate(np.asarray(dataframe.columns) ) )
        
    def _get_indicies(self, *names):
        ''' Takes in a list of names and returns indicies corresponding to.  Useful for label
        mappers.'''
        return [self.idxget(str(name)) for name in names]

    ######## These are used by chaco to inform the plot that a certain region of data is selected

    def get_selection(self, name):
        """ Returns the selection for the given column name """
        return self.selections.get(name, None)

    def set_selection(self, name, selection):
        # Store the selection in a separate dict mapping name to its
        # selection array
        self.selections[name] = selection
        self.data_changed = True
