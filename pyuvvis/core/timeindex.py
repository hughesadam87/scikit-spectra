from pyuvvis.core.abcindex import ConversionIndex, _parse_unit
from pyuvvis.units.abcunits import UnitError
from pyuvvis.units.intvlunit import INTVLUNITS, TimeDelta, DateTime
import numpy as np
from pandas import DatetimeIndex, Timestamp
from pandas.core.index import Index

class TimeIndex(ConversionIndex):
   """ """
   unitdict = INTVLUNITS

   # Overload because datetime and interval need different array types
   # i.e. seconds --> float64 while dti ---> timestamp
   def __new__(cls, input_array, unit=None):
      """ Unit is valid key of unitdict """
      if unit:
#         if unit == 'dti':
#            dtype = '<M8[ns]'  #dtype of pandas.DatetimeIndex
         if unit == 'intvl' or unit == 'dti':
            dtype = 'object'
         else:
            dtype = 'float64'
            
         # IF INPUTARRAY COMES IN AS A PANDAS DATETIMEINDEX, FORMATS IT
         # TO AN ARRAY OF DATETIMES THEN TO AN ARRAY OF TIMESTAMPS,
         # THE ARRAY OF TIMESTAMPS IS NECESSARY FOR TIMEINDEX
         if isinstance(input_array, DatetimeIndex):
            input_array = np.array(input_array.to_pydatetime())
            input_array = np.array([Timestamp(x) for x in input_array])
            #Convert datetimes to timestamp
         obj = np.asarray(input_array, dtype=dtype).view(cls)   
#         obj.convert(None).convert('s')
      
      # If unit is None, don't force a particular type; use type of last 
      else:
         obj = np.asarray(input_array).view(cls)                  
      
      obj._unit = _parse_unit(unit, cls.unitdict)
      return obj   
 
 
   @classmethod
   def from_datetime(cls, dti):
      """ Construct IntervalIndex from a pandas DatetimeIndex.
      
      Parameters
      ----------      
      dti: DateTimeIndex
      
      cumsum: bool (True)
          Interval will be returned as running sum.  Ie 0,3,6 for 3 second
          intervals.  If not, returns 3, 3, 3
          
      Returns
      -------
      TimeIndex
      
      Additional
      ----------
      This generates an IntervalIndex, but populates the DateTime unit with
      attributes directly from the datetimeindex, including start, stop, 
      periods, freq etc through the from_datetime method()"""
      
      if not isinstance(dti, DatetimeIndex):
         raise UnitError("Please pass a datetime index.")

      datetimeunit = DateTime.from_datetime(dti)
             
      # Set DateTime unit to the one just created through from_datetime 
      intervalindex = cls(dti, unit='dti')
      intervalindex.unitdict['dti'] = datetimeunit
      return intervalindex
   
   # DOESNT WORK
   @property
   def cumsum(self):
      return self.unitdict['dti'].cumsum
   
   @cumsum.setter
   def cumsum(self, cumsum):
      if cumsum:
         cumsum = True
      else:
         cumsum = False
      self.unitdict['dti'].cumsum = cumsum
      
            

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