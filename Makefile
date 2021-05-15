.PHONY: default run clean

default: venv

venv: requirements.txt
	python3 -m venv venv
	( \
		. venv/bin/activate; \
		pip install --upgrade pip; \
		pip install -r requirements.txt; \
	)

run: venv tzbot.py
	@( \
		. venv/bin/activate; \
		python3 tzbot.py; \
	)

clean:
	rm -rf venv
	find -iname "*.pyc" -delete
