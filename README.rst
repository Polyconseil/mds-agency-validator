MDS Agency Validator
====================

This projet allows you to run a headless service that accepts incoming HTTPS 
POST request and check the payload format against MDS Agency API specifications.

Currently, only version 0.4.0 is supported.

Installation
------------

First of all, clone the repository :

.. code-block:: sh

    git clone https://github.com/Polyconseil/mds-agency-validator.git

You may then install the project's dependencies.

.. code-block:: sh

    pip install -e .

Use
---

Run the following command to start the flask service from the project repository

.. code-block:: sh

    make serve

You can now post data to test your Agency API implementation.

.. code-block:: sh

    curl -d '{"invalid": "payload"}' -H "Content-Type: application/json" -X POST  http://127.0.0.1:5000/v0.4.0

Warnings
--------

Sadly mds-agency-validator currently does not handle HTTPS request as
self-signed certificates are not accepted when posting request with curl.

It does not handle oauth2 token generation either yet (since it's not really
usefull without HTTPS).

You may generate a fake token to put in the request headers with this command :

.. code-block:: python

    import jwt
    import uuid

    jwt.encode({'provider_id': str(uuid.uuid4())}, 'secret')
