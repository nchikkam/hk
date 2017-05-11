Steps to run the server:
---------------------------------------------------------------------------------------------------------------------------------------
install pip
install virtualenv
virtualenv venv
. venv/bin/activate
pip install Django==1.11.1 --timeout 2000
cd mysite
python manage.py runserver

localhost:8000/admin
localhost:8000/polls

Packaging the app in a way to reuse it:
---------------------------------------------------------------------------------------------------------------------------------------
Packaging your app¶

Python packaging refers to preparing your app in a specific format that can be easily installed and used. Django itself is packaged very much like this. For a small app like polls, this process isn’t too difficult.

First, create a parent directory for polls, outside of your Django project. Call this directory django-polls.

Choosing a name for your app

When choosing a name for your package, check resources like PyPI to avoid naming conflicts with existing packages. It’s often useful to prepend django- to your module name when creating a package to distribute. This helps others looking for Django apps identify your app as Django specific.

Application labels (that is, the final part of the dotted path to application packages) must be unique in INSTALLED_APPS. Avoid using the same label as any of the Django contrib packages, for example auth, admin, or messages.
Move the polls directory into the django-polls directory.

Create a file django-polls/README.rst with the following contents:

django-polls/README.rst
=====
Polls
=====

Polls is a simple Django app to conduct Web-based polls. For each
question, visitors can choose between a fixed number of answers.

Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "polls" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'polls',
    ]

2. Include the polls URLconf in your project urls.py like this::

    url(r'^polls/', include('polls.urls')),

3. Run `python manage.py migrate` to create the polls models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to create a poll (you'll need the Admin app enabled).

5. Visit http://127.0.0.1:8000/polls/ to participate in the poll.
Create a django-polls/LICENSE file. Choosing a license is beyond the scope of this tutorial, but suffice it to say that code released publicly without a license is useless. Django and many Django-compatible apps are distributed under the BSD license; however, you’re free to pick your own license. Just be aware that your licensing choice will affect who is able to use your code.

Next we’ll create a setup.py file which provides details about how to build and install the app. A full explanation of this file is beyond the scope of this tutorial, but the setuptools docs have a good explanation. Create a file django-polls/setup.py with the following contents:

django-polls/setup.py
import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-polls',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    license='BSD License',  # example license
    description='A simple Django app to conduct Web-based polls.',
    long_description=README,
    url='https://www.example.com/',
    author='Your Name',
    author_email='yourname@example.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: X.Y',  # replace "X.Y" as appropriate
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
Only Python modules and packages are included in the package by default. To include additional files, we’ll need to create a MANIFEST.in file. The setuptools docs referred to in the previous step discuss this file in more details. To include the templates, the README.rst and our LICENSE file, create a file django-polls/MANIFEST.in with the following contents:

django-polls/MANIFEST.in
include LICENSE
include README.rst
recursive-include polls/static *
recursive-include polls/templates *
It’s optional, but recommended, to include detailed documentation with your app. Create an empty directory django-polls/docs for future documentation. Add an additional line to django-polls/MANIFEST.in:

recursive-include docs *
Note that the docs directory won’t be included in your package unless you add some files to it. Many Django apps also provide their documentation online through sites like readthedocs.org.

Try building your package with python setup.py sdist (run from inside django-polls). This creates a directory called dist and builds your new package, django-polls-0.1.tar.gz.

For more information on packaging, see Python’s Tutorial on Packaging and Distributing Projects.

Using your own package¶

Since we moved the polls directory out of the project, it’s no longer working. We’ll now fix this by installing our new django-polls package.

Installing as a user library

The following steps install django-polls as a user library. Per-user installs have a lot of advantages over installing the package system-wide, such as being usable on systems where you don’t have administrator access as well as preventing the package from affecting system services and other users of the machine.

Note that per-user installations can still affect the behavior of system tools that run as that user, so virtualenv is a more robust solution (see below).
To install the package, use pip (you already installed it, right?):

pip install --user django-polls/dist/django-polls-0.1.tar.gz
With luck, your Django project should now work correctly again. Run the server again to confirm this.

To uninstall the package, use pip:

pip uninstall django-polls
Publishing your app¶

Now that we’ve packaged and tested django-polls, it’s ready to share with the world! If this wasn’t just an example, you could now:

Email the package to a friend.
Upload the package on your website.
Post the package on a public repository, such as the Python Package Index (PyPI). packaging.python.org has a good tutorial for doing this.


Once the *.tar.gz is created, move it to mysite directory, install it using pip: pip install *.tar.gz, it will install the app.
run server: python manage.py runserver 
the app must run with out any errors.
