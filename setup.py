import sys
import os.path as op
#from distutils.core import setup
from setuptools import setup, find_packages

NAME = 'pyuvvis'

# Python >= 2.7 ?
user_py = sys.version_info
if user_py < (2, 7):
    raise SystemExit('%s requires python 2.7 or higher (%s found).' % \
                     (NAME, '.'.join(str(x) for x in user_py[0:3])))


#XXX Get current module path and do path.join(requirements)
#with open(op.join(sys.path[0], 'requirements.txt')) as f:
with open('requirements.txt', 'r') as f:
    required = f.readlines()
    required = [line.strip() for line in required]
    
# For now, most of these are in here for testing.  Dependency version 
#requirements can probably be relaxed, especially chaco.
setup(
    name = NAME,
    version = '0.2',
    author = 'Adam Hughes',
    maintainer = 'Adam Hughes',
    maintainer_email = 'hughesadam87@gmail.com',
    author_email = 'hughesadam87@gmail.com',
    packages = find_packages(),

    # include .tex and .ipynb files
    package_data={
      'pyuvvis.scripts.gwu_script.tex_templates': ['*.tex'],
      'pyuvvis.scripts.gwu_script.mlab_templates': ['*.m'],   
#      'pyparty.bundled':['*.css'],   
      'pyuvvis.examples.Notebooks':['*.ipynb'],
      'pyuvvis.scripts.gwu_script':['*.png'],
      'pyuvvis.data':['*'],
      'pyuvvis.bundled':['*.css']
   },
       
    entry_points = {'console_scripts': 
                    [
                       'gwuspec = pyuvvis.scripts.gwu_script.gwuspec:main',
                       'gwureport = pyuvvis.scripts.gwu_script.gwureport:main'
                    ]
                    },
    
    url = 'http://pypi.python.org/pypi/PyUvVis/',
    download_url = 'https://github.com/hugadams/pyuvvis',
    license = 'LICENSE.txt',
    description = 'Pandas-based toolkit for spectral data analysis, primarily '
    'UVVis spectra for now.',
      classifiers = [
          'Development Status :: 2 - Pre-Alpha',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Developers',
          'Natural Language :: English',
#          'Operating System :: OSIndependent',  #This is limited only by 
          'Programming Language :: Python :: 2',
          'Topic :: Scientific/Engineering :: Visualization',
          'Topic :: Scientific/Engineering :: Chemistry',
          'Topic :: Scientific/Engineering :: Physics',
          'Topic :: Scientific/Engineering :: Medical Science Apps.',
          ],
)
