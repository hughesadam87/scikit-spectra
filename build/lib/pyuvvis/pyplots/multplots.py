''' These are multiplots which are intended to'''
import matplotlib.pyplot as plt
import pylab
from pandas import DataFrame

from pyuvvis import divby, specplot, absplot

def quadplot(df, s, a):
    # Can't do this way and only share 2 of the four  axis #
#    fig, ((ax1,ax2), (ax3,ax4))=plt.subplots(2,2)  
    #fig.axes[0]=specplot(df)
    #fig.axes[1]=specplot(df)
    
    #ax1 = plt.subplot(2, 2, 1)
    #ax2 = plt.subplot(2, 2, 3, sharex=ax1)
    
    #ax3 = plt.subplot(2, 2, 2)
    #ax4 = plt.subplot(2, 2, 4, sharex=ax3)    
    
    #print ax1, type(ax1)
    fig=plt.figure()
    fig.axes.append(s)
    fig.axes.append(a)
    

    #ax2.plot(df.divby())
    
    #ax4=specplot(df)
    
    fig.show()
    
    #### Look for uv-vis ranges in data, if not found, default to equally slicing spectrum by 7
    #try:
        #uv_ranges=sp.uv_ranges
        #if isinstance(uv_ranges, float) or isinstance(uv_ranges, int):
            #uv_ranges=spec_slice(df.index, uv_ranges)   
    
    #except AttributeError:
        #uv_ranges=spec_slice(df.index, 8)   
    
    #### Time averaged plot, not scaled to 1 (relative intenisty dependson bin width and actual intensity)
    #dfsliced=wavelength_slices(df, ranges=uv_ranges, apply_fcn='mean')
    #range_timeplot(dfsliced, ylabel='Average Intensity', xlabel='Time ('+timeunit+')' ) #legstyle =1 for upper left
    #plt_clrsave(outdir, options.rname+'raw_time')
    
    #### Now scale curves to 1 for objective comparison
    #dfsliced_norm=dfsliced.apply(lambda x: x/x[0], axis=1)
    #range_timeplot(dfsliced_norm, title='Normalized Range Timeplot', ylabel='Scaled Average Intensity',\
                   #xlabel='Time ('+timeunit+')', legstyle=1 )
    #plt_clrsave(outdir, options.rname+'norm_time')        
    
    #### Area plot using simpson method of integration
    #dfarea=wavelength_slices(df, ranges=(min(df.index), max(df.index)), apply_fcn='simps')                
    #range_timeplot(dfarea, ylabel='Power', xlabel='Time ('+timeunit+')', legend=False,
                   #title='Spectral Power vs. Time (%i nm - %i nm)'%  ## Eventually make nm a paremeter and class method
                   #(min(df.index), max(df.index)), color='r')
    #plt_clrsave(outdir, options.rname+'full_area')

if __name__=='__main__':
    print 'ya'
    df=DataFrame([1,2,3,4])
    s=specplot(df)
    dfa=divby(df)
    a=absplot(dfa)
    plt.clf()
    quadplot(df, s, a)


