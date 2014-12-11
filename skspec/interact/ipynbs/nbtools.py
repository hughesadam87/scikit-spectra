import time

def mpl2html(fig, title="Figure"):
    """ Converts a matplotlib fig into an IPython HTML Core object for display 
    compatibility in widgets."""
    from IPython.core.pylabtools import print_figure
    import base64

    fdata64 = base64.b64encode(print_figure(fig))
    html_tpl = '<img alt="{title}" src="data:image/png;base64,{fdata64}">'
    return html_tpl.format(**locals())


def log_message(f):
    def wrapper(*args, **kwargs):
        """ args[0] is Spectrogram; args[1] is name of calling function"""

        # Some methods like gui button clicks don't pass args right
        try:
            caller = args[1]
        except IndexError:
            caller = ''
        
        tstart = time.time()
        args[0].message = '<div class="alert alert-warning"> %s triggered by' \
                ' %s </div>' % (f.__name__, caller)
        try:
            out = f(*args, **kwargs)
        except Exception as exc:
            args[0].message = '<div class="alert alert-danger"> %s Failed with' \
                ' exception: (%s) </div>' % (caller, exc.message)
            raise exc
        else:
            args[0].message = '<div class="alert alert-success"> %s() complete' \
                ' (%.2f sec) </div>' % (f.__name__, time.time()-tstart)
        
        return out
    return wrapper