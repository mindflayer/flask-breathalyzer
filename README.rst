==================
Flask-Breathalyzer
==================

.. image:: https://api.travis-ci.org/mindflayer/flask-breathalyzer.png?branch=master
    :target: http://travis-ci.org/mindflayer/flask-breathalyzer

.. image:: https://coveralls.io/repos/mindflayer/flask-breathalyzer/badge.png?branch=master
    :target: https://coveralls.io/r/mindflayer/flask-breathalyzer

A Flask module pushing exceptions to Datadog
--------------------------------------------

.. image:: https://raw.githubusercontent.com/mindflayer/flask-breathalyzer/master/Flask-Breathalyzer.png

Installation
============
Using pip::

    $ pip install flask_breathalyzer[datadog]

Issues
============
When opening an **Issue**, please add few lines of code as failing test, or -better- open its relative **Pull request** adding this test to our test suite.

Quick example
=============
Let's create a new virtualenv with all we need::

    $ virtualenv example
    $ source example/bin/activate
    $ pip install pytest datadog flask_breathalyzer[datadog]

As second step, we create a test `example.py` file as the following one:

.. code-block:: python

    from flask import Flask
    import datadog

    from flask_breathalyzer import Breathalyzer


    def test_example():

        app = Flask(__name__)

        @app.route("/")
        def boom():
            1/0

        # from http://docs.datadoghq.com/api/
        options = {
            'api_key': 'your-datadog-api-key',
            'app_key': 'your-datadog-app-key'
        }

        ba = Breathalyzer(app, **options)
        with ba.app.app_context():
            response = test_client.get('/')
            assert response.status == '500 INTERNAL SERVER ERROR'
            assert b'<title>500 Internal Server Error</title>' in response.data
            assert response.mimetype == 'text/html'
            assert isinstance(ba.last_event_id, int)  # your exception is now on Datadog with this ID


Let's fire our example test::

    $ py.test example.py
