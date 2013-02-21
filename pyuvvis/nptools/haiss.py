''' Series of utilities for determining the size of spherical gold nanoparticles 
    from the optical aborsbance spectra, as published in:

    Haiss, Thanh, Aveyard, Fernig, Determination of Size and Concentration of Gold 
    Nanoparticles from UV-Vis Spectra Anal. Chem, 79, 2007.

    Three functions are build based on the results of this paper, as well as a utility
    for estimating nanoparticle concentration.'''

import math
import numpy as np

def quick_haiss_m1(ts, style='boxcar', width=None, limit_range=(400.0,700.0)):
    ''' Wrapper function for Haiss method  1.  Allows for range slicing/smoothing and applies
        haiss_m1 over the entire timespectra object.

        Parameters:
        ---------
  
        ts: TimeSpectra.
        style: Smoothing style.  For now, only boxcar is used.
        width: Smoothing binwidth in units of ts.specunit.  If None or 0, no smoothing is performed.
        boxcar: the value of boxcar when smoothing the spectrum
        limit_range: width of the range used (default is (400.0,700.0)
    
        Notes:
        -----------
    
        TimeSpectra must have iunit of absorbance.  Code attempts to convert it but does not attempt
        to add a baseline if ts.iunit results in an error.  
        
        Boxcar is an INSTANCE METHOD of TimeSpectra.  A boxcar function that returns a dataframe can 
        be found in pyuvvis.core.utilities.
        
        Code may error if user passes a curve with
        a maximum very far from 510 (lam0 in haiss_m1) as the log will blowup.         
    
    '''

    ### Make sure data is in absorbance mode
    if ts.iunit != 'a':
        try:
            ts.iunit='a'
        except Exception:
            raise TypeError('%s must be in absorbance units for quick_haiss_m1 to function.'%ts.name)

    if width==0.0:
        width=None

    ### Smoothing    
    if width:
        if style=='boxcar':
            try:
                ts=ts.boxcar(width)
            except AttributeError:
                raise AttributeError('Cannot find boxcar() method on %s object.'%ts.name)
        else:
            raise NotImplementedError('Only boxcar smoothing is available')
    
    ### Slice data
    if limit_range:        
        if len(limit_range) != 2:
            raise AttributeError('Limit_range must be a length-2 iterable.')
        
        ts=ts.ix[ limit_range[0]:limit_range[1] ]

    ### Feed index at maxiumum. to haiss function
    spr=ts.idxmax()    
    return spr.apply(haiss_m1)
        

def quick_haiss_m2(ts, ref=450.0, width=None, style='boxcar', ref_width=None, 
                    peak_wdith=None, limit_range=(400.0,700.0), exp=True):
    ''' Wrapper for haiss_m2 to return diamter of nanoparticles based on features of its
        absorbance spectrum relative to water.  Program has special call options to handle
        smoothing and range slicing on the fly.

    Parameters:
    ----------
    curve: 
    smooth: If True, applies smoothing to ts.
    boxcar: The value of boxcar when smoothing the spectrum.
    width: Smoothing binwidth in units of ts.specunit.
    limit_range: width of the range used (default is (400.0,700.0)
    peak_width: The width of the range which we regard as the peak window.
    Xspr: x value (wavelength) corresponding to max y
    Aspr: if using peak_width, uses average value of absorbance in range [Xspr-peak_width : Xspr+peak_width] as maximum absorbance. Otherwise, defaults to max value.
    ref_width: The width of the range designated for reference point window
    Aref: if using ref_width, uses average value of absorbance in range [refspr-ref_width : refspr+ref_width] as reference value. Otherwise, defaults to max value

    Notes:
    -----------
    TimeSpectra must have iunit of absorbance.  Code attempts to convert it but does not attempt
        to add a baseline if ts.iunit results in an error.  
        
        Boxcar is an INSTANCE METHOD of TimeSpectra.  A boxcar function that returns a dataframe can 
        be found in pyuvvis.core.utilities.

        Code may error if user passes a curve with
        a maximum very far from 510 (lam0 in haiss_m1) as the log will blowup.
    '''
    ### Make sure data is in absorbance mode
    if ts.iunit != 'a':
        try:
            ts.iunit='a'
        except Exception:
            raise TypeError('%s must be in absorbance units for quick_haiss_m1 to function.'%ts.name)

    ### Smoothing    
    if width==0.0:
        width=None
        
    if width:
        if style=='boxcar':
            try:
                ts=ts.boxcar(width)
            except AttributeError:
                raise AttributeError('Cannot find boxcar() method on %s object.'%ts.name)
        else:
            raise NotImplementedError('Only boxcar smoothing is available')
    
    ### Slice data
    if limit_range:        
        if len(limit_range) != 2:
            raise AttributeError('Limit_range must be a length-2 iterable.')
        
        ts=ts.ix[ limit_range[0]:limit_range[1] ]    
    
    return ts.apply(_quick_haiss_m2, ref=ref, peak_width=peak_width, ref_width=ref_width, exp=exp)


def _quick_haiss_m2(curve, ref=450.0, peak_width=None, ref_width=None, exp=True):
    ''' Private method to quick_haiss_m2.  This separation is necessary to allow
        haissm2 (with 2 required arguments) to be compatable with quick_haiss_m2.
        This handles the single curve/series operations.
    '''

	
    ### Get Aspr from peak value with or w/o averaging neighbors    
    if peak_width:
        Xspr=curve.idxmax(axis=0)
        Aspr=curve[Xspr-peak_width : Xspr+peak_width].mean()
    else:
        Aspr=curve.max(axis=0)

    ### Get Aref from peak value with or w/o averaging neighbors
    if ref_width:
        Aref=curve[ref-ref_width : ref+ref_width].mean()
    else:
        Aref=curve.ix[ref].mean()  #Use single wavelength (raises error if not exact)
     
    ### Depending on type of data passed in (eg if baseline is in set than absorbance is all 0's)
    ### Can get erroneous diameter estimates
    if Aspr==0.0 or Aref==0.0:
        d=np.NaN
    else:
        d= haiss_m2(Aspr, Aref, exp=exp)
    return d

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
        exp: If true, experimentally derived Haiss fit parameters are used; theoretical otherwise.
     
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
