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
			err = 0
			warn = 0
			# vCPUS
			if (flv.vcpus < ret[0].cpus):
				print("ERROR: Flavor %s has only %i vCPUs, should have >= %i" % \
					(flv.name, flv.vcpus, ret[0].cpus), file=sys.stderr)
				err += 1
			elif (flv.vcpus > ret[0].cpus):
				print("WARNING: Flavor %s has %i vCPUs, only needs %i" % \
					(flv.name, flv.vcpus, ret[0].cpus), file=sys.stderr)
				warn += 1
			# RAM
			flvram = int((flv.ram+51)/102.4)/10
			if (flvram < ret[0].ram):
				print("ERROR: Flavor %s has only %.1f GiB RAM, should have >= %.1f GiB" % \
					(flv.name, flvram, ret[0].ram), file=sys.stderr)
				err += 1
			elif (flvram > ret[0].ram):
				print("WARNING: Flavor %s has %.1f GiB RAM, only needs %.1f GiB" % \
					(flv.name, flvram, ret[0].ram), file=sys.stderr)
				warn += 1
			# DISK
			accdisk = (0, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000)
			if not ret[1].parsed:
				ret[1].disksize = 0
			if ret[1].disksize not in accdisk:
				print("WARNING: Flavor %s advertizes disk size %i, should have (5, 10, 20, 50, 100, 200, ...)" % \
					(flv.name, ret[1].disksize), file=sys.stderr)
				warn += 1
			if (flv.disk < ret[1].disksize):
				print("ERROR: Flavor %s has only %i GB root disk, should have >= %i GB" % \
					(flv.name, flv.disk, ret[1].disksize), file=sys.stderr)
				err += 1
			elif (flv.disk > ret[1].disksize):
				print("WARNING: Flavor %s has %i GB root disk, only needs %i GB" % \
					(flv.name, flv.disk, ret[1].disksize), file=sys.stderr)
				warn += 1
			if err:
				wrongFlv.append(flv.name)
			else:
				if flv.name in fnmck.scsMandatory:
					fnmck.scsMandatory.remove(flv.name)
					MSCSFlv.append(flv.name)
				else:
					SCSFlv.append(flv.name)
				if warn:
					warnFlv.append(flv.name)
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

