# Run all tests.
.PHONY: test
test:
	python -m unittest discover -s test

# Runs all tests and shows code coverage information. Depends on coveragy.py
# (http://nedbatchelder.com/code/coverage/).
# Install it with
#   $ sudo easy_install coverage
# or
# 	$ sudo pip install coverage
.PHONY: test-coverage
test-coverage: clean-coverage
	coverage run --branch -m unittest discover -s test
	coverage report
	coverage html
	@echo "Open htmlcov/index.html to see detailed coverage information."

# Cleans up everything.
.PHONY: clean
clean: clean-coverage

# Cleans up test coverage data.
.PHONY: clean-coverage
clean-coverage:
	coverage erase
	rm -rf htmlcov
