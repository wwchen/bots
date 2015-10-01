#!/bin/bash

# problemm: I'm seeing the websocket expires or something, but doesn't error out
# quick hack: bash script to kill the python every so often

LOCKFILE=/tmp/jirabot.lock

if [[ -f $LOCKFILE ]]; then
  kill $(cat $LOCKFILE)
fi

python jirabot.py &
echo $! > $LOCKFILE
