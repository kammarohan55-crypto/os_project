#!/usr/bin/env python3
import json

f = 'logs/run_669_1768915610.json'
print(f'Checking: {f}')

with open(f) as fh:
    data = json.load(fh)

print(f'Program: {data.get("program")}')
print(f'Profile: {data.get("profile")}')
print(f'Summary: {data.get("summary")}')
