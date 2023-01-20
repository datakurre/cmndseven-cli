format:
	black cmndseven_cli

test:
	black --check cmndseven_cli
	mypy cmndseven_cli

build:
	poetry build

publish:
	twine publish dist/*
