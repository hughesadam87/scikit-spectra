from distutils.core import setup

### For now, most of these are in here for testing.  Dependency version requirements can probably be relaxed, especially chaco.
setup(
    name='PyUvVis',
    version='0.1.0',
    author='Adam Hughes, Zhaowen Liu and GWU Physics Reeves Lab students',
    maintainer='Adam Hughes',
    maintainer_email='hughesadam87@gmail.com',
      packages=['pyuvvis',
                'pyuvvis.scripts',
                'pyuvvis.chaco_interface',
                'pyuvvis.core',
                'pyuvvis.deprecates_oldprograms',
                'pyuvvis.IO',
                'pyuvvis.pandas_utils',
                'pyuvvis.pyplots',
                'pyuvvis.tests',
                ],
      package_data={'pyuvvis.data' : ['example_data/*.pickle', 
					### Do I want to include this?
				      'gwuspecdata/*.txt',   
                                       'gwuspecdata.fiber1/*.txt',
                                        'gwuspecdata.NPConcentration/*.txt']
                   },
    url='http://pypi.python.org/pypi/PyUvVis/',
    download_url='https://github.com/hugadams/pyuvvis',
    license='LICENSE.txt',
    description='Pandas-based toolkit for spectral data analysis, primarily UVVis spectra for now.',
    long_description=open('README.rst').read(),
    install_requires=[
        "pandas >= 0.8.0",
        "chaco >= 4.2.0",
    ],
      classifiers=[
          'Development Status :: 2 - Pre-alpha',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Developers',
	  'Natural Language :: English',
          'Operating System :: MacOS :: MacOS X',  #This is limited only by chaco.  Pandas claims to be OS independent.  
          'Operating System :: Microsoft :: Windows',
          'Operating System :: Linux :: Ubuntu',
          'Programming Language :: Python :: 2',
          'Topic :: Scientific/Engineering :: Visualization',
          'Topic :: Scientific/Engineering :: Chemistry',
          'Topic :: Scientific/Engineering :: Physics',
          'Topic :: Scientific/Engineering :: Medical Science Apps.',
          ],
)
