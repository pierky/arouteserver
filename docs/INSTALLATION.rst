Installation
============

Dependencies
------------

Some components used by ARouteServer need Python dev header files and static libraries: some distributions have them already included, others may need to manually install them:

.. code:: bash

   # Debian Jessie, Ubuntu Trusty
   apt-get install python-dev  # for Python 2
   apt-get install python3-dev # for Python 3

   # CentOS
   yum -y install gcc python-devel

Please note that ARouteServer also needs `bgpq3 <https://github.com/snar/bgpq3>`_ to build IRR-based filters: details on its installation can be found within the :ref:`External programs` section.

Install using ``pip`` (suggested)
---------------------------------

If you plan to just use the program to build configurations or to run your own live tests scenarios, you can install it using ``pip``.

Strongly suggested: setup a `Virtualenv <https://virtualenv.pypa.io/>`_.

.. code:: bash

   # on Debian/Ubuntu:
   sudo apt-get install python-pip python-virtualenv

   # on CentOS:
   sudo yum install epel-release
   sudo yum install python-pip python-virtualenv

   # setup a virtualenv
   mkdir -p ~/.virtualenvs/arouteserver
   virtualenv ~/.virtualenvs/arouteserver
   source ~/.virtualenvs/arouteserver/bin/activate

   # install the program
   pip install arouteserver

More: ``virtualenv`` `installation <https://virtualenv.pypa.io/en/latest/installation.html>`_ and `usage <https://virtualenv.pypa.io/en/latest/userguide.html>`_.

.. note:: If you receive the following error while installing the program (or its requirements): **error in setup command: 'install_requires' must be a string or list of strings containing valid project/version requirement specifiers** then please upgrade the *setuptools* package that is used in your virtualenv: ``pip install --upgrade setuptools``.

.. note:: In the case the pip installation process breaks with the **Failed building wheel for py-radix / fatal error: Python.h: No such file or directory** error, please verify that the dependencies are satisfied.

Install from GitHub
-------------------

If you plan to run built-in :doc:`Live tests <LIVETESTS>` on your own or to contribute to the project, clone the GitHub repository locally and install dependencies:

.. code:: bash

   mkdir -p ~/src/arouteserver
   cd ~/src/arouteserver

   # use the URL of your fork here:
   git clone https://github.com/USERNAME/arouteserver.git ./

   export PYTHONPATH="`pwd`"
   pip install -r requirements.txt

Setup and initialization
------------------------

- Setup your system layout (confirmation will be asked before each action):

  .. code:: bash

    # if you used pip
    arouteserver setup

    # if you installed from GitHub
    export PYTHONPATH="`pwd`"
    ./scripts/arouteserver setup

  The program will ask you to create some directories (under ``~/arouteserver`` by default) and to copy some files there.
  These paths can be changed by editing the ``arouteserver.yml`` program configuration file or by using command line arguments. More information in the :doc:`configuration section <CONFIG>`.

- Define the route server configuration policies, using the ``configure`` command or manually by editing the ``general.yml`` file:

  .. code:: bash

    # if you used pip
    arouteserver configure

    # if you installed from GitHub
    ./scripts/arouteserver configure

  The ``configure`` command asks some questions about the route server environment (ASN, router ID, local subnets) and then it builds a policy definition file based on best practices and suggestions which also includes a rich BGP communities list.

External programs
-----------------

ARouteServer uses the following external programs:

- (mandatory) `bgpq3 <https://github.com/snar/bgpq3>`_ is used to gather information from IRRDBs.
  
  To install it:

  .. code:: bash

    mkdir /path/to/bgpq3/directory
    cd /path/to/bgpq3/directory
    git clone https://github.com/snar/bgpq3.git ./
    # make and gcc packages required
    ./configure
    make
    make install

- (optional) `Docker <https://www.docker.com/>`_ is used to perform :doc:`live validation <LIVETESTS>` of configurations.

  To install it, please refer to its `official guide <https://www.docker.com/products/overview>`_.

- (optional) `KVM <https://www.linux-kvm.org/page/Main_Page>`_ is also used to perform :doc:`live tests <LIVETESTS>` of OpenBGPD configurations on an OpenBSD virtual machine.

  To install it:

  .. code:: bash

    apt-get install qemu-kvm virtinst

  More details: https://wiki.debian.org/KVM

- (optional) `rtrlib <https://github.com/rtrlib>`_ and `bird-rtrlib-cli <https://github.com/rtrlib/bird-rtrlib-cli>`_; ARouteServer can use these tools to load RPKI data into BIRD. More details in :ref:`ROAs sources`.

  To install them:

  .. code:: bash

    curl -o rtrlib.zip -L https://github.com/rtrlib/rtrlib/archive/v0.3.6.zip
    unzip rtrlib.zip
    
    cd rtrlib-0.3.6 && \
        cmake -D CMAKE_BUILD_TYPE=Release . && \
        make && \
        make install
    
    curl -o bird-rtrlib-cli.zip -L https://github.com/rtrlib/bird-rtrlib-cli/archive/v0.1.1.zip
    unzip bird-rtrlib-cli.zip
    
    cd bird-rtrlib-cli-0.1.1 && \
        cmake . && \
        make


  More details: https://github.com/rtrlib/rtrlib/wiki/Installation

  To configure bird-rtrlib-cli please refer to the `README <https://github.com/rtrlib/bird-rtrlib-cli>`_.

Upgrading
---------

Often upgrades bring new features and new options, sometimes they also introduce changes that might break backward compatibility with previous versions.
It is advisable to always check the :doc:`CHANGELOG <CHANGELOG>` to verify what's new: the ``arouteserver show_config`` command can also be used to verify if new configuration options are available and how they are set by default.

To upgrade the program, download the new version...

.. code:: bash

    # if you cloned the repository from GitHub,
    # from within the local repository's directory:
    git pull origin master

    # if you installed it with pip:
    pip install --upgrade arouteserver

... then sync the local templates with those distributed in the new version:

.. code:: bash

    arouteserver setup-templates

If local templates have been edited, make a backup of your files in order to merge your changes in the new ones later.
To customize the configuration of the route server with your own options, please consider using :ref:`site-specific-custom-config` instead of editing the template files.

Development and pre-release versions
------------------------------------

.. note:: Consider your needs carefully before using a version other than the current production versions. These are preview releases, and their use is not recommended in production settings.

The **dev** `branch <https://github.com/pierky/arouteserver/tree/dev>`__ is used for the development of the project, while the **master** branch always contains the latest, (hopefully) stable production-ready code.

To install or to upgrade to `the latest pre-release version <https://test.pypi.org/project/arouteserver/>`__ use the `TestPyPI <https://packaging.python.org/guides/using-testpypi/>`__ instance of the Python Package Index (PyPI):

.. code:: bash

    pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple --pre arouteserver

Ansible role
------------

An Ansible role to install and configure ARouteServer can be found on `Galaxy <https://galaxy.ansible.com/pierky/arouteserver/>`__ or on `GitHub <https://github.com/pierky/ansible-role-arouteserver>`__.

It is tested on Debian (Jessie, Stretch), Ubuntu (Trusty, Xenial) and CentOS 7.
