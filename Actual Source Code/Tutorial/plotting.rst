Plotting
========

.. role:: red  #This doesn't work...

**Note, many of the coloring features introduced here don't work with older versions of matplotlib.**
I tested this on 1.1.0-2, on Ubuntu 10.04.  Please email me a hughesadam87@gmail.com for help and suggestions.

Intro
-----

**pyuvvis** plotting is based on pandas and matplotlib plotting capabilities.  These 
include wrappers around matplotlib's contour and 3d plotting API, as well as easier
normalized color mapping.  This section will demonstrate these basic new plotting components,
and then how one can extend them into other areas of interest, such as 2d correlation analysis (2dca_).

   .. _2dca: http://en.wikipedia.org/wiki/Two-dimensional_correlation_analysis

The three new plotting functions introduced by pyuvvis are **_genplot**, **plot2d**, and **plot3d**.  
These plots will assign plot labels and aesthetics based on a hierarchy of access of keywords, attribute
and then defaults.  In the absence of keywords, these plotting programs will look for the following attributes.

* Title-  **df.name**
* Xlabel- **df.index.name**
* Ylabel- **df.columns.name**

In the absence of these name attributes, it will settle on default values. I am hoping that in the future, these 
attributes become built in to the DataFrame class.

It is easy to change default aesthetics of 1d, 2d or 3d plots, while retaining this attribute hierarchy.  For example,
let me show how the function, **specplot()** is a customized version of **_genplot()**.


.. code-block:: python

    def specplot(df, **pltkwds):
        pltkwds['linewidth']=pltkwds.pop('linewidth', 1.0 )          
        pltkwds['ylabel_def']='Intensity'
        pltkwds['xlabel_def']='Wavelength'
        pltkwds['title_def']='Spectral Plot'   
        return _genplot(df, **pltkwds)

We see that the xlabel, ylabel and title have special keywords that are overwritten, these being xlabel_def, ylabel_def and title_def.  This is necessary to
ensure correct attribute lookup.  Any other pyplot keywords, in this case *linewidth*, can be overwritten using *pop()* as shown above.  This custom plotting very easy, and is more
useful with 2d and 3d plotting.  It ought to work the same way, except instead of **_genplot()**, one uses either **plot2d()** or **plot3d()**.



1d plotting
-----------

Basic 1d plotting is a light wrapper around **pandas'** df.plot().  We can load this function, _genplot(), using:

.. sourcecode:: ipython

   In [73]: from pyuvvis.basic_plots import _genplot  

Upon calling **specplot(df)**, this will yield a plot:

   .. image:: Tutorial_images/specplot.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center

However, the default plot labeling and titling behavior is automatically overwritten in the presence of the ".name" attribute on the DataFrame, and its labels, as described in the preface to this section.  For example, if I assign these name attributes:

.. sourcecode:: ipython

   In [73]: df.name='title'
   In [73]: df.index.name='rowlabel'
   In [73]: df.columns.name='columnlabel'
   In [73]: specplot(df)

The plot no longer relies on its default values:

   .. image:: Tutorial_images/labels.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center

However, they can be manually overwritten with manual keyword passing.

.. sourcecode:: ipython

   In [1]: specplot(df, xlabel='X test', ylabel='Y test', title='Title here')


color mapping
~~~~~~~~~~~~~

Pandas df.plot() already supports solid color assignment through the color keyword parameter.  _genplot()
or any calling wrappers will also have this option.  For example:

.. sourcecode:: ipython

   In [73]: specplot(df, color='r')

Produces:

   .. image:: Tutorial_images/red.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center

.. _here: http://dept.astro.lsa.umich.edu/~msshin/science/code/matplotlib_cm/ 

For now, the color mapping can only map colors to a single curve (eg, 1 color to 1 curve).  Curves currently are colored either by their mean or maximum values along an axis; however, the next pyuvvis update will allow the user to pass *any general function* to determine coloring.  For example, one could color curves based on their mean value proximity to a prime number, or even on a completely different set of criteria stored in another DataFrame.

By default, color maps are normalized to the DataFrame's max and min column values.  We can generate a color map through _df_colormapper().  For example:

.. sourcecode:: ipython

   In [1]: from pyuvvis.pyplots.plot_utils import cmget, _df_colormapper
   In [73]: autumncolors=_df_colormapper(df, 'autumn')
   In [43]: specplot(df, color=autumncolors)

Yields the following plot:

   .. image:: Tutorial_images/autumn.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center


We can choose the upper and lower value limits for normalizability.  For example, if we want the color map to apply to DataFrame curves whose maximum values are between 410.0 and 710.0 (in this case, intensity units of my spectral data), then this is quite easy to assign.

.. sourcecode:: ipython

   In [73]: scaledautumn=_df_colormapper(df, 'autumn', vmin=410.0, vmax=710.0)
   In [43]: specplot(df, color=scaledautumn)

Yields the following plot:

   .. image:: Tutorial_images/autumnscaled.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center

We see that any value greater than 710.0 is yellow, and any value below 410.0 is red.  

Additionally, for certain instances, it is useful to color map along the orthogonal axis:

.. sourcecode:: ipython

   In [1]: uvvis=_df_colormapper(df, 'jet', vmin=410.0, vmax=710.0, axis=1)

This may not be generally practical, but has uses in the scope of pyuvvis.  For example, we can look at the temporal evolution of various wavelength averages in the spectrum, while normalizing based on a prescribed color pattern to the visible light spectrum.  EG:

   .. image:: Tutorial_images/norm_time.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center

More on this plot and analysis will come with the official pyuvvis documentation.


2d plotting
-----------

pyuvvis provides a **plot2d** function, a DataFrame-based wrapper for matplotlib's contour_ plotting function, plt.contour().
   .. _contour: http://matplotlib.org/examples/pylab_examples/contour_demo.html

**plt.contour(df)** will produce a plot; however, will not deduce the proper axis labels from the DataFrame.  I have included a plot2d wrapper that behaves much the same way as the 1d *_genplot()* function, in terms of how it handles name attributes and default values.  Plot2d and also handles other unexpected nuances in regard to the interplay between matplotlib and the pandas DataFrame that most users would not rather be bothered with.  Additionally, more bells and whistles have been included to make it easy to customize some contour plots.

.. sourcecode:: ipython

   In [50]: plot2d(DataFrame, xlabel='xlabel', ylabel='ylabel')

Yields:

   .. image:: Tutorial_images/cont.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center

Colormapping is more easily integrated, taking either literal mapltolib.cm objects, or string wrappers to the aformentioned libraries.  Additionally, the contours input has been changed to keyword input for various reasons.

.. sourcecode:: ipython

   plot2d(df, title='Full Contour', cmap='gray', contours=70)

Produces:

   .. image:: Tutorial_images/gary.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center

It is possible to trick out matplotlib contour plots as shown in the tutorial_; however, I have tried to simplify some of the hassle of this.  In particular, easier control of the labeling style, plot background and colorbars.  Special keyword arguments have been included in plot2d to add some defaul behaviors in all three areas. These are **label**, **colorbar**, and  **background**.  For now, only a few rudimentary defaults have been built in as a proof of concept.  Default styles are chosen using integer arguments.  

.. _tutorial: http://matplotlib.org/examples/pylab_examples/contour_demo.html

For example, we can add plot labels and a colorbar:

.. sourcecode:: ipython

   plot2d(df, title='Full Contour', cmap='jet', contours=15, label=1, colorbar=1)

Producing,

   .. image:: Tutorial_images/c2.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center

Custom labeling styles and colorbars can be manually passed in as shown in the tutorial_ with calls to the plotting methods, plt.clabel() and plt.colorbar() respectively.  As **pyuvvis** grows, more default styles will be added.

The **background** keyword lets the user pass either a formatted color map or custom image directly into the plot background (open any image in PIL first).  This is a wrapper around plt.imshow() (see tutorial_).  Two default color maps are builtin.  For example:

.. sourcecode:: ipython

    plot2d(A, title='Full Contour', cmap='autumn', contours=15, label=1, colorbar=1, background=1)

Gives:

   .. image:: Tutorial_images/cool.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center

This looks pretty cool; however, there are a few bugs I haven't worked out when a background is passed in, the most prominent one of which is that depending on the values of the DataFrame, the plot tends to look very squished!  Another problem is that if you pass in a custom image background, the plot does not yet scale it to fit.  Fixes coming soon.


3d plotting
-----------

**pyuvvis** introduces the plot3d() wrapper, which converts a DataFrame into an Axes3d_ object or Mayavi_ scene.

.. _Axes3d: http://matplotlib.org/mpl_toolkits/mplot3d/tutorial.html

.. _Mayavi: http://code.enthought.com/projects/mayavi/

This does a lot under the hood to make to get nice scene formatting and label behavior, as well as intuitive color and contour mapping, thus it is more than just a laborious wrapper like plot2d() and _genplot().

A default call to plot3d, specifying default elevation and azimuth coordinates (defaults to 0,0):

.. sourcecode:: ipython
   
   plot3d(df, elev=24, azim=-29)

Yields a fully interactive Axes3D subobject:

   .. image:: Tutorial_images/3d.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center

The contour plots projections can be turned on and off selectively via the proj_xy, proj_xz, and proj_yz arguments.  To turn them off:

.. sourcecode:: ipython
   
   plot3d(df, elev=24, azim=-29, proj_xy=None, proj_yz=None, proj_xz=None)

Gives

   .. image:: Tutorial_images/3dNone.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center

For convienence, permutations of the plane projections in the keywords will work as well.  (EG proj_xy or proj_yx are the same keyword).  

The appearance and layout of this surface object takes in a bevy of typical keywords, which can be passed in directly.  I've added two new keywords for convienence, **c_iso** and **r_iso**.  These allow the user to control the number of columnwise and rowwise isolines that are drawn across the surface.  This is a corollary to the Axes3d keywords, **cstrides** and **rstrides**, which control the spacing between the lines.  Depending on use, either of these may be specified in the call to plot3d.  In the following example, I'm playing with the number of isolines (c_iso and r_iso), as well as increasing the surface transparancy (keyword- alpha), as well as adding a title. 

.. sourcecode:: ipython
   
   plot3d(df, elev=24, azim=-29, proj_xy=None, proj_yz=None, proj_xz=None, cmap='jet', c_iso=30, r_iso=30, title='hi there', alpha=0.9)


Yielding

   .. image:: Tutorial_images/3d3.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center

There are three more important keywords to plot3d.  These are: **kind**, **contour_color**, **contour_cmap** and **contour_cmap**.  Kind can take values of "contour" and "contourf", to specify whether the contours should be filled or not.  **contour_color** and **contour_cmap** allow the user to pass a solid color or colormapping to the projections (sorry, for now there is not support for specifying separate colors for each projection.)  The resulting behavior is illustrated below.

.. sourcecode:: ipython

   plot3d(df, elev=24, azim=-29, kind='contourf')
   plot3d(df, elev=24, azim=-29, contour_color='red')
   plot3d(df, elev=24, azim=-29, contour_cmap=cmget('autumn'))

Yielding the following three plots respectively.

   .. image:: Tutorial_images/3dfull.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center

   .. image:: Tutorial_images/3dred.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center

   .. image:: Tutorial_images/3dautumn.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center


We also have included a **poly3d** plotting utility to wrap matplotlib's polygonal plotting facilities.  This is still in development, and seems to have a few kinks to work out.  It should still work out of the box if anyone wants to play around with it.  The issues come in when formatting the plot, and I believe are indigenous to matplotlib itself.

.. sourcecode:: ipython
   from pyuvvis.advanced_plots import poly3d

   poly3d(df)

Produces something akin to, but not exactly, the following:

   .. image:: Tutorial_images/polygon.png
      :height: 5in
      :width: 8in
      :scale: 100 %
      :alt: alternate text
      :align: center




  




























　

　

　
