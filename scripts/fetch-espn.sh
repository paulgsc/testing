#!/usr/bin/env bash
# Fetches one NFL regular season's ESPN scoreboards, one file per week.
#
#   scripts/fetch-espn.sh 2026 out/espn/2026
#
# Week 18 of a season still in progress is fetched too: its games are on
# the schedule, unplayed, which is what tells the evaluator what is left.
set -euo pipefail

year="$1"
dir="$2"
mkdir -p "$dir"
for week in $(seq 1 18); do
  file="$dir/week-$(printf %02d "$week").json"
  curl --fail --silent --show-error --retry 3 --retry-delay 5 \
    "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=${year}&seasontype=2&week=${week}&limit=40" \
    -o "$file"
done
