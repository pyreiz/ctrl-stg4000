.. STG4000 documentation master file, created by
   sphinx-quickstart on Wed Dec 18 18:18:37 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Welcome to STG4000's documentation!
===================================


.. image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://en.wikipedia.org/wiki/MIT_License
   

.. image:: https://github.com/pyreiz/ctrl-stg4000/workflows/pytest/badge.svg
   :target: https://github.com/pyreiz/ctrl-stg4000/actions
 

.. image:: https://coveralls.io/repos/github/pyreiz/ctrl-stg4000/badge.svg?branch=develop
   :target: https://coveralls.io/github/pyreiz/ctrl-stg4000?branch=develop



This documentation explains the python package wrapping the `C# .dll <https://www.multichannelsystems.com/software/mcsusbnetdll>`_ offered by 
multichannelsystems to control their STG4000 range of electrical stimulators. 

Installation
------------

.. code-block:: bash

    git clone https://github.com/pyreiz/app-stg4000
    cd app-stg4000
    pip install -r requirements.txt
    pip install -e .    
    #download and install the dll from mulitchannelsystems
    python -m stg.install 

Because of this, the package only works on Windows. If the package is run on Linux, skip the installation of the requirements. On linux, the package automatically mocks the interface to the STG4000. This allows to run tests and build documentation, and can help when you write scripts for your experiments.

Testing
-------

Connect your oscilloscope and start the following example:

.. code-block:: python

   from stg.api import PulseFile, STG4000
   stg = STG4000()
   stg.download(0, *PulseFile().compile())
   stg.start_stimulation([0])

You can run full tests using pytest, mypy or everything with :code:`make test` from the root of the package. By default, downloading the dll is not tested, but can be tested selectively with :code:`pytest -m "install"`.


Documentation
-------------

.. toctree::
   :maxdepth: 2

   api
   benchmark
   example


Indices and tables
******************

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
