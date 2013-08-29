''' Full credit to:
http://ssscripting.wordpress.com/2009/03/03/python-recursive-directory-walker/
for the original DirWalker class. '''

import os,sys

class DirWalker(object):
    ''' Class to handle many walking operations and return directory 
        structures.'''

    def walk(self, direc, callback):
        """ walks a directory, and executes a callback on each file """
        direc = os.path.abspath(direc)
        for f in [f for f in os.listdir(direc) if not f in [".",".."]]:
            nfile = os.path.join(direc,f)
            callback(nfile)
            if os.path.isdir(nfile):
                self.walk(nfile,callback)
                
    def testwalk(self, direc, **walkargs):
        walker=os.walk(direc, **walkargs)       
        (rootpath, rootdirs, rootfiles)= walker.next()
        while rootdirs:
            (rootpath, rootdirs, rootfiles)= walker.next()
            print rootdirs
            


### Various callback functions
def print_all(f):
    print f
    
def get_immediate_subdirectories(dir):
    return [name for name in os.listdir(dir)
            if os.path.isdir(os.path.join(dir, name))]


#### TESTING ###
if __name__ == '__main__':
    x=DirWalker()
#    x.walk('.', print_all)
    x.testwalk('.')
    