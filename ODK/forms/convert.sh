#!/bin/bash

for i in *.xlsx; do
    name="`echo $i | sed -e 's:.xlsx::'`"
    echo -n "Converting $i: "
    pyxform.sh $i ${name}.xml
done

