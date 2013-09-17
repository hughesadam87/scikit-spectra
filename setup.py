import sys
import os.path as op
#from distutils.core import setup
from setuptools import setup, find_packages

NAME='PyUvVis'

# Python >= 2.7 ?
user_py = sys.version_info
if user_py < (2, 7):
    raise SystemExit('%s requires python 2.7 or higher (%s found).' % \
                     (NAME, '.'.join(str(x) for x in user_py[0:3])))


#XXX Get current module path and do path.join(requirements)
with open(op.join(sys.path[0], 'requirements.txt')) as f:
    required = f.readlines()
    required = [line.strip() for line in required]
    
# For now, most of these are in here for testing.  Dependency version 
#requirements can probably be relaxed, especially chaco.
setup(
    name = 'PyUvVis',
    version = '0.1.2-1',
    author = 'Adam Hughes',
    maintainer = 'Adam Hughes',
    maintainer_email = 'hughesadam87@gmail.com',
    author_email = 'hughesadam87@gmail.com',
    packages = find_packages(),
   
    # Remove later after tested that not error incurred
    #packages=['pyuvvis',
              #'pyuvvis.chaco_interface',
              #'pyuvvis.core',
              #'pyuvvis.IO',
              #'pyuvvis.nptools',
              #'pyuvvis.pandas_utils',
              #'pyuvvis.pyplots',
              #'pyuvvis.tests',
              #'pyuvvis.scripts',
              #'pyuvvis.scripts.gwu_scripts',
              #],

    #package_data = {'pyuvvis' : ['example_data/NPSAM/*', 
              #'example_data/spectra.pickle',
              #'example_data/spectra.csv']
                  #},
    
    entry_points = {'console_scripts': [
                       'gwuspec = scripts.gwu_script.gwuspec:main']
                    },
    
    url='http://pypi.python.org/pypi/PyUvVis/',
    download_url='https://github.com/hugadams/pyuvvis',
    license='LICENSE.txt',
    description='Pandas-based toolkit for spectral data analysis, primarily '
    'UVVis spectra for now.',
    long_description=open(op.join(sys.path[0], 'README.rst')).read(),
    install_requires=[
        "pandas >= 0.12.0",
#   	"numpy >= 1.6.0",  #Pandas puts this in
#        "chaco",
     	"scipy", #Probably too high version requirement
                     ],
      classifiers=[
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
