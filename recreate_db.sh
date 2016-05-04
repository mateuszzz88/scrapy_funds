#!/usr/bin/env bash

rm db.sqlite3
rm report/migrations/ -fr
./manage.py makemigrations report
./manage.py migrate
echo "enter new password for admin"
./manage.py createsuperuser --username admin --email ""