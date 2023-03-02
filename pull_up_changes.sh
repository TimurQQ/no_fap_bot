#!/usr/bin/env bash

git pull origin master
kill $(ps aux | grep -E '[p]ython\s+-\w+\s+no_fap.py' | awk '{print $2}')
cp storage/all_scores_saved.json backup/all_scores_saved.json
python -B no_fap.py &
