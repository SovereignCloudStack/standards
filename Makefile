TARGETS=GettingStarted.html

default: $(TARGETS)

%.html: %.MD
	multimarkdown $< > $@


clean:
	rm -f $(TARGETS)
