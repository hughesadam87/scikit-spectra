import numpy as np
from chaco.api import AbstractPlotData
from traits.api import Any, Dict, Tuple
import collections

import time #testing

class PandasPlotData(AbstractPlotData):

    ''' Chaco requires a PlotData interface to manage plot/data mapping; however, pandas
    already is its own nice data handler, so this class mostly provides a wrapper that tries
    to be a hidden middle man.  As such, I try to make this PandasPlotData feel like a pandas
    df.  It would be nice to have chaco communicate with a df directly, but for now
    it must do so through this liason class.'''

    df=Any()
    
    # Used to store actual column values and string representation
    _colmap=Dict()
    _extras=Dict()
    _reserved=Tuple('index', 'columns')
    
    # Dict mapping data series name to a mask array holding the selections
    selections = Dict()    
    
     

    def __init__(self, df, extras=None, **kwtraits):
        """PandasPlotData exposes a PlotData interface from a df.
        It is chosen that this object MUST be initialized with a df.
        """

        super(PandasPlotData, self).__init__(**kwtraits) #Trait initialization 
        
        if len(df.shape) > 2:
            raise NotImplementedError('Multidimensional dfs of order 3 or higher \
	    are not supported by in PandasPlotData') #Do 1d arrays work?
        
        self.set_df(df)

    #------------------------------------------------------------------------
    # Dictionary Interface to PandasPlot Data
    #------------------------------------------------------------------------

    def __getitem__(self, name):
        return self.df[name]

    def __setitem__(self, name, value):
        raise NotImplemented
        
    def __delitem__(self, name):
        raise NotImplemented           

    def list_data(self, as_strings=False):
        """ Returns a list of the names of the selections managed by this instance. 
 
            as_strings: If true, names are converted to strings.  Useful for passing 
                        directly into getdata in which strings are stored.
        """
        if self.df is None:
            return []        
        if as_strings:
            return [str(col) for col in self.df.columns]
        else:
            return list(self.df.columns.values)

    def get_data(self, name):
        ''' Must be called via string name because Plot() enforces that all stored
            datasources are accessed via string!.'''
        
        

        
        ### If not a string, immediately return dataframe value
        if not isinstance(name, basestring):
            return self.df[name].values


        else:

            ### Should do test for reserved names to avoid conflicts here
            if name=='index':
                return self.df.index.values
            
            elif name=='columns':
                return self.df.columns.values            
            
            ### Try to get value from stringmap to dataframe columns
            try:
                return self.df[self._colmap[name]].values
            except KeyError:
                pass
            
            ### Try to get value from extras 
            try:
                return self._extras[name]
            except KeyError:
                raise AttributeError('%s not found in pandasplotdata.  Please check list_data() for valid entries.'%name)
        
                
            
    def del_data(self, name):
        """ Deletes the array specified by *name*, or raises a KeyError if
        the named array does not exist.
        """
        raise NotImplementedError('Do I want to delete data from a df?')
                                


    ### SHOULD TIME TEST TO SEE HOW LONG IS TAKES
    def set_data(self, name, new_data):
        """ Takes in name/array data similar to arrayplotdata.  Unlike arrayplotdata,
        this never adds values to the self.arrays.  Unlike arrayplotdata, this is not
        willing to accept new entries.  It is up to the Plot object pass in the correct
        data.
        """
        if not self.writable:
            return None

        try:
            new_data = np.array(new_data) #Convert to array data
        except Exception:
            raise Exception('set_data failed to convert type %s data to array'%type(new_data))

                
        if not isinstance(name, basestring):
            raise TypeError('set_data() can only accept string keys.')
                
        
        if name in self._stringmap:
            raise AttributeError('%s cannot correspond to a string name already present in \
                                  in the underlying dataframe.'%name)
            
        if name in self._reserved:
            raise NameError('%s conflicts with pandasplotdata reserved names: "%s"'%(name, ','.join(self._reserved)))
 
                   
        if name in self._extras:
            self.data_changed = {'changed':[name]}       
        else:
            self.data_changed = {'added':[name]}       

        self._extras[name]=new_data

        return name #THIS MUST BE HERE (why?)

    
    def set_df(self, dfnew):
        ''' Set an entirely new dataframe.  Calls _set_df() to handle event changes.  
            Returns T/F to let plot know if event was "changed" vs. added or removed.
            _set_df() prevents mixed events of changed + added/removed.'''
        
        event=self._set_df(dfnew)
        event2=self._reset_extras()

        if event2:
            event.update(event2)
            
        self.data_changed=event
        
        if event.has_key('changed'): #Changed will be the only call.
            return True
        return False
    
           
    def _set_df(self, dfnew):
        ''' Handles add/remove/change events for a new dataframe.'''
        
        event={}
        
        ### If self.df not initialized, add all entries
        if isinstance(self.df, type(None)):
            pass
    
        else:
            ### If only column names are changing, trigger change event and exit
            if np.array_equal(dfnew.columns.values, self.df.columns.values): #very fast operation
                self.df=dfnew
                event['changed']=self._colmap.keys()
                return event
                
            else:
                ### Remove old columns
                event['removed']=self._colmap.keys()

        ### Add new columns/update self.df
        event.update(self._add_df(dfnew))  
            
        return event 
        
        ### MORE COMPLEX VERSION ANY FASTER? ###
#        if not np.array_equal(dfnew.columns.values, self.df.columns.values):
    ##        raise IOError('set_df may only be called for objects of identical columns.')
            #event={'removed':self._colmap.keys()}
            #event['added']=dfnew.columns.values
    
        
        #else:
            #self.df=dfnew
            #event = {'changed':dfnew.columns.values}       
           
        #self.data_changed=event         
        
    def _reset_extras(self):
        if self._extras:
            return {'removed':self._extras.keys()}
        
    def _add_df(self, dfnew):
        ''' Add all columns of new df, update colmap, set self.df'''
        self._colmap=dict((str(c), c) for c in dfnew.columns.values)        
        self.df=dfnew        
        return {'added':self._colmap.keys()}
                   
    def _get_indicies(self, *names):
        ''' Takes in a list of names and returns indicies corresponding to.  Useful for label
        mappers.'''
        raise NotImplemented
#        return [self.idxget(str(name)) for name in names]

    ### These are used by chaco to inform the plot that a certain region of data is selected
    def get_selection(self, name):
        """ Returns the selection for the given column name """
        print 'hi being selected in plotdata'
        return self.selections.get(name, None)

    def set_selection(self, name, selection):
        # Store the selection in a separate dict mapping name to its
        # selection array
        self.selections[name] = selection
        self.data_changed = True
