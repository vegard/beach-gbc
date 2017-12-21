#! /bin/bash

set -e
set -x

rgbds/rgbasm -o main.o main.asm
rgbds/rgblink -m main.map -o main.gb main.o
rgbds/rgbfix -v -p 0 main.gb
