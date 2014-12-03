""" Wrappers and utilitiles for MPLD3 customization """

import mpld3
from mpld3.plugins import Reset, Zoom, BoxZoom, \
           PointLabelTooltip, PointHTMLTooltip, LineLabelTooltip, \
           MousePosition, LineHTMLTooltip

ALLPLUGINS = dict(
   reset=Reset,
   zoom=Zoom,
   boxzoom=BoxZoom, 
   pointlabel=PointLabelTooltip,
   pointHTMLlabel = PointHTMLTooltip, 
   linelabel=LineLabelTooltip, 
   linehtml=LineHTMLTooltip,
   mousepos=MousePosition
   )

# Reversed dictionary
ALLPLUGINS_REV = dict((v, k) for k,v in ALLPLUGINS.items())

# Plugins that require access to lines
LABELPLUGINS = [LineLabelTooltip, PointLabelTooltip]
HTMLPLUGINS = [LineHTMLTooltip, PointHTMLTooltip]

DEFAULTS = ('reset','boxzoom','zoom')

class PluginManagerError(Exception):
   """ """

class PluginManager(object):
   """ Wrapper for adding/removing/printing plugins available on a 
   mplfigure.  Returns a figure (via self.fig) with seleted plugins attached.
   Used primarily for widgets/guis where the state of plugins
   needs managed.  Otherwise, using MPLD3 API directly with a mpl figure
   is simple and preferred.
   """
   
   def __init__(self, fig, ax=None, names=None):
      """ """
 
      # Set fig logic through property
      self.reset_plugins()
      # Goes through property
      self.fig = fig
      
      self.ax = ax
      if self.ax is None:
         self.ax = fig.get_axes()[0]
         if len(fig.get_axes()) > 1:
            raise PluginManager('Multiple axes found in figure; pass axes directly!') 

      self.lines = self.ax.get_lines()
      if not self.lines:
         raise PluginManagerError('No lines found on axes; is this a line plot?') #should be warn

      # Set some names for lines
      self.names = names
      if not self.names:
         self.names = ['Line: %s' % i for i in range(len(self.lines))]
     
        
   def reset_plugins(self):
      """ Sets plugins to default values """
      self._plugins = dict((k,ALLPLUGINS[k]) for k in DEFAULTS
                           if k in ALLPLUGINS) 
   
   @property
   def fig(self):
      """ Returns figure with plugins attached."""
      mpld3.plugins.clear(self._fig)
      for p in self._plugins.values():
         if p in LABELPLUGINS:
            for idx, line in enumerate(self.lines):
               mpld3.plugins.connect(self._fig, p(*self.lines))            

         else:
            mpld3.plugins.connect(self._fig, p())
     #    except TypeError:
     #       mpld3.plugins.connect(self._fig, p(*self.lines))            
      return self._fig
                           
   @fig.setter
   def fig(self, fig):
      """ Upon new fig, sets default plugins from that figure. """
      if fig is None:
         raise PluginManager('FIG CANNOT BE NONE')
      
      self._fig = fig
      self._plugins = {}
      
      # By default, mpld3 adds plugins if finds mpl plot
      oldplugs = mpld3.plugins.get_plugins(fig)

      for plug in oldplugs:
         pclass = plug.__class__
         if pclass in ALLPLUGINS_REV:
            self.add(ALLPLUGINS_REV[pclass]) #Set key from class
         else:
            # fig has a plugin that we don't know about
            # (maybe should jsut add it with custom key like unknown plugin1
            raise PluginManagerError('UNKNOWN PLUGIN %s' % plug)
            
   @property
   def plugins(self):
      return self._plugins.values()
   
   @property
   def available(self):
      return self.ALLPLUGINS 
   
   def add(self, *plugins):
      """ Add a plugin to figure """
      for plugin in plugins:
         if not isinstance(plugin, basestring):
            raise PluginManagerError('Can only add plugins as strings; use dictionary'
                                  ' interface to add new plugins.')
         self._plugins[plugin] = ALLPLUGINS[plugin]
      
   def remove(self, *plugins):
      # Let dictionary do its own error handling...
      for plugin in plugins:
         del self._plugins[plugin]

   def __getitem__(self, *args, **kwargs):
      return self._plugins.__getitem__(*args, **kwargs)
   
   def __setitem__(self, *args, **kwargs):
      self._plugins.__setitem__(*args, **kwargs)
      
   def __delitem__(self, *args, **kwargs):
      self._plugins.__delitem__(*args, **kwargs)
      
#   def __repr__(self, *args, **kwargs):
#      """ """
 
if __name__ == '__main__':
   import matplotlib.pyplot as plt
   f, ax = plt.subplots()
   ax.plot([1,2,3,4])
   ax.plot([1,3,6,10])
   
#   points = ax.plot(range(10), 'o')
#   print points

#   points = ax.scatter(range(40), range(40))
   pman = PluginManager(fig=f)
   
   
   pman.add('mousepos')
   print pman._plugins
   pman.remove('boxzoom')
   pman.remove('zoom')
#   pman.add('linelabel')
   print pman._plugins
   
   

#   plugins.connect(fig, PointLabelTooltip(points[0]))
#   fig_to_html(fig)   
   mpld3.show(pman.fig)