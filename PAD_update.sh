#!/bin/bash
branch='herbs'
cd /home/pi/Documents
git fetch origin $branch
git reset --hard origin/$branch
git pull
