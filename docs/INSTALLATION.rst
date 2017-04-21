Installation
============

1. Strongly suggested: install ``pip`` and setup a `Virtualenv <https://virtualenv.pypa.io/en/latest/installation.html>`_:

  .. code:: bash

    # on Debian/Ubuntu:
    sudo apt-get install python-virtualenv

    # on CentOS:
    sudo yum install epel-release
    sudo yum install python-pip python-virtualenv 

    # setup a virtualenv
    mkdir -p ~/.virtualenvs/arouteserver
    virtualenv ~/.virtualenvs/arouteserver
    source ~/.virtualenvs/arouteserver/bin/activate

  More: ``virtualenv`` `installation <https://virtualenv.pypa.io/en/latest/installation.html>`_ and `usage <https://virtualenv.pypa.io/en/latest/userguide.html>`_.

2. Install the program.
   
        - If you plan to run built-in :doc:`Live tests <LIVETESTS>` on your own or to contribute to the project, clone the GitHub repository locally and install dependencies:

        .. code:: bash

            # from within the previously created arouteserver directory
            git clone https://github.com/pierky/arouteserver.git ./
            export PYTHONPATH="`pwd`"
            pip install -r requirements.txt


        - If you plan to just use the program to build configurations or to run your own live tests scenarios, you can install it using ``pip``:

        .. code:: bash

           pip install arouteserver

3. Setup your system layout (confirmation will be asked before each action):

  .. code:: bash

    # if you installed from GitHub
    export PYTHONPATH="`pwd`"
    ./scripts/arouteserver setup

    # if you used pip
    arouteserver setup

  The program will ask you to create some directories (under ``~/arouteserver`` by default) and to copy some files there.
  These paths can be changed by editing the ``arouteserver.yml`` program configuration file or by using command line arguments. More information in the :doc:`configuration section <CONFIG>`.

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

- (optional) `rtrlib <https://github.com/rtrlib>`_ and `bird-rtrlib-cli <https://github.com/rtrlib/bird-rtrlib-cli>`_; indirectly ARouteServer needs these tools to load RPKI data into BIRD.

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
