''' GWU in-house script for dataanalysis of fiberoptic probe data.'''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2013, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"


import os
import time
import shutil
import sys
import imp
import collections 
from optparse import OptionParser

import matplotlib.pyplot as plt
import numpy as np


## This file is local... maybe make my own toolset?

## ASBOLUTE IMPORTS
from pyuvvis.pyplots.basic_plots import specplot, areaplot, absplot, range_timeplot
from pyuvvis.pyplots.advanced_plots import spec_surface3d, surf3d, spec_poly3d, plot2d, plot3d
from pyuvvis.core.spec_labeltools import datetime_convert, spec_slice
from pyuvvis.core.utilities import boxcar, hasNaN
from pyuvvis.core.baseline import dynamic_baseline
from pyuvvis.pyplots.plot_utils import _df_colormapper, cmget
from pyuvvis.IO.gwu_interfaces import from_timefile_datafile, from_spec_files
from pyuvvis.core.imk_utils import get_files_in_dir, make_root_dir
from pyuvvis.core.baseline import dynamic_baseline
from pyuvvis.core.corr import ca2d, make_ref, sync_3d, async_3d
from pyuvvis.core.timespectra import mload, mloads, Idic
from pyuvvis.custom_errors import badkey_check

### Import some parameters
from pyuvvis.scripts.usb_2000 import params as p2000
from pyuvvis.scripts.usb_650 import params as p650

def plt_clrsave(outpath, outname): # dpi=600):
    ''' Save plot then clear afterwards.  dpi=600 saves a nicer quality picture for publication.'''
    plt.savefig('%s/%s' %(outpath, outname)) #, dpi=600 )
    plt.clf()
    
def _lgfile(logfile, verbose, message):
    ''' Writes information to logfile and optionally to screen if user uses --verbose=True 
        in core_analysis() call.
        Params:
        -------
           outfile: logfile opened in write mode
           verbose: if true, contents are printed to screen in addition to written to log'''
    if verbose:
        print message
    logfile.write(message)
    
def currenttime(tstart):
    ''' Return the timedelta in HMS given original time. '''
    tf=time.time()-tstart
    if tf > 86400:
        tf = '> 1 day' #Fix later to actually record number of days
    else:
        tf=time.strftime('%H:%M:%S', time.gmtime(tf))    
    return tf


def core_analysis():
    img_ignore=['png', 'jpeg', 'tif', 'bmp'] 
    
    ### Default configuration parameters    
    params=p2000 #Don't change to p650 without modifying _valid_range test later in script!
    
    ################################################################################################
    ### Option Parser to catch indirectory, outdirectory, wheter to ignore images in a directory,  #
    ### and to overwrite output directory if it already exists                                     #
    ################################################################################################
    
    parser = OptionParser(usage='usage: %prog -i indirectory -o outdirectory ', version='%prog 0.1.0')
    parser.add_option('-i', '--indir',
                      action='store',
                      dest='wd',
                     # default='.', #Most common use
                      default='./scriptinput',  #FOR DEBUGGING
                      
                      help='Path to root directory where file FOLDERS are located',)
    parser.add_option('-o', '--outdir',
                      action='store',
                      dest='od',
                      default='./output',  #FOR DEBUGGING
          #            default=None,
                      help='Path to root directory where output folder is built',) 

    parser.add_option('-r', '--runname',
                      action='store',
                      dest='rname',
                      default='', #None causes errors
                      help='Title of trial/run, used in filenames and other places.',)     
    
    parser.add_option('-c', '--config',
                      action='store',
                      dest='cfig',
                      default=None,
                      help='Path to parameter configuration files.  Parameters can be individually overwritten by  \
                      passing arguments into optparser as keywords (eg xmin=50).  Config file must contain a dictionary  \
                      named "params".'
                      )
    
    parser.add_option('-l', '--logfile',
                      action='store',
                      dest='lfname',
                      default='RunLog.txt',
                      help='Path to runlog file.  Defaults to "RunLog.txt". For now, no option to shut off (sorry).'
                      )
    
    parser.add_option('--ignore', action='store_true', default=True, 
                      dest='ignore',  help='Ignore the most commonly found image types \
                      (.png, .jpeg etc...) when parsing data files.')

    parser.add_option('--clean', action='store_true', default=True, #REMOVE
                      dest='clean',
                      help='This will clean and overwrite files found in the output directory\
                       before writing new results.  Careful, this will delete ALL files in any\
                       directory that you pass.')
    
    parser.add_option('--verbose', action='store_true', default=True, #REMOVE
                      dest='verb',
                      help='If true, anything written to logfile will also be printed to screen.')    


    (options, kwargs) = parser.parse_args()

    ##############################
    ### Configuration parameters #
    ##############################
    ### If user enters configuration parameters file
    if options.cfig:
        
        ### If user enters keys to builtin params style
        if options.cfig.lower() in ['usb650', '650']:
            params=p2000
        elif options.cfig.lower() in ['usb2000', '2000']:
            params=p650
        
        ### If user enters parms from config file
        else:
        
            ### Use absolute path
            cfig=os.path.abspath(options.cfig)
            basename=os.path.basename(cfig)         
                    
            ### Ensure path/file exists
            if not os.path.exists(cfig):
                raise IOError('Cannot find config filepath: "%s"'%cfig)
            
            ### Split.py extension (Needed for imp.fine_module() to work correctly
            cfig, ext=os.path.splitext(cfig)
            if ext != '.py':
                raise IOError('%s must be a .py file: %s'%basename)
                        
            sys.path.append(os.path.dirname(cfig))
            try:
                cbase=basename.split('.')[0]  
                cfile=imp.load_source(cbase, os.path.abspath(options.cfig))
            except Exception as E:
                raise Exception('Could not import config file "%s".  The following import error was returned: %s'%(basename,E))
    
            ### Try to load parameters from params
            try:
                cparms=cfile.params
            except AttributeError:
                raise AttributeError('Cannot find "params" dictionary in config file, %s'%basename)
    
            ### Overwrite defaults completely.  Does not force user to have every relevant parameter.
            else:
                params=cparms
    
    ### Overwrite parameters from commandline variable keyword args
    ### Args are list [x,y,z] but enforcing kwarg from input of form ['x=3', 'y=5']    
    if kwargs:
        try:
            kwargs=dict(zip( [x.split('=')[0] for x in kwargs],[x.split('=')[1] for x in kwargs] ))
        except Exception:
            raise IOError('Please enter keyword args in form: x=y')
        else:
            ### Update parameters 
            invalid=[]
            for key in kwargs:
                if key in params:
                    params[key]=kwargs[key]
                else:
                    invalid.append(key)
            if invalid:
                raise IOError('Parameter(s) "%s" not understood.  Valid parameters are: \n   %s'%('","'.join(invalid), '\n   '.join(params.keys()) ) )
    
    ### Ensure proper type of spectral intensity parameters        
    if params.has_key('outtypes'):
        for otype in params['outtypes']:
            badkey_check(otype, Idic.keys())
    else:
        params['outtypes']=None #Only raw data will be used    

    ### Ensure indir/outdir were passed
    inroot, outroot=options.wd, options.od 
    if not outroot:
        ### Arguments will default to None, so can't do try: except AttributeError        
        parser.error("Please enter an outdirectory (-o)")

    ### If runname, add underscore for output file formatting
    if options.rname !='':
        options.rname+='_'  

    ### Open logfile to track various IO steps
    start=time.time()
    lf=open(outroot + '/'+ options.lfname, 'w')

    ### Copy of runparameters file for later reference
    f=open(outroot+'/run_parameters', 'w')
    f.write('Run parameters (make me a better header)')
    for key in params:
        f.write('\n%s\t%s'%(key, params[key]))
    f.close()

    ### Read in data from all folders in root input directory. ###
    ### Walk a single directory down    
    walker=os.walk(inroot, topdown=True, onerror=None, followlinks=False)
    (rootpath, rootdirs, rootfiles)= walker.next()
    
    if not rootdirs:
        raise IOError('"%s" directory is empty.'%rootpath)
    
    for iteration, folder in enumerate(rootdirs):
        ### Format first iteration differently for aesthetics
        if iteration==0:
            print '\n'
            _lgfile(lf, options.verb, "Analyzing run directory %s"%folder)
        else:
            _lgfile(lf, options.verb, "\n\nAnalyzing run directory %s"%folder)

        wd=inroot+'/'+folder
        infiles=get_files_in_dir(wd, sort=True)

        ### Remove pre-made images from the indirectory (for backwards compatibility)
        if options.ignore:
            infiles=[afile for afile in infiles if not afile.split('.')[-1] in img_ignore]

        ### READ IN GWU DATA.  IF PICKLE FILE IS FOUND IN DIRECTORY, THIS IS USED FIRST.
        ### IF NOT, DATAFIELS ARE USED.  IF DATEFILES==2, USES TIMEFILE-DATAFILE
        ### OTHERWISE, IT USES FROM_SPEC_FILES

        picklefile=[afile for afile in infiles if afile.split('.')[-1]=='pickle']

        if len(picklefile)>1:
            _lgfile(lf, options.verb,'Failed to load in folder, %s, had more than one .pickle files.\n'%folder)
            raise IOError('Indirectory must contain only one pickle file if you want to use it!!!')

        elif len(picklefile)==1:
            _lgfile(lf, options.verb,'Loaded contents of folder, %s, using the ".pickle" file, %s.'%(folder, get_shortname(picklefile[0])))            
            ts_full=mload(picklefile[0])        

        ### If no picklefile found try reading in datafile directly
        else:
            if len(infiles) == 2:
                timefile=[afile for afile in infiles if 'time' in afile.lower()]
                if len(timefile) == 1:
                    _lgfile(lf, options.verb,'Loading contents of "%s", using the timefile/datafile conventional import'%folder)                       
                    infiles.remove(timefile[0])
                    ts_full=from_timefile_datafile(datafile=infiles[0], timefile=timefile[0])

                ### ACCOUNT FOR REMOTE POSSIBILITY THAT 2 FILES COULD STILL JUST BE TWO RAW DATA FILES INSTEAD OF DATAFILE/TIMEFILE
                elif len(timefile) == 0:
                    _lgfile(lf, options.verb,'Loading contents of folder "%s" multiple raw spectral files %s.  (If these were \
                    supposed to be datafile/timefile and not raw files, couldnt find word "time" in filename.) \
                    \n'%(folder, len(infiles)))                     
                    ts_full=from_spec_files(infiles)


                else:
                    _lgfile(lf, options.verb,'Failure: multiple timefile matches found in folder %s'%folder)                                
                    raise IOError('Timefile not found.  File must contain word "time"')                    

            else:
                 
                try:
                    ts_full=from_spec_files(infiles)
                    _lgfile(lf, options.verb,'Loading contents of folder, %s, multiple raw spectral files %s.'%(folder, len(infiles)))                                             
                except Exception as E:
                    _lgfile(lf, options.verb,'SCRIPT ERROR: Could not load contents of %s.\n Following exception was returned:\n%s'%(folder, E))
                    continue

                

        _lgfile(lf, options.verb, 'Time to import %s to TimeSpectra: %s'%(folder, currenttime(start))) 
        
        ### Attempt to catch error if user enteres p650 data but uses p2000 setting and vice versa
        ### Only works if user didn't specify config file or manual cfig params
        if not options.cfig and not kwargs:
            dmin, dmax=ts_full.index[0], ts_full.index[-1]
            pmin, pmax=params['_valid_minmax']
            
            ### Try usb 650 parms
            if  dmin < pmin or dmax > pmax:
                _lgfile(lf, options.verb,'Parameters _valid_range criteria not met, changing to p650')                
                params=p650
                pmin, pmax=params['_valid_minmax']
                
                ### 
                if  dmin < pmin or dmax > pmax:
                    _lgfile(lf, options.verb,'Failure: multiple timefile matches found in folder %s'%folder)                                
                    raise IOError('%s index limits %s, are not contained within the range of of config ranges %s.'
                                  %(ts_full.__class__.__name__, (pmin, pmax), (dmin, dmax)))                        
                
                
                
        #############################
        ### Setup outputdirectory ###
        #############################  
  
        ### Eventually make this overwrite if directory 
        try:
            outroot=make_root_dir(outroot+'/'+folder, overwrite=options.clean)  ## BE VERY CAREFUL WITH THIS
        except IOError:
            raise IOError('Root output directory %s already exists.\n  To overwrite, use option -c True.  Use with caution\n\
            preexisting data will be deleted from directory!'%(outroot))        

            
        ### Set specunit/intvlunit       
        try:
            ts_full.specunit=params['specunit']
        except AttributeError:
            ts_full.specunit='nm'
    
        ## Convert time axis to specified unit          
        try:
            ts_full.intvlunit=params['intvlunit'] #Take from params file  
        except AttributeError:
            ts_full.intvlunit='intvl'               
            
        ### Output the pickled dataframe   
        ts_full.save(outroot+'/rundata.pickle')         

        ### Subtract the dark spectrum if it has one.  Note that all programs should produce an attribute for darkseries,
        ### which may be None, but the attribute should still be here.
        if hasattr(ts_full, 'darkseries') and params['sub_dark']==True:
            if isinstance(ts_full.darkseries, type(None) ):
                ts=ts_full #need this                
                _lgfile(lf, options.verb,'Warning: darkseries not found in data of run directory %s\n'%folder)            
            else:    
                ts=ts_full.sub(ts_full.darkseries, axis='index') 
        else:
            ts=ts_full #need this
            _lgfile(lf, options.verb,'Warning: darkseries attribute is not found on dataframe in folder %s!\n'%folder)            
    
        ### Fit first order baselines automatically?
        if params['line_fit']:
            blines=dynamic_baseline(ts, params['fit_regions'] )
            ts=ts-blines 

        ### Slice spectra and time start/end points.  Doesn't stop script upon erroringa
        try:
            ts=ts[params['tstart']: params['tend'] ] 
        except Exception:
            _lgfile(lf, options.verb,'Parameters Error: unable to slice tstart and tend to specified range in directory %s\n'%folder)           
    
        try:
            ts=ts.ix[params['x_min']: params['x_max'] ] 
        except Exception:
            _lgfile(lf, options.verb,'Parameters Error: unable to slice x_min and x_max range in directory %s\n'%folder)              
            
            
        ### Set Baseline (MUST SET BASELINE AFTER SLICING RANGES TO AVOID ERRONEOUS BASELINE DATA)
        if params.has_key('baseline'):
            ts.baseline=params['baseline']
        else:
            ts.baseline=0
        

        ### Set data to interval
        try:
            ts.to_interval(params['intvlunit'])
        except KeyError:
            ts.to_interval()
            
        ###############################################
        ## TEST FOR NAN VALUES BEFORE CONTINUING  #####
        ###############################################
        
        if hasNaN(ts):
            _lgfile(lf, options.verb,'NaNs found in %s during some step in preprocessing.  Could not perform analysis!'
                    %(ts.__class__.__name__))
            continue                        
            
        ###########################################
        ### Intensity-unit dependent operations  ##
        ###########################################
        
        iunits=params['outtypes']
        if not isinstance(iunits, collections.Iterable): #In case non-iterable parameter input style
            iunits=[iunits]

        for iu in iunits:
            od=outroot+'/'+Idic[iu]
            if iu=='r':
                od=outroot+'/'+'Relative Inverse'  # The (1/T) messes up directory structure!
            os.mkdir(od)             
            
            ts=ts.as_iunit(iu) #ts.iunit should also work but rather make copies
       
            ###### Basic spectral and absorbance plots    
            specplot(ts, title=options.rname+'Full spectrum')
            plt_clrsave(od, options.rname+'full_spectrum')
    
            ### Look for uv-vis ranges in data, if not found, default to equally slicing spectrum by 8
            try:
                uv_ranges=params['uv_ranges']   
            except (KeyError):
                uv_ranges=8   
                    
            #### Time averaged plot, not scaled to 1 (relative intenisty dependson bin width and actual intensity)
            tssliced=ts.wavelength_slices(uv_ranges, apply_fcn='mean')
            range_timeplot(tssliced, ylabel='Average Intensity', xlabel='Time ('+ts.timeunit+')' ) #legstyle =1 for upper left
            plt_clrsave(od, options.rname+'stripchart')
 
            ### Area plot using simpson method of integration
            areaplot(ts, ylabel='Power', xlabel='Time ('+ts.timeunit+')', legend=False,
                           title='Spectral Power vs. Time (%i nm - %i nm)'%  ## Eventually make nm a paremeter and class method
                           (min(ts.index), max(ts.index)), color='r')
            plt_clrsave(od, options.rname+'full_area')
            
            ###### Polygon Plot
            spec_poly3d(ts, title=options.rname+'3d Poly Spec')
            plt_clrsave(od, options.rname+'polygon')           
        
            #### correlation analysis
            outcorr=od+'/2dCorrAnal'
            os.mkdir(outcorr)        
            ref=make_ref(ts, method='empty')     
    
            S,A=ca2d(ts, ref)
            sync_3d(S, title='Synchronous Spectrum (%s-%s %s)'%(round(min(ts), 1), round(max(ts),1), ts.full_timeunit)) #min/max by columns      
            plt_clrsave(outcorr, options.rname+'full_sync')                
            async_3d(A, title='Asynchronous Spectrum (%s-%s %s)'%(round(min(ts), 1), round(max(ts),1), ts.full_timeunit))
            plt_clrsave(outcorr, options.rname+'full_async')        
    
    
            #### 2d contour plot (solid color or cmap accepted)
            plot2d(ts, title='Full Contour', cmap='autumn', contours=7, label=1, colorbar=1, background=1)
            plt_clrsave(od, options.rname+'full_contour')        
       
            ### 3D Plots.  Set row and column step size, eg 10 would mean 10 column traces on the contours ###
            c_iso=10 ; r_iso=10
            kinds=['contourf', 'contour']
            views=( (14, -21), (28, 17), (5, -13), (48, -14), (14,-155) )  #elev, aziumuth
            for kind in kinds:
                out3d=od+'/3dplots_'+kind
                os.mkdir(out3d)
    
                for view in views:        
                    spec_surface3d(ts, kind=kind, c_iso=c_iso, r_iso=r_iso, cmap=cmget('gray'), contour_cmap=cmget('autumn'),
                                   elev=view[0], azim=view[1], xlabel='Time ('+ts.timeunit+')')
                    plt_clrsave(out3d, '%sfull_3d_%s_%s'%(options.rname, view[0], view[1])   )    
        

    ### Record runtime and close logfile    
    _lgfile(lf, options.verb,'Script total runtime: %s'%(currenttime(start)))
    lf.close()

if __name__=='__main__':  
    core_analysis()
