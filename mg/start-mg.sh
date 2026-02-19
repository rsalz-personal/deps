#! /bin/bash
x=$(/bin/pwd)
docker run -p 7687:7687 -p 7444:7444 --name memgraph \
    -v $x/mg/data:/var/lib/memgraph \
    -v $x/mg:/import \
    -v $x/mg:/home/memgraph \
    memgraph/memgraph-mage 
