Enrichers
=========

- Enrichers (``BaseConfigEnricher`` derived classes) run in the main thread; they start as many *worker threads* (``BaseConfigEnricherThread`` derived classes) as those configured.

- Each enricher has its own worker thread class (``WORKER_THREAD_CLASS`` attribute).

- The ``ConfigBuilder`` instance that has in charge the whole config building process is passed as the first parameter during the ``__init__()``, so that enrichers have full access over the builder and its internal data structure.

- The ``prepare()`` method is called to allow the setup of the enricher. This code run in the main thread.

- *Worker threads* are then setted up (and, optionally, configured via the ``_config_thread()`` method). This code run in the main thread.

- The ``add_tasks()`` method of the enricher is called; its purpose is to add *tasks* to the ``self.tasks_q`` queue. This code run in the main thread.

- Threads are then started; here, *tasks* are fetched from the tasks queue and passed to the ``do_task()`` method. This code run in the worker threads.

- When the method returns, its return value is passed to the ``save_data()`` along with the original task; ``save_data()`` is executed inside a lock.

- Exceptions raised within the worker threads are added to the worker thread's ``self.errors_q`` queue, that is finally read by the enricher; if one exception occurred in any of the worker threads a ``BuilderError()`` exception is raised.

Example
+++++++

.. code:: python

    class MyOwn_ConfigEnricher(BaseConfigEnricher):

        WORKER_THREAD_CLASS = MyOwn_ConfigEnricher_WorkerThread

        def add_tasks(self):
            task = read_from_config_builder()
            self.tasks_q.put(task)


    class MyOwn_ConfigEnricher_WorkerThread(BaseConfigEnricherThread):

        DESCR = "MyOwnEnricher"

        def do_task(self, task):
            # Perform some time-wasting job related to task, for example
            # acquire external data from slow sources...
            myown_data = do_something_with(task)

        def save_data(self, task, data):
            myown_data = data
            modify_something_on_config_builder(myown_data)
