.PHONY: dev setup

setup:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/python manage.py migrate
	@echo "Run 'make dev' to start the server."

dev:
	.venv/bin/python manage.py runserver 8123
