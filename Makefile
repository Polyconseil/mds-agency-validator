.PHONY: clean
clean:
	rm -fr build/
	rm -fr dist/
	find . -name '*.pyc' -delete
	find . -name '*.pyo' -delete
	find . -name '*~' -delete

.PHONY: docs
docs:
	sphinx-build -W -n -b html docs ./build/sphinx/html

.PHONY: quality
quality:
	python setup.py check --strict --metadata --restructuredtext
	pylint --reports=no setup.py mds_agency_validator tests

.PHONY: release
release: clean
	fullrelease

.PHONY: serve
serve:
	FLASK_APP=mds_agency_validator/app.py flask run

.PHONY: serve-dev
serve-dev:
	PYTHONBREAKPOINT=ipdb.set_trace FLASK_ENV=development $(MAKE) serve

.PHONY: test
test:
	py.test tests
