#!/bin/bash

while [ true ]; do
    "python3 main.py"
    if [$? -eq 0]; then
        break
    fi
done

