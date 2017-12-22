#! /bin/bash

set -e
set -x

rgbds/rgbasm -o main.o main.asm
rgbds/rgblink -m main.map -o beach.gbc main.o
rgbds/rgbfix -v -p 0 beach.gbc
