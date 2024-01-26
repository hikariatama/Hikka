#!/bin/bash

if [ $(uname -m) = "aarch64" ]; then
  ./isolate_aarch64
elif [ $(uname -m) = "x86_64" ]; then
  ./isolate_x86-64
elif [ $(uname -m) = "armv7l" ]; then
  ./isolate_armv7l
fi
