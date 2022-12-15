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
# SPDX-License-Identifier: CC-BY-SA 4.0

import os, sys
import openstack
import importlib
import yaml
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
	MSCSFlv = []
	SCSFlv = []
	wrongFlv = []
	nonSCSFlv = []
	warnFlv = []
	errors = 0
	for flv in flavors:
		if flv.name and flv.name[:4] != "SCS-":
			nonSCSFlv.append(flv.name)
			continue
		try:
			ret = fnmck.parsename(flv.name)
			assert(ret)
			if flv.name in fnmck.scsMandatory:
				fnmck.scsMandatory.remove(flv.name)
				MSCSFlv.append(flv.name)
			else:
				SCSFlv.append(flv.name)
			# TODO: Check OpenStack params vs name
		except NameError as e:
			errors += 1
			wrongFlv.append(flv.name)
			print("Wrong flavor \"%s\": %s" % (flv.name, e), file=sys.stderr)
	MSCSFlv.sort()
	SCSFlv.sort()
	nonSCSFlv.sort()
	wrongFlv.sort()
	warnFlv.sort()
	if (fnmck.scsMandatory):
		ln = len(fnmck.scsMandatory)
		errors += ln
	flvRep = {"MandatoryFlavors": MSCSFlv,
			"GoodSCSFlavors": SCSFlv,
			"WrongSCSFlavors": wrongFlv,
			"nonSCSFlavors": nonSCSFlv,
			"WarnSCSFlavors": warnFlv,
			"MissingFlavors": fnmck.scsMandatory}
	flvSum = {"MandatoryFlavors": len(MSCSFlv),
			"GoodSCSFlavors": len(SCSFlv),
			"WrongSCSFlavors": len(wrongFlv),
			"nonSCSFlavors": len(nonSCSFlv),
			"MissingFlavors": len(fnmck.scsMandatory),
			"warnings": len(warnFlv),
			"errors": errors} 
	Report = {cloud: {"FlavorReport": flvRep, "FlavorSummary": flvSum}}
	print("%s" % yaml.dump(Report, default_flow_style=False))
	return errors


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))

