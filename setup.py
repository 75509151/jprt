# coding: utf-8                                                                                                                                                                                              
                               
import sys
from setuptools import setup, find_packages
import ast                     
import re                      
  
_version_re = re.compile(r'__version__\s+=\s+(.*)')
  
with open('prt/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))
  
with open('README.md') as f:  
    long_description = f.read()
  
with open('requirements.txt') as f:
    requires = f.read()
 
 
setup(name='jprt', version=version,
      long_description=long_description,
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      description='printer manager',
      )

