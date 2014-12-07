''' Utilities for converting various file formats to a skspec TimeSpectra.
 To convert a list of raw files, use from_spec_files()
 To convert old-style timefile/spectral data file, use from_timefile_datafile()
 To convert spectral datafiles from Ocean Optics USB2000 and USB650, pas file list in 
 from_spec_files.
 
 Returns a skspec TimeSpectra with custom attributes "metadata", "filedict", "baseline".
 '''

__author__ = "Adam Hughes, Zhaowen Liu"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

import os

# 3RD Party Imports
from pandas import DataFrame, Series, datetime, read_csv, concat
import numpy as np

# skspec imports
from skspec.core.timespectra import TimeSpectra
from skspec.core.specindex import SpecIndex
from skspec.core.file_utils import get_files_in_dir, get_shortname


import logging
logger = logging.getLogger(__name__)


### Verified OCean Optics month naming conventions (Actually it capitalizes but this call with month.lower() ###
spec_suite_months={'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6, 'jul':7,
                   'aug':8, 'sep':9, 'oct':10, 'nov':11, 'dec':12}  

spec_dtype = np.dtype([ ('wavelength', float), ('intensity', float) ])


def get_shortname(filepath, cut_extension=False):
    ''' simply get the filename of fullpath.  Cut extension will remove file extension'''
    shortname = os.path.basename(filepath) 
    if cut_extension:
        shortname = os.path.splitext(shortname)[0]
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

def get_headermetadata_dataframe(dataframe, time_file_dict, name=''):
    ''' After creation of the dataframe and datetime-to-file dic, various metadata attributes 
    come together like filecount, filestart, filend etc...
    **run title becomes name of dataframe and can be adopted by plots'''
    filecount=len(dataframe.columns)
    timestart, timeend=dataframe.columns[0], dataframe.columns[-1]
    filestart, fileend=time_file_dict[timestart], time_file_dict[timeend]
    specstart, specend=dataframe.index[0], dataframe.index[-1]

    return {'filecount':filecount, 
            'timestart':timestart, 
            'timeend':timeend, 
            'filestart':filestart, 
            'fileend':fileend, 
            'specstart':specstart, 
            'specend':specend}

##########################################################
### Below are the 2 main functions to extract the data ###
##########################################################

def from_spec_files(file_list, name='', skiphead=17, skipfoot=1, check_for_overlapping_time=True, extract_dark=True):
    ''' Takes in raw files directly from Ocean optics USB2000 and USB650 spectrometers and returns a
    skspec TimeSpectra. If spectral data stored without header, can be called with skiphead=0.

    Parameters
    ----------
       name: Set name of returned TimeSpectra.
       
       check_for_overlapping_time: will raise errors if any files have identical times. Otherwise, time
                                   is overwritten.  Really only useful for testing or otherwise cornercase instances.
       
       extract_dark: Attempt to find a filename with caseinsenstive string match to "dark".  If dark spectrum
                     not found, will print warning.  If multiple darks found, will raise error.
      
       skiphead/skipfoot: Mostly for reminder that this filetype has a 17 line header and a 1 line footer.
       
    Notes
    -----
        Built to work with 2-column data only!!!

        Dataframe is constructed from a list of dictionaries.
        Each dataframe gets an appended headerdata attribute (dataframe.headerdata) which is a dictionary,
        keyed by columns and stores (infile, header, footer) data so no info is lost between files.

        Constructed to work for non-equally spaced datafiles, or non-identical data (aka wavelengths can have nans).
    '''

    dict_of_series={} #Dict of series eventually merged to dataframe   
    time_file_dict={} #Dict of time:filename (darkfile intentionally excluded)
    
    _overlap_count = 0 # Tracks if overlapping occurs

    ### If looking for a darkfile, this will find it.  Bit redundant but I'm lazy..###
    if extract_dark:
        darkfile=extract_darkfile(file_list, return_null=True)

        if darkfile:
            with open(darkfile) as f:
                header=[f.next().strip() for x in xrange(skiphead)]

            wavedata=np.genfromtxt(darkfile, dtype=spec_dtype, skip_header=skiphead, skip_footer=skipfoot) 
            darktime=_get_datetime_specsuite(header)        
            baseline=Series(wavedata['intensity'], index=wavedata['wavelength'], name=darkfile)

            file_list.remove(darkfile)
            f.close()
        else:
            baseline=None
            
    file_list = [f for f in file_list 
                 if os.path.basename(f) != '.gitignore']

    for infile in file_list:

        ###Read in only the header lines, not all the lines of the file
        ###Strips and splits in one go
        with open(infile) as f:
            header=[f.next().strip() for x in xrange(skiphead)]

        #Store wavelength, intensity data in a 2-column datatime for easy itemlookup 
        #Eg wavedata['wavelength']
        wavedata=np.genfromtxt(infile, dtype=spec_dtype, skip_header=skiphead, skip_footer=skipfoot) 

        # Extract time data from header
        datetime=_get_datetime_specsuite(header) 
        
        if datetime in time_file_dict:
            _overlap_count += 1        

        # Make sure timepoints aren't overlapping with any others
        if check_for_overlapping_time and _overlap_count:
            raise IOError('Duplicate time %s found in between files %s, %s.'
                          ' To overwrite, set check_for_overlapping_time = False.'
                           %( datetime, infile, time_file_dict[datetime] ))            
            

        time_file_dict[datetime]=infile
        dict_of_series[datetime]=Series(wavedata['intensity'], index=wavedata['wavelength'])

        f.close()

    ### Make timespec, add filenames, baseline and metadata attributes (note, DateTimeIndex auto sorts!!)
    timespec=TimeSpectra(DataFrame(dict_of_series), name=name) #Dataframe beacuse TS doesn't handle dict of series
    timespec.specunit='nm'
    timespec.filedict=time_file_dict
    timespec.baseline=baseline  #KEEP THIS AS DARK SERIES RECALL IT IS SEPARATE FROM reference OR REFERENCE..  

    ### Take metadata from first file in filelist that isn't darkfile
    for infile in file_list:
        if infile != darkfile:
            with open(infile) as f:
                header=[f.next().strip() for x in xrange(skiphead)]         
            meta_partial=_get_metadata_fromheader(header)
            break      

    meta_general=get_headermetadata_dataframe(timespec, time_file_dict) 
    meta_general.update(meta_partial)
    timespec.metadata=meta_general   

    if _overlap_count:
        logger.warn('Time duplication found in %s of %s files.  Duplicates were '
            'removed!' % (_overlap_count, len(file_list)))
            
    return timespec


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
# Authors Zhaowen Liu/Adam Hughes, 10/15/12

def from_timefile_datafile(datafile, timefile, extract_dark=True, name=''): 
    ''' Converts old-style spectral data from GWU phys lab into  
    a dataframe with timestamp column index and wavelength row indicies.

    Creates the DataFrame from a dictionary of Series, keyed by datetime.
    **name becomes name of dataframe''' 

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
        ####Find baseline by reverse lookup (lookup by value) and get index position

        #darkindex, darktime=[(idx, time) for idx, (time, afile) in enumerate(sorted_tfd) if afile == darkfile][0]
        darkindex=sorted_files.index(darkfile)
        darktime=sorted_times[darkindex]
        baseline=Series(data[:,darkindex], index=wavelengths, name=darkfile) 


        del time_file_dict[darktime] #Intentionally remove
        sorted_times=list(sorted_times) #Need to do in two steps
        sorted_times.remove(darktime)
        data=np.delete(data, darkindex, 1)  #Delete dark column from numpy data           
    else:
        baseline=None

    dataframe=TimeSpectra(data, columns=sorted_times, index=wavelengths)      
    

    ### Add field attributes to dataframe
    dataframe.baseline=baseline 
    dataframe.filedict=time_file_dict
    if name:
        dataframe.name=name

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
    dataframe.specunit='nm'  #This autodetected in plots    

    ### Sort dataframe by ascending time (could also sort spectral data) ###
    dataframe.sort(axis=1, inplace=True) #axis1=columns

    return dataframe

def from_gwu_chem_UVVIS(filelist, sortnames=False, shortname=True, cut_extension=False, name=''):
    ''' Format for comma delimited two column data from GWU chemistry's UVVis.  These have no useful metadata
    or dark data and so it is important that users either pass in a correctly sorted filelist.  Once the 
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
        

    dflist=[read_csv(afile, sep=',', header=None, index_col=0, skiprows=2, na_values=' ',  #Used to be ' \r', or is this from IR?
                               names=[fget(afile)]) for afile in filelist]
    
    ### THIS IS BUSTED, PUTTING NANS EVERYWHERE EXCEPT ONE FILE, but dflist itself ws nice.
    dataframe=concat(dflist, axis=1)
                        
    ### concat tries to sort these, so this will preserve the sort order
    if sortnames:
        dataframe=dataframe.reindex(columns=sorted(working_names))

    dataframe=TimeSpectra(dataframe) #this is fine

    dataframe.metadata=None
    dataframe.filedict=None
    dataframe.baseline=None
    dataframe.specunit='nm' #This autodetected in plots    
    if name:
        dataframe.name=name
    
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

def from_oceanoptics(directory, sample_by=None, sort=True, **from_spec_files_kwds):
    ''' Wrapper to from_spec_files to both generate a file list from a directory and read files into time spectra.
        
        Parameters:
        -----------
            directory: directory with raw spectral files.
            sample_by: Sample every X files.  (Useful for reducing large datsets prior to readin)
            **from_spec_files_kwds: All kwds passed to from_spec_files().
            
        Notes:
        ------
            Slice works by taking the 0 file every time and counting from there.  So if you enter sample_by=3,
            expect to get files 0, 3, 6 etc... but if sample_by_10, you get files 0,10,20
    '''
    
    files=get_files_in_dir(directory, sort=sort)

    if sample_by:    
        files=files[0::sample_by]  #Slice already takes cares of most errors
    
    return from_spec_files(files, **from_spec_files_kwds)

if __name__=='__main__':
    # Assumes datapath is ../data/gwuspecdata...
    
    ### Test of raw fiber spectral data
    
    ts=from_oceanoptics('../data/gwuspecdata/fiber1', sample_by=10, sort=True, name='oceanopticstest')

    files=get_files_in_dir('../data/gwuspecdata/fiber1')
    ts=from_spec_files(files, name='Test Spectra')
    #print ts, type(ts)
    
    ### Test of timefile/datafile
    #dfile='../data/gwuspecdata/ex_tf_df/11_data.txt'
    #tfile='../data/gwuspecdata/ex_tf_df/11_tfile.txt'
    #ts2=from_timefile_datafile(dfile, tfile, extract_dark=True, name='Test Spec 2')
    #print ts2, type(ts2)
    
    ### Test of chem UVVIS data
    files=get_files_in_dir('../data/gwuspecdata/IRData')
    ts3=from_gwu_chem_UVVIS(files, name='IR Spec')
    print ts3, type(ts3), ts3[ts3.columns[0]]
    
    ### ADD CHEM IR DATA (Did it in a notebook at one point actually)