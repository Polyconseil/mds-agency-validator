MDS Agency Validator
====================

This projet allows you to run a headless service that accepts incoming HTTPS 
POST request and check the payload format against MDS Agency API specifications.

Installaton
-----------

.. code-block::

    pip install -e .

Use
---


Run the following command to start the flask service

.. code-block::

    FLASK_APP=mds_agency_validator/app.py flask run

You can now post data to test your Agency API implementation.

.. code-block::

    curl -d '{"invalid": "payload"}' -H "Content-Type: application/json" -X POST  http://127.0.0.1:5000/v0.4
