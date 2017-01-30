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
    mkdir arouteserver
    cd arouteserver
    virtualenv venv
    source venv/bin/activate

  More: ``virtualenv`` `installation <https://virtualenv.pypa.io/en/latest/installation.html>`_ and `usage <https://virtualenv.pypa.io/en/latest/userguide.html>`_.

2. Clone the GitHub repository locally:

  .. code:: bash

    # from within the previously created arouteserver directory
    git clone https://github.com/pierky/arouteserver.git ./
    export PYTHONPATH="`pwd`"

3. Install dependencies:

  .. code:: bash

    pip install -r requirements.txt

4. Setup the default directory layout:

  .. code:: bash

    mkdir /etc/arouteserver
    cp config.d/* /etc/arouteserver
    mkdir /etc/arouteserver/templates
    cp templates/bird/* /etc/arouteserver/templates

    # this is the cache directory
    mkdir /var/lib/arouteserver

  These paths can be changed by editing the ``arouteserver.yml`` program configuration file or by using command line arguments. More information in the :doc:`configuration section <CONFIG>`.

External programs
-----------------

ARouteServer uses the following external programs:

- `bgpq3 <https://github.com/snar/bgpq3>`_ is used to gather information about routing policies.
  
  To install it:

  .. code:: bash

    mkdir /path/to/bgpq3/directory
    cd /path/to/bgpq3/directory
    git clone https://github.com/snar/bgpq3.git ./
    # make and gcc packages required
    ./configure
    make
    make install

- `Docker <https://www.docker.com/>`_ is used to perform :doc:`live validation <LIVETESTS>` of configurations.

  To install it, please refer to its `official guide <https://www.docker.com/products/overview>`_.
