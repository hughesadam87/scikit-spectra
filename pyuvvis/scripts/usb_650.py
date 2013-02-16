''' Parameters interface for USB650 spectrometer to be accessed primarily by
gwu_spec script. '''

params={

### Meta parameter to help gwu_spec tell if user is using incorrect config file
'_valid_minmax':(200.0, 850.0), #nm

### Spectral output types.
'outtypes':(None, 'r', 'a'),
'baseline':0,  #This is set to 0 automatically if user doesn't explicitly overwrite (even from external parms file)
'specunit':'nm',
'intvlunit':'s',  #This will actually force data into interval represnetation         

### slicing ###
'x_min':None,     #Define range over which data is used in file
'x_max':None,
'tstart':None,  #In units of timeunit
'tend':None,

### Baseline Correction (sub_dark means subtract darkspectrum)  
'sub_dark':True,

## Cant line fit because no wings (could take end points I guess... but its overkill)
'line_fit':False,

### Ranged Timeplot parms    
#'uv_ranges':((430.0,450.0), (450.0,515.0), (515.0, 570.0), (570.0,620.0), (620.0,680.0)),
'uv_ranges':8,
}