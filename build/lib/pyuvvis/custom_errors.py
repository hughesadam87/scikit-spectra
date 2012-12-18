''' Utilities in regard to custom exceptions, used throughout pyuvvis.  Mostly used 
to alert users when they've passed incorrect attributes to a function.'''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

def badvalue_error(attribute, errorstring):
    ''' Wrong value of attribute passed.'''
    return AttributeError('Received attribute, %s, however, allowed values are: %s'%(attribute, errorstring))

def badtype_error(attribute, errorstring):
    ''' Wrong type of attribute passed. '''
    return AttributeError(' attribute, %s, however, %s'%(attribute, errorstring))
    

### IS THIS TOO GENERIC!?  Make ones for type() and len() issues?