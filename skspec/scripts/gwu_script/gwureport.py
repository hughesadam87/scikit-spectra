import argparse
import shlex
import logging
import os
import os.path as op

from gwu_reporter import Reporter

import logging
logger = logging.getLogger(__name__)
from skspec.logger import logclass, configure_logger

SCRIPTNAME = __name__.split('.')[-1]
SEP_DEFAULT = '/' #Not used atm

@logclass(log_name=__name__, public_lvl='debug')
def main(args=None):
    
    if args:
        if isinstance(args, basestring):
            args=shlex.split(args)
        sys.argv = args               
    
    
    parser = argparse.ArgumentParser(SCRIPTNAME, description='GWU skspec composite' 
            ' latex report assembly script', epilog='Additional help not found', 
            usage='%s --globals <command> --cmdopts' % SCRIPTNAME)    
        
    parser.add_argument('-v', '--verbosity', help='Set screen logging; '
                         'defaults to info.', nargs='?',
                         default='warning', const='info', metavar='')    
    parser.add_argument('-o', '--overwrite', action='store_true')

#    parser.add_argument('-s', '--sep', metavar='',
#                         help='Latex section separator.  Defaults to %s.  '
#                         'Set to None to avoid auto sub-sectioning' %SEP_DEFAULT)

    # Sub Commands
    subparsers = parser.add_subparsers(title='commands', metavar='', dest='op')    
    
    # TEMPLATE SUBCOMMAND
    p_template = subparsers.add_parser('template', 
        usage = '%s --globals <template> outpath --opts ' % SCRIPTNAME,    
        help='template help',
        epilog='PUT EXAMPLES HERE')
    p_template.add_argument('outpath', metavar='outfile',
        help='Name of outfile (eg foo.tex or path/to/foo.tex)')

    p_template.add_argument('-s', '--sections', metavar='', nargs='*', help='List of sections to add.'
        'or tree file.  If not tree file, default section template will be "template/section" '
        'section names will auto-break into subsections based on value of --sep',
        default=[]) 
    p_template.add_argument('-t', '--template_file', metavar='')
    
    
    
    # BUILD SUBCOMMAND
    p_build = subparsers.add_parser('build', help='Adds latex doc header including ' 
        'begin/close document, title, author etc...',
         usage = '%s --globals <build> texfile outpath --opts ' % SCRIPTNAME,    
         epilog='Put examples here')
    p_build.add_argument('texfile', help='Output file of %s template' % SCRIPTNAME)
    p_build.add_argument('outpath', metavar='outfile',
        help='Name of outfile (eg foo.tex or path/to/foo.tex)')
    
    p_build.add_argument('--title', default='Untitled', metavar='', help='Title '
                         ' in outfile')
    p_build.add_argument('--author', default='Adam Hughes', metavar='', 
                         help='Author in outfile')
    p_build.add_argument('--email', default='hugadams@gwmail.gwu.edu', metavar='', 
                         help='Email in outfile')
            

    # Compile and open
    p_build.add_argument('--nocompile', action='store_true', help='Do not compile outfile'
                         ' (eg latex outfile.tex)' ) 
    p_build.add_argument('--nopdf', action='store_true', help='When compiling,' 
                         ' will call "latex" instead of "pdflatex"')
    p_build.add_argument('-c', '--clean', action = 'store_true', help='Remove .aux, .log'
        ' and other latex temporary files.')

    
    #SUMMARY SUBCOMMAND (not implemented)
    #p_summary = subparsers.add_parser('summary', help='summary help')
    #p_summary.add_argument('texfile')

    ns = parser.parse_args()
        
    # No logfile implemented
    configure_logger(screen_level='debug', name=__name__)
    logger.info('Namespace is: %s' % ns)
    
    reporter = Reporter(**ns.__dict__) # Is this ok?
    
    if ns.op == 'template':
        reporter.output_template(ns.outpath)
    
    elif ns.op == 'build':
        reporter.make_report(ns.texfile, ns.outpath)

        # If compiling, choose pdflatex or latex
        if not ns.nocompile:
         
            if not ns.nopdf:
                latex_type = 'pdflatex'

            else:
                latex_type = 'latex'
            
            # Run latex or pdflatex twice to ensure contents load    
            os.system('%s %s' % (latex_type, ns.outpath) )
            os.system('%s %s' % (latex_type, ns.outpath) )

            
        # Cleanup latex .toc/.log/.aux files of outfile
        if ns.clean:
            outdir, outname = op.split(op.abspath(ns.outpath))
            outname = op.splitext(outname)[0]
            for ext in ['toc', 'log', 'aux', 'out']:
                wastefile = op.join(outdir, outname + '.' + ext)
                if op.isfile(wastefile):
                    logger.info('Cleaning up file: "%s"' % wastefile)
                    os.remove(wastefile)
    
    else:
        NotImplemented

if __name__ == '__main__':
    main()