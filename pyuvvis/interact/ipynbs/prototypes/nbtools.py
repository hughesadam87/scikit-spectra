def mpl2html(fig, title="Figure"):
    """ Converts a matplotlib fig into an IPython HTML Core object for display 
    compatibility in widgets."""
    from IPython.core.pylabtools import print_figure
    import base64

    fdata64 = base64.b64encode(print_figure(fig))
    html_tpl = '<img alt="{title}" src="data:image/png;base64,{fdata64}">'
    return html_tpl.format(**locals())
