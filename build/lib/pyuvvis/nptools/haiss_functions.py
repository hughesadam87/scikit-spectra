''' Series of utilities for determining the size of spherical gold nanoparticles 
    from the optical aborsbance spectra, as published in:

    Haiss, Thanh, Aveyard, Fernig, Determination of Size and Concentration of Gold 
    Nanoparticles from UV-Vis Spectra Anal. Chem, 79, 2007.

    Three functions are build based on the results of this paper, as well as a utility
    for estimating nanoparticle concentration.'''

import math

def haiss_m1(lambda_spr):
    ''' Return diameter from wavelength at spr maximum of absorbance curve.

    Parameters:
    -----------
    lambda_spr: the wavelength at spr absorbance maximum.

    Notes:
    -----------
    this method is not accurate for particles with diameter less than 25nm.

    '''
    lambda_0=512
    L1=6.53
    L2=0.0216

    d=(math.log((lambda_spr-lambda_0)/L1))/L2
    return d

#def full_haiss_m2(spectra, start_450=449.0, stop_450=451.0, start_spr, stop_spr, method='average'):
    #'''Wrapper to haiss_m2 that takes in a spectra, averaging regions '''


def haiss_m2(Aspr, A450, exp=True):
    ''' Return diameter from absorbance at spr and 450 from Haiss et al. 

    Parameters:
        -----------
           Aspr: the absorbance at spr max.
           A450: the absorbance at 450nm.
           exp: If true, experimentally derived Haiss fit parameters are used.
                Otherwise, theoretical Haiss fit parameters are used.

        Notes:
        -----------
           the diameter is calcualted by dividing the absorbance at the spr 
           maximum by that at 450nm and fitting to experimental/theoretical
           parameters.
    '''

    ### Calculate diameter from experimental fit parameters
    if exp:
        B1=3.00 
        B2=2.20
        d=math.exp( (B1 * (Aspr/A450) - B2) )

    ### Calculate diameter from theoretical fit parameters 
    else:
        B1=3.55
        B2=3.11
        d=math.exp( (B1 * (Aspr/A450) - B2) )

    return d


def haiss_m3(Aspr, Cau, exp=True):
    ''' Return diatmeter from starting concentration of gold (in M) and 
        Absorbance at spr max from Haiss et al.

    Parameters:
        -----------	    
    Aspr: the absorbance at spr max,
    	Cau: initial concentration of gold(in mol per liter).
            exp: If true, experimentally derived Haiss fit parameters are used.
                Otherwise, theoretical Haiss fit parameters are used.

        Notes:
        -----------	    

    '''

    term=5.89*10**-6

    ### Calculate diameter from experimental fit parameters
    if exp:
        C1=-4.75
        C2=0.314 
        d=( (Aspr * term )/(Cau * math.exp(C1) ) )**(1.0/C2)

    ### Calculate diameter from theoretical fit parameters 
    else:
        C1=-4.70
        C2=0.300
        d=( (Aspr * term )/ (Cau * math.exp(C1) ) )**(1.0/C2)

    return d

def haiss_conc(A450, d):
    ''' Compute number nanoparticles from A450 and diameter '''
    num=A450 * 10**14
    t1=1.36*math.exp(-( (d-96.8)/(78.2)  )**2  )
    den=d**2 * (-0.295+ t1)
    return(num/den)
