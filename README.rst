MDS Agency Validator
====================

This projet allows you to run a headless service that accepts incoming HTTPS 
POST request and check the payload format against MDS Agency API specifications.

Currently, only version 0.4.0 is supported.

Installation
------------

First of all, clone the repository :

.. code-block::

    git clone https://github.com/Polyconseil/mds-agency-validator.git

You may then install the project's dependencies.

.. code-block::

    pip install -e .

Use
---

Run the following command to start the flask service from the project repository

.. code-block::

    FLASK_APP=mds_agency_validator/app.py flask run

You can now post data to test your Agency API implementation.

.. code-block::

    curl -d '{"invalid": "payload"}' -H "Content-Type: application/json" -X POST  http://127.0.0.1:5000/v0.4
