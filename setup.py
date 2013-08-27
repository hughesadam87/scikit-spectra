from distutils.core import setup

# For now, most of these are in here for testing.  Dependency version 
#requirements can probably be relaxed, especially chaco.
setup(
    name='PyUvVis',
    version='0.1.2-1',
    author='Adam Hughes',
    maintainer='Adam Hughes',
    maintainer_email='hughesadam87@gmail.com',
    author_email='hughesadam87@gmail.com',
      packages=['pyuvvis',
                'pyuvvis.chaco_interface',
                'pyuvvis.core',
                'pyuvvis.IO',
   		        'pyuvvis.nptools',
                'pyuvvis.pandas_utils',
                'pyuvvis.pyplots',
                'pyuvvis.tests',
#                'pyuvvis.example_data',
                ],

      # See line in manifest.in that had to be included as well as this.
      # Can load package data using import pkgutil
      # data= pkgutil.get_data('pyuvvis', 'data/example_data/specdata.pickle')
      # Apparently this is useful for impoting using different OS distributions
      package_data={'pyuvvis' : ['example_data/NPSAM/*', 
				'example_data/spectra.pickle',
				'example_data/spectra.csv']
                    },
    url='http://pypi.python.org/pypi/PyUvVis/',
    download_url='https://github.com/hugadams/pyuvvis',
    license='LICENSE.txt',
    description='Pandas-based toolkit for spectral data analysis, primarily '
    'UVVis spectra for now.',
    long_description=open('README.rst').read(),
    install_requires=[
        "pandas >= 12.0",
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
