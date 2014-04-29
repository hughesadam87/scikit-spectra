#!/usr/bin/env python
# Author:   --<Adam Hughes>
# Purpose: 
# Created: XX/XX/XXXX

from __future__ import division
import sys
import os
import os.path as op
import argparse #http://docs.python.org/dev/library/argparse.html

import logging


# DEFAULT PARAMETERS
# ------------------
SCRIPTNAME = 'findstring'

class MainError(Exception):
    pass
    

class Controller(object):
    """ Class has parser methods, main, logger etc... """
    
    def run_main(self):
        """ Configure logger, parser and run script """
        
        # Configure Logger
        logging.basicConfig(level=logging.DEBUG)
        self.LOGGER = logging.getLogger(__name__)

        # Parse
        self.ARGS = self.parse()
        
        files = os.listdir(self.ARGS.directory)
        self.LOGGER.info('Found %s files in directory "%s"' %
                         (len(files), self.ARGS.directory))
        for afile in files:

            if op.isdir(afile):
                continue
            
            with open(afile, 'r') as f:
                if self.ARGS.string in f.read():
                    self.LOGGER.info("String found: %s" % afile)

                    if self.ARGS.delete:
                        self.LOGGER.info("Removing %s" % afile)
                        os.remove(afile)
                
        
    def parse(self):
        """ Returns arguments in parser.  All validation is done in separate
        method so that self.LOGGER can be first set in __main__()."""
                        
        parser = argparse.ArgumentParser(
            prog = '%s'%SCRIPTNAME,
            usage = '%s <directory> <string> --options' % SCRIPTNAME,
            description = 'Searches datafiles in a directory for a certain string.',
            epilog = 'Created originally to look for spectral data values in USB2000'
                      ' spectrometer in Reeves lab.  Does not walk directories, nor'
                      ' handle multiple directories.  All filetypes are examined.'
        )   
    
        parser.add_argument("directory", 
                            nargs = "?",
                            default = '.', 
                            help="Directory to search files")
        
        parser.add_argument("string", 
                            nargs = "?",
                            default='4095.00', 
                            help='String to search in files')
        
        parser.add_argument("-d", 
                            "--delete",  
                            action = 'store_true',
                            help='Delete files that contain string.')
                        
        args = parser.parse_args()
    
        # Do argumnet checking here
            
        return args
    
    
def main(*args, **kwargs):
    controller = Controller()
    controller.run_main()
    

if __name__ == '__main__':
    main()
    