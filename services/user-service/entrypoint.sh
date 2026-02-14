#!/bin/bash
python manage.py migrate
python manage.py seed_users --count=1000
python manage.py runserver 0.0.0.0:8000