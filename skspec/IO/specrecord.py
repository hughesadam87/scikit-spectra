### Actually use namedtuple for this, just storing these in case I ever fix pyrecords to take null values.
from collections import namedtuple

metadata_full=( 
             ### File related attributes ###
             ('filecount', int(0) ), #0-256 bins basically
             ('filestart', int(0) ),  
             ('fileend', int(0) ),


	     ### Time related attributes
             ('timestart',''), #datetime(0,0,0)),
             ('timeend',''),

	     ### Wavelength related attributes
             ('specstart', float(0.0)),
             ('specend', float(0.0)),

             ### Spectrometer datafile attributes

             ('spectrometer', ''),
            ('int_unit', ''),
            ('int_time',''),
            ('spec_avg',int(0)),
            ('boxcar',int(0)),
            ('dark_spec_pres',''), #String so can distingush unkown from No or Yes
            ('ref_spec_pres',''),
            ('electric_dark_correct',''),
            ('strobe_lamp',''),
            ('detector_nonlin_correct',''),
            ('stray_light_correct',''),
            ('pix_in_spec', int(0)),  #Int 0 or default to none
            )

MetaData=namedtuple('Spectralmetadata', [i[0] for i in metadata_full])


