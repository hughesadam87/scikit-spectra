''' Utilities in regard to custom exceptions, used throughout pyuvvis.  Mostly used 
to alert users when they've passed incorrect attributes to a function.'''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

def badvalue_error(attribute, allowedvalues):
    ''' Wrong value of attribute passed.'''
    return AttributeError('Received attribute, %s, however, allowed values are: %s'%(attribute, allowedvalues))

def badtype_error(attribute, allowedtypes):
    ''' Wrong type of attribute passed. Provide attribute and allowed types'''
    return TypeError('Received attribute "%s" of type %s; however, allowed types are %s'%(attribute, type(attribute), allowedtypes))

def badkey_check(key, allowedvalues, case_sensitive=False):
    ''' Either string not passed or wrong value passed.  
        allowedvalues is a list of values that the key attribute can take on. 
        Useful for case when you want to make sure the keyword has one of x values.
  
    **case_sensitive: If False, will compare attribute.lower() to allowedvalues.lower().
    
    Returns: None (Raises errors if test fails)'''

    ### Make sure attribute is a string
    if not isinstance(key, basestring):
        raise badtype_error(key, basestring)

    ### Can I compare lowercase strings?
    if case_sensitive ==False:
        key=key.lower()
        allowedvalues=[v.lower() for v in allowedvalues]
        
    ### If attribute not found
    if key not in allowedvalues:
        raise badvalue_error(key, allowedvalues)

    return 

### IS THIS TOO GENERIC!?  Make ones for type() and len() issues?
