''' A set of run parameters to control gwu_spec.py script.'''

# Thought about making these options in optparse, but would need to open
# this file and find the names anyway.  Runname is an option in the script.

########################################
#####   Data Manipulation Parameters  ##
########################################

x_min=430.0     #Define range over which data is used in file
x_max=680.0
timeunit='seconds'          #hours, minutes, seconds, interval       
tstart=None  #In units of timeunit
tend=None
#x and t sampling params would probably be superfulous, but if put them in, can cut with df[start:end:sample] 
 
###############################
##### Baseline Correction  ####
###############################

sub_base=True
line_fit=True
fit_regions=((345.0, 395.0), (900.0, 1000.0))

#############################
#### Ranged Timeplot parms ##
#############################

#uv_ranges=((430.0,450.0), (450.0,515.0), (515.0, 570.0), (570.0,620.0), (620.0,680.0))
uv_ranges=8
