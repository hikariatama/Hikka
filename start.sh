#!/bin/bash

cd private
while true; do
  python3 listener.py
  if [ $? -ne 1 ]; then
    break
  fi
done
