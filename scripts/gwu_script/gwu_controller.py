''' GWU in-house script for dataanalysis of fiberoptic probe data.'''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2013, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

import os
import os.path as op
import datetime as dt 
import shutil
import sys
import imp
import shlex
import logging
import argparse
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
from pyuvvis.core.file_utils import get_files_in_dir, get_shortname
from pyuvvis.core.baseline import dynamic_baseline
from pyuvvis.core.corr import ca2d, make_ref, sync_3d, async_3d
from pyuvvis.core.timespectra import Idic
from pyuvvis.pandas_utils.metadframe import mload, mloads
from pyuvvis.exceptions import badkey_check, ParserError, GeneralError, LogExit

# Import some spectrometer configurations
from usb_2000 import params as p2000
from usb_650 import params as p650

logger = logging.getLogger(__name__)
from pyuvvis.logger import log, configure_logger, logclass

SCRIPTNAME = 'gwuspec'
DEF_CFIG = p2000
DEF_INROOT = './scriptinput'
DEF_OUTROOT = './output'

# Do extra namespace parsing manually (This could be an action, if sure that it will
# be called after CfigAction (which generates parms based on cfig)
def _parse_params(namespace):
    ''' Spectra parameters in form "xmin=400" are formatted into a dictionary 
        inplace on namespace object.'''

    # cfig dictionary sets default parameters
    default = namespace.cfig

    if not namespace.params:
        namespace.params=[]
    
    try:
        kwargs = dict (zip( [x.split('=', 1 )[0] for x in namespace.params],
                            [x.split('=', 1)[1] for x in namespace.params] ) )

    except Exception:
        raise IOError('Please enter keyword args in form: x=y')

    invalid = []
    for key in kwargs:
        if key in default:
            logger.debug('Overwriting %s parameter from cmdline input' % key)
            default[key] = kwargs[key]
        else:
            invalid.append(key)

    if invalid:
        raise IOError('Parameter(s) "%s" not understood.  Valid parameters:' 
        '\n   %s' % ('","'.join(invalid), '\n   '.join(default.keys()) ) )
    
    namespace.params = default
    delattr(namespace, 'cfig')
    return
    
    
# Convenience fcns
def ext(afile): 
    ''' get file extension'''
    return op.splitext(afile)[1]

def timenow():
    return dt.datetime.now()

def logmkdir(fullpath):
    ''' Makes directory path/folder, and logs.'''
    logger.info('Making directory: %s' % fullpath)
    os.mkdir(fullpath)


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
                raise AttributeError('Cannot find "params" dictionary in config'
                                     ' file, %s' % basename)
    
            setattr(namespace, self.dest, params)
            return 

#skip class methods
@logclass(log_name=__name__ , public_lvl='debug',
          skip=['_ts_from_picklefiles', 'from_namespace'])
class Controller(object):
    ''' '''

    name = 'Controller' #For logging

    # Extensions to ignore when looking at files in a directory       
    img_ignore=['png', 'jpeg', 'tif', 'bmp', 'ipynb'] 
    
    # For now, this only takes in a namespace, but could make more flexible in future
    def __init__(self, **kwargs):
        
        # These should go through the setters
        
        self.inroot = kwargs.get('inroot', DEF_INROOT) 
        self.outroot = kwargs.get('outroot', DEF_OUTROOT)
        self.params = kwargs.get('params', None)
        self.sweepmode = kwargs.get('sweep', False)
        self._plot_dpi = kwargs.get('plot_dpi', None) #Defaults based on matplotlibrc file
        
        self.rname = kwargs.get('rname', '')
        self.dryrun = kwargs.get('dryrun', False) 
        self.overwrite = kwargs.get('overwrite', False)
        
        # Configure logger
        verbosity = kwargs.get('verbosity', 'warning')
        trace = kwargs.get('trace', False)
                    

        # Add logging later; consider outdirectory conflicts
        self.build_outroot()
        
        configure_logger(screen_level=verbosity, name = __name__,
                 logfile=op.join(self.outroot, 'Runlog.txt'), mode='w')

        
        with open(op.join(self.outroot, 'Parameters'), 'w') as f:
            f.write('Spectral Parameters:\n')
            f.write('\n'.join(['\t'+str(k)+'\t'+str(v) 
                               for k, v in self.params.items()]))
        
            f.write('\n\nRun Parameters:\n')
            f.write('\n'.join(['\t'+(str(k) + '\t' + str(v)) 
                               for k,v in kwargs.items()]))

        if self._plot_dpi > 600:
            logger.warn('Plotting dpi is set to %s.  > 600 may result in slow'
                       ' performance.')
                        
        
        
    def _valid_inpath(self, value):
        if value is None:
            return 
 
        path = op.abspath(value)
        if not op.exists(path):
            raise IOError('Inroot path does not exist: %s' % path)
        return path

    @property
    def inroot(self):
        if not self._inroot:
            raise AttributeError('Root indirectory not set')
        return self._inroot #Abspath applied in setter

    
    @inroot.setter
    def inroot(self, value):
        ''' Ensure inpath exists before setting'''
        self._inroot = self._valid_inpath(value)

    @property
    def inpath(self):
        if not self._inpath:
            raise AttributeError('Inpath not set')
        return self._inpath #Abspath applied in setter

    
    @inpath.setter
    def inpath(self, value):
        ''' Ensure inpath exists before setting'''
        self._inpath = self._valid_inpath(value)        
        
        
        
    @property
    def outroot(self):
        if not self._outroot:
            raise AttributeError('Root outdirectory not set')
        return self._outroot
        

    @outroot.setter
    def outroot(self, value):
        if value is None:
            self._outroot = None
        else:
            self._outroot = op.abspath(value)
            
 
    @property
    def outpath(self):
        if not self._outpath:
            raise AttributeError('Outpath not set')
        return self._outpath
        

    @outpath.setter
    def outpath(self, value):
        if value is None:
            self._outpath = None
        else:
            self._outpath = op.abspath(value)           
            
        
    @property
    def infolder(self):
        return op.basename(self.inpath)


    @property
    def outfolder(self):
        if not self.outpath:
            raise AttributeError('outfolder not found - outpath not set!')
        return op.basename(self.outpath)


    @property
    def params(self):
        if not self._params:
            raise AttributeError('Spec parameters not set')
        return self._params
    
    
    @params.setter
    def params(self, params):
        if params is None:
            self._params = params
            return 
        
        if not isinstance(params, dict):
            raise AttributeError('"params" must be dict but is %s' % str(type(params)))
 
        if params.has_key('iunits'):
            if not hasattr('__iter__', params['iunits']):
                logger.debug("Converting params['iunits'] from str to list")
                params['iunits'] = params['iunits'].split()
                
                
            # Make sure all outtypes (a, r, None) are valid; convert "None" to none
            for idx, otype in enumerate(params['iunits']):
                if otype == 'None':
                    logger.debug('Changing "None" string to None')
                    otype = None
                    params['iunits'][idx] = otype                    
                badkey_check(otype, Idic.keys())

        else:
            logger.warn('"outtypes" parameter not found.  Setting to [None].  Only'
                        ' rawdata will be analyzed.')
            logger.debug("Converting params['iunits'] from str to list")            
            params['iunits'] = [None] 
                                
        self._params = params   
        
            
    def start_run(self):

        if self.sweepmode:
            self.main_walk()
        else:
            self._inpath = self.inroot
            self._outpath = op.join(self.outroot, self.infolder)
            self.analyze_dir()
            

    def main_walk(self):
        walker = os.walk(self.inroot, topdown=True, onerror=None, followlinks=False)
        (rootpath, rootdirs, rootfiles) = walker.next()   
    
        if not rootdirs:
            raise IOError('"%s" directory is empty.' % op.basename(rootpath))    
    
        while rootdirs:

            for iteration, folder in enumerate(rootdirs):
                
                # Outsuffix is working folder minus inroot (eg inroot/foo/bar --> foo/bar)
                wd = op.join(rootpath, folder)
                outsuffix = wd.split(self.inroot)[-1].lstrip('/') 
                
                self._inpath = wd
                self._outpath = op.join(self.outroot, outsuffix)

                logger.debug('inpath is: %s' % self._inpath)
                logger.debug('outpath is: %s' % self._outpath)
                
                try:
                    self.analyze_dir()
                except LogExit: #log exit
                    logger.critical('FAILURE: "%s" finished with errors.' % self.infolder) 
                else:
                    logger.info('SUCCESS: "%s" analyzed successfully' % self.infolder)

        # Move down to next directory.  Need to keep iterating walker until a
        # directory is found or until StopIteraion is raised.
            rootpath, rootdirs, rootfile=walker.next()
            if not rootdirs:
                try:
                    while not rootdirs:
                        rootpath, rootdirs, rootfile=walker.next()
                except StopIteration:
                    logger.info('Reached end of directory tree.')
                    break


    def analyze_dir(self):
        ''' Analyze a single directory, do all analysis. '''

        logger.info("ANALYZING RUN DIRECTORY: %s\n\n" % self.infolder)

        start = timenow()
        ts_full = self.build_timespectra()        
        logger.info('SUCCESS imported %s in %s seconds' % 
                (ts_full.full_name, (timenow() - start).seconds))
        ts_full = self.validate_ts(ts_full) 

        
        # make rundir = outpath/infolder; save
        rundir = op.join(self.outpath)#, self.infolder)
        logmkdir(rundir)
        
        logger.info('Saving %s as %s.pickle' % (ts_full.full_name, self.infolder))
        ts_full.save(op.join(rundir, '%s.pickle' % self.infolder)) 

        # Set ts
        ts = ts_full  
        ts = self.apply_parameters(ts)
        
        #Iterate over various iunits
        for iu in self.params['iunits']:
            od = op.join(rundir , Idic[iu])
            # Rename a few output units for clear directory names
            if iu =='r':
                od=op.join(rundir, 'Linear_ratio') 
            elif iu == None:
                od = op.join(rundir, 'Full_data')
            logmkdir(od)
 
            ts = ts.as_iunit(iu)
            out_tag = ts.full_iunit.split()[0] #Raw, abs etc.. added to outfile
            
            self.plots_1d(ts, outpath=od, prefix=out_tag)
            

    def apply_parameters(self, ts):
        ''' Performs several timespectr manipulations such as slicing, baseline 
            subtraction etc..  similar to self.validate_ts(), but is performed
            after the full timespectra object has been changed. '''
        

        # Subtract the dark spectrum if it has one.  
        #if self.params['sub_base']:
            #if ts.baseline is None:
                #logger.warn('Warning: baseline not found on %s)' % ts.full_name)            
            #else:    
                #ts.sub_base() 
                #logger.info('Baseline has been subtracted')
        #else:
            #logger.info('Parameter "sub_base" not set to True.' 
            #'No baseline subtraction will occur.')            
    
        ### Fit first order references automatically?
        #if self.params['bline_fit']:
            #blines = dynamic_baseline(ts, self.params['fit_regions'] )
            #ts = ts - blines 
            #logger.info('Dynamically fit baselines successfully subtracted.')
    
        # Slice spectra and time start/end points.  Doesn't stop script upon erroringa
        try:
            tstart, tend = self.params['tstart'], self.params['tend']
            if tstart and tend:
                ts = ts[ tstart : tend ] 
                logger.info('Timesliced %s to (%s, %s)' % (ts.full_name, tstart, tend))                
        except Exception:
            logger.warn('unable to timeslice to specified specified by parameters')                   
            
        try:
            xstart, xend = self.params['x_min'], self.params['x_max']
            if xstart and xend:              
                ts = ts.ix[ xstart : xend ] 
                logger.info('Wavelength-sliced %s to (%s, %s)' % (ts.full_name, xstart, xend))                
        except Exception:
            logger.warn('unable to slice x_min and x_max range specified by parameters')                          
            
            
        # Set reference (MUST SET reference AFTER SLICING RANGES TO AVOID ERRONEOUS reference DATA)
        ts = self._try_apply(ts, 'reference', 0)
    
        try:
            ts.to_interval(self.params['intvlunit'])
        except KeyError:
            ts.to_interval()        
            logger.warn('Cannot set "intvlunit" from parameters; running'
                        ' ts.to_interval()')
            
        return ts    

    def build_outroot(self):
        if op.exists(self.outroot):
            if not self.overwrite:
                raise IOError("Outdirectory already exists!")                
            else:
                logger.warn('Directory "%s" and its contents will be overidden' % 
                            op.basename(self.outroot))
                shutil.rmtree(self.outroot)
        logmkdir(self.outroot)

        
    def validate_ts(self, ts):
        ''' Tries to catch errors in index, as well as sets some defaults.  ''' 
        
        logger.info('Testing spectral index bounds against parameters min/max')

        pmin, pmax = self.params['_valid_minmax']                
        if  ts.index[0] < pmin or ts.index[-1] > pmax:
            raise GeneralError('Parameters _valid_range criteria not met.  Data' 
            ' index (%s,%s); parameters _valid_range (%s,%s)' % (dmin, dmax, pmin,pmax))  
            
        # Set some defaults if params fails
        ts = self._try_apply(ts, 'specunit', 'nm')
        ts = self._try_apply(ts, 'intvlunit', 'intvl')
        
        # TEST FOR NAN VALUES BEFORE CONTINUING  #####
        if countNaN(ts): #0 will evaluate to false
            raise GeneralError('NaNs found in %s during preprocessing.' 
                    ' Cannot proceed with analysis.' % ts.full_name)
        return ts


    def build_timespectra(self):
        ''' '''
                
        # Get all the files in working directory, ignore certain extensions
        infiles = get_files_in_dir(self.inpath, sort=True)
        infiles = [f for f in infiles if not ext(f) in self.img_ignore]
                
        if not infiles:
            raise IOError("No valid files found in %s" % self.infolder)        
        
        # Try get timespectra from picklefiles
        ts_full = self._ts_from_picklefiles(infiles)
        if ts_full:
            return ts_full

        # Try get timespectra from timefile/datafile (legacy)
        ts_full = self._ts_from_legacy(infiles)
        if ts_full:
            return ts_full
        
        # Import from raw specfiles (name t
        logger.info('Loading contents of %s multiple raw spectral '
                    'files %s.' % (self.infolder, len(infiles)))     
        try:
            return from_spec_files(infiles, name=self.infolder) 
        except Exception as exc:
            logger.critical('Could not import files from pickle, legacy or' 
            ' from_spec_files()')
            raise
        
        
    
    def _ts_from_legacy(self, infiles):
        
        if len(infiles) != 2:
            logger.debug('Legacy import failed: requires 2 infiles (timefile/darkfile); '
            '%s files found' % len(infiles))
            return

        timefile=[afile for afile in infiles if 'time' in afile.lower()]            

        if len(timefile) != 1:
            logger.debug('Legacy import failed: required one file with "time" in'
            ' filenames; found %s' % len(infiles))
            return
        
        logger.info('Loading contents of "%s", using the timefile/datafile '
                    'conventional import' % self.infolder)                       
        timefile = timefile[0]
        infiles.remove(timefile) #remaing file is datafile
        return from_timefile_datafile(datafile=infiles, timefile=timefile, 
                                      name=self.infolder)

    @classmethod
    def _ts_from_picklefiles(cls, infiles, infolder='unknown'):
        ''' Look in a list of files for .pickle extensions.  Infolder name
            is only used for better logging. '''

        logger.debug('Looking for .pickle files in folder: %s' % infolder)
        
        picklefiles = [f for f in infiles if ext(f) == 'pickle']
        
        if not picklefiles:
            logger.debug('Pickle files not found in %s' % infolder)
            return
        
        elif len(picklefiles) > 1:
            raise IOError('%s pickle files found; expected only 1')
        
        else:
            picklefile = picklefiles[0]
            logger.info('Loaded contents of folder, %s, using the ".pickle" ' 
                       'file, %s.' % (folder, op.basename(picklefile)))            
            return mload(picklefile)     

    def _try_apply(self, ts, attr, default):
        '''Boilerplate reduction: sets an attributed on ts based on its value in
           self.params, and takes a default if not found. '''

        if not self.params.has_key(attr):
            logger.warn('%s not found in supplied parameters. '  
            'Automatically setting to "%s"' % (attr, default))
            setattr(ts, attr, default)
        
        else:
            try:
                setattr(ts, attr, self.params[attr])
                logger.info('Set %s from parameters to "%s"' %
                            (attr, self.params[attr]))
            except Exception: #Too stringent?
                logger.warn('Failed to set %s from parameters.  Automatically'
                            ' setting to %s' % (attr, default))
                setattr(ts, attr, default)

        return ts
    
 
    def plots_1d(self, ts, outpath, prefix=''):
        ''' Plots several 1D plots.  User passes in ts w/ proper iunit.
            outpath: filepath (str)
            prefix: str
               Put in front of file name (eg outpath/prefix_area.png) for area plot
        '''
        
        specplot(ts)
        self.plt_clrsave(op.join(outpath, prefix+'_spectrum'))

        # Area plot using simpson method of integration
        areaplot(ts, ylabel='Power', xlabel='Time ('+ts.timeunit+')', legend=False,
                 title='Spectral Power vs. Time (%i - %i %s)' % 
                    (min(ts.index), max(ts.index), ts.specunit), color='r')
        self.plt_clrsave(op.join(outpath, prefix+'_area'))

        # Ranged time plot
        try:
            uv_ranges = self.params['uv_ranges']   
        except (KeyError):
            uv_ranges = 8   
            logger.warn('Uv_ranges parameter not found: setting to 8.')
                
        # Time averaged plot, not scaled to 1 (relative intenisty dependson bin width and actual intensity)
        tssliced = ts.wavelength_slices(uv_ranges, apply_fcn='mean')
        range_timeplot(tssliced, ylabel='Average Intensity', xlabel = 
                       'Time ('+ts.timeunit+')' ) #legstyle =1 for upper left
        self.plt_clrsave(op.join(outpath, prefix+'_strip'))        
        
    def plots_2d(self, ts):
        NotImplemented
        
    def plots_3d(self, ts):
        NotImplemented   
        
   
    def plt_clrsave(self, outpath):
        logger.info('Saving plot: %s' % outpath)                
        plt.savefig(outpath, dpi=self._plot_dpi)
        plt.clf()       

    @classmethod
    def from_namespace(cls, args=None):
        ''' Create Controller from argparse-generated namespace. '''
        
        if args:
            if isinstance(args, basestring):
                args=shlex.split(args)
            sys.argv = args               
        
        
        parser = argparse.ArgumentParser(SCRIPTNAME, description='GWU PyUvVis fiber data '
        'analysis.', epilog='Additional help not found', 
        usage='%s <indir> <outdir> --globals' % SCRIPTNAME)

        # Global options
        parser.add_argument('inroot', metavar='indir', action='store', default=DEF_INROOT, 
                          help='Path to root directory where file FOLDERS are '
                          'located.  Defaults to %s' % DEF_INROOT)
        
        parser.add_argument('outroot', metavar='outdir', action='store', default = DEF_OUTROOT,  
                          help = 'Path to root output directory.  Defaults to %s'
                          % DEF_OUTROOT) 
        
        parser.add_argument('-s','--sweep', action='store_true', 
                            help='Script will recursively analyze directories '
                            'from the top down of indir')
    
        parser.add_argument('-c', '--config', dest='cfig', default=DEF_CFIG, action=CfigAction,
                          help='usb650, usb2000, or path to parameter ' 
                          'configuration file. defaults to usb2000', metavar='')            
        
        parser.add_argument('-o','--overwrite', action='store_true', 
                            help='Overwrite contents of output directories if '
                            'they already exist')
        
        parser.add_argument('-v', '--verbosity', help='Set screen logging '
                             'If no argument, defaults to info.', nargs='?',
                             default='warning', const='info', metavar='')

                
        parser.add_argument('-p','--params', nargs='*', help='Overwrite config '
                            'parameters manually in form k="foo value" '  
                            'Ex: --params xmin=440.0 xmax=700.0', metavar='')
    
        parser.add_argument('-d','--dryrun', dest='dry', action='store_true',
                            help='Not yet implemented')

        # This must be "-t, --trace" for logger compatability; don't change!
        parser.add_argument('-t', '--trace', action='store_true', dest='trace',
                          help='Show traceback upon errors')       
        
        parser.add_argument('--dpi', type=int, help='Plotting dots per inch.')
    
    
        # Store namespace, parser, runn additional parsing
        ns = parser.parse_args()

        # Run additional parsing based on cfig and "params" to set spec params
        _parse_params(ns)   
        
        return cls(inroot=ns.inroot, outroot=ns.outroot, plot_dpi = ns.dpi,
                   verbosity=ns.verbosity, trace=ns.trace, params=ns.params, 
                   dryrun=ns.dry, overwrite=ns.overwrite, sweep=ns.sweep)
              