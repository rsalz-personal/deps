
FILES= duplicate-reports.txt self-reported.txt

all: $(FILES)

$(FILES): alsof.py compdeps.csv
	./alsof.py || rm $(FILES)

clean:
	rm -f $(FILES)
