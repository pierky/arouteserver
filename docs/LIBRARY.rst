Using ARouteServer as a library
===============================

External programs can take advantage of ARouteServer's features to automatically build route server configurations by using the following builder classes:

- BIRDConfigBuilder
- OpenBGPDConfigBuilder

How to use it
-------------

The ``__init__`` method takes care of initializing the builder object; this method also gathers any external information needed by the input route server configuration.

.. automethod:: pierky.arouteserver.builder.ConfigBuilder.__init__

The ``render_template`` method generates the output configuration.

.. automethod:: pierky.arouteserver.builder.ConfigBuilder.render_template

Example::

        import sys
        from pierky.arouteserver.builder import BIRDConfigBuilder
        builder = BIRDConfigBuilder(
                template_dir="~/arouteserver/templates/bird",
                template_name="main.j2",
                cfg_general="~/arouteserver/config.d/general.yml",
                cfg_clients="~/arouteserver/config.d/clients.yml",
                cfg_bogons="~/arouteserver/config.d/bogons.yml",
                cache_dir="~/arouteserver/var",
                ip_ver=4
        )
        builder.render_template(sys.stdout)

BGP daemon specific builder classes
-----------------------------------

.. autoclass:: pierky.arouteserver.builder.BIRDConfigBuilder
   :members: AVAILABLE_VERSION, DEFAULT_VERSION, LOCAL_FILES_IDS, LOCAL_FILES_BASE_DIR, HOOKS
   :undoc-members:

.. autoclass:: pierky.arouteserver.builder.OpenBGPDConfigBuilder
   :members: AVAILABLE_VERSION, DEFAULT_VERSION, LOCAL_FILES_IDS, LOCAL_FILES_BASE_DIR, HOOKS
   :undoc-members:
