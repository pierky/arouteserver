Logging
=======

ARouteServer's logging is based on the Python logging facility and can be configured using the `fileConfig() format <https://docs.python.org/2/library/logging.config.html#configuration-file-format>`__.

The ``logging_config_file`` parameter which can be found in the main program configuration file (``arouteserver.yml``) must be set with the path of the INI file that contains the logging configuration statements. By default, it is set to point to the ``log.ini`` file that ships with the program and that contains a basic configuration which simply prints log messages to stderr.

The ``log.ini`` shipped with the program contains some commented sections that can be used as guidance for setting up other logging methods: files, syslog (both local and remote via UDP), email, Slack.

Logging levels
--------------

- ``INFO``: quite verbose, informational messages are logged using this level to inform the user about the progress of the building process.

- ``WARN``: minor issues which do not prevent the configuration file from being built but that should be analyzed by a route server operator are logged using this level. This includes, for example, peers with missing AS-SETs when IRR-based filters are enabled, or empty AS-SETs, or new release notices.

- ``ERROR``: this level is used to log messages related to issues that prevent the configuration file from being built.

For example, >=INFO messages could be logged to stderr, >=WARN messages via a `buffered email <https://github.com/pierky/bufferedsmtphandler>`_ and >=ERROR via email and Slack (using a third-party component like `slacker-log-handler <https://pypi.python.org/pypi/slacker-log-handler>`_).

Output of an example execution is reported below:

.. code::

   WARNING The 'filtering.global_black_list_pref' option is missing or empty. It is strongly suggested to provide at least the list of local IPv4/IPv6 networks here.
   WARNING The 'filtering.irrdb.tag_as_set' option is set but no BGP communities are provided to tag prefixes.
   INFO Started processing configuration for /home/pierky/arouteserver/templates/bird/main.j2
   INFO Enricher 'IRRdb origin ASNs' started
   WARNING No AS-SETs provided for the 'AS3333_1' client. Only AS3333 will be expanded.
   WARNING No AS-SETs provided for the 'AS10745_1' client. Only AS10745 will be expanded.
   INFO Enricher 'IRRdb origin ASNs' completed successfully after 0 seconds
   INFO Enricher 'IRRdb prefixes' started
   INFO Enricher 'IRRdb prefixes' completed successfully after 0 seconds
   INFO Enricher 'PeeringDB max-prefix' started
   INFO Enricher 'PeeringDB max-prefix' completed successfully after 0 seconds
   INFO Configuration processing completed after 0 seconds.
   INFO Started template rendering for /home/pierky/arouteserver/templates/bird/main.j2
   INFO Template rendering completed after 1 seconds.
