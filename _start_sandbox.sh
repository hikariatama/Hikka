#!/bin/bash

if [ $(uname -m) = "aarch64" ]; then
  ./isolate_aarch64 python3 -m hikka --root
elif [ $(uname -m) = "x86_64" ]; then
  ./isolate_x86-64 python3 -m hikka --root
elif [ $(uname -m) = "armv7l" ]; then
  ./isolate_armv7l python3 -m hikka --root
fi
