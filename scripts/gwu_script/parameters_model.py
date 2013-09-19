''' Model for building correct parameters that will be assigned to timespectra
    in gwu_spec script.'''
from pyuvvis.exceptions import ParameterError, badkey_check
from pyuvvis.core.timespectra import Idic
import os.path as op

import logging
logger = logging.getLogger(__name__)

def _to_bool(attr, value):
    ''' Convert a value to bool.  If str is "true/false/none", converts.
        Useful since users may want to set iunit=None from cmdline, and argparse
        will yiled iunit="None" for example.'''

    if isinstance(value, basestring):
        if value.lower() == 'none':
            value = False
        elif value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
            
        else:
            raise ParameterError('Parameter must be true, false or None: %s'
                                 ' received %s' % value)            
    return bool(value)

class Parameters(object):
    ''' Defines timespectra scripting parameters. '''

    reference_default = 0
    specunit_default = 'nm'
    intvlunit_default = 's'
    uv_ranges_default = 8
    # or((430.0,450.0), (450.0,515.0), (515.0, 570.0),
    #(570.0,620.0), (620.0,680.0))
    
    t_start_default = None
    t_end_default = None 
    xmin_default = None
    xmax_default = None

    iunit_default = [None]
    sub_base_default = False
    
    valid_minmax_default = None #nm
    
    bline_fit_default = False
    fit_regions_default = None

    
    def __init__(self, **params):
        ''' Set defaults from either parameters or class defaults. '''
        
        self._params = params
        
        self.reference = self.loud_apply('reference', self.reference_default)
        try:
            self.reference = int(self.reference)
        except Exception:
            pass
        
        self.specunit = self.loud_apply('specunit', self.specunit_default)
        self.intvlunit = self.loud_apply('intvlunit', self.intvlunit_default)
        if self.intvlunit.lower() == 'none':
            self.intvlunit=None
        self.uv_ranges = self.loud_apply('uv_ranges', self.uv_ranges_default)
        
        self.t_start = self.loud_apply('t_start', self.t_start_default)
        self.t_end = self.loud_apply('t_end', self.t_end_default)

        # Slicing wavelengths (not sure how to handle times)
        self.x_min = self.loud_apply('x_min', self.xmin_default)
        self.x_max = self.loud_apply('x_max', self.xmax_default)
        
        # Float-convert slices (should be properties)
        if isinstance(self.x_min, basestring):
            if self.x_min.lower() == 'none':
                self.x_min = None
                
        if isinstance(self.x_max, basestring):
            if self.x_max.lower() == 'none':
                self.x_max = None                
                
        if self.x_min is not None:                    
            self.x_min = float(self.x_min)
        
        if self.x_max is not None:
            self.x_max = float(self.x_max)
            
        # Boolean defaults
        self.sub_base = self.loud_apply('sub_base', self.sub_base_default, boolean=True)       
        self.bline_fit = self.loud_apply('bline_fit', self.bline_fit_default, boolean=True)

        # Properties (don't use loud_apply)
        self.iunits = self._params.pop('iunits', self.iunit_default)
        self.fit_regions = self._params.pop('fit_regions', self.fit_regions_default)
        self.valid_minmax = self._params.pop('valid_minmax',
                                    self.valid_minmax_default)
        
        # Warn if unused self._params
        if self._params:
            name = self.__class__.__name__
            logger.critical("Unused parameters passed to %s: %s" % 
                        (name, self._params.keys()))
            
    @property
    def iunits(self):
        return self._iunits
        
    @iunits.setter
    def iunits(self, iunits):
        ''' Returns list of valid units (None, 'a', 'r') '''
        if not iunits:
            logger.warn('"iunits" parameter not found.  Setting to [None].  Only'
                        ' rawdata will be analyzed.')
            logger.debug("Converting 'iunits' from str to list")            
            self._iunits = [None]         
            return
        
        if not hasattr(iunits, '__iter__'):
            logger.debug("Converting 'iunits' list")
            iunits = iunits.split()
                
        # Make sure all outtypes (a, r, None) are valid; convert "None" to none
        for idx, otype in enumerate(iunits):
            if isinstance(otype, basestring):
                if otype.lower() == 'none':
                    logger.debug('Changing inuit="None" (str) to Nonetype')
                    iunits[idx] = None                    
            badkey_check(iunits[idx], Idic.keys())
 
        self._iunits = iunits         

        
    @property
    def fit_regions(self):
        return self._fit_regions
    
    # Probably best nto to set these through cmdline, as it's hard to ensure
    # proper type, but if must, this calls eval
    @fit_regions.setter
    def fit_regions(self, regions):
        if regions is None:
            self._fit_regions = regions
            return 
        
        if isinstance(regions, basestring):
            regions = eval(regions)
        if not hasattr(regions, '__iter__'):
            raise ParameterError('fit_regions must be an iterable of pairs: '
                                 'received %s' % (regions))
        self._fit_regions = regions

    @property
    def valid_minmax(self):
        return self._valid_minmax        
        
    @valid_minmax.setter
    def valid_minmax(self, minmax):
        if minmax is None:
            self._valid_minmax = None
            return 
        
        if isinstance(minmax, basestring):
            minmax = eval(minmax)
            
        if not hasattr(minmax, '__iter__'):
            raise ParameterError('fit_regions must be an iterable of pairs: '
                                 'received %s' % (minmax))
        
        if len(minmax) != 2:
            raise ParameterError('valid_minmax must be lenth two iterable IE '
                    '(560, 600).  Received: %s' % minmax)
  
        self._valid_minmax = minmax

    def loud_apply(self, attr, default, boolean=False):
        
        if self._params.has_key(attr):
            outval = self._params[attr]
            self._params.pop(attr)

        else:
            logger.debug('%s not found in user-supplied parameters. '  
            'Automatically setting to "%s"' % (attr, default))
            outval = default        

        if boolean:
            outval = _to_bool(attr, outval)
        
        return outval
    
    # Useful for methods calling params.items() (implement full dict interface later)
    def items(self):
        return [(attr, getattr(self, attr)) for attr in self.__dict__ 
                if attr != '_params']
            


class USB2000(Parameters):
    ''' Define some shared parameters between ocean optics spectrometers.'''
    
    # Change spectral parameter defaults in NM
    xmin_default = 430.0 
    xmax_default = 680.0
    valid_minmax_default = (339.0, 1024.0) #nm

    sub_base_default = True
    bline_fit_default = True
    fit_regions_default = ((345.0, 395.0), (900.0, 1000.0))
    
        
class USB650(Parameters):
    
    valid_minmax_default = (200.0, 850.0) #nm
    sub_base_default = True
    bline_fit_default = False
    
    # Set xmin/xmax?
        