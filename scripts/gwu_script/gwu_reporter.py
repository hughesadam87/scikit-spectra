import sys
import os
import os.path as op

from collections import OrderedDict

import logging
logger = logging.getLogger(__name__)
from pyuvvis.logger import log, configure_logger, logclass

TEMPLATE_DIR = '/home/glue/Desktop/PYUVVIS/pyuvvis/scripts/gwu_script/templates/'
EXP_TEMPLATE = op.join(TEMPLATE_DIR, 'experiment_main.tex')
HEADER_TEMPLATE = op.join(TEMPLATE_DIR, 'header.tex')
SEC_TEMPLATE = op.join(TEMPLATE_DIR, 'section.tex')

logger = configure_logger()

@logclass(public_lvl='info')
class Reporter(object):
    ''' Report is stored as an ordered dict.  Main is followed by sections. '''
    
    def __init__(self, **kwargs):
       
        self.overwrite = kwargs.get('overwrite', False)
       
        # Add main experimental body from template file or blank
        template_file = kwargs.get('template_file', None)
        if template_file:
            if not op.exists(template_file):
                raise IOError("Template file %s not found!")
            self.main_template = file(template_file, 'r').read() 

        else:
            self.main_template = file(EXP_TEMPLATE, 'r').read() 
        
        self.title = kwargs.get('title', 'Untitled')
        self.author = kwargs.get('author', 'Adam Hughes')
        self.email  = kwargs.get('email', 'hugadams@gwmail.gwu.edu')

        # Handle sections
        self.sections = OrderedDict()
        self.parse_sections(kwargs.get('sections'))

        
    def parse_sections(self, sections):
        ''' Adds sections to self.sections.  If length 1 iterable and the 
           entry is a file, treats this a a tree files and reads from tree file.
           Otherwise, adds blank sections.'''

        if not hasattr(sections, '__iter__'):
            raise AttributeError('Reporter.parse_sections must be iterable.')
        
        # Assumes section is a tree file
        if len(sections) == 1 and op.exists(sections[0]):
            logger.info("Trying to parse sections from treefile!")
            sections_dict = eval(open(section, 'r').read())

            # REPLACE THIS FUNCTIONALITY WITH ADD_SECTION
            
            for secname, section in sections_dict.items():
                self.add_section(secname, sectionfile=section)

        # Adds a blank section for each name in order as (section, SEC_TEMPLATE)
        else:
            for secname in sections:
                self.add_section(secname)
                
    @property
    def report(self):
        ''' Concatenates main_tamplate body and self.sections. '''
        body = self.main_template
        for section in self.sections:
            body += section
            
                
        
    def add_section(self, secname, sectionfile=None):
        ''' If not sectionfile, blank template is used. '''

        if sectionfile:
            logger.info("Appending section file for %s" % secname)
            self.sections['secname'] = file(section, 'r').read() 

        else:
            logger.info("Appending in blank section %s" % secname)
            self.sections['secname'] = file(SEC_TEMPLATE, 'r').read()
        
        
    def remove_section(self, secname):
        try:
            del self.sections[secname]
        except KeyError:
            raise KeyError('%s not found in "sections".  See (WHICH METHOD?)')


    def output_template(self, outpath, add_header=False):
        if op.exists(outpath):
            if not self.overwrite:
                # Replace these IOErrors everywhere with PathError?
                raise IOError('Outpath already exists: %s', outpath)
            logger.warn('Overwriting outpath: %s' % outpath)
            os.remove(outpath)

        file(outpath, 'w').write(self.report)
                                                
    def make_report(self, template, outpath='test.tex'):
        ''' Joins all the section strings from self.report.values();
            adds a header and mergers tex_params (author, email etc..).'''
        
        body = ''
        for section in self.report.values():
            body += section
                
        # Add the full report as the "body" into the header template
        self.tex_params['body'] = body
        
        template_main = file(HEADER_TEMPLATE, 'r').read()
            
        # Check for file extension, change to tex
        open('outpath', 'w').write(template_main % self.tex_params) 
        # do I need to close?
