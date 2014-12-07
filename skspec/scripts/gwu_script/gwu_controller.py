""" GWU in-house script for dataanalysis of fiberoptic probe data."""

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
from collections import OrderedDict
from time import gmtime, strftime

# skspec IMPORTS
#from skspec.bundled import run_nb_offline
from skspec.plotting import areaplot, range_timeplot, six_plot
#from skspec.plotting.advanced_plots import spec_surface3d, surf3d, spec_poly3d, plot2d, plot3d
from skspec.core.utilities import boxcar, countNaN
from skspec.core.baseline import dynamic_baseline
from skspec.plotting.plot_utils import _df_colormapper, cmget
from skspec.IO.gwu_interfaces import from_timefile_datafile, from_spec_files
from skspec.core.file_utils import get_files_in_dir, get_shortname
#from skspec.core.corr import ca2d, make_ref, sync_3d, async_3d
from skspec.core.spectra import _normdic
from skspec.pandas_utils.metadframe import mload, mloads
from skspec.exceptions import badkey_check, ParserError, GeneralError, \
     ParameterError, LogExit

from skspec.scripts.gwu_script.tex_templates import SECTION

# Import some spectrometer configurations
from parameters_model import Parameters, USB2000, USB650

logger = logging.getLogger(__name__)
from skspec.logger import configure_logger, logclass
from skspec.data import data_dir

SCRIPTNAME = 'gwuspec'
DEF_INROOT = './scriptinput'
DEF_OUTROOT = './output'
ALL_ANAL = ['1d', '2d', '3d', 'corr']   
ANAL_DEFAULT = ['1d']#, '2d']

# HOW TO READ THIS ABSOLUTE PATH
IPYNB = op.join(data_dir, '_script_nb.ipynb')  #IPYTHON NOTEBOOK TEMPLATE
NBVIEWPATHS = [] #Where various ipython notebook blob links are stored

def hideuser(abspath):
    """ Replace user home directory with ~.  Inverse operation for
    op.expanduser().  Must pass absolute path that starts with user.
    User is home/glue but on FD harddrive, it's media/backup, so hack
    to just replace
    """
    user = op.expanduser('~')
    if '/media/backup' in abspath:
        user = '/media/backup'
    return abspath.replace(user, '~')
    

def ext(afile): 
    """ get file extension"""
    return op.splitext(afile)[1]

def timenow():
    return dt.datetime.now()

def logmkdir(fullpath):
    """ Makes directory path/folder, and logs."""
    logger.info('Making directory: %s' % fullpath)
    os.mkdir(fullpath)
    
def latex_string(string):
    """ Replace underscore, newline, tabs to fit latex."""

    string = string.replace('_', '\\_')
#    string = string.decode('string-escape')
    
    string = string.replace('\n', '\\\\')
    return string.replace('\t', '\hspace{1cm}') #Chosen arbitrarily

def dict_out(header, dic, sort = True):
    """ Retures a string of form header \n k \t val """
    
    if sort:
        return header + ':\n\n' + '\n'.join(['\t' + (str(k) + '\t' + str(v)) 
                 for k,v in sorted(dic.items())])
    else:
        return header + ':\n\n' +'\n'.join(['\t' + (str(k) + '\t' + str(v)) 
                 for k,v in dic.items()])        
    
def latex_multicols(dic, title='', cols=2):
    """ Hacky: given a list of items, wraps a multicol iterable so that the list
        will be output as columns.  Title will be added in bold/large"""
    
    outstring = ''
    if title:
        outstring += r'{\bf \large %s}' % title

    outstring += r'\begin{multicols}{%s}\begin{itemize}' % cols
    for k, v in dic.items():
        outstring += r'\item{\ttfamily {\bf %s}:\hspace{.3cm}%s}' % (k, v)
    outstring += '\end{itemize}\end{multicols}'
    return latex_string(outstring)
    
    

# This could delete empty folders that were otherwise in the directory that 
# were there before starting script
def removeEmptyFolders(path):
    """ Removes any empty folders in path.  Useful because recursive mode
        of script makes every directory it finds, even if they are empty."""
    if os.path.isdir(path):
  
        # remove empty subfolders
        if os.listdir(path):
            for f in os.listdir(path):
                fullpath = os.path.join(path, f)
                if os.path.isdir(fullpath):
                    removeEmptyFolders(fullpath)
      
        else: 
            logger.info('Removing empty folder: "%s"' % path)
            os.rmdir(path)


class AddUnderscore(argparse.Action):
    """ Adds an underscore to end of value (used in "rootname") """
    def __call__(self, parser, namespace, values, option_string=None):
        if values != '':
            values += '_'
        setattr(namespace, self.dest, values)
    

#skip class methods
@logclass(log_name=__name__ , public_lvl='debug',
          skip=['_ts_from_picklefiles', 'from_namespace'])
class Controller(object):
    """ """

    name = 'Controller' #For logging

    # Extensions to ignore when looking at files in a directory       
    img_ignore=['.png', '.jpeg', '.tif', '.bmp', '.ipynb'] 
        
    nb_links = {} #Stores ipython notebook viewer links    
    
    # For now, this only takes in a namespace, but could make more flexible in future
    def __init__(self, **kwargs):
              
        # These should go through the setters        
        self.inroot = kwargs.get('inroot', DEF_INROOT) 
        self.outroot = kwargs.get('outroot', DEF_OUTROOT)
        self.sweepmode = kwargs.get('sweep', False)
        self.analysis = kwargs.get('analysis', ANAL_DEFAULT)

        self._plot_dpi = kwargs.get('plot_dpi', None) #Defaults based on matplotlibrc file
        self._plot_dim = kwargs.get('plot_dim', 'width=6cm')
        self._plot_fontsize = kwargs.get('fontsize', 18)
        # Ticksize defaults to 15 btw
    
        
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
        self._run_params_file = op.join(self.outroot, 'runparameters.tex')
        with open(self._run_params_file, 'w') as f:
            
            # Hacky way to write latex section from raw string literals
            f.write(r'\subsection{Script Parameters}')
            f.write(r'\fboxsep5mm')
            f.write(r'\fcolorbox{black}{yellow}{\vbox{\hsize=10cm \noindent \scriptsize ')
  
            f.write(latex_multicols(self.params, title='skspec Parameters'))
            f.write(latex_multicols(kwargs, 'Analysis Parameters'))
            f.write('}}')


        if self._plot_dpi > 600:
            logger.warn('Plotting dpi is set to %s.  > 600 may result in slow'
                       ' performance.')
            
        # Used for storing variables in reports/matlab other uses
        self._run_summary = '' 
        self._csv_paths = []
                        
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
        """ Values must be an iterable. """
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
        """ Ensure inpath exists before setting"""
        self._inroot = self._valid_inpath(value)

    @property
    def inpath(self):
        if not self._inpath:
            raise AttributeError('Inpath not set')
        return self._inpath #Abspath applied in setter

    
    @inpath.setter
    def inpath(self, value):
        """ Ensure inpath exists before setting"""
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
        """ Can be None, a dict, or an instance of Parameters. """
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
        """ Analyzes the root directory.  If sweep mode, subdirectories
            will be analyzed as well."""
        
        self._inpath = self.inroot
        self._outpath = op.join(self.outroot, self.infolder)
        self._treedic = OrderedDict()
        
        self.analyze_dir()
        
        # Remove empty folders that may have been generated during sweep
        if self.sweepmode:
            self.main_walk()   
            removeEmptyFolders(self.outroot)

        # Add main run parameters as section to end of treefile
        self._treedic['Analysis Parameters'] = self._run_params_file

        with open(op.join(self.outroot, 'tree'), 'w') as treefile:
            treefile.write(str(self._treedic))
            
        self.make_matlab(op.join(self.outroot, 'readfiles.m'))
            
        # Add notebooks links to params file    
        logger.info('Appending ipython notebook links to runparams.tex')
        with open(self._run_params_file, 'a') as f:
            # Hacky way to write latex section from raw string literals
            f.write(r'\subsection{IPython Notebooks}')
            f.write(r'\bad{Links will not work until git pushed.}')
            f.write(r'\begin{itemize}')
            for (name, path) in NBVIEWPATHS:
                f.write('\link{%s}{%s}' % (path, latex_string(name)))
            f.write(r'\end{itemize}')     




    def save_csv(self, ts, csv_path, meta_separate=None):
        """ Save timespectra to self.infolder (boilerplate reduction).  Saves
        csv, pickle and metadata.  This is called at least twice, once for 
        full unadalterated data, once for baseline/cropped data. """

        logger.info('Outputting csv to %s.  Metadata will be exluded.' % csv_path)
        ts.to_csv(csv_path, meta_separate=None)
        self._csv_paths.append(csv_path)
        
        
        
    def make_matlab(self, outpath):
        """ Fills simple.m template from mlab_templates with outpath, using
            self._csv_paths."""
        if op.splitext(outpath)[-1] != '.m':
            raise IOError('matlab file must end in ".m". '  
            'Received "%s"' % outpath)

        logger.info('Making matlab script: "%s"' % outpath)
        from skspec.scripts.gwu_script.mlab_templates import SIMPLE_M

        m_dic={}
        # Do some hacky string formatting to fit matlab code
        m_dic['files'] = ',\n'.join("'"+item+"'" for item in self._csv_paths)
        basenames = [op.splitext(op.basename(path))[0] for path in self._csv_paths]
        m_dic['basenames'] = ',\n'.join("'"+item+"'" for item in basenames)
        m_dic['attrnames'] = '\n'.join(['%s=myData.%s' % (i,i) for i in basenames])

        
        mfile = open(outpath, 'w')
        mfile.write( SIMPLE_M % m_dic )                        
        mfile.close()        
        

    def main_walk(self):
        """ Walks all the subdirectories of self.inroot; runs analyze_dir()"""
        
        walker = os.walk(self.inroot, topdown=True, onerror=None, followlinks=False)
        (rootpath, rootdirs, rootfiles) = walker.next()   

        rootdirs.sort() #Iterate alphebetically
        
        if not rootdirs:
            logger.warn('Recursive walk found no further directories after %s'
                        % self.infolder)    
    
        while rootdirs:
            
            # if npsam is in folder name, put that folder first.  
            for idx, folder in enumerate(rootdirs):
                if 'npsam' in folder.lower():
                    rootdirs.pop(idx)
                    rootdirs.insert(0, folder)
                    logger.info('Found "npsam" matching directory in folder "%s"'
                                ' resorting alphebatized directories.')
                    break                

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
        """ Wraps loging to self._analyze_dir """
        
        logger.debug('inpath is: %s' % self._inpath)
        logger.debug('outpath is: %s' % self._outpath)        
        try:
            self._analyze_dir()
        except LogExit: #log exit
            logger.critical('FAILURE: "%s" finished with errors.' % self.infolder) 
        else:
            # Generate report
            logger.info('SUCCESS: "%s" data analysis complete' % self.infolder)       
            self.section_report()
                        

    def section_report(self):
        """ Writes a section report for the current inpath.
            These are tracked via the treefile, for compatability
            with specreport.py"""
        
        # path/to/section/ ---> section [and latex formatted for "_" 
        secname = latex_string(self.outpath.split(self.outroot)[-1].lstrip('/'))
        logger.info('Generating section report for %s' % secname) 

        report_params = {
            'secname':secname, 
            'inpath':latex_string(self.inpath),
            'outpath':latex_string(self.outpath),        
            'plot_dim':self._plot_dim,
            'parameters':self._run_summary,
            # Hacky way to look for plots (leave it to the tex template) to use 
            'specplotfull': op.join(self.outpath, 'Full_data/Raw_spectrum'),
            'areaplotfull': op.join(self.outpath, 'Full_data/Raw_area'),
            
            'specplotabs': op.join(self.outpath,  'Abs_base10/Absorbance_spectrum'),
            'areaplotabs': op.join(self.outpath,  'Abs_base10/Absorbance_area'),
            
            'specplotrel':op.join(self.outpath, 'Linear_ratio/Relative_spectrum'),
            'areaplotrel':op.join(self.outpath, 'Linear_ratio/Relative_area')
                        } 

        report_path = op.join(self.outpath, 'sectionreport.tex')
        report = open(report_path, 'w')
        report.write( SECTION % report_params )                        
        report.close()
        
        logger.debug("Adding %s to tree dic." % self.infolder )
        self._treedic[latex_string(secname)] = report_path


    def _analyze_dir(self):
        """ Analyze a single directory, creates timespectra; performs analysis.
            Very much the main method in the whole class."""

        logger.info("ANALYZING RUN DIRECTORY: %s\n\n" % self.infolder)

        # outpath should be correctly set by main_walk()
        rundir = self.outpath
        logmkdir(rundir)

        start = timenow()
        ts_full = self.build_timespectra()        
        logger.info('SUCCESS imported %s in %s seconds' % 
                (ts_full.full_name, (timenow() - start).seconds))
        ts_full = self.validate_ts(ts_full) 
        
        logger.info('Saving %s as %s.pickle' % (ts_full.full_name, self.infolder))
        ts_full.save(op.join(rundir, '%s.pickle' % self.infolder)) 
        
        # Output metadata to file (read back into _run_summary)
        if getattr(ts_full, 'metadata', None):
            logger.info('Saving %s metadata' % ts_full.full_name)
            with open(op.join(rundir, '%s.full_metadata' % self.infolder), 'w') as f:
                f.write(dict_out('Spectrometer Parameters', ts_full.metadata))

            def _filter_metadata(dic):
                """ Return spectrometer parameters of interest for report. Changes
                    format of integration time parameter."""
                dic = OrderedDict( (k, (dic.get(k, '') )) for k in ['int_time', 'int_unit', 
                         'boxcar', 'spec_avg', 'timestart', 'timeend', 'filecount','spectrometer'])

                if 'usec' in dic['int_unit']:
                    dic['int_unit'] = 'usec'

                dic['int_time'] = str(dic['int_time']) + ' ' +  str(dic['int_unit'])
                del dic['int_unit']
                return dic
                
            self._run_summary = latex_multicols(_filter_metadata(ts_full.metadata), title='Spectrometer Parameters')

        else:
            logger.info('Metadata not found for %s' % ts_full.full_name)
            

        # To csv (loses metadata) set to meta_separate to False to preserve metadata
        logger.info('Outputting to %s.csv.  Metadata will be exluded.' % self.infolder)
        
        self.save_csv(ts_full, op.join(rundir, '%s.csv' % self.infolder))

        # Set ts, subtract baseline, crop
        ts = self.apply_parameters(ts_full)     # BASELINE SUBTRACTED/CROPPING HERE   
         
        cropped_csv_path =  op.join(rundir, '%s_cropped.csv' % self.infolder)
        self.save_csv(ts, cropped_csv_path)
        
        # Used to be in apply parameters, but pulled out so could save bline_cropped csv
        # Once jsonify, this can be returned to apply parameters fcn 
        if self.params.intvlunit:
            try:
                ts.varunit = self.params.intvlunit
            except KeyError:
                ts.varunit = 'intvl'        
                logger.warn('Cannot set "intvlunit" from parameters; running'
                        ' ts.to_interval()')
        else:
            logger.info('Intvlunit is None- leaving data as rawtime')
        
        #IPYTHON NOTEBOOK
        NBPATH =  op.join(rundir, '%s.ipynb' % self.infolder)
        logging.info("Copying blank .ipynb template to %s" % NBPATH)
        template = open(IPYNB, 'r').read()
        
        outshort = self.outpath.split(self.outroot)[1].lstrip('/')

        template = template.replace('---DIRECTORY---', outshort)
        template = template.replace('---CREATED---',  strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        template = template.replace('---ROOT---', hideuser(self.outroot))
        template = template.replace('---PARAMS---', self.params.as_markdownlist())
        template = template.replace('---COUNT---', str(ts.shape[1]))
        template = template.replace('---HIDDENOUT---', hideuser(rundir))

        cols = ts.shape[1]
        _warncolor = 'green'
        if cols >= 200 and cols < 500:
            _warncolor = 'orange'
        elif cols >= 500:
            _warncolor = 'red'
        template = template.replace('---COLOR---', _warncolor)
        
        
        # Pass the full csv file otherwise run_nb_offline won't be in right wd
        template = template.replace('---CSVPATH---', op.basename(cropped_csv_path))
        
        template = template.replace('---TSTART---', '%s'%ts_full.columns[0])
        template = template.replace('---TEND---', '%s'%ts_full.columns[-1])
        template = template.replace('---TDELTA---', '%s'%
                                    ts_full.as_varunit('intvl').columns[-1])                            

        open(NBPATH, 'w').write(template)

        # ADD NOTBOOK TO GITHUB
        if self.params.git:
            os.system("git add %s" % op.abspath(NBPATH))
            viewerpath = NBPATH.split('FiberData')[1].lstrip('/')
            viewerpath = 'http://nbviewer.ipython.org/github/hugadams/FiberData/blob/master/'+viewerpath
            localdir = self.inpath.replace(self.inroot, '').lstrip('/')
            NBVIEWPATHS.append((localdir, viewerpath)) 
       
        
        # Execute the notebook
#	        run_nb_offline(NBPATH) 
        #try:
            #from runipy.notebook_runner import NotebookRunner
            #from IPython.nbformat.current import read as nbread
            #from IPython.nbformat.current import write as nbwrite
        #except IOError:
            #logger.critical("Please install runipy (pip install runipy) to "
                            #"run .ipynb prior to opening.")
        #else:
            #notebook = nbread(open(NBPATH), 'json')
            #r = NotebookRunner(notebook)
            #r.run_notebook()            
            #nbwrite(r.nb, open(NBPATH, 'w'), 'json')
    
        # Quad plot (title is rootfolder:folder; for non -s, are the same
        if op.basename(self.inroot) == self.infolder:
            quadname = self.infolder 
        else:
            quadname = "%s:%s" % (op.basename(self.inroot), self.infolder)

        # SIXPLOT
        six_plot(ts, title=quadname, striplegend=True)
        self.plt_clrsave(op.join(rundir, '%s_sixplot.png' % self.infolder))
        
        # AREA THIRDS
        self.area_thirds_plot(ts)
        self.plt_clrsave(op.join(rundir, '%s_area_thirds.png' % self.infolder))
        
        
        #Iterate over various norms
        for iu in self.params.norms:
            od = op.join(rundir , _normdic[iu])
            # Rename a few output units for clear directory names
            if iu =='r':
                od = op.join(rundir, 'Linear_ratio') 
            elif iu == None:
                od = op.join(rundir, 'Full_data')
            elif iu == 'a':
                od = op.join(rundir, 'Abs_base10')
            logmkdir(od)
             
            ts = ts.as_norm(iu)
            out_tag = ts.full_norm.split()[0] #Raw, abs etc.. added to outfile
            
            
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
        """ Performs several timespectr manipulations such as slicing, baseline 
            subtraction etc..  similar to self.validate_ts(), but is performed
            after the full timespectra object has been changed. """
        

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
        """ Tries to catch errors in index, as well as sets some defaults.  """ 
        
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
        """ Attempts to build timespectra form picklefile, legacy and finally
            from the raw datafiles."""
                
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
        return from_timefile_datafile(datafile=infiles[0], timefile=timefile, 
                                      name=self.infolder)

    @classmethod
    def _ts_from_picklefiles(cls, infiles, infolder='unknown'):
        """ Look in a list of files for .pickle extensions.  Infolder name
            is only used for better logging. """

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
        """ Plots several 1D plots.  User passes in ts w/ proper norm.
            outpath: filepath (str)
            prefix: str
               Put in front of file name (eg outpath/prefix_area.png) for area plot
        """
        
        # Set plot and tick size larger than defaul
        sizeargs = {'labelsize': self._plot_fontsize, 
                    'ticksize':15, 
                    'titlesize':self._plot_fontsize}
        
    
        ts.plot(**sizeargs)
        self.plt_clrsave(op.join(outpath, prefix +'_spectrum'))

        # Area plot using simpson method of integration
        areaplot(ts, 
                 ylabel='Power',
                 xlabel='Time ('+ts.varunit+')',
                 legend=False,
                 title='Spectral Power vs. Time (%i - %i %s)' % 
                    (min(ts.index), max(ts.index), ts.specunit), color='black', **sizeargs)
        self.plt_clrsave(op.join(outpath, prefix +'_area'))

        # Short wavelengths min:525nm
        areaplot(ts.loc[:525.0, :], 
                 ylabel='Power',
                 xlabel='Time ('+ts.varunit+')',
                 legend=False,
                 title='Short Wavelengths vs. Time (%i - %i %s)' % 
                    (min(ts.index), 525.0, ts.specunit), color='b', **sizeargs)
        self.plt_clrsave(op.join(outpath, prefix +'_area_short'))

        # Middle wavelengths 525:590nm
        areaplot(ts.loc[525.0:590.0, :], 
                 ylabel='Power',
                 xlabel='Time ('+ts.varunit+')',
                 legend=False,
                 title='Medium Wavelengths vs. Time (%i - %i %s)' % 
                    (525.0, 590.0, ts.specunit), color='g', **sizeargs)
        self.plt_clrsave(op.join(outpath, prefix +'_area_middle'))
        
        # Long wavelenghts 590.0nm:
        areaplot(ts.loc[590.0:, :], 
                 ylabel='Power',
                 xlabel='Time ('+ts.varunit+')',
                 legend=False,
                 title='Long Wavelengths vs. Time (%i - %i %s)' % 
                    (590.0, max(ts.index), ts.specunit), color='r', **sizeargs)
        self.plt_clrsave(op.join(outpath, prefix +'_area_long'))        

        # Normalized area plot (divided by number x units)       
        areaplot(ts/len(ts.index),
                 ylabel='Power per unit %s' % ts.specunit,
                 xlabel='Time (' + ts.varunit+')', 
                 legend=False, 
                 title='Normalized Spectral Power vs. Time (%i - %i %s)' % 
                     (min(ts.index), max(ts.index), ts.specunit), color='orange', **sizeargs)
        self.plt_clrsave(op.join(outpath, prefix +'_area_normal'))
        
        # Normalized ABSOLUTE areaplot (divided by number x units)       
        areaplot(np.absolute(ts)/len(ts.index), 
                 ylabel='Power per unit %s' % ts.specunit, 
                 xlabel='Time (' + ts.varunit+')', 
                 legend=False, 
                 title='Normalized ABSOLUTE Power vs. Time (%i - %i %s)' % 
                     (min(ts.index), max(ts.index), ts.specunit), color='purple', **sizeargs)
        self.plt_clrsave(op.join(outpath, prefix +'_area_normal'))   
        
        
        
        
        # Lambda max vs. t plot
        
        # XXXXXX?

        # Ranged time plot
        try:
            uv_ranges = self.params.uv_ranges
        except (KeyError):
            uv_ranges = 8   
            logger.warn('Uv_ranges parameter not found: setting to 8.')
                
        # Time averaged plot, not scaled to 1 (relative intenisty dependson bin width and actual intensity)
        tssliced = ts.wavelength_slices(uv_ranges, apply_fcn='mean')
        range_timeplot(tssliced, ylabel='Average Intensity', xlabel = 
                       'Time ('+ts.varunit+')', **sizeargs ) #legstyle =1 for upper left
        self.plt_clrsave(op.join(outpath, prefix +'_strip'))        
        
    def area_thirds_plot(self, ts):
        # Special areaplot of normalized raw area in thirds
        # Should work on USB650, but untested.  Slices data into thirds to 
        # find limits, so should be independent.
        def _scaleto1(tslice):
            return np.divide(tslice, tslice[0])
        
        ax = areaplot(_scaleto1(ts.area()), linewidth=2, alpha=1, ls='--', custompadding=None)
        
        tspace = (ts.index.max() - ts.index.min()) /3
        tim = ts.index.min()
        
        short = ts.nearby[:tim+tspace].area()
        mid = ts.nearby[tim+tspace:tim+2*tspace].area()
        longer = ts.nearby[2*tspace+tim:].area()
        
        # Store slice ranges for plt.legend() below
        label_short = '%s:%s'% (ts.index[0], tim+tspace)
        label_mid = '%s:%s' % (tim+tspace, tim+2*tspace)
        label_long = '%s:%s' % (2*tspace+tim, ts.index[-1])
        
        for t, color in [(short, 'b'), (mid, 'g'), (longer, 'r')]:
            ax = range_timeplot(_scaleto1(t), ax=ax, color=color, 
                                linewidth=4, alpha=.4, custompadding=None)
        
        plt.title('Area slices %s: normalized at t=0' % ts.specunit)    
        plt.legend(['All $\lambda$', label_short, label_mid, label_long],
                    ncol=4, 
                    fontsize='10')        

        
    def corr_analysis(self, ts, outpath, prefix=''):
        
        # Make a 2dCorrAnal Directory
        corr_out = op.join(outpath, '2dCorrAnal')
        logmkdir(corr_out)
    
        ref = make_ref(ts, method='empty') 
        S,A = ca2d(ts, ref)
        sync_3d(S, title='Synchronous Spectrum (%s-%s %s)' % (round(min(ts), 1),
                round(max(ts),1), ts.full_varunit)) #min/max by columns      
        self.plt_clrsave(op.join(corr_out, prefix +'_sync'))        
        async_3d(A, title='Asynchronous Spectrum (%s-%s %s)' % 
                 (round(min(ts), 1), round(max(ts),1), ts.full_varunit))
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
                    elev=view[0], azim=view[1], xlabel='Time ('+ts.varunit+')'
                              )
                self.plt_clrsave(op.join(out3d, prefix + 'elev:azi_%s:%s' %
                                         (view[0], view[1])))         
   
    def plt_clrsave(self, outpath):
        logger.info('Saving plot: %s' % outpath)                
        plt.savefig(outpath, dpi=self._plot_dpi)
        plt.clf()       

    @classmethod
    def from_namespace(cls, args=None):
        """ Create Controller from argparse-generated namespace. """
        
        if args:
            if isinstance(args, basestring):
                args=shlex.split(args)
            sys.argv = args               
        
        
        parser = argparse.ArgumentParser(SCRIPTNAME, description='GWU skspec fiber data '
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

        parser.add_argument('-g', '--git', action='store_false', help='If true, '
                            'git will not attempt to be called on this run.'
                            'By default, git is synced.')
    
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
                            'Ex: --params x_min=440.0 x_max=700.0', metavar='')
        
        parser.add_argument('-a', '--analysis', nargs='*', help='Types of '
                'analysis to perform.  Choose 1 or more of the following: %s or '
                '"all".  Defaults to %s.' % (ALL_ANAL, ANAL_DEFAULT), 
                default=ANAL_DEFAULT, metavar='')
        
        parser.add_argument('-e', '--extra', action='store_true', 
            help='Adds report and sem directories to current working directory.'
            ' Not modular and only a convienence hack')
        
        parser.add_argument('-f', '--fontsize', type=int, default=18,
             help='Plot x/y/title fontsize.  Defaults to 18.  pyplot default = 12.')
    
#        parser.add_argument('-d','--dryrun', dest='dry', action='store_true',
#                            help='Not yet implemented')

        # This must be "-t, --trace" for logger compatability; don't change!
        parser.add_argument('-t', '--trace', action='store_true', dest='trace',
                          help='Show traceback upon errors')       
        
        parser.add_argument('--plot_dim', metavar='', default='width=6cm', help='Defaults to '
            '"width=6cm"; any valid latex plotsize parameters (\textwidth) are acceptable;' 
            ' enter directly as they would be in latex "includegraphics[]".')
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
        
        userparams['git'] = ns.git
        ns.params = model(**userparams)
        delattr(ns, 'cfig')        
        
        controller = cls(inroot=ns.inroot, outroot=ns.outroot, plot_dpi = ns.dpi,
                   verbosity=ns.verbosity, trace=ns.trace, params=ns.params, 
                   overwrite=ns.overwrite, sweep=ns.sweep, plot_dim = ns.plot_dim,
                   analysis=ns.analysis, fontsize=ns.fontsize)
            
        # Make REPORT/SEM directories for convienence
        if ns.extra:
            for dirname in ['Report', 'SEM']:
                logger.info('Making directory: "%s"' % dirname)
                if op.exists(dirname):
                    logger.critical('Cannot create directory: %s.  Not '
                        'comfortable overwriting...' % dirname)
                else:
                    os.mkdir(dirname)
                if dirname == 'Report' and not op.exists(dirname):
                    os.mkdir(op.join(dirname, 'images'))
                    
        return controller
