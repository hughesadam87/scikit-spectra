from copy import deepcopy, copy
import numpy as np
from pandas import DatetimeIndex, Timestamp

from pyuvvis.core.abcindex import ConversionIndex, _parse_unit
from pyuvvis.units.abcunits import UnitError
from pyuvvis.units.intvlunit import INTVLUNITS, TimeDelta, DateTime, DatetimeCanonicalError

class TimeIndex(ConversionIndex):
    """ Stores time labels as Timestamps, Time Deltas or cumulative intervals
    ie seconds, minutes, days from t=0.  Timestamps (e.g. datetimes) are 
    stored as objects, while seconds, minutes etc.. are stored as floats.  
    Therefore, some extra logic is in place to fix breaking points with the
    dtype would otherwise cause errors, mostly the case when dataframe does
    slicing or indexing.
    """
    unitdict = INTVLUNITS
    cumsum = True

    # Overload because datetime and interval need different array types
    # i.e. seconds --> float64 while dti ---> timestamp
    def __new__(cls, input_array, unit=None):
        """ Unit is valid key of unitdict """

        # Is datetimeindex stored on object, or is object itself datetimeindex
        datetimeindex = None 
        #NEEDS TO BE _STORED DTI FOR __new__, DATETIMEINDEX IS A PROPERTY!
        try:
            datetimeindex = input_array._stored_dti 
        except AttributeError:
            pass

    
        # IF INPUTARRAY COMES IN AS A PANDAS DATETIMEINDEX, FORMATS IT
        # TO AN ARRAY OF DATETIMES THEN TO AN ARRAY OF TIMESTAMPS,
        # THE ARRAY OF TIMESTAMPS IS NECESSARY FOR TIMEINDEX
        if isinstance(input_array, DatetimeIndex):
            #Convert datetimes to timestamp
            if unit != 'dti' and unit != None:
                raise IndexError("When creating TimeIndex from DatetimeIndex"
                     " unit must be 'dti' or None, recived %s" % unit)
            datetimeindex = input_array            
            input_array = np.array(input_array.to_pydatetime())
            input_array = np.array([Timestamp(x) for x in input_array])

                        
        if unit:
            # dti, timedelta
            if unit == 'intvl' or unit == 'dti':
                dtype = 'object'
            else:
                dtype = 'float64'

            obj = np.asarray(input_array, dtype=dtype).view(cls)   
        else:
            obj = np.asarray(input_array).view(cls)   

        if datetimeindex is not None:
            obj._stored_dti = datetimeindex

        # Ensure valid unit
        obj._unit = _parse_unit(unit, cls.unitdict)
        if cls.cumsum:
            obj.cumsum = True
        return obj   

    # Remove
    def validate_slicer(self, *args, **kwargs):
        pass


    def convert(self, outunit):
        """Converts spectral units (see abcindex.convert()).  Handles special
        case of converting to datetimeindex, since the DateTime unit does
        not have conversions; instead the datetimeindex is stored in this
        TimeIndex class and needs to be handled separately.
        """

        # Handle non-dti conversion and conversions involvin DTI and None
        try:
            out = super(TimeIndex, self).convert(outunit)
        except DatetimeCanonicalError:
            inunit = self._unit.short        
 
            # DTI (just pass self.datetimeindex into the constructor)
            if outunit == 'dti':
                if self.datetimeindex is None:
                    raise IndexError("Datetime index not stored; cannot convert to dti")
                return self.__class__(self.datetimeindex, unit = 'dti')
    
            #DTI TO SOMETHING ELSE            
            elif outunit != 'dti' and inunit == 'dti':
                nanoseconds = np.diff(self.datetimeindex.asi8)  #asi8 only defined on DatetimeIndex      
                seconds = nanoseconds * 10**-9  
                seconds = np.insert(seconds, 0, seconds[0]-seconds[0])
                if self.cumsum:
                    seconds = seconds.cumsum()
                out = self.__class__(seconds, unit=outunit)  #THIS MAKES NP ARRAY SO ADD DATETIMEINDEX
                out = self.unitdict[outunit].from_canonical(out)           
            # Should never happen
            else:
                raise IndexError("SOME LOGIC APPARENTLY NOT ACCOUNTED FOR")
        
        # all conversions go through numpy arrays, so need to manually assign DTI!
        #NEEDS TO BE _STORED DTI FOR __new__, DATETIMEINDEX IS A PROPERTY!        
        try:
            out._stored_dti = self.datetimeindex
        except AttributeError:
            pass
        
        return out


    @property
    def datetimeindex(self):
        try:
            return self._stored_dti
        except AttributeError:
            raise AttributeError("DatetimeIndex not stored.")


    @datetimeindex.deleter
    def datetimeindex(self):
        """ Delete stored datetimeindex.  Not sure if useful, but code will
        breatk if I allow this set to None, so must delete."""
        del(self._stored_dti)
            
        
    @datetimeindex.setter
    def datetimeindex(self, dti):
        
        if not isinstance(dti, DatetimeIndex):
            try:
                dti = DatetimeIndex(dti)
            except Exception:
                raise IndexError('Could not store DatetimeIndex; wrong type %s' \
                                 % type(dti))
            else:
                if len(self) != len(dti):
                    raise IndexError("Length mismatch between passed"
                         "datetimeindex %s and object %s" % (len(dti), len(self)))
                self._stored_dti = dti


    def __getslice__(self, start, stop) :
        """This solves a subtle bug, where __getitem__ is not called, and all
        the dimensional checking not done, when a slice of only the first
        dimension is taken, e.g. a[1:3]. From the Python docs:
           Deprecated since version 2.0: Support slice objects as parameters
           to the __getitem__() method. (However, built-in types in CPython
           currently still implement __getslice__(). Therefore, you have to
           override it in derived classes when implementing slicing.)
        """
        return self.__getitem__(slice(start, stop))

    def __getitem__(self, key):
        """ When slicing, the datetimeindex should also be sliced. Otherwise,
        when converting to datetimeindex, could have length mismatch.  EG:
        
        min = ts.convert('m')[0:5]
        len(min) = 5
        dti = min.convert('dti')
        len(dti) = <length of original array>
        """
        out = super(TimeIndex, self).__getitem__(key)
        # If not returning a single value (eg index[0])
        if hasattr(out, '__iter__'):
            # Slice datetime index as well
            #NEEDS TO BE _STORED DTI FOR __new__, DATETIMEINDEX IS A PROPERTY!            
            try:
                out._stored_dti = self.datetimeindex.__getitem__(key) 
            except AttributeError:
                pass
        return out
    
    def copy(self, *args, **kwargs):
        """ Datetimeindex not properly stored when running various copy routines
        either from dataframe.copy or import copy, so manually overriding.
        
        Args kwargs passed to copy (e.g. deep =True)
        """
        outdict = super(TimeIndex, self).copy( *args, **kwargs)
        try:
            outdict.__dict__['_stored_dti']= self.datetimeindex
        except AttributeError:
            pass
        return outdict


    @property
    def is_all_dates(self):
        """ Overwirte this Index method because it's source of many issues
        deep in cython level.  Basically, only should be called if python
        objects.  Otherwise, get ValueError:
             Buffer dtype mismatch, expected 'Python object' but got 'double'
        """
        if self.dtype != 'object':
            return False
        else:
            return super(ConversionIndex, self).is_all_dates    


    # Hack to return _engine type correctly for mixed index objects like TimeIndex
    @property
    def _engine_type(self):
        import pandas.index as _index      
        if self.dtype == 'object':
            return _index.ObjectEngine
        elif self.dtype == 'float64':
            return _index.Float64Engine
        else:
            raise IndexError("Not sure which Engine to return for dtype %s"\
                             % self.dtype)      

#    def _validate_slicer(self, key, f):
#        pass


if __name__ == '__main__':
    from pandas import date_range

    idx = TimeIndex([1,2,3])
    idx = idx.convert('s')
    idx = idx.convert('m')

    #From datetime constructor
    idx = TimeIndex.from_datetime(date_range(start='3/3/12',periods=30,freq='45s'))
    print idx
    for unit in INTVLUNITS:
        print unit, idx.convert(unit)

    print idx.unitdict.keys()

#   idx.cumsum = False
#   for unit in INTVLUNITS:
#      print unit, idx.convert(unit)   