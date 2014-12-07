from operator import attrgetter
import os
import os.path as op
import shutil

import logging
logger = logging.getLogger(__name__)

# XXX: Add logging/remove print statements

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

def get_files_in_dir(directory, sort=True):
    ''' Given a directory, returns just the files; ignores directories '''

    # If path entered with or without trailing '/', account for it
    directory = directory.rstrip('/')    
    files = [op.join(directory, item) for item in os.listdir(directory) if 
             op.isfile(op.join(directory, item))]

    if sort:
        files.sort()
    return files

            
def make_root_dir(rootout, overwrite=False, verbose=True):
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
    if verbose:
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
    
