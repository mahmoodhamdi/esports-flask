#!/bin/bash

# تثبيت المتطلبات
pip install -r requirements.txt

# تشغيل Gunicorn مباشرة
gunicorn --bind 0.0.0.0:5000 app:app
