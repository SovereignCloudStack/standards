#!/usr/bin/env python3
import os
import sys
import traceback
import cgi

def main(argv):
    "Entry point for for cgi"
    import importlib
    fnmd = importlib.import_module("flavor-name-describe")
    print("Content-Type: text/html\n")
    form = cgi.FieldStorage()
    try:
        fnm = form["flavor"].value
        print(f"<h1>SCS flavor name {fnm}</h1>")
        pnm = fnmd.main((fnm,))
    except (TypeError,NameError,KeyError) as exc:
        print(exc)
    print("\n<br/><br/><a href=\"/\">Back to main page</a>")

if __name__ == "__main__":
    main(sys.argv[1:])
