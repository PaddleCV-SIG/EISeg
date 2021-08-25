rm dist/*
python setup.py sdist bdist_wheel
twine upload --repository testpypi dist/* --verbose
# twine upload --repository-url https://upload.pypi.org/legacy/  dist/* --verbose
