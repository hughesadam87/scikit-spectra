float_display_units = 3 #When outputting floats to plots/printout, how many 
                        # labels to display
                        
multicols = 3 #Default number of columns when making multiplot of stacked data

PAD = 4 * ' ' #padding

#I'd like a config do diplay full or short name of time unit/spec unit/iunit on plots...

# DEFAULT PLOT Options
# --------------------

# Fonts/Labels
LABELSIZE = 'medium'
TITLESIZE = 'large'


# 1D
CMAP_1DSPECPLOT = 'coolwarm' #Divergent red/blue/gray middle

# Contour
CMAP_CONTOUR = 'seismic'  #Divergent red/blue white middle
NUM_CONTOURS = 20
FILL_CONTOUR = False


# 3D
COLOR_3DPLOT = 'gray'
PROJECTION_CMAP = 'jet' #Default color of PRoJECTION in add_projection
MESH = 10 #Strides in surf/wire plots.  If data is under this number
C_MESH = MESH
R_MESH = MESH  #If want default mesh to be non-square

# Spectra output spacing
HEADERDELIM = '\t'
HEADERHTMLDELIM = '&nbsp;' * 8

# Default specifier to Spectrum
SPECIFIERDEF = 'values' 
MISSING = '??' #When unit info is missing, header/plotting will refer to this
