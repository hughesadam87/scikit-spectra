import sys
import os.path as op
from setuptools import setup, find_packages

NAME = 'scikit-spectra'

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
    version = '0.3.2-1',
    author = 'Adam Hughes',
    maintainer = 'Adam Hughes',
    maintainer_email = 'hughesadam87@gmail.com',
    author_email = 'hughesadam87@gmail.com',
    packages = find_packages(),

    # include .tex and .ipynb files
    package_data={
      'skspec.scripts.gwu_script.tex_templates': ['*.tex'],
      'skspec.scripts.gwu_script.mlab_templates': ['*.m'],   
#      'pyparty.bundled':['*.css'],   
      'skspec.examples.Notebooks':['*.ipynb'],
      'skspec.scripts.gwu_script':['*.png', '*.ipynb'],
      'skspec.data':['*'],
      'skspec.bundled':['*.css']
   },
       
    entry_points = {'console_scripts': 
                    [
                       'gwuspec = skspec.scripts.gwu_script.gwuspec:main',
                       'gwureport = skspec.scripts.gwu_script.gwureport:main'
                    ]
                    },
    
    url = 'http://hugadams.github.io/scikit-spectra/',
    download_url = 'https://github.com/hugadams/scikit-spectra',
    license = 'LICENSE.txt',
    description = 'Spectroscopy in Python built on Pandas.',
      classifiers = [
          'Development Status :: 3 - Alpha',
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
