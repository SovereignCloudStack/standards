#!/usr/bin/env python3
#
# Flavor naming checker
# https://github.com/SovereignCloudStack/Docs/Design-Docs/tools
# 
# Uses the flavor-name-check.py tool
# Assumes a connection to an OpenStack tenant,
# retrieves the list of flavors from there and validates them.
# Something similar could be achieved by:
# flavor-name-check.py -c $(openstack flavor list -f value -c Name)
# In addition we check consistency by looking at the information
# provided by openstack, such as the number of vCPUs and memory.
# 
# (c) Kurt Garloff <garloff@osb-alliance.com>, 12/2022
# License: CC-BY-SA 4.0

import os, sys
import openstack
import importlib
fnmck = importlib.import_module("flavor-name-check")

def usage():
	print("Usage: flavor-names-openstack.py [--os-cloud OS_CLOUD]", file=sys.stderr)
	sys.exit(1)

def main(argv):
	cloud = None
	try:
		cloud = os.environ["OS_CLOUD"]
	except KeyError:
		pass
	if len(argv):
		if argv[0][:10] == "--os-cloud":
			if len(argv[0]) > 10 and argv[0][10] == "=":
				cloud = argv[0][11:]
			elif argv[0] == "--os-cloud" and len(argv) == 2:
				cloud = argv[1]
			else:
				usage()
		else:
			usage()
	if not cloud:
        	print("You need to have OS_CLOUD set or pass --os-cloud=CLOUD.", file=sys.stderr)
	conn = openstack.connect(cloud=cloud, timeout=32)
	flavors = conn.compute.flavors()
	nonSCSFlv = []
	SCSFlv = []
	wrongFlv = []
	warnFlv = []
	errors = 0
	for flv in flavors:
		if flv.name and flv.name[:4] != "SCS-":
			nonSCSFlv.append(flv.name)
			continue
		try:
			ret = fnmck.parsename(flv.name)
			assert(ret)
			SCSFlv.append(flv.name)
			if flv.name in fnmck.scsMandatory:
				fnmck.scsMandatory.remove(flv.name)
			# TODO: Check OpenStack params vs name
		except NameError as e:
			errors += 1
			wrongFlv.append(flv.name)
			print("Wrong flavor \"%s\": %s" % (flv.name, e), file=sys.stderr)
	SCSFlv.sort()
	wrongFlv.sort()
	warnFlv.sort()
	print("Flavor analysis report on %s" % cloud)
	print("Good flavors (%i): %s" % (len(SCSFlv), SCSFlv))
	print("WRONG flavors (%i): %s" % (len(wrongFlv), wrongFlv))
	print("Warnings (%i): %s" % (len(warnFlv), warnFlv))
	if (fnmck.scsMandatory):
		ln = len(fnmck.scsMandatory)
		errors += ln
		print("Missing mandatory SCS flavors (%i): %s" % (ln, fnmck.scsMandatory))
	return errors


if __name__ == "__main__":
	main(sys.argv[1:])

