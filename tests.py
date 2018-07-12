# An example test script.
# Run this with
#    pytest tests.py

from wsgi import hello


def test_default_route_method_says_hello():
    assert hello() == "Hello World!"

