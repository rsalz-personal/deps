
FILES= duplicate-reports.txt \
       self-reported.txt mg/self-nodes.csv mg/self-edges.csv \
       merged-compdeps.csv mg/nodes.csv mg/edges.csv

all: $(FILES)

duplicate-reports.txt: alsof.py compdeps.csv
	./alsof.py -d || rm $@
mg/self-nodes.csv mg/self-edges.csv \
self-reported.txt: alsof.py compdeps.csv
	./alsof.py -s || rm $@
mg/nodes.csv mg/edges.csv: merged-compdeps.csv
	./alsof.py -c -f merged-compdeps.csv || rm $@
merged-compdeps.csv: alsof.py compdeps.csv
	./alsof.py -m

clean:
	rm -f $(FILES)
