from setuptools import setup

setup(name='legiscrape',
      version='0.0.1',
      description='Legistar Scraper',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.5',
          'Environment :: Console',
      ],
      entry_points = {
        'console_scripts': ['legiscrape-video=legiscrape.cli:main'],
      },
      url='http://github.com/notpeter/legiscrape',
      author='Peter Tripp',
      author_email='petertripp@gmail.com',
      license='MIT',
      packages=['legiscrape'],
      include_package_data=True,
      install_requires=['jsonschema'],
      zip_safe=False
)
