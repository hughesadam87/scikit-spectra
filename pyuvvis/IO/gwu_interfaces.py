''' Utilities for converting various file formats to a spectral dataframe.
 To convert a list of raw files, use from_spec_files()
 To convert old-style timefile/spectral data file, use from_timefile_datafile()
 Returns a pandas DataFrame with custom attributes "metadata", "filedict", "darkseries".
 For correct serialization, use spec_serial.py module, not native pickle module.'''

__author__ = "Adam Hughes, Zhaowen Liu"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__version__ = "1.0.1"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

import os

# 3RD Party Imports
from pandas import DataFrame, Series, datetime, read_csv, concat
import numpy as np

# Local imports
from specrecord import MetaData

## For testing
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy import integrate
from advanced_plots import spec_surface3d, surf3d, spec_poly3d
#from dataframeserial import df_dump, df_load
from df_attrhandler import transfer_attr
from spec_labeltools import datetime_convert, spectral_convert
from spec_utilities import boxcar, wavelength_slices, divby
from df_attrhandler import restore_attr
from spec_aesthetics import specplot, timeplot, absplot, range_timeplot, _df_colormapper
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import numpy as np

### Verified OCean Optics month naming conventions (Actually it capitalizes but this call with month.lower() ###
spec_suite_months={'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6, 'jul':7,
                   'aug':8, 'sep':9, 'oct':10, 'nov':11, 'dec':12}  

spec_dtype = np.dtype([ ('wavelength', float), ('intensity', float) ])

def get_files_in_dir(directory):
    ''' Given a directory, this returns just the files in said directory.  Surprisingly
        no one line solution exists in os that I can find '''
    files=[]
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            files.append(directory+'/'+item)
    return files

def get_shortname(filepath, cut_extension=False):
    ''' simply get the filename of fullpath.  Cut extension will remove file extension'''
    shortname=os.path.basename(filepath) 
    if cut_extension:
        shortname=os.path.splitext(shortname)[0]  #Cut file extension
    return shortname


### Following two functions are utilized by both data interfacing functions. ###
def extract_darkfile(filelist, return_null=True):
    ''' Attempts to pick out a dark file from a list using string matching.  Handling of darkfile
    is done by other functions.  Opted to raise errors and warnings here, instead of downstream.

    If return_null: it will return none if no dark file is found.  Otherwise it will raise an error.'''

    darkfiles=[]
    for infile in filelist:
        if "dark" in infile.lower() or "drk" in infile.lower():
            darkfiles.append(infile)

    ### If not darkfiles found, return null or raise ###       
    if len(darkfiles)==0:
        if return_null:
            return None
        else:
            raise Warning("WARNING: Darkfile not found in filelist:  \
         startfile %s - endfile %s"%(filelist[0], filelist[-1]))

    ### If multiple darkfiles found, RAISE a warning ###
    elif len(darkfiles)>1:
        raise Warning("Multiple darkfiles founds in filelist:  \
      startfile %s - endfile %s"%(filelist[0], filelist[-1]))

    else:
        return darkfiles[0]

def get_headermetadata_dataframe(dataframe, time_file_dict, runname=None):
    ''' After creation of the dataframe and datetime-to-file dic, various metadata attributes 
    come together like filecount, filestart, filend etc...
    **run title becomes name of dataframe and can be adopted by plots'''
    filecount=len(dataframe.columns)
    timestart, timeend=dataframe.columns[0], dataframe.columns[-1]
    filestart, fileend=time_file_dict[timestart], time_file_dict[timeend]
    specstart, specend=dataframe.index[0], dataframe.index[-1]

    return {'filecount':filecount, 'timestart':timestart, 'timeend':timeend, 'filestart':filestart, 
            'fileend':fileend, 'specstart':specstart, 'specend':specend}

##########################################################
### Below are the 2 main functions to extract the data ###
##########################################################

def from_spec_files(file_list, specframe=None, skiphead=17, skipfoot=1,\
                    check_for_overlapping_time=True, extract_dark=True, runname=None):
    ''' Takes in raw files directly from Ocean optics spectrometer and creates a spectral dataframe.   
    This is somewhat customized to my analysis, but has general arguments for future adaptations.

    Built to work with 2-column data only!!!

    Dataframe is constructed from a list of dictionaries.
    Each dataframe gets an appended headerdata attribute (dataframe.headerdata) which is a dictionary,
    keyed by columns and stores (infile, header, footer) data so no info is lost between files.

    Constructed to work for non-equally spaced datafiles, or non-identical data (aka wavelengths can have nans).
    **kwargs
       - check_for_overlapping will raise errors if any files have identical times. Otherwise, time
       is overwritten.  Really only useful for testing or otherwise cornercase instances.
       - Extract dark will attempt to find a filename with caseinsenstive string match to "dark".  If dark
       not found, will print warning.  If multiple darks found, will raise error.
       -skiphead/skipfoot are mostly for reminder that this filetype has a 17 line header and a 1 line footer.'''


    ### Need to add functionality for spectral dataframe (join/concat)
    if specframe:
        raise NotImplemented

    dict_of_series={} #Dict of series eventually merged to dataframe   
    time_file_dict={} #Dict of time:filename (darkfile intentionally excluded)

    ### If looking for a darkfile, this will find it.  Bit redundant but I'm lazy..###
    if extract_dark:
        darkfile=extract_darkfile(file_list, return_null=True)

        if darkfile:
            with open(darkfile) as f:
                header=[f.next().strip() for x in xrange(skiphead)]

            wavedata=np.genfromtxt(darkfile, dtype=spec_dtype, skip_header=skiphead, skip_footer=skipfoot) 
            darktime=_get_datetime_specsuite(header)        
            darkseries=Series(wavedata['intensity'], index=wavedata['wavelength'], name=darkfile)

            file_list.remove(darkfile)
            f.close()
        else:
            darkseries=None

    for infile in file_list:

        ###Read in only the header lines, not all the lines of the file
        ###Strips and splits in one go
        with open(infile) as f:
            header=[f.next().strip() for x in xrange(skiphead)]

        ###Store wavelength, intensity data in a 2-column datatime for easy itemlookup 
        ###Eg wavedata['wavelength']
        wavedata=np.genfromtxt(infile, dtype=spec_dtype, skip_header=skiphead, skip_footer=skipfoot) 

        ### Extract time data from header
        datetime=_get_datetime_specsuite(header) 

        ### Make sure timepoints aren't overlapping with any others
        if check_for_overlapping_time:
            try:
                time_file_dict[datetime]
            except KeyError:
                pass
            else:
                raise KeyError('Duplicate time %s found in between files %s, %s'\
                               %(datetime,infile, time_file_dict[datetime]) )

        time_file_dict[datetime]=infile
        dict_of_series[datetime]=Series(wavedata['intensity'], index=wavedata['wavelength'])

        f.close()

    ### Make dataframe, add filenames, darkseries and metadata attributes (note, DateTimeIndex auto sorts!!)
    dataframe=DataFrame(dict_of_series)      
    dataframe.index.name='Wavelength'  #This autodetected in plots
    dataframe.filedict=time_file_dict
    dataframe.darkseries=darkseries
    if runname:
        dataframe.runname=runname    

    ### Take metadata from first file in filelist that isn't darkfile
    for infile in file_list:
        if infile==darkfile:
            pass
        else:
            with open(infile) as f:
                header=[f.next().strip() for x in xrange(skiphead)]         
            meta_partial=_get_metadata_fromheader(header)
            break      

    meta_general=get_headermetadata_dataframe(dataframe, time_file_dict) 
    meta_general.update(meta_partial)
    dataframe.metadata=meta_general   


    return dataframe

def _get_datetime_specsuite(specsuiteheader):
    ''' Special, Ocean-optics specific function to get date information from a their customized header.'''
    dateline=specsuiteheader[2].split()
    year, month, day=int(dateline[6]), dateline[2], int(dateline[3]) 

    month=spec_suite_months[month.lower()]

    hrs, mins, secs=dateline[4].split(':')
    hrs=int(hrs) ; mins=int(mins) ; secs=int(secs)
    return datetime(year, month, day, hrs, mins, secs)

def _get_metadata_fromheader(specsuiteheader):
    ''' Populates metadata attributes from the speactrasuite datafile header'''
    sh=specsuiteheader #for ease in calling
    return {'dark_spec_pres':sh[4].split()[3], 'spectrometer':sh[7].split()[1],  
            'int_unit':sh[8].split()[2], 'int_time':int(sh[8].split()[3]), 
            'spec_avg':int(sh[9].split()[2]), 'boxcar':int(sh[10].split()[2]), 
            'ref_spec_pres':sh[5].split()[3], 'electric_dark_correct':sh[11].split()[4], 
            'strobe_lamp':sh[12].split()[2],'detector_nonlin_correct':sh[13].split()[4], 
            'stray_light_correct':sh[14].split()[4], 'pix_in_spec':int(sh[15].split()[6])}


######### Get dataframe from timefile / datafile #####
## Authors Zhaowen Liu/Adam Hughes, 10/15/12

def from_timefile_datafile(datafile, timefile, extract_dark=True, runname=None): 
    ''' Converts old-style spectral data from GWU phys lab into  
    a dataframe with timestamp column index and wavelength row indicies.

    Creates the DataFrame from a dictionary of Series, keyed by datetime.
    **runname becomes name of dataframe''' 

    tlines=open(timefile,'r').readlines()
    tlines=[line.strip().split() for line in tlines]           
    tlines.pop(0)

    time_file_dict=dict((_get_datetime_timefile(tline),tline[0]) for tline in tlines)

    ### Read in data matrix, separate first row (wavelengths) from the rest of the data
    wavedata=np.genfromtxt(datafile, dtype='float', skip_header=1)
    data, wavelengths=wavedata[:,1::], wavedata[:,0] #Separate wavelength column

    ### Sort datetimes here before assigning/removing dark spec etc...
    sorted_tfd=sorted(time_file_dict.items())
    sorted_times, sorted_files=zip(*( (((i[0]), (i[1])) for i in sorted_tfd)))

    ### Seek darkfile.  If found, take it out of dataframe. ###
    if extract_dark:
        darkfile=extract_darkfile(sorted_files, return_null=True)   

    if darkfile:    
        ####Fine darkseries by reverse lookup (lookup by value) and get index position

        #darkindex, darktime=[(idx, time) for idx, (time, afile) in enumerate(sorted_tfd) if afile == darkfile][0]
        darkindex=sorted_files.index(darkfile)
        darktime=sorted_times[darkindex]
        darkseries=Series(data[:,darkindex], index=wavelengths, name=darkfile) 


        del time_file_dict[darktime] #Intentionally remove
        sorted_times=list(sorted_times) #Need to do in two steps
        sorted_times.remove(darktime)
        data=np.delete(data, darkindex, 1)  #Delete dark column from numpy data           
    else:
        darkseries=None

    dataframe=DataFrame(data, columns=sorted_times, index=wavelengths)      


    ### Add field attributes to dataframe
    dataframe.darkseries=darkseries 
    dataframe.filedict=time_file_dict
    if runname:
        dataframe.runname=runname

    ### Get headermeta data from first line in timefile that isn't darkfile.  Only checks one line
    ### Does not check for consistency
    for line in tlines:
        if line[0]==darkfile:
            pass
        else:
            meta_partial=_get_headermetadata_timefile(line[0])  #DOUBLE CHECK THIS WORKS
            break   

    ### Extract remaining metadata (file/time info) and return ###
    meta_general=get_headermetadata_dataframe(dataframe, time_file_dict) 
    meta_general.update(meta_partial)
    dataframe.metadata=meta_general
    dataframe.index.name='Wavelength'  #This autodetected in plots    

    ### Sort dataframe by ascending time (could also sort spectral data) ###
    dataframe.sort(axis=1, inplace=True) #axis1=columns

    return dataframe

def from_gwu_chem_IR(filelist, sortnames=False, shortname=True, cut_extension=False):
    ''' Format for comma delimited two column data from GWU chemistry's IR.  These have no useful metadata
    or dark data nad so it is important that users either pass in a correctly sorted filelist.  Once the 
    dataframe is created, on can do df=df.reindex(columns=[correct order]).  
    
    It uses read_csv() to and creates a list of dataframes.  Afterwards, concat() merges these.
    
    Kwds:
       sortnames- Will attempt to autosort the filelist. Otherwise, order of files passed in is
                  directly used as columns.
       shortname- If false, full file path is used as the column name.  If true, only the filename is used. 
       
       cut_extension- If using the shortname, this will determine if the file extension is saved or cut from the data.'''

    if shortname:
        fget=lambda x:get_shortname(x, cut_extension=cut_extension)
    else:
        fget=lambda x: x
    
    ### Either full names or short names of filelist    
    working_names=[fget(afile) for afile in filelist]
        

    dflist=[read_csv(afile, sep=',', header=None, index_col=0, skiprows=2, na_values=' \r',
                               names=[fget(afile)]) for afile in filelist]
    
    ### THIS IS BUSTED, PUTTING NANS EVERYWHERE EXCEPT ONE FILE, but dflist itself ws nice.
    dataframe=concat(dflist, axis=1)
                        
    ### concat tries to sort these, so this will preserve the sort order
    if sortnames:
        dataframe=dataframe.reindex(columns=sorted(working_names))

    dataframe.metadata=None
    dataframe.filedict=None
    dataframe.darkseries=None
    dataframe.index.name='Wavelength'  #This autodetected in plots    
    
    return dataframe
            

def _get_datetime_timefile(splitline):
    ''' Takes in SPLIT line of timefile (aka a list), returns datetime object '''
    hrs, mins, secs=splitline[4].split(':')
    hrs=int(hrs) ; mins=int(mins) ; secs=int(secs)
    day, month, year=int(splitline[3]), spec_suite_months[splitline[2].lower()], int(splitline[1])

    return datetime(year, month, day, hrs, mins, secs)   

def _get_headermetadata_timefile(splitline):
    ''' Return the reduced, available components of headermetadata from timefile (missing data).''' 
    ### Take items that are present ###
    filldic=dict(zip(['int_time', 'int_unit', 'spec_avg', 'boxcar'], splitline[5:]))

    ### Append null for items that are missing ###
    missing=('spectrometer','dark_spec_pres', 'ref_spec_pres', 'electric_dark_correct', 
             'strobe_lamp', 'detector_nonlin_correct', 'stray_light_correct', 'pix_in_spec')
    missingdic=dict((item, None) for item in missing)

    ### MANUALLY ADDING SPECTROMETER FOR THIS DATATYPE! COULD BE PROBLEMATIC IF I CHANGE SPECTROMETERS
    ### OR USE THIS PROGRAM TO OPEN OTHER DATAFILES (UNLIKELY)
    missingdic['spectrometer']='USB2E7196'  

    return missingdic

### NOTE TO SELF:
    # TO FIX (Datetime is being ordered automatically but not taking in account year, month, it is actually
    # not working.  Fix this, and think about including ordered dict to prevent this!

if __name__=='__main__':
    #filelist=get_files_in_dir('NPConcentration')
    #df=from_gwu_chem_IR(filelist, sortnames=True)
    df=from_timefile_datafile('./npsam/All_f1_npsam_by_1', './npsam/f1_npsam_timefile.txt')
    
    ### subtract the dark spectrum
    df=df.sub(df.darkseries, axis='index')


    df.columns=datetime_convert(df.columns, return_as='seconds')
    

    #df=boxcar(df, 2.0)
    dfsliced=wavelength_slices(df, ranges=((350.0,370.0), (450.0,500.0), (550.0,570.0), (650.0,680.0), (680.0,700.0)),\
                               apply_fcn='simps')
                             #  apply_fcn=np.histogram, bins=3)

    dfarea=wavelength_slices(df, ranges=(min(df.index), max(df.index)), apply_fcn='simps')
                             
    df=df.ix[400.0:700.0]
   # colormapper=_df_colormapper(df, axis=0, vmin=300.0, vmax=700.0, cmap=cm.gist_heat)
    #specplot(df, colors=colormapper)
    #plt.show()

#    timeplot(df, colors=_df_colormapper(df, axis=1,cmap=cm.autumn))
    range_timeplot(dfsliced)
    plt.show()
    df=boxcar(df, 10.0, axis=1)


    df=df.ix[400.0:800.0] 
    #df=df.ix[500.0:600.0]
   
    #spec_surface3d(df, kind='contourf', xlabel='Time (s)', ylabel='Wavelength (nm)')
  

    #plt.title('9/5/12 NPSam')
    #plt.show()
              
    #spec_surface3d(df, kind='contourf', xlabel='Time (s)', ylabel='Wavelength (nm)')
    #spec_surface3d(df)



    #mlab.surf(np.asarray(list(df.columns)), np.asarray(list(df.index)) , np.asarray(df), warp_scale='auto')
    spec_poly3d(df)
    plt.show()

    #transfer_attr(df, df2)     
    #specax=specplot(df2)

    #dftime=df.transpose()  ### Store a custom axis.
    #dftime.runname='Spec test name'
    #timeax=timeplot(dftime)
    #fig = plt.figure()
    #fig.axes.append(timeax)

    hz=spectral_convert(df.index)
    print 'hi'
    #df=df.transpose()
    #plt.figure()
    #df.plot()
    #plt.leged=False
    #plt.show()
