import os
from optparse import OptionParser

## For testing
import matplotlib.pyplot as plt, sys
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D

from scipy import integrate
import numpy as np


### ONCE DONE, DELETE AND THEN REPLACE PYUVVIS EVERWHERE
sys.path.append('../../pyuvvis')
from pyplots.advanced_plots import spec_surface3d, surf3d, spec_poly3d
from pandas_utils.dataframeserial import df_load, df_dump
from pandas_utils.df_attrhandler import transfer_attr
from core.spec_labeltools import datetime_convert, spectral_convert
from core.spec_utilities import boxcar, wavelength_slices, divby
from pyplots.spec_aesthetics import specplot, timeplot, absplot, range_timeplot, _df_colormapper
from IO.gwu_interfaces import from_timefile_datafile, get_files_in_dir, from_spec_files


### UPDATE PACKAGE THEN CHANGE THIS
#from pyuvvis.core.imk_utils import make
from imk_utils import make_root_dir, get_files_in_dir, get_shortname

def plt_clrsave(outpath, outname):
    ''' Save plot then clear afterwards '''
    plt.savefig('%s/%s' %(outpath, outname) )
    plt.clf()
    


if __name__=='__main__':  
    
    img_ignore=['png', 'jpeg', 'tif', 'bmp'] #no .
    logfilename='RUNLOG'
    
    parser = OptionParser(usage='usage: %prog -i indirectory -o outdirectory ', version='%prog 0.1.0')
    parser.add_option('-d', '--indir',
                      action='store',
                      dest='wd',
                      default='./scripttest', #REMOVE
                      help='Path to root directory where file FOLDERS are located',)
    parser.add_option('-o', '--outdir',
                      action='store',
                      dest='od',
                      default='./junk',  #Remove
                      help='Path to root directory where output folder is built',) 

    parser.add_option('-r', '--runname',
                      action='store',
                      dest='rname',
                      default='', #None causes errors
                      help='Title of trial/run, used in plot titles and other places.',)     
    
    parser.add_option('-i', '--ignore', action='store_true', default=True, #type='choice', choices=['True', 'False'],
                      dest='ignore',  help='Ignore the most commonly found image types \
                      (.png, .jpeg etc...) when parsing data files.')
    
    parser.add_option('-c', '--clean', action='store_true', default=True, #REMOVE
                       dest='clean',
                       help='This will clean and overwrite files found in the output directory\
                       before writing new results.  Careful, this will delete ALL files in any\
                       directory that you pass.')
                       
    
    (options, args) = parser.parse_args()
    
    ### Arguments will default to None
    inroot, outroot=options.wd, options.od 
    if inroot==None or outroot == None:
        parser.error("Please both enter an indirectory (-d) and outdirectory (-o)")

    if options.rname !='':
        options.rname+='_'  #Add underscore to runname if it exists
    
    ### Open logfile
    lf=open(outroot + '/'+ logfilename, 'w')


    ### Walk subdirectories    
    walker=os.walk(inroot, topdown=True, onerror=None, followlinks=False)
    (rootpath, rootdirs, rootfiles)= walker.next()
    for folder in rootdirs:    

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
            raise IOError('Output directory %s already exists.\n  To overwrite, use option -c True.  Use with caution\n\
            preexisting data will be deleted from directory!'%(od))
        
        ### READ IN GWU DATA.  IF PICKLE FILE IS FOUND IN DIRECTORY, THIS IS USED FIRST.
        ### IF NOT, DATAFIELS ARE USED.  IF DATEFILES==2, USES TIMEFILE-DATAFILE
        ### OTHERWISE, IT USES FROM_SPEC_FILES

        picklefile=[afile for afile in infiles if afile.split('.')[-1]=='pickle']
        
        if len(picklefile)>1:
            lf.write('Failed to load in folder, %s, had more than one .pickle files.\n'%folder)
            raise IOError('Indirectory must contain only one pickle file if you want to use it!!!')
     
        elif len(picklefile)==1:
            df_full=df_load(picklefile[0])        
            lf.write('Loaded contents of folder, %s, using the ".pickle" file, %s.\n'%(folder, get_shortname(picklefile[0])))            
            
        ### If no picklefile found try reading in datafile directly
        else:
            if len(infiles) == 2:
                timefile=[afile for afile in infiles if 'time' in afile.lower()]
                if len(timefile) == 1:
                    infiles.remove(timefile[0])
                    df_full=from_timefile_datafile(datafile=infiles[0], timefile=timefile[0])
                    lf.write('Loading contents of folder, %s, using the timefile/datafile conventional import\n'%folder)   
 
                ### ACCOUNT FOR REMOTE POSSIBILITY THAT 2 FILES COULD STILL JUST BE TWO RAW DATA FILES INSTEAD OF DATAFILE/TIMEFILE
                elif len(timefile) == 0:
                    df_full=from_spec_files(infiles)
                    lf.write('Loading contents of folder, %s, multiple raw spectral files %s.  (If these were \
                    supposed to be datafile/timefile and not raw files, couldnt find word "time" in filename.) \
                    \n'%(folder, len(infiles))) 

                else:
                    lf.write('Failure: multiple timefile matches found in folder %s\n'%folder)                                
                    raise IOError('Timefile not found.  File must contain word "time"')                    
                
            else:
                df_full=from_spec_files(infiles)
                lf.write('Loading contents of folder, %s, multiple raw spectral files %s.\n'%(folder, len(infiles)))            
                
                
                

        ### Output the pickled dataframe    
        df_dump(df_full, outdir+'/rundata.pickle')
        
        ### Subtract the dark spectrum if it has one.  Note that all program should produce an attribute for darkseries,
        ### which may be None, but the attribute should still be here.
        if hasattr(df_full, 'darkseries'):
            if isinstance(df_full.darkseries, type(None) ):
                df=df_full #need this                
                lf.write('Warning: darkseries not found in data of run directory %s'%folder)            
            else:    
                df=df_full.sub(df_full.darkseries, axis='index')
        else:
            df=df_full #need this
            lf.write('Warning: darkseries attribute is no found on dataframe in folder %s !'%folder)            

        
        ### Make parameter.  Really don't need this except autoscaling plots with the full data, primarily setting
        ### the xlim manually and autoscaling the yaxis is a bit tricky.
        df=df.ix[430.0: 680.0] 


        ### Replace columns with default time unit (seconds)
        timeunit='seconds' #Take from params file         
        df.columns=datetime_convert(df.columns, return_as=timeunit)  
        transfer_attr(df_full, df, speakup=False)
        

        ### Fix colors after uploading    
        specplot(df, title=options.rname+'full_spectrum', colors=None)
        plt_clrsave(outdir, options.rname+'full_spectrum')
        
        absplot(divby(df), title=options.rname+'relative_spectrum' )
        plt_clrsave(outdir, options.rname+'relative')
       
        ### Make parameter
        uv_ranges=((430.0,450.0), (450.0,515.0),(515.0,570.0),(570.0, 620.0),(620.0, 680.0) )      
       
        ### Time averaged plot, not scaled to 1 (relative intenisty depend son bin width and actual intensity)
        dfsliced=wavelength_slices(df, ranges=uv_ranges, apply_fcn='mean')
        range_timeplot(dfsliced, ylabel='Average Intensity', xlabel='Time ('+timeunit+')' )
        plt_clrsave(outdir, options.rname+'raw_time')
        
        ### Now scale curves to 1 for objective comparison
        dfsliced_norm=dfsliced.apply(lambda x: x/x[0], axis=1)
        range_timeplot(dfsliced_norm, ylabel='Scaled Average Intensity', xlabel='Time ('+timeunit+')' )
        plt_clrsave(outdir, options.rname+'norm_time')        
        
        
        dfarea=wavelength_slices(df, ranges=(min(df.index), max(df.index)), apply_fcn='simps')                
        range_timeplot(dfarea, ylabel='Power', xlabel='Time ('+timeunit+')', legend=False,
                       title='Spectral Power vs. Time (%i nm - %i nm)'%  ## Eventually make nm a paremeter and class method
                       (min(df.index), max(df.index)), colors=None)
        plt_clrsave(outdir, options.rname+'full_area')
        
        
        
        ### 3D Plots.  Set row and column step size, eg 10 would mean 10 column traces on the contours ###
        c_iso=10 ; r_iso=10
        kinds=['contourf', 'contour']
        views=( (14, -21), (10,-30) )  #elev, aziumuth
        for kind in kinds:
            out3d=od+'/3dplots_'+kind
            os.mkdir(out3d)
        
            for view in views:        
                spec_surface3d(df, kind=kind, c_iso=c_iso, r_iso=r_iso, cmap=cm.autumn, elev=view[0], azim=view[1],
                               xlabel='Time ('+timeunit+')')
                plt_clrsave(out3d, '%sfull_3d_%s_%s'%(options.rname, view[0], view[1])   )    
                
         
                spec_surface3d(divby(df), kind=kind, c_iso=c_iso, r_iso=r_iso, cmap=cm.autumn, elev=view[0], azim=view[1],
                               xlabel='Time ('+timeunit+')')
                plt_clrsave(out3d, '%srelative_3d_%s_%s'%(options.rname, view[0], view[1])   )    
        

        

    ### Close logfile    
    lf.close()
            

    
    #df_stream=pkgutil.get_data('pyuvvis', 'data/example_data/spectra.pickle') 
    #df=df_loads(df_stream)
    
    #### subtract the dark spectrum
    #df=df.sub(df.darkseries, axis='index')


    #df.columns=datetime_convert(df.columns, return_as='seconds')
    

    ##df=boxcar(df, 2.0)
    #dfsliced=wavelength_slices(df, ranges=((350.0,370.0), (450.0,500.0), (550.0,570.0), (650.0,680.0), (680.0,700.0)),\
                               #apply_fcn='simps')
                             ##  apply_fcn=np.histogram, bins=3)

    #dfarea=wavelength_slices(df, ranges=(min(df.index), max(df.index)), apply_fcn='simps')
                             
    #df=df.ix[400.0:700.0]
   ## colormapper=_df_colormapper(df, axis=0, vmin=300.0, vmax=700.0, cmap=cm.gist_heat)
    ##specplot(df, colors=colormapper)
    ##plt.show()

##    timeplot(df, colors=_df_colormapper(df, axis=1,cmap=cm.autumn))
    #range_timeplot(dfsliced)
    #plt.show()
    #df=boxcar(df, 10.0, axis=1)


    #df=df.ix[400.0:800.0] 
    ##df=df.ix[500.0:600.0]
   
    ##spec_surface3d(df, kind='contourf', xlabel='Time (s)', ylabel='Wavelength (nm)')
  

    ##plt.title('9/5/12 NPSam')
    ##plt.show()
              
    ##spec_surface3d(df, kind='contourf', xlabel='Time (s)', ylabel='Wavelength (nm)')
    ##spec_surface3d(df)



    ##mlab.surf(np.asarray(list(df.columns)), np.asarray(list(df.index)) , np.asarray(df), warp_scale='auto')
    #spec_poly3d(df)
    #plt.show()

    ##transfer_attr(df, df2)     
    ##specax=specplot(df2)

    ##dftime=df.transpose()  ### Store a custom axis.
    ##dftime.runname='Spec test name'
    ##timeax=timeplot(dftime)
    ##fig = plt.figure()
    ##fig.axes.append(timeax)

    #hz=spectral_convert(df.index)
    #print 'hi'
    ##df=df.transpose()
    ##plt.figure()
    ##df.plot()
    ##plt.leged=False
    ##plt.show()
