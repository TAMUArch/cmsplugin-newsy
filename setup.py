from os.path import dirname, join

from setuptools import setup, find_packages



version = '0.7a2'

setup(
    name = 'cmsplugin-newsy',
    version = version,
    description = "Django CMS Plugin for News",
    long_description = open(join(dirname(__file__), 'README.rst')).read() + "\n" + 
                       open(join(dirname(__file__), 'HISTORY.rst')).read(),
    classifiers = [
        "Framework :: Django",
        "Development Status :: 4 - Beta",
        #"Development Status :: 5 - Production/Stable",
        "Programming Language :: Python",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Apache Software License"],
    keywords = 'django cms plugin photologue',
    author = 'Texas A&M University, College of Architecture',
    author_email = 'webadmin@arch.tamu.edu',
    url = 'https://github.com/TAMUArch/cmsplugin-newsy',
    packages = find_packages(),
    include_package_data = True,
    zip_safe = False,
    install_requires = [
        'setuptools',
        'django-photologue>=2.5',
        'django-cms',
        'django-tagging>=0.3.1']
)
