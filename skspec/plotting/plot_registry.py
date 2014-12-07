_DESCRIPTION_CHARS = 40 #Max number of characters to format in description

class RegisterError(Exception):
    """ """

class PlotInfo(object):
    """Stores key, function, metadata and description for plot"""

    def __init__(self, key, function, is_3d, description=None):
            
        self.key = key
        self.function = function

        # Track module for each function
        self._module = function.__module__
        
        if not isinstance(is_3d, bool):
            raise AttributeError('is_3d must be True or False, got %s' % is_3d)
        self.is_3d = is_3d

        if not description:
            description = function.__doc__        
        self.description = description
        
    def __repr__(self):
        description = self.description
        if len(description) > _DESCRIPTION_CHARS:
            description = description[0:10] + '...'
        return '\t'.join([str(self.key),
                          self.function.__name__ + '()', 
                          str(self.is_3d), 
                          description])

    def __shortrepr__(self):
        """ Short representaiton, substitue for __repr__() """
        description = self.description
        if len(description) > _DESCRIPTION_CHARS:
            description = description[0:10] + '...'
        return '\t'.join([str(self.key),description])


class PlotRegister(object):
    """ Basic storage class to track all various plot types in skspec;
    simple relational mapper for operations like "return all 3D plots.
    
    Notes:
    ------
    
    Need to be able to parse plots in Spectra.plot() and also in widget notebooks.
    As plotting gets more involved, this will become more useful.
    """
    
    def __init__(self, plots={}):
        for p in plots:
            if not isinstance(PlotInfo):
                raise RegisterError('All plots in registry must be PlotInfo object')
        self.plotdict = dict((p.key, p) for p in plots)

    @property
    def plots(self):
        plots = self.plotdict.values()
        return sorted(plots, key=lambda x: x.key)
        
    @property
    def keys(self):
        return sorted(self.plotdict.keys()) 

    @property
    def functions(self):
        return sorted([p.function for p in self.plots])
    
    #@property
    #def is_3d(self):
        #return sorted([p.is_3d for p in self.plots]) 
    
    def is_3d(self, kind):
        """ Is this kind a 3d plot """
        return self.plotdict[kind].is_3d
    
    def is_2d(self, kind):
        """ Is this a 2d plot (contour)"""
        if kind in ['contour']:
            return True
        return False
    
    def is_2d_3d(self, kind):
        """ Is 3d or contour/other mesh plots?"""
        if self.is_2d(kind) or self.is_3d(kind):
            return True
        return False
    
    @property
    def descriptions(self):
        return sorted([p.description for p in self.plots])   
    
    def add(self, *args, **kwargs):
        """ Passed to PlotInfo"""
        pout = PlotInfo(*args, **kwargs)
        self.plotdict[pout.key] = pout   
    
    @property
    def plots_3d(self):
        """ Return plot names that are 3D; for created 3d axes mostly """
        out = []
        for p in self.plots:
            if p.is_3d:
                out.append(p.key)
        return out

    @property
    def plots_2d_3d(self):
        """ All 3d plots + contour"""
        return self.plots_3d + ['contour']
    
    #Dict Interface / Magic
    def __getitem__(self, key):
        return self.plotdict.__getitem__(key)
        
    def __delitem__(self, key):
        return self.plotdict.__delitem__(key)
    
    def __setitem__(self, key, value):
        return self.plotdict.__setitem__(key, value)    

    def items(self):
        return self.plotdict.items()

    def keys(self):
        return self.plotdict.keys()
    
    def values(self):
        return self.plotdict.values() 

    def __repr__(self):
        # MAKE ACTUAL COLUMNS
        out = '\t'.join(['KIND', 'FUNCTION', '3D', 'DESCRIPTION'])
        out += '\n------------------------------------------'
        out += '\n\n'
        out += '\n'.join([v.__repr__() for v in self.plots])
        return out    
    

    def __shortrepr__(self):
        # MAKE ACTUAL COLUMNS
        out = '\t'.join(['KIND', 'DESCRIPTION'])
        out += '\n----------------'
        out += '\n\n'
        out += '\n'.join([v.__shortrepr__() for v in self.plots])
        return out    
    
