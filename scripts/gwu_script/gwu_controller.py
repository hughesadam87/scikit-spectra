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

# PYUVVIS IMPORTS
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
from pyuvvis.exceptions import badkey_check, ParserError, GeneralError, \
     ParameterError, LogExit

# Import some spectrometer configurations
from parameters_model import Parameters, USB2000, USB650

logger = logging.getLogger(__name__)
from pyuvvis.logger import configure_logger, logclass

SCRIPTNAME = 'gwuspec'
DEF_INROOT = './scriptinput'
DEF_OUTROOT = './output'
ALL_ANAL = ['1d', '2d', '3d', 'corr']   
ANAL_DEFAULT = ['1d', '2d']

# Make installable
SEC_TEMPLATE = '/home/glue/Desktop/PYUVVIS/pyuvvis/scripts/gwu_script/templates/section.tex'

    
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
    
def latex_path(fullpath):
    fullpath = fullpath.replace('_', '\\_')
    return fullpath.decode('string-escape')


def dict_out(header, dic, sort = True):
    ''' Retures a string of form header \n k \t val '''
    
    if sort:
        return header + ':\n' + '\n'.join(['\t'+(str(k) + '\t' + str(v)) 
                 for k,v in sorted(dic.items())])
    else:
        return header + ':\n' +'\n'.join(['\t'+(str(k) + '\t' + str(v)) 
                 for k,v in dic.items()])        

class AddUnderscore(argparse.Action):
    ''' Adds an underscore to end of value (used in "rootname") '''
    def __call__(self, parser, namespace, values, option_string=None):
        if values != '':
            values += '_'
        setattr(namespace, self.dest, values)
    

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
        self.sweepmode = kwargs.get('sweep', False)
        self._plot_dpi = kwargs.get('plot_dpi', None) #Defaults based on matplotlibrc file
        self.analysis = kwargs.get('analysis', ANAL_DEFAULT)
        
        self.rname = kwargs.get('rname', '')
        self.overwrite = kwargs.get('overwrite', False)
        
        # Configure logger
        verbosity = kwargs.get('verbosity', 'warning')
        trace = kwargs.get('trace', False)
                    
        # Pop kwargs['params'] for output below
        self.params = kwargs.pop('params', None)


        # Add logging later; consider outdirectory conflicts
        self.build_outroot()
        
        configure_logger(screen_level=verbosity, name = __name__,
                 logfile=op.join(self.outroot, 'runlog.txt'), mode='w')
        
        # Output the parameters
        with open(op.join(self.outroot, 'run_parameters.txt'), 'w') as f:
            f.write(dict_out('Spectral Parameters', self.params))
            f.write(dict_out('\n\nRun Parameters', kwargs))



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
    
    @property
    def analysis(self):
        return self._analysis

    @analysis.setter
    def analysis(self, values):
        ''' Values must be an iterable. '''
        if not values:
            self._analysis = ANAL_DEFAULT
            return
        
        values = list(set(values)) #Remove duplicates
        values = [str(v).lower() for v in values] #String convert 
                
        if 'all' in values or values == ['all']:
            self._analysis = ALL_ANAL
                
        else:
            invalid = [v for v in values if v not in ALL_ANAL]
            if invalid:
                raise ParameterError('Invalid analysis parameter(s) received '
                    '%s.  Choices are %s' % (invalid, ALL_ANAL))
            self._analysis = values
            
                
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
        ''' Can be None, a dict, or an instance of Parameters. '''
        if params is None:
            self._params = params
            
        else:
            if isinstance(params, Parameters):
                self._params = params
    
            elif isinstance(params, dict):
                self._params = Parameters(**params)
            else:            
                raise ParameterError('Spectral parameters must be a dictionary '
                      'or parameters_model.Parameters object.  Got object of type %s'
                       % type(params))
            
        
            
    def start_run(self):
        ''' Analyzes the root directory.  If sweep mode, subdirectories
            will be analyzed as well.'''
        
        self._inpath = self.inroot
        self._outpath = op.join(self.outroot, self.infolder)
        self._treefile = open(op.join(self.outroot, 'tree'), 'w')
        
        self.analyze_dir()
        if self.sweepmode:
            self.main_walk()        

        self._treefile.close()

    def main_walk(self):
        ''' Walks all the subdirectories of self.inroot; runs analyze_dir()'''
        
        walker = os.walk(self.inroot, topdown=True, onerror=None, followlinks=False)
        (rootpath, rootdirs, rootfiles) = walker.next()   
    
        if not rootdirs:
            logger.warn('Recursive walk found no further directories after %s'
                        % self.infolder)    
    
        while rootdirs:

            for iteration, folder in enumerate(rootdirs):
                
         # Outsuffix is working folder minus inroot (inroot/foo/bar --> foo/bar)
                wd = op.join(rootpath, folder)
                outsuffix = wd.split(self.inroot)[-1].lstrip('/') 
                
                self._inpath = wd
                self._outpath = op.join(self.outroot, outsuffix)
                
                self.analyze_dir()

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
        ''' Wraps loging to self._analyze_dir '''
        
        logger.debug('inpath is: %s' % self._inpath)
        logger.debug('outpath is: %s' % self._outpath)        
        try:
            self._analyze_dir()
        except LogExit: #log exit
            logger.critical('FAILURE: "%s" finished with errors.' % self.infolder) 
        else:
            # Generate report
            logger.info('SUCCESS: "%s" analyzed successfully' % self.infolder)       
            self.section_report()
                        

    def section_report(self):
        ''' Writes a section report for the current inpath.
            These are tracked via the treefile, for compatability
            with specreport.py'''
        
        secname = self.outpath.strip(self.outroot)
        sec_template = file(SEC_TEMPLATE, 'r').read()

        report_params = {
            'secname':secname, 
            'inpath':latex_path(self.inpath),
            'outpath':latex_path(self.outpath),        
            # Hacky way to look for plots (leave it to the tex template) to use 
            'areaplotfull': op.join(self.outpath, 'Full_data/Raw_area'),
            'specplotfull': op.join(self.outpath, 'Full_data/Raw_spectrum'),
            
            'specplotabs': op.join(self.outpath,  'Abs_base10/Absorbance_spectrum'),
            'areaplotabs': op.join(self.outpath,  'Abs_base10/Absorbance_area'),
            
            'specplotrel':op.join(self.outpath, 'Linear_ratio/Relative_area'),
            'areaplotrel':op.join(self.outpath, 'Linear_ratio/Relative_spect')
                        } 

        report = open(op.join( self.outpath, 'sectionreport.tex'), 'w')
        report.write( sec_template % report_params )
                        
        report.close()
        
        logger.debug("Adding %s to tree file." % self.infolder )
        self._treefile.write(str({secname: report_params}))            


    def _analyze_dir(self):
        ''' Analyze a single directory, creates timespectra; performs analysis.
            Very much the main method in the whole class.'''

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
        
        # Output metadata
        if getattr(ts_full, 'metadata', None):
             logger.info('Saving %s metadata' % ts_full.full_name)
             with open(op.join(rundir, '%s.metadata' % self.infolder), 'w') as f:
                 f.write(dict_out('Spectral Parameters', ts_full.metadata))
        else:
            logger.info('Metadata not found for %s' % ts_full.full_name)
            

        # To csv (loses metadata) set to meta_separate to False to preserve metadata
        logger.info('Outputting to %s.csv.  Metadata will be exluded.' % self.infolder)
        ts_full.to_csv(op.join(rundir, '%s.csv' % self.infolder), meta_separate=None)


        # Set ts
        ts = ts_full  
        ts = self.apply_parameters(ts)       
        
        #Iterate over various iunits
        for iu in self.params.iunits:
            od = op.join(rundir , Idic[iu])
            # Rename a few output units for clear directory names
            if iu =='r':
                od = op.join(rundir, 'Linear_ratio') 
            elif iu == None:
                od = op.join(rundir, 'Full_data')
            elif iu == 'a':
                od = op.join(rundir, 'Abs_base10')
            logmkdir(od)
 
            ts = ts.as_iunit(iu)
            out_tag = ts.full_iunit.split()[0] #Raw, abs etc.. added to outfile
            
            # 1d Plots
            if '1d' in self.analysis:
                self.plots_1d(ts, outpath=od, prefix=out_tag)
            
            # 2d Plots
            if '2d' in self.analysis:
                self.plots_2d(ts, outpath=od, prefix=out_tag)
            
            # Correlation analysis  
            if 'corr' in self.analysis:
                self.corr_analysis(ts, outpath=od, prefix=out_tag)
          
            # 3d Plots
            if '3d' in self.analysis:
                self.plots_3d(ts, outpath=od, prefix=out_tag)
            

    def apply_parameters(self, ts):
        ''' Performs several timespectr manipulations such as slicing, baseline 
            subtraction etc..  similar to self.validate_ts(), but is performed
            after the full timespectra object has been changed. '''
        

        ## Subtract the dark spectrum if it has one.  
        #if self.params.sub_base:
            #if ts.baseline is None:
                #logger.warn('Warning: baseline not found on %s)' % ts.full_name)            
            #else:    
                #ts.sub_base() 
                #logger.info('Baseline has been subtracted')
        #else:
            #logger.info('Parameter "sub_base" not set to True.' 
            #'No baseline subtraction will occur.')            
    
        # Fit first order references automatically?
        if self.params.bline_fit:
            blines = dynamic_baseline(ts, self.params.fit_regions )
            ts = ts.sub(blines, axis=0)
            logger.info('Dynamically fit baselines successfully subtracted.')
    
        # Slice spectra and time start/end points.  Doesn't stop script upon erroringa
        try:
            tstart, tend = self.params.t_start, self.params.t_end
            if tstart and tend:
                ts = ts[ tstart : tend ] 
                logger.info('Timesliced %s to (%s, %s)' % (ts.full_name, tstart, tend))             
            else:
                logger.debug('Cannot timeslice: tstart and/or tend not found')
        except Exception:
            logger.warn('unable to timeslice to specified by parameters')                   
            raise
            
        try:
            xstart, xend = self.params.x_min, self.params.x_max
            if xstart and xend:              
                ts = ts.ix[ xstart : xend ] 
                logger.info('Wavelength-sliced %s to (%s, %s)' % (ts.full_name, xstart, xend))                
            else:
                logger.debug('Cannot spectralslice: xstart and/or xend not found')

        except Exception:
            logger.warn('unable to slice x_min and x_max range specified by parameters')                          
            
            
        # Set reference (MUST SET reference AFTER SLICING RANGES TO AVOID ERRONEOUS reference DATA)
        ts.reference = self.params.reference
    
        if self.params.intvlunit:
            try:
                ts.to_interval(self.params.intvlunit)
            except KeyError:
                ts.to_interval()        
                logger.warn('Cannot set "intvlunit" from parameters; running'
                        ' ts.to_interval()')
        else:
            logger.info('Intvlunit is None- leaving data as rawtime')
            
            
        return ts    

    def build_outroot(self):
        if self.outroot == self.inroot:
            raise ParameterError('Inroot and outroot cannot be the same! '
                'Input data would be lost...')
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

        pmin, pmax = self.params.valid_minmax                
        if  ts.index[0] < pmin or ts.index[-1] > pmax:
            raise GeneralError('Parameters _valid_range criteria not met.  Data' 
            ' range (%s,%s) - parameters "_valid_range" (%s,%s)' % 
            (ts.index[0], ts.index[-1], pmin,pmax))  
            
        ts.specunit = self.params.specunit 
        ts.intvlunit = self.params.intvlunit 
        
        # TEST FOR NAN VALUES BEFORE CONTINUING  #####
        if countNaN(ts): #0 will evaluate to false
            raise GeneralError('NaNs found in %s during preprocessing.' 
                    ' Cannot proceed with analysis.' % ts.full_name)
        return ts


    def build_timespectra(self):
        ''' Attempts to build timespectra form picklefile, legacy and finally
            from the raw datafiles.'''
                
        # Files in working directory, ignore certain extensions; ignore directories
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
        
        # Import from raw specfiles (overwrite if data < 1s apart)
        logger.info('Loading contents of %s multiple raw spectral '
                    'files %s.' % (self.infolder, len(infiles)))     
        try:
            return from_spec_files(infiles, name=self.infolder, 
                                   check_for_overlapping_time=False) 
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
 
    def plots_1d(self, ts, outpath, prefix=''):
        ''' Plots several 1D plots.  User passes in ts w/ proper iunit.
            outpath: filepath (str)
            prefix: str
               Put in front of file name (eg outpath/prefix_area.png) for area plot
        '''
        
        specplot(ts)
        self.plt_clrsave(op.join(outpath, prefix +'_spectrum'))

        # Area plot using simpson method of integration
        areaplot(ts, ylabel='Power', xlabel='Time ('+ts.timeunit+')', legend=False,
                 title='Spectral Power vs. Time (%i - %i %s)' % 
                    (min(ts.index), max(ts.index), ts.specunit), color='r')
        self.plt_clrsave(op.join(outpath, prefix +'_area'))

        # Normalized area plot (divided by number x units)       
        areaplot(ts/len(ts.index), ylabel='Power per unit %s' % ts.specunit, xlabel='Time (' +
                 ts.timeunit+')', legend=False, title='Normalized Spectral' 
                 'Power vs. Time (%i - %i %s)' % 
                 (min(ts.index), max(ts.index), ts.specunit), color='r')
        self.plt_clrsave(op.join(outpath, prefix +'_area_normal'))
        
        # Lambda max vs. t plot
        
        

        # Ranged time plot
        try:
            uv_ranges = self.params.uv_ranges
        except (KeyError):
            uv_ranges = 8   
            logger.warn('Uv_ranges parameter not found: setting to 8.')
                
        # Time averaged plot, not scaled to 1 (relative intenisty dependson bin width and actual intensity)
        tssliced = ts.wavelength_slices(uv_ranges, apply_fcn='mean')
        range_timeplot(tssliced, ylabel='Average Intensity', xlabel = 
                       'Time ('+ts.timeunit+')' ) #legstyle =1 for upper left
        self.plt_clrsave(op.join(outpath, prefix +'_strip'))        
        
        
    def corr_analysis(self, ts, outpath, prefix=''):
        
        # Make a 2dCorrAnal Directory
        corr_out = op.join(outpath, '2dCorrAnal')
        logmkdir(corr_out)
    
        ref = make_ref(ts, method='empty') 
        S,A = ca2d(ts, ref)
        sync_3d(S, title='Synchronous Spectrum (%s-%s %s)' % (round(min(ts), 1),
                round(max(ts),1), ts.full_timeunit)) #min/max by columns      
        self.plt_clrsave(op.join(corr_out, prefix +'_sync'))        
        async_3d(A, title='Asynchronous Spectrum (%s-%s %s)' % 
                 (round(min(ts), 1), round(max(ts),1), ts.full_timeunit))
        self.plt_clrsave(op.join(corr_out, prefix +'_async'))        

        
    def plots_2d(self, ts, outpath, prefix=''):
        
        plot2d(ts, title='Full Contour', cmap='autumn', contours=7, label=1,
               colorbar=1, background=1)
        self.plt_clrsave(op.join(outpath, prefix +'_contour'))    
        
        
    def plots_3d(self, ts, outpath, prefix=''):
        c_iso = 10 ; r_iso=10
        kinds = ['contourf', 'contour']
        views = ( (14, -21), (28, 17), (5, -13), (48, -14), (14,-155) )  #elev, aziumuth
        for kind in kinds:
            out3d = op.join(outpath, '3dplots_'+kind)
            logmkdir(out3d)

            for view in views:        
                spec_surface3d(ts, kind=kind, c_iso=c_iso, r_iso=r_iso, 
                    cmap=cmget('gray'), contour_cmap=cmget('autumn'),
                    elev=view[0], azim=view[1], xlabel='Time ('+ts.timeunit+')'
                              )
                self.plt_clrsave(op.join(out3d, prefix + 'elev:azi_%s:%s' %
                                         (view[0], view[1])))         
   
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
    
        parser.add_argument('-c', '--config', dest='cfig', metavar='', 
                           choices=['usb650', 'usb2000'], default='usb2000',
                           help='usb650, usb2000, defaults to usb2000')            
         
        parser.add_argument('-o','--overwrite', action='store_true', 
                            help='Overwrite contents of output directories if '
                            'they already exist')
        
        parser.add_argument('-v', '--verbosity', help='Set screen logging '
                             'If no argument, defaults to info.', nargs='?',
                             default='warning', const='info', metavar='')

                
        parser.add_argument('-p','--params', nargs='*', help='Overwrite config '
                            'parameters manually in form k="foo value" '  
                            'Ex: --params xmin=440.0 xmax=700.0', metavar='')
        
        parser.add_argument('-a', '--analysis', nargs='*', help='Types of '
                'analysis to perform.  Choose 1 or more of the following: %s or '
                '"all".  Defaults to %s.' % (ALL_ANAL, ANAL_DEFAULT), 
                default=ANAL_DEFAULT, metavar='')
        
        parser.add_argument('-e', '--extra', action='store_true', 
            help='Adds report and sem directories to current working directory.'
            ' Not modular and only a convienence hack')
    
#        parser.add_argument('-d','--dryrun', dest='dry', action='store_true',
#                            help='Not yet implemented')

        # This must be "-t, --trace" for logger compatability; don't change!
        parser.add_argument('-t', '--trace', action='store_true', dest='trace',
                          help='Show traceback upon errors')       
        
        parser.add_argument('--dpi', type=int, help='Plotting dots per inch.')
    
    
        # Store namespace, parser, runn additional parsing
        ns = parser.parse_args()

        # Run additional parsing based on cfig and "params" to set spec params
        if ns.cfig == 'usb650':
            model = USB650
    
        elif ns.cfig == 'usb2000':
            model = USB2000
    
        if not ns.params:
            ns.params=[]
        
        try:
            userparams = dict (zip( [x.split('=', 1 )[0] for x in ns.params],
                                [x.split('=', 1)[1] for x in ns.params] ) )
    
        except Exception:
            raise IOError('Please enter keyword args in form: x=y')
        
        ns.params = model(**userparams)
        delattr(ns, 'cfig')        
        
        controller = cls(inroot=ns.inroot, outroot=ns.outroot, plot_dpi = ns.dpi,
                   verbosity=ns.verbosity, trace=ns.trace, params=ns.params, 
                   overwrite=ns.overwrite, sweep=ns.sweep, 
                   analysis=ns.analysis)
            
        # Make REPORT/SEM directories for convienence
        if ns.extra:
            for dirname in ['Report', 'SEM']:
                logger.info('Making directory: "%s"' % dirname)
                if op.exists(dirname):
                    logger.critical('Cannot create directory: %s.  Not'
                        'comfortable overwriting...' % dirname)
                else:
                    os.mkdir(dirname)
                    
        return controller