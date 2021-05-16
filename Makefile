.PHONY: default init run clean test

default: init

init: venv

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
	rm -rf *.db
	find -name "*.pyc" -delete
	find -type d -name "__pycache__" -exec rm -rf "{}" \;
	find -type d -name ".pytest_cache" -exec rm -rf "{}" \;

test: venv
	@( \
		. venv/bin/activate; \
		pytest; \
	)
