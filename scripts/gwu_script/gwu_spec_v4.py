''' GWU in-house script for dataanalysis of fiberoptic probe data.'''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2013, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

import os
import os.path as op
import time
import shutil
import sys
import imp
import shlex
import collections 
import logging
from argparse import ArgumentParser

import matplotlib.pyplot as plt
import numpy as np

# ASBOLUTE IMPORTS
from pyuvvis.pyplots.basic_plots import specplot, areaplot, absplot, range_timeplot
from pyuvvis.pyplots.advanced_plots import spec_surface3d, surf3d, spec_poly3d, plot2d, plot3d
from pyuvvis.core.spec_labeltools import datetime_convert, spec_slice
from pyuvvis.core.utilities import boxcar, countNaN
from pyuvvis.core.baseline import dynamic_baseline
from pyuvvis.pyplots.plot_utils import _df_colormapper, cmget
from pyuvvis.IO.gwu_interfaces import from_timefile_datafile, from_spec_files
from pyuvvis.core.imk_utils import get_files_in_dir, make_root_dir, get_shortname
from pyuvvis.core.baseline import dynamic_baseline
from pyuvvis.core.corr import ca2d, make_ref, sync_3d, async_3d
from pyuvvis.core.timespectra import Idic
from pyuvvis.pandas_utils.metadframe import mload, mloads
from pyuvvis.exceptions import badkey_check, ParserError

# Import some spectrometer configurations
from usb_2000 import params as p2000
from usb_650 import params as p650

logger = logging.getLogger(__name__)
from pyuvvis.logger import log, configure_logger

DEF_CFIG = p2000
DEF_inroot = './scriptinput'
DEF_outroot = './output'

# Do extra namespace parsing manually (This could be an action, if sure that it will
# be called after CfigAction (which generates parms based on cfig)
def _parse_params(namespace):
    ''' Spectra parameters in form "xmin=400" are formatted into a dictionary 
        inplace on namespace object.'''

    if not namespace.params:
        return 
    
    try:
        kwargs = dict (zip( [x.split('=', 1 )[0] for x in namespace.params],
                            [x.split('=', 1)[1] for x in namespace.params] ) )

    except Exception:
        raise IOError('Please enter keyword args in form: x=y')

    invalid = []
    for key in kwargs:
        if key in namespace.params:
            namespace.params[key] = kwargs[key]
        else:
            invalid.append(key)
    if invalid:
        raise IOError('Parameter(s) "%s" not understood.  Valid parameters:' 
        '\n   %s' % ('","'.join(invalid), '\n   '.join(params.keys()) ) )


class AddUnderscore(argparse.Action):
    ''' Adds an underscore to end of value (used in "rootname") '''
    def __call__(self, parser, namespace, values, option_string=None):
        if values != '':
            values += '_'
        setattr(namespace, self.dest, values)
        

class CfigAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):

        cfig = values.lower()
        
        # Use p650, p2000 files
        if cfig in ['usb650', '650']:
            setattr(namespace, self.dest, p650)
            return                    
 
        elif cfig in ['usb2000', '2000']:
            setattr(namespace, self.dest, p2000)
            return 

        # Import "params" directly from a file        
        else:

            cfig = op.abspath(cfig)
            basename = op.basename(cfig)         
                    
            # Ensure path/file exists
            if not op.exists(cfig):
                raise IOError('Cannot find config filepath: "%s"' % cfig)
        
            # Split.py extension (Needed for imp.fine_module() to work correctly
            cbase, ext = op.splitext(cfig)
            if ext != '.py':
                raise IOError('%s must be a .py file: %s' % basename)
                    
            sys.path.append( op.dirname( cfig ) )

            try:
                cbase=basename.split('.py')[0]  
                cfile=imp.load_source(cbase, cfig)
            except Exception as E:
                raise Exception('Could not import config file "%s". '
                        'The following was returned: %s'%(basename,E))

            # Try to load parameters from cfile.params
            try:
                params = cfile.params
            except AttributeError:
                raise AttributeError('Cannot find "params" dictionary in config file, %s'%basename)
    
            setattr(namespace, self.dest, params)
            return 

#logify?
class Controller(object):
    ''' '''

    # Default configuration parameters        
    img_ignore=['png', 'jpeg', 'tif', 'bmp', 'ipynb'] 
    
    # For now, this only takes in a namespace, but could make more flexible in future
    def __init__(self, **kwargs):
        
        # These should go through the setters
        self.inroot = kwargs.pop('inroot', None)
        self.outroot = kwargs.pop('outroot', None)
        self.params = kwargs.pop('params', None)
        
        self.clean = kwargs.pop('clean', False)
        self.rname = kwargs.pop('rname', '')
        self.dryrun = kwargs.pop('dryrun', False) 
        self.overwrite = kwargs.pop('overwrite', False)
        

        # Configure logger
        verbosity = kwargs.pop('verbosity', 'warning')
        trace = kwargs.pop('trace', False)

        # Does this conflict w/ sys.argv configure_logger stuff?                           
        configure_logger(screen_level=verbosity, name = __name__,
                         logfile=op.join(self._outroot, 'Runlog.txt')) 

    @property
    def inroot(self):
        if not self._inroot:
            raise AttributeError('Root indirectory not set')
        return self._inroot #Abspath applied in setter

    
    @setter
    def inroot(self, value):
        ''' Ensure inpath exists before setting'''
        if value is None:
            self._inroot = None
        else:
            inpath = op.abspath(value)
            if not op.exists(inpath):
                raise IOError('Inroot path does not exist: %s' % inpath)
            self._inroot = inpath
        
        
    @property
    def outroot(self):
        if not self._outroot:
            raise AttributeError('Root outdirectory not set')
        return self._outroot
        

    @setter
    def outroot(self, value):
        if value is None:
            self._outroot = None
        else:
            self._outroot = op.abspath(value)
        

    @property
    def params(self):
        if not self._params:
            raise AttributeError('Spec parameters not set')
        return self._params
    
    
    @setter
    def params(self, params):
        if params is None:
            self._params = params
            return 
        
        if not isinstance(dict, params):
            raise AttributeError('"params" must be dict but is %s' % str(type(params)))
 
        if params.has_key('outtypes'):
            for otype in params['outtypes']:
                badkey_check(otype, Idic.keys())
        else:
            logger.warn('"outtypes" parameter not found.  Setting to None.  Only'
                        ' rawdata will be analyzed.')
            params['outtypes'] = None  
         self._params = params   
        

    # Public methods
    def output_params(outname='run_parameters'):
        with open(op.join(outroot, outname), 'w') as f:
            f.write('Run Parameters')
            for key in params:
                 f.write('\n%s\t%s'%(key, params[key]))    

    @classmethod
    def from_namespace(cls, args=None):
        ''' Create Controller from argparse instance. '''
        
        if args:
            if isinstance(args, basestring):
                args=shlex.split(args)
            sys.argv = args               
        
        
        parser = ArgumentParser('GWUSPEC', description='GWU PyUvVis fiber data '
        'analysis.', epilog='Additional help not found')

        # Global options
        parser.add_argument('inroot', metavar='in-directory', action='store', default=DEF_inroot, 
                          help='Path to root directory where file FOLDERS are '
                          'located.  Defaults to %s' % DEF_inroot)
        
        parser.add_argument('outroot', metavar='out-directory', action='store', default = DEF_outroot,  
                          help = 'Path to root output directory.  Defaults to %s'
                          % DEF_outroot) 
    
        parser.add_argument('-r', '--runname', action=TweakRname,
                          dest='rname', default='', #None causes errors
                          help='Title of trial/run, used in filenames and other places.',)     
        
        parser.add_argument('-c', '--config', dest='cfig', default=DEF_CFIG, action=CfigAction,
                          help='usb650, usb2000, or path to parameter configuration file.  '
                          'defaults to usb2000' #Set by CFIGDEF
                          )
        
        parser.add_argument('--overwrite', action='store_true', dest='ow',
                            help='Overwrite contents of output directory if '
                            'it already exists')
        
    
        parser.add_argument('--clean', action='store_true', dest='clean',
                          help='This will clean and overwrite files found in the' 
                          ' outrootectory before writing new results.  CAUTTION: '
                          'deletes ALL files in outrootectory.')
        
        parser.add_argument('-v', '--verbosity', help='Set screen logging '
                       'level.  If no argument, defaults to info.',
                        default='warning', const='info', metavar='VERBOSITY',)

        
        parser.add_argument('-t', '--trace', action='store_true', dest='trace',
                          help='Show traceback upon errors')   
                
        parser.add_argument('--params', nargs='*', help='Overwrite config parameters'
                            ' manually in form k="value str".'  
                            'Ex: --params xmin=440.0 xmax=700.0')
    
        parser.add_argument('--dryrun', dest='dry', action='store_true')
    
    
        # Store namespace, parser, runn additional parsing
        ns = parser.parse_args()

        # Run additional parsing based on cfig and "params"
        _parse_params(ns)   
        
        return cls(_inroot=ns.inroot, _outroot=ns.outroot, rname=ns.rname, 
                   clean=ns.clean, verbosity=ns.verbosity, trace=ns.trace, 
                   spec_parms=ns.params, dryrun=ns.dry, overwrite=ns.ow)
              