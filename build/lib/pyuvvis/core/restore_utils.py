''' 
DOESN"T WORK

Simple functions to take custom dataframes (like TimeSpectra) and 
restore them to original pandas types.  Simply call them from a non-monkey
patched module.'''

from pandas import DataFrame, Index, DatetimeIndex

### This doesn't work, would need to delete all monkeypatching
def as_dataframe(df):
    return DataFrame(df)

def as_index(index):
    if isinstance(index, DatetimeIndex):
        return DatetimeIndex(Index)
    else:
        return Index(index)
