""" Define various notebook styles that may be launched easily in-line in an 
active notebook.  Same IO API as pyparty.data"""

import os.path as op
from skspec import bundled_dir
from IPython.display import display, HTML

def load(path):
    with open((op.join(bundled_dir, path)), 'r') as f:
        return f.read()

def gwu():
    """ Ivory background; Computer Modern Roman for text """
    return load('gwu.css')

def plain():
    return ''


__all__ = {
           'gwu': gwu(),
           'plain' : plain()
           }

# In-line function called in the notebook to update the style.  This is the
# work of Brian Granger; all credit to him for this and his help in general
# discussions of notebooks styling.
# https://github.com/ellisonbg/talk-cplug2013/blob/master/load_style.py
def load_style(s, figsize=None, loghide=False):
    """Load a CSS stylesheet in the notebook either by builtin styles, or
    from a file, or from a URL.

    Examples::
        %load_style 
        %load_style mystyle.css
        %load_style http://ipynbstyles.com/otherstyle.css
    """
    if s in __all__:
        style = __all__[s]
    
    elif s.startswith('http'):
        try:
            import requests
        except ImportError:
            raise ImportError('Failed to import python "requests" library;'
                              'please install to use load_style(url)')
        r =requests.get(s)
        style = r.text

    else:
        try:
            with open(s, 'r') as f:
                style = f.read()
        except IOError:
            raise IOError('Failed to load style as a url, file or builtin type.'
               ' Valid builtins are "%s"' % '","'.join(__all__.keys() ))

    out = '<style>\n{style}\n</style>'.format(style=style)
    
    if figsize:
        if figsize == True:
            figsize = 8, 5.5
        else:
            try:
                fx, fy = figsize
            except Exception:
                fx, fy = figsize, figsize
            
        fstring = "\ninput:pylab.rcParams['figure.figsize'] = %s, %s\n" \
            % (fx,fy)
        out += fstring

    display(HTML(out))
    
    if loghide:
        import warnings #supress non-skspec log msgs
        warnings.filterwarnings('ignore')             
    
def load_ipython_extension(ip):
    """Load the extension in IPython."""
    ip.register_magic_function(load_style)