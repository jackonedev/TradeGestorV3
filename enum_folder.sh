#!/bin/bash

TARGET_DIR=$1
COPY_DIR=$2
i=1

while [ -d "$TARGET_DIR/${COPY_DIR}${i}" ]; do
    i=$((i + 1))
done

echo $i