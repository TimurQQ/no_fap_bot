#!/usr/bin/env bash

git pull origin master
kill $(ps aux | grep '[p]ython no_fap.py' | awk '{print $2}')
cp storage/all_scores_saved.json backup/all_scores_saved.json
python -B no_fap.py &
