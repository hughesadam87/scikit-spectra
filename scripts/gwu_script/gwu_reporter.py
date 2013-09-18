import sys
import os
import os.path as op

from collections import OrderedDict

import logging
logger = logging.getLogger(__name__)
from pyuvvis.logger import log, configure_logger, logclass

#Also used in gwu_controller.  Make more robust?
TEMPLATE_DIR = '/home/glue/Desktop/PYUVVIS/pyuvvis/scripts/gwu_script/templates/'
EXP_TEMPLATE = op.join(TEMPLATE_DIR, 'experiment_main.tex')
HEADER_TEMPLATE = op.join(TEMPLATE_DIR, 'header.tex')
BLANK_SEC_TEMPLATE = op.join(TEMPLATE_DIR, 'blank_section.tex')

logger = configure_logger(name=__name__)

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
        self.parse_sections(kwargs.get('sections', []))


    def parse_path(self, outpath):
        ''' Handles path overwriting of a single file. '''

        outpath = op.abspath(outpath)
        
        if op.exists(outpath):
            if not self.overwrite:
                # Replace these IOErrors everywhere with PathError?
                raise IOError('Outpath already exists: "%s"', outpath)
            logger.warn('Overwriting outpath: "%s"' % outpath)
            os.remove(outpath)

        return outpath
    
    def parse_sections(self, sections):
        ''' Adds sections to self.sections.  If length 1 iterable and the 
           entry is a file, treats this a a tree files and reads from tree file.
           Otherwise, adds blank sections.'''

        if not hasattr(sections, '__iter__'):
            raise AttributeError('Reporter.parse_sections must be iterable.')
        
        # Assumes section is a tree file
        if len(sections) == 1 and op.exists(sections[0]):
            logger.info("Trying to parse sections from treefile!")
            sections_dict = eval(open(sections[0], 'r').read())

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
        for secname, section in self.sections.items():
            body += section + '\n'
        return body
            
                
    def latex_secname(self, secname):
        ''' Try to format subsections to something more fancy.  Since templates
            define the sections themselves, this is not implemented.  Would need
            to refactor templates to no longer declare \section \subsection etc..'''
        NotImplemented
#        return '\SubSection{%s}' % secname
        
    def add_section(self, secname, sectionfile=None):
        ''' If not sectionfile, blank template is used. '''
        
    #    secname = self.latex_secname(secname)

        if sectionfile:
            logger.info("Appending section file for %s" % secname)
            self.sections[secname] = str(open(sectionfile, 'r').read())

        else:
            # Need to fill in "secname" via %, while treefile already did this
            logger.info("Appending in blank section %s" % secname)
            self.sections[secname] = str(open(BLANK_SEC_TEMPLATE, 'r').read() % 
                                         {'secname':secname})
        
        
    def remove_section(self, secname):
        try:
            del self.sections[secname]
        except KeyError:
            raise KeyError('%s not found in "sections".  See self.sections')


    def output_template(self, outpath, add_header=False):

        outpath = self.parse_path(outpath)
        open(outpath, 'w').write(self.report)
        logger.info('Template written to: "%s"' % outpath)

        
                                                
    def make_report(self, template_file, outpath):
        ''' Joins all the section strings from self.report.values();
            adds a header and mergers tex_params (author, email etc..).'''
        
                        
        if not op.exists(template_file):
            raise IOError('Template file not found: "%s"' % template_file)
        
        # Add the full report as the "body" into the header template_file
        tex_params = {}
        tex_params['title'] = self.title
        tex_params['author'] = self.author
        tex_params['email'] = self.email
        tex_params['body'] = open(template_file, 'r').read()
        
        template_main = file(HEADER_TEMPLATE, 'r').read()

        outpath = self.parse_path(outpath)       
        open(outpath, 'w').write(template_main % tex_params) 
        logger.info('Report written to: "%s"' % outpath)
