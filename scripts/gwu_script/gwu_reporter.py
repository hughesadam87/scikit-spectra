import sys
import os
import os.path as op

from collections import OrderedDict

logger = logging.getLogger(__name__)
from pyuvvis.logger import log, configure_logger, logclass

EXP_TEMPLATE = 'templates/experiment_main.tex'
HEADER_TEMPLATE = 'templates/header.tex'

class Reporter(object):
    ''' '''
    
    def __init__(self, **kwargs):
       
        # Add main experimental body
        general_body = file(EXP_TEMPLATE, 'r').read() 
        self.report = OrderedDict( ('main', general_body) )
        
        main_params = {'title': 'FOO TITLE', 
          'author':'Adam Hughes', 
          'email':'hugadams@gwmail.gwu.edu', 
                }
    
    def add_section(self):
        NotImplemented

    def remove_section(self):
        NotImplemented                       
                
    def sections(self):
        return [k for k in self.report]
    
    def make_report(self, outpath='test.tex'):
        ''' Joins all the section strings from self.report.values();
            adds a header and mergers main_params (author, email etc..).'''
        
        body = ''
        for section in self.report.values():
            body += section
                
        # Add the full report as the "body" into the header template
        main_params['body'] = body
        
        template_main = file(HEADER_TEMPLATE, 'r').read()
            
        # Check for file extension, change to tex
        open('outpath', 'w').write(template_main % main_params) 
        # do I need to close?
