
from distutils.core import setup

setup(
    name='MultiMap',
    version='1.0.3',
    description='Mapping class which allows multiple values per key and preserves order by value; values with the same key are not grouped together.',
    url='http://github.com/mikeboers/multimap',
    py_modules=['multimap'],
    
    author='Mike Boers',
    author_email='multimap@mikeboers.com',
    license='BSD-3',
    
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
