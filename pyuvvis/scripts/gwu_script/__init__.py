import os.path as op

# UNLIKE TEX_TEMPLATE __INIT__, RETURNS PATH INSTEAD CONTENTS OF FILE 
# Removes .png

LOGO_PATH = op.splitext(op.join(op.dirname(__file__), 'gwulogo.png'))[0]