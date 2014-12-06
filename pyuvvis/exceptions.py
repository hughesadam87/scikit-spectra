''' Utilities in regard to custom exceptions, used throughout skspec.  Mostly used 
to alert users when they've passed incorrect attributes to a function.'''

__author__ = "Adam Hughes"
__copyright__ = "Copyright 2012, GWU Physics"
__license__ = "Free BSD"
__maintainer__ = "Adam Hughes"
__email__ = "hugadams@gwmail.gwu.edu"
__status__ = "Development"

from operator import attrgetter

class GeneralError(Exception):

    ''' Default custom error.  Basic interface to define a default error; but
        easily overwritten when the user wants to pass a custom message.'''

    default = ''

    def __init__(self, msg=None):
        self.message = msg

    def __str__(self):
        if self.message:
            return repr(self.message)
        else:
            return repr(self.default)
        
class BaselineError(GeneralError):
    
    default = 'Baseline operation failure'
    

class ParameterError(GeneralError):
    
    default = "Parmater unknown"
    
class RefError(GeneralError):
    ''' Error raised when a user-supplied iterable does not have same spectral
    values as those of the timespectra.'''
    
    def __init__(self, index, timespectra):
        sunit = timespectra.specunit
        self.message = ('Cannot resolve length %s reference (%s%s - %s%s) and length %s %s (%s%s - %s%s)'\
                      %(len(index), index[0], sunit,  index[-1], sunit, len(timespectra.reference), \
                        timespectra.name, timespectra.df.index[0], sunit, timespectra.df.index[-1], sunit) )
        
        
# See grits client to show how to make this indistinguishable from normal argparse error
class ParserError(GeneralError):
    
    default = 'Failed to construct parser'
        
class LogExit(SystemExit):
    ''' Used by logger. '''
    

# Functions 
def badvalue_error(attribute, allowedvalues):
    ''' Wrong value of argument passed.'''
    return AttributeError('Received attribute, %s, however, allowed values are:' 
    ' %s'%(attribute, allowedvalues))

def badtype_error(attribute, allowedtypes):
    ''' Wrong type of argument passed. Provide attribute and allowed types'''
    return TypeError('Received attribute "%s" of type %s; however, allowed types are %s'%(attribute, type(attribute), allowedtypes))

def badcount_error(numallowed, numreceived, numtotal, argnames=None):
    ''' Function required x of arguments y (out of z arguments total) to work, but user
        entered wrong amount.  If argnames, error will print the names of attributes required.
        Argnames should be the names of the total number of arguments (eg if numtotal = 4, argnames 
        should be 4 strings)'''

    if argnames:
        return AttributeError('requires %s of %s nonull keywords for %s but received %s.'%(numallowed, numtotal, argnames, numreceived))
    else:
        return AttributeError('requires %s of %s nonull keywords but received %s.'%(numallowed, numtotal, numreceived))


# Phase this out?
def badkey_check(key, allowedvalues, case_sensitive=False):
    ''' Either string not passed or wrong value passed.  
        allowedvalues is a list of values that the key attribute can take on. 
        Useful for case when you want to make sure the keyword has one of x values.
  
        **case_sensitive: If False, will compare attribute.lower() to allowedvalues.lower().
        
        Notes
        -----
           Messy because I added option that key can be None type and also string.  This is
           only useful so far in TimeSpectra iunits dictionary.
        
        Returns: None (Raises errors if test fails).'''
    
    ### Handle case of key=None
    if key==None:
        if None in allowedvalues:
            return
        else:
            raise badvalue_error(key, "%s"%(','.join(allowedvalues)) )
            

    ### Make sure attribute is a string
    if not isinstance(key, basestring):
        raise badtype_error(key, basestring)

    ### Can I compare lowercase strings?
    if case_sensitive ==False:
        key=key.lower()

        ### Handle case of None in possible keys (ie allowedvalues)
        if None in allowedvalues:
            allowedvalues.remove(None)        
            allowedvalues=[v.lower() for v in allowedvalues]
            allowedvalues.append(None)
        
    ### If attribute not found
    if key not in allowedvalues:
        if None in allowedvalues:
            allowedvalues.remove(None)
            allowedvalues.append('None')
        raise badvalue_error(key, "%s"%(','.join(allowedvalues)) )

    return 

### IS THIS TOO GENERIC!?  Make ones for type() and len() issues?

def null_attributes(obj, callfcn, *attr_required):
    ''' Logic gate ensures non-null values for required attributes on an object.
    
    Parameters
    ----------
       obj:  The Python object whose attributes are to be examine.
       callfcn: Reference to the function that called this, so make Errors more clear.
       attr_requried:  List of attributes that must have non-null values.
       
    Example
    -------
       If I want to make sure an object has valid values for x,y,z before continuing.
       null_attributes(obj, 'x','y','z')
       
    Notes:
    ------
    Null refers to a value of NONE, not False.
    
    The object does not have one of the required attributes to begin with, attrgetter will raise an error 
    in first line below. '''
    try:
        values=attrgetter(*attr_required)(obj)
    except AttributeError:
        raise AttributeError('%s call to null_attribute() missing some of the required attributes for examination'%callfcn)

    ### Zip together, and if only a single value (eg not iterable), just piece manually
    if len(attr_required)==1:
        dic={attr_required[0]:values}
    else:
        dic=dict(zip(attr_required, values))

    missing=[k for k in dic if dic[k] == None]
    
    if missing:
        raise AttributeError('%s requires non-null values for attribute(s): "%s".  Returned null for "%s"'%(callfcn, '","'.join(attr_required), ','.join(missing)))
    