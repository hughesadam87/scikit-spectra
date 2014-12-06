''' Series of utilities for determining the size of spherical gold nanoparticles 
    from the optical aborsbance spectra, as published in:

    Haiss, Thanh, Aveyard, Fernig, Determination of Size and Concentration of Gold 
    Nanoparticles from UV-Vis Spectra Anal. Chem, 79, 2007.

    Three functions are build based on the results of this paper, as well as a utility
    for estimating nanoparticle concentration.'''

import math
import numpy as np
import warnings

def _haiss_preformat(ts, style='boxcar', width=None, limit_range=(400.0,700.0)):
    '''Called by other haiss method to preforma the timespectra before calling
       haiss functions.
       
        See description under haiss_m1 for explanation of parameters.  '''


    ### Ensure ts is in units of absorbance and has nanometer spectral unit
    if ts.iunit != 'a':
        try:
            ts.iunit='a'
        except Exception:
            raise TypeError('%s must be in absorbance units for quick_haiss_m1 to function.'%ts.name)
        else:
            warnings.warn('Converted iunit to absorbance in haiss function.')
        
    
    if ts.specunit != 'nm':
        try:
            ts.specunit='nm'
        except Exception:
            raise TypeError('%s must have specunits of nm to be consistent with published formulae.'%ts.name)
        else:
            warnings.warn('Converted specunit to nm in haiss function.')
            
                    
  
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
        
    return ts

def haiss_m1(ts, style='boxcar', width=None, limit_range=(400.0,700.0)):
    ''' Wrapper function for Haiss method  1.  Allows for range slicing/smoothing and applies
        haiss_m1 over the entire timespectra object.

        Parameters:
        ---------
  
        ts: TimeSpectra.
        style: Smoothing style.  For now, only boxcar is used.
        width: Smoothing binwidth in units of ts.specunit.  If None or 0, no smoothing is performed.
        limit_range: width of the range used (default is (400.0,700.0)
    
        Notes:
        -----------
    
        TimeSpectra must have iunit of absorbance.  Code attempts to convert it but does not attempt
        to add a reference if ts.iunit results in an error.  
        
        Boxcar is an INSTANCE METHOD of TimeSpectra.  A boxcar function that returns a dataframe can 
        be found in skspec.core.utilities.
        
        Code may error if user passes a curve with
        a maximum very far from 510 (lam0 in haiss_m1) as the log will blowup.         
    
    '''

    ts=_haiss_preformat(ts, style=style, width=width, limit_range=limit_range)

    ### Feed index at maxiumum. to haiss function
    spr=ts.idxmax()    
    return spr.apply(_haiss_m1)
        

def haiss_m2(ts, ref=450.0, width=None, style='boxcar', ref_width=None, 
                    peak_width=None, limit_range=(400.0,700.0), exp=True):
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
    peak_width: +/- wavelength to average around peak value when determining Absorbance at SPR.
    Xspr: x value (wavelength) corresponding to max y
    Aspr: if using peak_width, uses average value of absorbance in range [Xspr-peak_width : Xspr+peak_width] as maximum absorbance. Otherwise, defaults to max value.
    ref_width: The width of the range designated for reference point window
    Aref: if using ref_width, uses average value of absorbance in range [refspr-ref_width : refspr+ref_width] as reference value. Otherwise, defaults to max value
    exp: If true, use experimental parameters from Haiss et. al. to do fit; otherwise use theoretical.

    Notes:
    -----------
    TimeSpectra must have iunit of absorbance.  Code attempts to convert it but does not attempt
        to add a reference if ts.iunit results in an error.  
        
        Boxcar is an INSTANCE METHOD of TimeSpectra.  A boxcar function that returns a dataframe can 
        be found in skspec.core.utilities.

        Code may error if user passes a curve with
        a maximum very far from 510 (lam0 in haiss_m1) as the log will blowup.
    '''
    
    ts=_haiss_preformat(ts, style=style, width=width, limit_range=limit_range)
    
    return ts.apply(_m2_haiss, ref=ref, peak_width=peak_width, ref_width=ref_width, exp=exp)


def _m2_haiss(curve, ref=450.0, peak_width=None, ref_width=None, exp=True):
    ''' Private method to quick_haiss_m2.  This separation is necessary to allow
        haissm2 (with 2 required arguments) to be compatable with quick_haiss_m2.
        In other words, because we need to compute Aspr and Aref separately, can't
        just call .apply() method in the normal fashion as done for example
        in _haiss_m1/_haiss_m3. This handles the single curve/series operations.
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
        Aref=curve.ix[ref]   #FIND CLOSEST WAVELENGTH
                
 
    if Aspr==0.0 or Aref==0.0:
        d=np.NaN
    else:
        d= _haiss_m2(Aspr, Aref, exp=exp)
    return d

def _haiss_m1(lambda_spr):
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


def _haiss_m2(Aspr, A450, exp=True):
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

def haiss_m3(ts, Cau, dilution=None, style='boxcar', width=None, limit_range=(400.0,700.0), peak_width=None, exp=True):
    ''' Wrapper function for Haiss method  3.  Estimates diamter of gold nanoparticles
        based on the SPR max of the absorbance and the initial concentration of gold use to synthesize
        the nanoparticles.  Should be valid between 5-50nm diatmeters.  Please take note of the dilution
        parameter description below.

        Parameters:
        ---------
  
        ts: TimeSpectra.
        Cau: Initial concentration of gold used to synthesize nps (in mol/L)
        dilution: This method requires absorbance of FULLY concentrated np solution.  If data was taken for
                  a dilute conenctration, say 10% stock NP concentration, then use dilution=0.1.
        style: Smoothing style.  For now, only boxcar is used.
        width: Smoothing binwidth in units of ts.specunit.  If None or 0, no smoothing is performed.
        limit_range: width of the range used (default is (400.0,700.0)
        peak_width: +/- wavelength to average around peak value when determining Absorbance at SPR.
        exp: If true, use experimental parameters from Haiss et. al. to do fit; otherwise use theoretical.

    
        Notes:
        -----------
    
        TimeSpectra must have iunit of absorbance.  Code attempts to convert it but does not attempt
        to add a reference if ts.iunit results in an error.  
        
        Boxcar is an INSTANCE METHOD of TimeSpectra.  A boxcar function that returns a dataframe can 
        be found in skspec.core.utilities.
        
        We've independently verified that Absorbance at relevant wavelengths (400-700nm) scales linearly 
        with concentration from dilutions as low as 1% up to fully concentrated NP's.  By fully concentrated,
        we mean the typical batch concentration made from the Turkevich protocol (Generally 10^12-14 np's/mL)
        In extremely dilute or concentrate solutions, this linearity may breakdown and the accuracy of this 
        function is reduced.

    '''

    ts=_haiss_preformat(ts, style=style, width=width, limit_range=limit_range)

    ### Feed index at maxiumum. to haiss function
    ### Get Aspr from peak value with or w/o averaging neighbors    
    if peak_width:
        ### Need to compute a slice average based on SPR xvalue (bit tricky when ts not a single curve)
        Xspr=ts.idxmax(axis=0)
        xrng0=Xspr-peak_width
        xrng1=Xspr+peak_width
        xavg=(xrng0 + xrng1) / 2.0
        Aspr=ts.ix[xavg].mean()
    else:
        Aspr=ts.max(axis=0)
        
    ### Scale up Aspr based on dilution factor.
    if dilution:
        Aspr=Aspr/dilution

    return Aspr.apply(_haiss_m3, Cau=Cau, exp=exp)


def _haiss_m3(Aspr, Cau, exp=True):
    ''' See descriptoin for haiss_m3 '''

    term=5.89*10**-6

    ### Calculate diameter from experimental fit parameters
    if exp:
        C1=-4.75
        C2=0.314 

    ### Calculate diameter from theoretical fit parameters 
    else:
        C1=-4.70
        C2=0.300

    return ( (Aspr * term )/ (Cau * math.exp(C1) ) )**(1.0/C2)

def haiss_conc(ts, d, style='boxcar', width=None, limit_range=(400.0,700.0), ref=450.0, ref_width=None, exp=True):
    ''' Return estimation of AuNP concentration given the diameter of gold nanoparticles as the Absorbance
        at 450nm (or other wavelength controlled by ref).  Should be valid for particles with diameters ranging
        from 2.5nm to 100nm and possibly beyond these limits.  Works for stock and dilute samples.
        
        Parameters:
        ---------
  
        ts: TimeSpectra.
        d: Size of gold nanoparticles in nm
        style: Smoothing style.  For now, only boxcar is used.
        width: Smoothing binwidth in units of ts.specunit.  If None or 0, no smoothing is performed.
        limit_range: width of the range used (default is (400.0,700.0)
        ref: Wavelength used for calibration in haiss paper (default is 450nm)
        ref_width: +/- wavelength to average around peak value when determining Absorbance at ref.
        exp: If true, use experimental parameters from Haiss et. al. to do fit; otherwise use theoretical.
       
        Notes:
        -----
          I verified that dilution is not a factor by including it into some trials.  Since N scales linearly 
          with A450, then a dilution of .1 yeilds 1/10th N and so forth.  Therefore, uses can take results form
          this function, and scale them up by the dilution factor to get the full-batch number density.
        
        '''
    ts=_haiss_preformat(ts, style=style, width=width, limit_range=limit_range)
    ### Get Aref from peak value with or w/o averaging neighbors
    if ref_width:
        Aref=ts.ix[ref-ref_width : ref+ref_width]  #Stil slices by wavelength
    else:
        Aref=ts.ix[ref]  #FIND CLOSEST WAVELENGTH    
    
    return Aref.apply(_haiss_conc, d=d)


def _haiss_conc(Aref, d):
    ''' See haiss conc '''
    num=Aref * 10**14
    t1=1.36 * math.exp(-( (d-96.8)/(78.2))**2 )
    den=d**2 * (-0.295+ t1)
    return num/den
