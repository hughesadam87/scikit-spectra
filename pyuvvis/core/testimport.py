''' Module used to import testdata so that I can test TimeSpectra() without monkeypatched testdata'''

from pandas import date_range

dates=date_range(start='3/3/12',periods=3,freq='h')
