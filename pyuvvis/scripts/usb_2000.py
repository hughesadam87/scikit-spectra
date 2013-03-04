''' Parameters interface for USB2000 spectrometer to be accessed primarily by
gwu_spec script. '''

params={

### Meta parameter to help gwu_spec tell if user is using incorrect config file
'_valid_minmax':(339.0, 1024.0), #nm


### Spectral output types.
'outtypes':(None, 'r', 'a'),
'reference':0,  #This is set to 0 automatically if user doesn't explicitly overwrite (even from external parms file)
'specunit':'nm',
'intvlunit':'s',  #This will actually force data into interval represnetationkl         

### slicing ###
'x_min':430.0,     #Define range over which data is used in file
'x_max':680.0,
'tstart':None,  #In units of timeunit
'tend':None,

### reference Correction   
'sub_base':True,
'bline_fit':True,
'fit_regions':((345.0, 395.0), (900.0, 1000.0)),

### Ranged Timeplot parms    
#'uv_ranges':((430.0,450.0), (450.0,515.0), (515.0, 570.0), (570.0,620.0), (620.0,680.0)),
'uv_ranges':8,
}