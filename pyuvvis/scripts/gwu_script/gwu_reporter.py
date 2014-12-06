import sys
import os
import os.path as op
from collections import OrderedDict

from skspec.scripts.gwu_script.tex_templates import EXPERIMENT_MAIN, HEADER, \
    BLANK_SECTION

import logging
logger = logging.getLogger(__name__)
from skspec.logger import log, configure_logger, logclass

from skspec.scripts.gwu_script import LOGO_PATH

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
            self.main_template = EXPERIMENT_MAIN
        
        self.title = kwargs.get('title', 'Untitled')
        self._author = kwargs.get('author', 'Adam Hughes')
        self.email  = kwargs.get('email', 'hugadams@gwmail.gwu.edu')

        # Handle sections
        self.sections = OrderedDict()
        self.parse_sections(kwargs.get('sections', []))

    @property
    def author(self):
        ''' (First, Last) name of author '''
        try:
            # BUG: This will put > 2 arguments into last name.  IE Adam STEPHEN HUGHES
            first, last = self._author.split(' ', 1)
            return (first, last)
        except Exception:
            raise AttributeError('Author must first and last name of the form:' 
                                 ' First Last')

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
            
            for secname, section_file in sections_dict.items():
                self.add_section(secname, section_file)

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
            
        
    def add_section(self, secname, section_file=None):
        ''' If not section_file, blank template is used. '''

    #    secname = self.latex_secname(secname)

        if section_file:
            logger.info("Appending section string from file file for %s" % secname)
            self.sections[secname] =str(open(section_file, 'r').read())

        else:
            # Need to fill in "secname" via %, while treefile already did this
            logger.info("Appending in blank section %s" % secname)
            self.sections[secname] = BLANK_SECTION  % {'secname':secname}
        
        
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
        tex_params['logopath'] = LOGO_PATH
        tex_params['authorfirstname'] = self.author[0]
        tex_params['authorlastname'] = self.author[1]
        tex_params['email'] = self.email
        tex_params['body'] = open(template_file, 'r').read()
        
        outpath = self.parse_path(outpath)       
        open(outpath, 'w').write(HEADER % tex_params) 
        logger.info('Report written to: "%s"' % outpath)
