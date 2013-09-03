#
# Canopy product code
#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is confidential and NOT open source.  Do not distribute.
#

''' Client logging tools.  configure_logger() returns a root_logger with separate
    file and stream handlers.  log() is a flexible decorator that logs a function,
    displays its arguments and their values, and formatts errors different based
    on the value of logging.trace; logging.testmode.
    
    In the future, this should be consolidated into a Class'''

import inspect       
import logging        
import sys

from traceback import print_exception
from functools import wraps

from pyuvvis.exceptions import LogExit


logger = logging.getLogger(__name__) 

# STRING FORMATTING
def _fmt_word(word, max_chars = 60, crop_front=True):
    '''str-convert a word.  If it exceeds max_chars, crop it to max_chars - 3
       and prefix it with "..."  eg:
          areallylongword --->  ....lylongword
        
    '''        
    word = str(word)
    if len(word) > max_chars:
        if crop_front:
            word='...' + word[-(max_chars-3):]
        else:
            word=word[:(max_chars -3)] + '...'
    return word

def configure_logger(screenlog=True, logfile=None, screen_level=logging.INFO,
                file_level=logging.DEBUG, time=True, name=None, **filekws):
    ''' Instantiates a logger with streamhandler, filehandler or both.
        Very similar to logging.basicConfig except it allows for simultaneous
        to-screen and to-file output.

        Parameters
        ----------
        screenlog : bool
            Log handler writes to screen.

        logfile : str (filename)
            Filename to which loghandler writes

        screen_level : str of logging.CATEGORY or int
             Set logging level for screen handler (error, info, debug etc...)

        file_level : str of logging.CATEGORY or int
             Set logging level for file handler (error, info, debug etc...)

        time : bool
            Prefix log messages with date and time IE:
               08-12 10:45:27 DEBUG    path/to/module "message"
                            vs.
               DEBUG   path/to/module "message"


        Notes
        -----
            Apparently one must set the root logger level to info, regardless
            of the child handler level settings to get everything working.  To
            limit the handler to just ONE type of error, it then requires the
            use of Filters.

            The show_all keyword merely changes the root logger name between
            __name__ and '' which gives this behavior.

        Returns
        -------
        logger : logging.Logger instance

       '''

    # Formatting for message, date, time
    out_fmt = '%(levelname)-8s %(name)-12s:  %(message)s'

    # Ascii fmt of time, if time is enabled
    asci_fmt = '%m-%d %H:%M:%S'

    # Output time with logs?
    if time:
        out_fmt = '%(asctime)s ' + out_fmt

    if not screenlog and not logfile:
        raise ValueError('Cannot create logger without stream.')
    
    # If users pass string args to screen_level, file_level
    screen_level= decode_lvl(screen_level)
    file_level = decode_lvl(file_level)

    root_logger = logging.getLogger('')
    root_logger.setLevel(logging.DEBUG)  # Needs to be set; despite handler levels
    
    # Reset any currnet handlers (useful if multiple files call this)
    root_logger.handlers = []
    
    # Add file handler to logger
    if logfile:        

        file_handler = logging.FileHandler(logfile, **filekws)
        file_handler.setFormatter(logging.Formatter(out_fmt, asci_fmt))
        file_handler.setLevel(file_level)
        root_logger.addHandler(file_handler)

    # Add screen handler to logger
    if screenlog:        

        screen_handler = logging.StreamHandler()
        screen_handler.setFormatter(logging.Formatter(out_fmt, asci_fmt))
        screen_handler.setLevel(screen_level)
        root_logger.addHandler(screen_handler)

    # Better here than getLogger('') so that its root status is retained
    root_logger.name = name
    root_logger.debug('Initialized root logger')
    
    return root_logger


#XXX This needs tested more, particularly when wrapping fcn w/ kwargs
def log(level='info', show_args=False, show_values=False, crop_values=True,
        log_name=None, method=False):
    '''  Decorates a function and logs its call signature.

    Parameters
    ----------
    level : str/int 
        valid logging level (eg 'info', 'error', 40) at which to log mesage.
        
    show_args : bool
        If true, function arguments names will be displayed.  For example:
            foo('arg1', 'arg2', 'arg3')
            
    show_values : bool
        If true, function argument values will be display.  For example:
            foo( 30, <FooObject at 320323>, {'bar':'baz'}
            
    If show_args and show_values, call signature is reconstructed fully:
            foo ( 'arg1' = 30, 'arg2' = <FooObject at 320323> ...)
            
    crop_values : bool
        If true, values longer than certain character limit ( utils._fmt_word() )
        will be truncated to end with "...".  This is useful when function 
        arguments are long lists of values.
        
    log_name : str or None
        This decorator does not attempt to inspect the function it is wrapping,
        so log_name is used to explicitly pass the name which will go to getLogger().
      
    Notes
    -----
        description
        
    Returns
    -------
    attr : type
        description
      
    '''

    # Configure logger if it hasn't been done already
    if not logging.getLogger().handlers:
        screen_level='warning'
        if '-debug' in sys.argv:
            screen_level='debug'
        elif '-info' in sys.argv:
            screen_level='info'
        configure_logger(screen_level=screen_level)
         
    
    # Either use module logger or (@ so can tell where decorator called)
    if log_name:
        logger = logging.getLogger(log_name)   
    else:
        logger = logging.getLogger(__name__)
        
    def _wraps(fcn_name, fcn, *args, **kwargs):

        arg_names = fcn.func_code.co_varnames    

        if show_args:
            arg_str = arg_names
        
        if show_values:
            val_str = args #kwargs?
            if crop_values:
                val_str = [_fmt_word(val, crop_front=False) for val in val_str]
            
        if show_args and show_values:
                
            # This is failing for functions with *args/**kwargs
            try:
                outstr = ', '.join([(str(arg_names[i]) +' = ' + str(val_str[i]) ) \
                                for i in range(len(args))])
            except IndexError:
                logger.debug('LOG WRAPPER FAILED FOR %s' % fcn_name)
                outstr = arg_str  
            else:  
                outstr = '(' + outstr + ')'
        
        elif show_args:
            outstr = arg_str
            
        elif show_values:
            outstr = val_str
        
        else:
            outstr = '()'
        
        # Log command ( *@* to distinguish from manually logged commands)
        logger.log(decode_lvl(level), '%s%s' % (fcn_name, outstr))
        
        try:            
            
            return fcn(*args, **kwargs)             
        
        except Exception as exc:
            
            ex_type, ex, tb = sys.exc_info()
        
            # -t USES sys.argv (until fixed; argparse must use -t)
            trace = False
            if '-t'  or '--trace' in sys.argv:
                trace = True
            
            if trace:
                trc_msg = '{See trace below}'
            else:
                trc_msg = '{-t, --trace for full traceback}'            
        
            fmt_str = '' if trace else '%s: %s' % (ex.__class__.__name__, exc)
            logger.error('%s() failed %s %s\n', fcn_name, fmt_str, trc_msg)                
        
            if trace:
                print_exception(ex_type, ex, tb)
            
            raise LogExit 
    

    def deco(fcn):
        ''' Generic logger that writes function name and arugment namesto INFO. 
            It also wraps a class method, if the "method" keyword was passed
            to log().  Its up to the user to make sure actual methods are passed
            when setting method=True.'''
        
        if method:
            
            # Wrap a method, add "self" to args and call function
            def wraps(self, *args, **kwargs):
                           
                fcn_name = getattr(self, 'name', '') +'.' + fcn.__name__
                args = list(args)
                args.insert(0, self)
                return _wraps(fcn_name, fcn, *args, **kwargs)
                    
        else:
            def wraps(*args, **kwargs):
                fcn_name = fcn.__name__
                return _wraps(fcn_name, fcn, *args, **kwargs)
            
                       
        return wraps
    return deco

        
# These logging facilities ought to be consolidated into a class.        
def decode_lvl(level):
    ''' Converts logging level code ('info, 'debug') to int for logging.log()'''

    if isinstance(level, basestring):
        try:
            level = int(level)
        except ValueError:       
            level = getattr(logging, level.upper())

    return level

def logclass(public_lvl='info', private_lvl='debug', skip=[], **logkwargs):
    ''' Adds a log decorator to all class methods.  Private methods (_foo)
        are logged to debug.  Public methods are logged to info.  Magic methods
        (__foo__) are skipped; as well as methods in the "skip" list.
        
        Note: This is a class method, so instance attributes like "name"
              aren't defined.  Individual methods should add more explicit
              logging for this reason.'''

    def wraps(cls):
        logkwargs['method'] = True
        
        magic = [method for method in dir(cls) if method.startswith('__') and \
                 method.endswith('__')]
                    
        for method in dir(cls):
            value = getattr(cls, method)
    
            # skip attributes, magic methods
            if not callable(value) or method in magic or method in skip:
                continue 
            else:
                if method.startswith('_'):
                    setattr(cls, method, log(private_lvl, **logkwargs)(value))  
                else:
                    setattr(cls, method, log(public_lvl, **logkwargs)(value)) 
        return cls
    return wraps