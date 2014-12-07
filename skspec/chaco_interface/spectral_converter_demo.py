from traits.api import HasTraits, Float, Array, Property, Enum, Trait, CFloat, Constant
from traitsui.api import View, Item, Group, HSplit, VSplit
from numpy import linspace, array
from math import pi

# Help text:
ViewHelp = """
This program is based on the Converter example in the TraitsUI examples archive.  This example is similar with
the following changes:
  1.  Full arrays are used in the place of single values for all the conversions.
  2.  The conversions allow for reciprocal unit systems, which is often necessary in spectrometry.  For example,
      the energy of a photon can be described in energy units, but also in units of wavelength and frequency using 
      the formulas:  E=hf  and lf=c   
	E=photon energy, c=speed of light, l=wavelength of light, f=frequency of light, c=speed of light
        Therefore, the energy and wavelength are related inversely by E=hc/l
  3.  The first and last values of the array are shown in the View to give the view some idea of the underlying array
      manipulations taking place.  This is merely for aesthetics.
"""

class SpectralConverter ( HasTraits ):
    '''Converts between many sets of spectral units'''
    h=float(6.626068*10**-34)          #Planck's constant m**2 kg / s
    eVtoJ=float(1.60217646 * 10**-19)  #Number of Joules in one eV (needed becasue eV is not the standard MKS unit of energy)
    c=float(299792458)                 #speed of light m/

    # Units trait maps all units to meters.  This allows us to use the physical constants in there MKS default units:
    Units = Trait( 'Meters', { 'Meters':      1.0,        
				   'Centimeters':.01,
				   'Micrometers':.000001,    #All of these are proportional to units of length
				   'Nanometers': .000000001,          
				   'cm-1': .01,              #All of these are inversely proportional to units of length
				   'Wavenumber(nm-1)':.000000001, 
				   'Frequency(Hz)':  c,  
				   'Angular Frequency(rad)': 2.0*pi*c,
				   'eV': h*c/(eVtoJ)  
					 } )

    #Next we specify which units are related to length directly and inversely#
    proportional=['Meters', 'Nanometers', 'Centimeters', 'Micrometers'] 
    reciprocal=['cm-1', 'eV', 'Wavenumber(nm-1)', 'Frequency(Hz)', 'Angular Frequency(rad)']             

    input_array  = Array( )   #Set on initialization
    input_units  = Units( )   #Set on initialization
    output_array = Property(Array, depends_on = [ 'input_array', 'input_units',
                                             'output_units' ])
    output_units  = Units('Frequency(Hz)')  #Default output unit

    #Property Traits#
    xstart=Property(Float, depends_on='input_array')
    xend=Property(Float, depends_on='input_array')

    xnewstart=Property(Float, depends_on='output_array')
    xnewend=Property(Float, depends_on='output_array')

    traits_view=View(  
		VSplit(
		Group(HSplit( Item('xstart', label='Old Spectral Min', style='readonly'), 
			      Item('xend', label='Old Spectral Max', style='readonly'),
			      Item('input_units' , style='simple', label='Input Units' ))  ),
		Group(HSplit( Item('xnewstart', label='New Spectral Min'),
			      Item('xnewend', label='New Spectral Max'), 
			      Item('output_units', label='Output Units')  )
		      )
		      ),  kind='modal', width=800, # help=ViewHelp,
		          buttons = [ 'Undo', 'OK', 'Cancel', 'Help' ])

    # Property implementations#
    def _get_xstart(self): return self.input_array[0]

    def _get_xend(self):  
	end=(self.input_array.shape[0])-1
	return self.input_array[end]

    def _get_xnewstart(self): return self.output_array[0]
	
    def _get_xnewend(self): 
	end=self.output_array.shape[0]-1
	return self.output_array[end]

    #This computes the new array, and depending on the relation between the input and output values,
    # it changes the output to account for the relative inversion between the quanties.  There are four
    # cases to consider:
	 #(both inputs are in proportional list--no relative inverion)
         #(both inputs are in reciprocal list--double inversion)
         #(one input in reciprocal, one in proprotional- single inversion (2 cases)
    def _get_output_array ( self ):
	if self.input_units in self.proportional and self.output_units in self.proportional:
	        return (self.input_array * self.input_units_) / self.output_units_

	elif self.input_units in self.proportional and self.output_units in self.reciprocal:
	        return 1.0/( (self.input_array * self.input_units_) / self.output_units_)

	elif self.input_units in self.reciprocal and self.output_units in self.proportional:
	        return 1.0/( (self.input_array * self.output_units_) / self.input_units_)   #Output/input

	elif self.input_units in self.reciprocal and self.output_units in self.reciprocal:
	        return  (self.input_array * self.output_units_) / self.input_units_

if __name__ == '__main__':
    #Populate an aribtrary array to mimic the visible light spectrum (400nm -700nm)#
    x=linspace(400, 700, num=100)
    f=SpectralConverter()
    f.input_array=x; f.input_units='Nanometers'
    f.configure_traits()
