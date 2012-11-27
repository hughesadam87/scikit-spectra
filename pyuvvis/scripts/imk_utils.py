from operator import attrgetter
import os, shutil

def get_shortname(filepath, cut_extension=False):
    ''' simply get the filename of fullpath.  Cut extension will remove file extension'''
    shortname=os.path.basename(filepath) 
    if cut_extension:
        shortname=os.path.splitext(shortname)[0]  #Cut file extension
    return shortname

def sort_summary(summary_file, delim='\t'):
    f=open(summary_file, 'r')
    lines=f.readlines()
    lines=[line.strip().split(delim) for line in lines]
    header=lines.pop(0)
    f.close()
    ### Tries to sort by filenames then magnification of form 'f1_3000.tif'
    try:
        lines=sorted(lines, key=lambda item: (item[0].split('_')[0], int( item[0].split('_')[1].strip('.tif')) ) )
    except Exception:
        ### Following exceptions are adhoc fixes for non-standard run names.
        ## Test for style ## F1_b2_30kx... (8/13/12)
        firstname=lines[0][0].split('_')
        if 'f' in firstname[0] and 'b' in firstname[1]:
            try:
                lines=sorted(lines, key=lambda item: (item[0].split('_')[1],(item[0].split('_')[0] ) ))
            except Exception:
                print 'Could not sort summary file, failed at A'


        ## Test for style ## 8_b2_f1_... (8/6/12)                        
        elif 'f' in firstname[2] and 'b' in firstname[1]:
            try:
                lines=sorted(lines, key=lambda item: (item[0].split('_')[1],(item[0].split('_')[2] ),(item[0].split('_')[3] ) ))
            except Exception:
                print 'Could not sort summary file, failed at B'

       ### TO ADD ###     
       ## Test for style ## 8_b2_f1_... (8/6/12) (test for 822)                       

    else:
        f=open(summary_file, 'w')
        f.write(delim.join(header)+'\n\n')
        for i, line in enumerate(lines):
            ### Add a row divider between fibers
            if i > 0:
                if lines[i][0].split('_')[0] != lines[i-1][0].split('_')[0]:  #If switching fibers
                    f.write('\n')
                    
            f.write(delim.join(line) + '\n')

        f.close()

def get_files_in_dir(directory):
    ''' Given a directory, this returns just the files in said directory.  Surprisingly
        no one line solution exists in os that I can find '''
    files=[]
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            files.append(directory+'/'+item)
    return files

### The following methods navigate subdirectories and return file names in dictionaries ###

def magdict_foldersbymag(indir):
    ''' Makes a dictionary keyed by magnification of all files in subdirectories stored by magnification.
    Key=mag
    Value=Rootdirectory, [files]'''
    scaledict={}
    walker=os.walk(indir, topdown=True, onerror=None, followlinks=False)
    ### Walk subdirectories
    (rootpath, rootdirs, rootfiles)= walker.next()
  #  outfiles=[(path+'/'+f) for f in files]
    for d in rootdirs:
        mag=d  #Value for magnification is in filename
        try:
            mag=int(mag)  #Raw magnification
        except:
            ValueError
            try:
                mag=int(mag.strip('k') )
                mag=mag*1000 #SCALE UP BY 1000            
            except:
                ValueError
                print 'failed to convert', d
            else:
                outfiles=get_files_in_dir(rootpath+'/'+d)
                scaledict[mag]=(d, tuple(outfiles) )
        else:
            outfiles=get_files_in_dir(rootpath+'/'+d)            
            scaledict[mag]=(d, tuple(outfiles) )
    return scaledict

def magdict_foldersbyrun(indir):
    ''' Makes a dictionary keyed by magnification of all files in subdirectories stored by run.
    This function, unlike scaledict, will exam all folders in the indirectory, but only can
    keep files if they have a magnifciation in their name with underscore delimiters.  Returns
    any files that were not understood.
    Key=mag
    Value=Rootdirectory, [files]'''
    raise NotImplementedError('This module is broken, really it is tough to return key by \
    mag because of how directory is structured.  Makes for sense to just use rundict_foldersbyrun\
    and modify main_script.py to make right outdir')
    filedict={}
    walker=os.walk(indir, topdown=True, onerror=None, followlinks=False)
    ### Walk subdirectories
    (rootpath, rootdirs, rootfiles)= walker.next()
    warnings=[] #Stores names of files that could not be 
    for folder in rootdirs:
        all_files=get_files_in_dir(rootpath+'/'+folder) #list of lists (files per folder)           
        for afile in all_files:
            shortname=get_shortname(afile, cut_extension=True)
            sfile=shortname.split('_')  #Will not error even if no underscore
            mag=[]  #Store magnification of file
            for piece in sfile:
                try:
                    number=int(piece)
                except ValueError:
                    pass
                else:
                    mag.append(number)
            if len(mag) != 1:
                warnings.append(get_shortname(afile, cut_extension=False))
            else:
                mag=mag[0]
                if mag not in filedict.keys():
                    filedict[mag]=[]
                for entry in filedict[mag]:
                    if not entry:  #If list is empty
                        filedict[mag].append([folder, [] ])
                filedict[mag].insert(0, [folder, [] ] )
                filedict[mag][0][1].append(afile)
    warnings='\t'.join(warnings)
    return filedict, warnings


def rundict_foldersbyrun(indir):
    ''' Takes in folders by run and keys dictionary by folder name.  Values are 
    magnification to filename pairs.  If magnification can't be determined from
    filename, warnings will track it.
    
    Key=Rootdirectory
    Value=mag, [files]'''
    filedict={}
    walker=os.walk(indir, topdown=True, onerror=None, followlinks=False)
    ### Walk subdirectories
    (rootpath, rootdirs, rootfiles)= walker.next()
    all_files=[get_files_in_dir(rootpath+'/'+d) for d in rootdirs] #list of lists (files per folder)   
    warnings=[] #Stores names of files that could not be 
    for folder in rootdirs:
        filedict[folder]=[]
        for afile in get_files_in_dir(rootpath + '/'+d):
            shortname=get_shortname(afile, cut_extension=True)
            sfile=shortname.split('_')  #Will not error even if no underscore
            mag=[]  #Store magnification of file
            for piece in sfile:
                try:
                    number=int(piece)
                except ValueError:
                    pass
                else:
                    mag.append(number)
            if len(mag) != 1:
                warnings.append(get_shortname(afile, cut_extension=False))
            else:
                mag=mag[0]
                filedict[folder].append( (mag, afile) )
    warnings='\t'.join(warnings)
    return filedict, warnings    
    
    
                
                
                    
            
                
        
        #mag=d  #Value for magnification is in filename
        #try:
            #mag=int(mag)  #Raw magnification
        #except:
            #ValueError
            #try:
                #mag=int(mag.strip('k') )
                #mag=mag*1000 #SCALE UP BY 1000            
            #except:
                #ValueError
                #print 'failed to convert', d
            #else:
                #outfiles=get_files_in_dir(rootpath+'/'+d)
                #scaledict[mag]=(d, tuple(outfiles) )
        #else:
            #outfiles=get_files_in_dir(rootpath+'/'+d)            
            #scaledict[mag]=(d, tuple(outfiles) )
    #return scaledict    
    
            
def make_root_dir(rootout, overwrite=False):
    ''' Creates directory structure for program results output.  Warning, if overwriting, all files and subfolders
        in the root out directory will be destroyed, not just ones pertaining to the relevant infiles.'''
    ### Check if outdirectory already exists and react decide to overwrite or error ###
    if os.path.exists(rootout):
        if overwrite:
            print 'Deleting directory and all contents of, %s' %rootout
            shutil.rmtree(rootout)
        else:
            raise IOError('Directory %s already exists, remove or set overwrite to True'%rootout)
        
    ### Make output directory and subdirectories ###    
    print 'making directory %s' %rootout
    os.makedirs(rootout)
    return rootout


### Deprecated functions below ###
def out_getter(imjobject, with_header=True, delim='\t'):
    ''' This is a special getter which takes in attribute fields as well as corresponding mapping functions
    to format return in a sexy way.  Couldn't quite rig it up properly so this is not in use!'''

    empty=lambda x: x #How to handle null case
    fround=lambda x: round(x, 2) #Quick rounding
  #  scaleout='%s/pixel'%units, round(scale,3) #NEED TO MAKE UNITS AN ATTRIBUTE GETTER!!!
    join_it=lambda x: delim.join([str(item) for item in x])
    
    outparms=[('shortname',empty), ('af_coverage',fround), ('bw_coverage', fround,), ('diam_min_mode_max', join_it), \
              ('percent_sampled',fround), ('scale',fround),('field_of_view', join_it,)]
    
    outfields=[item[0] for item in outparms]
    f=attrgetter(*outfields)    
    atts=f(imjobject)
    outstring=''
    if with_header:
        outstring=outstring+'#'+(delim.join(outfields))+'\n'
        
#    for i, item in enumerate(outparms):
 #       outstring=outstring+delim+str(item[1](atts[i]))
        
    outstring=outstring+delim.join(str(item[1](atts[i])) for i,item in enumerate(outparms) )+'\n'
        
    return outstring
    
