#!/bin/bash
python manage.py migrate
python manage.py seed_inventory --count=1000
python manage.py runserver 0.0.0.0:8000