
FILES= duplicate-reports.txt self-reported.txt

all: $(FILES)

duplicate-reports.txt: alsof.py compdeps.csv
	./alsof.py -d || rm $@
self-reported.txt: alsof.py compdeps.csv
	./alsof.py -s || rm $@

clean:
	rm -f $(FILES)
