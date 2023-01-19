#!/usr/bin/env bash

git pull origin master
kill $(ps aux | grep '[p]ython no_fap.py' | awk '{print $2}')
python no_fap.py &
