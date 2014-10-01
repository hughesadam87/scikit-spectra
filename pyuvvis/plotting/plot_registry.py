import pyuvvis.plotting.basic_plots as bp
import pyuvvis.plotting.advanced_plots as ap
import pyuvvis.plotting.multiplots as mp


class PlotInfo(object):
    """Stores name, function, metadata and description for plot"""

    def __init__(self, name, function, is_3d, description=None):
        if not description:
            description = pfcn.__doc__
            
        self.name = name
        self.function = function
        self.is_3d = is_3d
        self.description = description
        

class PlotRegister(object):
    """ Basic storage class to track all various plot types in pyuvvis;
    simple relational mapper for operations like "return all 3D plots"
    """
    
    def __init__(self, *args, **kwargs):
        self.pnames = []
        self.pfcns = []
        self.is_3d = []
        
        
        
    def add(pname, pfcn, is_3d, description=None):
        if not description:
            description = pfcn.__doc__
            
        if pname not in 