""" Utilities to run notebooks offline, among others.  CREDIT FOR MOST OF THIS GOES TO:
https://github.com/ipython/ipython/wiki/Cookbook%3a-Notebook-utilities """

import os,sys,time

from Queue import Empty
try:
    from IPython.kernel import KernelManager
except ImportError:
    from IPython.zmq.blockingkernelmanager import BlockingKernelManager as KernelManager 
from IPython.nbformat.current import reads, NotebookNode
 

MAX_TIMEOUT = 60 #Seconds before cell is timed out

# IMPLEMENT LOGGING SOON

import logging
logger = logging.getLogger(__name__)


def run_nb_offline(nb_path):
    """ Read notebook from filepath and execute it; report errors in code cells.
    """
    if not os.path.isfile(nb_path):
        raise Exception('Invalid path: %s' % nb_path)
    with open(nb_path) as f:
        nb = reads(f.read(), 'json')
	
    logging.info("Running notebook %s" % nb.metadata.name)
    km = KernelManager()
    km.start_kernel(stderr=open(os.devnull, 'w'))
    try:
        kc = km.client()
    except AttributeError:
        # 0.13
        kc = km
    kc.start_channels()
    shell = kc.shell_channel
    # simple ping:
    shell.execute("pass")
    shell.get_msg()
    
    cells = 0
    failures = 0
    for ws in nb.worksheets:
        for cell in ws.cells:
            if cell.cell_type != 'code': #ONLY RUN CODE CELLS
                continue
            shell.execute(cell.input)
            # wait for finish, maximum TIMEOUT
            reply = shell.get_msg(timeout=MAX_TIMEOUT)['content']
            if reply['status'] == 'error':
                failures += 1
                logging.info("\nNotebook FAILURE:")
                logging.info(cell.input)
                logging.info('-----')
                logging.info('raised:')
                logging.info('\n'.join(reply['traceback']))
            cells += 1
#            sys.stdout.write('.')
 
    logging.info("Finished running notebook")
    logging.info( "    ran %3i cells" % cells)
    if failures:
        logging.warning( "    %3i cells raised exceptions" % failures)
    kc.stop_channels()
    km.shutdown_kernel()
    del km
 
if __name__ == '__main__':
    for ipynb in sys.argv[1:]:
        run_notebook(nb)
