from distutils.core import setup
setup(
  name = 'bestiapop',
  packages = ['bestiapop'],
  version = '3.0',
  license='bsd-3-clause',
  description = 'Climate Data Mining Automation Framework',
  author = 'Diego Perez & Jonathan Ojeda',
  author_email = 'darkquasar7@gmail.com',
  url = 'https://github.com/JJguri/bestiapop',
  download_url = 'https://github.com/JJguri/bestiapop/archive/v_30.tar.gz',
  keywords = ['silo', 'apsim', 'nasapower', 'dssat', 'met', 'wth', 'crop modelling', 'crops', 'agriculture', 'data science', 'climate', 'weather', 'automation'],
  install_requires=[
            'coloredlogs>=10.0',
            'h5netcdf>=0.7.4',
            'jinja2>=2.11.1',
            'numpy>=1.16.2',
            'pandas>=0.24.2',
            'requests>=2.21.0',
            's3fs>=0.4.0',
            'tabulate>=0.8.3',
            'tqdm>=4.39.0',
            'xarray>=0.14.0'
        ],
  classifiers=[
    'Development Status :: 4 - Beta',      # "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Data Scientists',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: bsd-3-clause',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
  ],
)