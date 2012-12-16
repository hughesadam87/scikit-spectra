import os, time, shutil, sys
from optparse import OptionParser

import matplotlib.pyplot as plt

### GWU run parameters file ###
import specparms as sp  #if change filename, change shutil call


## LOCAL IMPORTS
#sys.path.append('../../pyuvvis')
#from pyplots.advanced_plots import spec_surface3d, surf3d, spec_poly3d, plot2d, plot3d
#from pandas_utils.dataframeserial import df_load, df_dump
#from pandas_utils.df_attrhandler import transfer_attr
#from core.spec_labeltools import datetime_convert, spectral_convert, spec_slice
#from core.spec_utilities import boxcar, wavelength_slices, divby
#from core.baseline import dynamic_baseline
#from pyplots.basic_plots import specplot, timeplot, absplot, range_timeplot
#from pyplots.plot_utils import _df_colormapper, cmget
#from IO.gwu_interfaces import from_timefile_datafile, get_files_in_dir, from_spec_files
#from core.baseline import dynamic_baseline
#from imk_utils import make_root_dir, get_files_in_dir, get_shortname
#from corr2d import corr_analysis, make_ref, sync_3d, async_3d

### UPDATE PACKAGE THEN CHANGE THIS
from pyuvvis import spec_surface3d, surf3d, spec_poly3d, plot2d, plot3d
from pyuvvis import df_load, df_dump
from pyuvvis import transfer_attr
from pyuvvis import datetime_convert, spectral_convert, spec_slice
from pyuvvis import boxcar, wavelength_slices, divby
from pyuvvis import dynamic_baseline
from pyuvvis import make_root_dir, get_files_in_dir, get_shortname
from pyuvvis import specplot, timeplot, absplot, range_timeplot, _genplot
from pyuvvis import _df_colormapper, cmget
from pyuvvis import from_timefile_datafile, get_files_in_dir, from_spec_files
from pyuvvis import corr_analysis, make_ref, sync_3d, async_3d


def plt_clrsave(outpath, outname): # dpi=600):
    ''' Save plot then clear afterwards.  dpi=600 saves a nicer quality picture for publication.'''
    plt.savefig('%s/%s' %(outpath, outname)) #, dpi=600 )
    plt.clf()

if __name__=='__main__':  

    img_ignore=['png', 'jpeg', 'tif', 'bmp'] #no .
    logfilename='RUNLOG'

    ### Option Parser to catch indirectory, outdirectory, wheter to ignore images in a directory, 
    ### and to overwrite output directory if it already exists 
    parser = OptionParser(usage='usage: %prog -i indirectory -o outdirectory ', version='%prog 0.1.0')
    parser.add_option('-d', '--indir',
                      action='store',
                      dest='wd',
                      default='./scripttest', #REMOVE
                      help='Path to root directory where file FOLDERS are located',)
    parser.add_option('-o', '--outdir',
                      action='store',
                      dest='od',
                      default='./output',  #Remove
                      help='Path to root directory where output folder is built',) 

    parser.add_option('-r', '--runname',
                      action='store',
                      dest='rname',
                      default='', #None causes errors
                      help='Title of trial/run, used in filenames and other places.',)     

    parser.add_option('-i', '--ignore', action='store_true', default=True, 
                      dest='ignore',  help='Ignore the most commonly found image types \
                      (.png, .jpeg etc...) when parsing data files.')

    parser.add_option('-c', '--clean', action='store_true', default=True, #REMOVE
                      dest='clean',
                      help='This will clean and overwrite files found in the output directory\
                       before writing new results.  Careful, this will delete ALL files in any\
                       directory that you pass.')


    (options, args) = parser.parse_args()

    ### Ensure indir/outdir were passed
    inroot, outroot=options.wd, options.od 
    if inroot==None or outroot == None:
        ### Arguments will default to None, so can't do try: except AttributeError        
        parser.error("Please both enter an indirectory (-d) and outdirectory (-o)")

    ### If runname, add underscore for output file formatting
    if options.rname !='':
        options.rname+='_'  

    ### Open logfile to track various IO steps
    start=time.time()
    lf=open(outroot + '/'+ logfilename, 'w')

    ### Copy of runparameters file for later reference
    shutil.copyfile('specparms.py', outroot+'/run_parameters')

    ### Walk a single directory down    
    walker=os.walk(inroot, topdown=True, onerror=None, followlinks=False)
    (rootpath, rootdirs, rootfiles)= walker.next()
    for folder in rootdirs:    
        print "Analyzing run directory %s"%folder

        wd=inroot+'/'+folder
        od=outroot+'/'+folder
        infiles=get_files_in_dir(wd)

        ### Remove pre-made images from the indirectory (for backwards compatibility)
        if options.ignore:
            infiles=[afile for afile in infiles if not afile.split('.')[-1] in img_ignore]

        ### Eventually make this overwrite if directory 
        try:
            outdir=make_root_dir(od, overwrite=options.clean)  ## BE VERY CAREFUL WITH THIS
        except IOError:
            raise IOError('Output directory %s already exists.\n\n  To overwrite, use option -c True.  Use with caution\n\n\
            preexisting data will be deleted from directory!'%(od))

        ### READ IN GWU DATA.  IF PICKLE FILE IS FOUND IN DIRECTORY, THIS IS USED FIRST.
        ### IF NOT, DATAFIELS ARE USED.  IF DATEFILES==2, USES TIMEFILE-DATAFILE
        ### OTHERWISE, IT USES FROM_SPEC_FILES

        picklefile=[afile for afile in infiles if afile.split('.')[-1]=='pickle']

        if len(picklefile)>1:
            lf.write('Failed to load in folder, %s, had more than one .pickle files.\n\n'%folder)
            raise IOError('Indirectory must contain only one pickle file if you want to use it!!!')

        elif len(picklefile)==1:
            df_full=df_load(picklefile[0])        
            lf.write('Loaded contents of folder, %s, using the ".pickle" file, %s.\n\n'%(folder, get_shortname(picklefile[0])))            

        ### If no picklefile found try reading in datafile directly
        else:
            if len(infiles) == 2:
                timefile=[afile for afile in infiles if 'time' in afile.lower()]
                if len(timefile) == 1:
                    infiles.remove(timefile[0])
                    df_full=from_timefile_datafile(datafile=infiles[0], timefile=timefile[0])
                    lf.write('Loading contents of folder, %s, using the timefile/datafile conventional import\n\n'%folder)   

                ### ACCOUNT FOR REMOTE POSSIBILITY THAT 2 FILES COULD STILL JUST BE TWO RAW DATA FILES INSTEAD OF DATAFILE/TIMEFILE
                elif len(timefile) == 0:
                    df_full=from_spec_files(infiles)
                    lf.write('Loading contents of folder, %s, multiple raw spectral files %s.  (If these were \
                    supposed to be datafile/timefile and not raw files, couldnt find word "time" in filename.) \
                    \n\n'%(folder, len(infiles))) 

                else:
                    lf.write('Failure: multiple timefile matches found in folder %s\n\n'%folder)                                
                    raise IOError('Timefile not found.  File must contain word "time"')                    

            else:
                df_full=from_spec_files(infiles)
                lf.write('Loading contents of folder, %s, multiple raw spectral files %s.\n\n'%(folder, len(infiles)))                    

        ### Output the pickled dataframe    
        df_dump(df_full, od+'/rundata.pickle')
        df_full.to_csv(od+'/rundata.csv')

        ### Subtract the dark spectrum if it has one.  Note that all program should produce an attribute for darkseries,
        ### which may be None, but the attribute should still be here.
        if hasattr(df_full, 'darkseries') and sp.sub_base==True:
            if isinstance(df_full.darkseries, type(None) ):
                df=df_full #need this                
                lf.write('Warning: darkseries not found in data of run directory %s\n\n'%folder)            
            else:    
                df=df_full.sub(df_full.darkseries, axis='index')
        else:
            df=df_full #need this
            lf.write('Warning: darkseries attribute is no found on dataframe in folder %s!\n\n'%folder)            

        ### Fit first order baselines automatically?
        if sp.line_fit:
            blines=dynamic_baseline(df, sp.fit_regions )
            df=df-blines 

        ### Convert time axis to specified unit          
        try:
            timeunit=sp.timeunit #Take from params file  
        except AttributeError:
            timeunit='interval'
        df.columns=datetime_convert(df.columns, return_as=timeunit)     

        ### Slice spectra and time start/end points.  Doesn't stop script upon erroringa
        try:
            df=df[sp.tstart: sp.tend] 
        except Exception:
            lf.write('Parameters Error: unable to slice tstart and tend to specified range in directory %s\n\n'%folder)           

        try:
            df=df.ix[sp.x_min: sp.x_max] 
        except Exception:
            lf.write('Parameters Error: unable to slice x_min and x_max range in directory %s\n\n'%folder)      


        transfer_attr(df_full, df, speakup=False)
        df.columns.name=timeunit  #Useful for plotting 2d-3d for autodetection, but not necessary       

        ###### Polygon Plot
        spec_poly3d(df, title=options.rname+'3d Poly Spec')
        plt_clrsave(outdir, options.rname+'polygon')

        ##### Basic spectral and absorbance plots    
        specplot(df, title=options.rname+'Full spectrum')
        plt_clrsave(outdir, options.rname+'full_spectrum')

        absplot(divby(df), title=options.rname+'Relative spectrum' )
        plt_clrsave(outdir, options.rname+'relative')

        ### Look for uv-vis ranges in data, if not found, default to equally slicing spectrum by 7
        try:
            uv_ranges=sp.uv_ranges
            if isinstance(uv_ranges, float) or isinstance(uv_ranges, int):
                uv_ranges=spec_slice(df.index, uv_ranges)   

        except AttributeError:
            uv_ranges=spec_slice(df.index, 8)   

        ### Time averaged plot, not scaled to 1 (relative intenisty dependson bin width and actual intensity)
        dfsliced=wavelength_slices(df, ranges=uv_ranges, apply_fcn='mean')
        range_timeplot(dfsliced, ylabel='Average Intensity', xlabel='Time ('+timeunit+')' ) #legstyle =1 for upper left
        plt_clrsave(outdir, options.rname+'raw_time')

        ### Now scale curves to 1 for objective comparison
        dfsliced_norm=dfsliced.apply(lambda x: x/x[0], axis=1)
        range_timeplot(dfsliced_norm, title='Normalized Range Timeplot', ylabel='Scaled Average Intensity',\
                       xlabel='Time ('+timeunit+')', legstyle=1 )
        plt_clrsave(outdir, options.rname+'norm_time')        

        ### Area plot using simpson method of integration
        dfarea=wavelength_slices(df, ranges=(min(df.index), max(df.index)), apply_fcn='simps')                
        range_timeplot(dfarea, ylabel='Power', xlabel='Time ('+timeunit+')', legend=False,
                       title='Spectral Power vs. Time (%i nm - %i nm)'%  ## Eventually make nm a paremeter and class method
                       (min(df.index), max(df.index)), color='r')
        plt_clrsave(outdir, options.rname+'full_area')


        #### correlation analysis
        outcorr=od+'/corr_analysis'
        os.mkdir(outcorr)        
        ref=make_ref(df, method='empty')     

        S,A=corr_analysis(df, ref)
        sync_3d(S, title='Synchronous Spectrum (%s-%s %s)'%(round(min(df), 1), round(max(df),1), timeunit)) #min/max by columns      
        plt_clrsave(outcorr, options.rname+'full_sync')                
        async_3d(A, title='Asynchronous Spectrum (%s-%s %s)'%(round(min(df), 1), round(max(df),1), timeunit))
        plt_clrsave(outcorr, options.rname+'full_async')        


        absdf=divby(df) 
        S,A=corr_analysis(absdf, ref)        
        sync_3d(S, title='Synchronous Spectrum (%s-%s %s)'%(round(min(df), 1), round(max(df),1), timeunit)) #min/max by columns      
        plt_clrsave(outcorr, options.rname+'relative_sync')                
        async_3d(A, title='Asynchronous Spectrum (%s-%s %s)'%(round(min(df), 1), round(max(df),1), timeunit))
        plt_clrsave(outcorr, options.rname+'relative_async')         


        #### 2d contour plot (solid color or cmap accepted)
        plot2d(df, title='Full Contour', cmap='autumn', contours=7, label=1, colorbar=1, background=1)
        plt_clrsave(outdir, options.rname+'full_contour')        



        ### 3D Plots.  Set row and column step size, eg 10 would mean 10 column traces on the contours ###
        c_iso=10 ; r_iso=10
        kinds=['contourf', 'contour']
        views=( (14, -21), (28, 17), (5, -13), (48, -14), (14,-155) )  #elev, aziumuth
        for kind in kinds:
            out3d=od+'/3dplots_'+kind
            os.mkdir(out3d)

            for view in views:        
                spec_surface3d(df, kind=kind, c_iso=c_iso, r_iso=r_iso, cmap=cmget('gray'), contour_cmap=cmget('autumn'),
                               elev=view[0], azim=view[1], xlabel='Time ('+timeunit+')')
                plt_clrsave(out3d, '%sfull_3d_%s_%s'%(options.rname, view[0], view[1])   )    


                spec_surface3d(divby(df), kind=kind, c_iso=c_iso, r_iso=r_iso, cmap=cmget('gray'), contour_cmap=cmget('autumn'),
                               elev=view[0], azim=view[1], xlabel='Time ('+timeunit+')')
                plt_clrsave(out3d, '%srelative_3d_%s_%s'%(options.rname, view[0], view[1])   )    




    ### Close logfile    
    lf.write('Time for completion, %s'%(round(time.time()-start,1)))
    lf.close()
