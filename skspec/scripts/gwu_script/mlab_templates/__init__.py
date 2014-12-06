# Return various templates directly as strings

import os.path as op

def opd(basename):
    ''' Allows one to open datafile using module path directory instead
        of working directory.'''
    return open(op.join(op.dirname(__file__), basename), 'r').read()


# These are returned as strings (due to .read() method above)
SIMPLE_M = opd('simple.m')


