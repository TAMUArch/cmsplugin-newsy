Introduction
------------

This is a `Django CMS` plugin for news. To see an example, check out the Texas
A&M University, `College of Architecture's Newsletter`.

Installation
------------

First, you must install `Django CMS` and `photologue` which require `Django` 
and a few other libraries such as `PIL`. For full details, see the installation 
instructions for those packages.

Install ``cmsplugin-newsy`` to your environment with a tool such as `PIP`, 
`setuptools`, or `buildout`.

Add ``newsy`` to the ``INSTALLED_APPS`` list in your project's 
``settings.py`` and run the ``syncdb`` command on your ``manage.py``.

.. _Django: http://www.djangoproject.com/
.. _Django CMS: https://www.django-cms.org/
.. _photologue: http://code.google.com/p/django-photologue/
.. _PIL: http://www.pythonware.com/products/pil/
.. _PIP: http://www.pip-installer.org/
.. _setuptools: http://pypi.python.org/pypi/setuptools/
.. _buildout: http://pypi.python.org/pypi/zc.buildout/
.. _College of Architecture's Newsletter: http://one.arch.tamu.edu/

What's Inside
-------------

A news item model that behaves similary to the Django CMS Page model. Content
placeholders are read from the template selected for the news item and editors
can then add plugins into the placeholders.

