build:
	python -m venv env

deps: build
	env/bin/pip install -r requirements/requirements.txt

migrations: deps
	env/bin/python manage.py makemigrations

migrate: migrations
	env/bin/python manage.py migrate

seed: migrate
	env/bin/python manage.py seeddb

run: migrate
	env/bin/python manage.py runserver

shell:
	env/bin/python manage.py shell

test:
	env/bin/python manage.py test
