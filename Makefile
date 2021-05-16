.PHONY: default init run clean test aliases

default: init

init: venv aliases

venv: requirements.txt
	python3 -m venv venv
	( \
		. venv/bin/activate; \
		pip install --upgrade pip; \
		pip install -r requirements.txt; \
	)

run: venv
	@( \
		. venv/bin/activate; \
		python3 tzbot.py; \
	)

clean:
	rm -rf venv
	rm -rf *.db
	find . -type f -name '*.pyc' -delete 
	find . -type d -name __pycache__ -delete
	rm -rf .pytest_cache

test: venv aliases.json
	@( \
		. venv/bin/activate; \
		pytest; \
	)

aliases aliases.json:
	( \
		. venv/bin/activate; \
		python3 build_aliases.py; \
	)
