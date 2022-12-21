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

import os, sys, getopt
import openstack
import yaml
import importlib
fnmck = importlib.import_module("flavor-name-check")

def usage(rcode = 1):
	print("Usage: flavor-names-openstack.py [--os-cloud OS_CLOUD] [-C mand.yaml] [-v] [-q]", file=sys.stderr)
	print(" This tool retrieves the list of flavors from the OpenStack cloud OS_CLOUD", file=sys.stderr)
	print(" and checks for the presence of the mandatory SCS flavors (read from mand.yaml)", file=sys.stderr)
	print(" and reports inconsistencies, errors etc. It returns 0 on success.", file=sys.stderr)
	sys.exit(rcode)

def main(argv):
	cloud = None
	verbose = False
	quiet = False
	scsMandFile = fnmck.mandFlavorFile

	try:
		cloud = os.environ["OS_CLOUD"]
	except KeyError:
		pass
	try:
        	opts, args = getopt.gnu_getopt(argv, "c:C:vhq", \
				("os-cloud=", "mand=", "verbose", "help", "quiet"))
	except getopt.GetoptError as exc:
		print("%s" % exc, file=sys.stderr)
		usage(1)
	for opt in opts:
		if opt[0] == "-h" or opt[0] == "--help":
			uages(0)
		elif opt[0] == "-c" or opt[0] == "--os-cloud":
			cloud = opt[1]
		elif opt[0] == "-C" or opt[0] == "--mand":
			scsMandFile = opt[1]
		elif opt[0] == "-v" or opt[0] == "--verbose":
			verbose = True
		elif opt[0] == "-q" or opt[0] == "--quiet":
			quiet = True
		else:
			usage(2)
	if len(args):
		print("Extra arguments %s" % str(args), file=sys.stderr)
		usage(1)
	
	scsMandatory = fnmck.readmandflavors(scsMandFile)

	if not cloud:
        	print("You need to have OS_CLOUD set or pass --os-cloud=CLOUD.", file=sys.stderr)
	conn = openstack.connect(cloud=cloud, timeout=32)
	flavors = conn.compute.flavors()
	# Lists of flavors: mandatory, good-SCS, bad-SCS, non-SCS, with-warnings
	MSCSFlv = []
	SCSFlv = []
	wrongFlv = []
	nonSCSFlv = []
	warnFlv = []
	errors = 0
	for flv in flavors:
		# Skip non-SCS flavors
		if flv.name and flv.name[:4] != "SCS-":
			nonSCSFlv.append(flv.name)
			continue
		try:
			ret = fnmck.parsename(flv.name)
			assert(ret)
			# We have a successfully parsed SCS- name now
			# See if the OpenStack provided data fulfills what we
			# expect from the flavor based on its name
			err = 0
			warn = 0
			# Split list for readability
			cpuram = ret[0]
			disk = ret[1]
			# next qwould be hype, hwvirt, cpubrand, gpu, ib
			# see flavor-name-check.py: parsename()
			# vCPUS
			if (flv.vcpus < cpuram.cpus):
				print("ERROR: Flavor %s has only %i vCPUs, should have >= %i" % \
					(flv.name, flv.vcpus, cpuram.cpus), file=sys.stderr)
				err += 1
			elif (flv.vcpus > cpuram.cpus):
				print("WARNING: Flavor %s has %i vCPUs, only needs %i" % \
					(flv.name, flv.vcpus, cpuram.cpus), file=sys.stderr)
				warn += 1
			# RAM
			flvram = int((flv.ram+51)/102.4)/10
			# Warn for strange sizes (want integer numbers, half allowed for < 10GiB)
			if (flvram >= 10 and flvram != int(flvram) or flvram*2 != int(flvram*2)):
				print("WARNING: Flavor %s uses discouraged uneven size of memory %.1f GiB" % \
					(flv.name, flvram), file=sys.stderr)
			if (flvram < cpuram.ram):
				print("ERROR: Flavor %s has only %.1f GiB RAM, should have >= %.1f GiB" % \
					(flv.name, flvram, cpuram.ram), file=sys.stderr)
				err += 1
			elif (flvram > cpuram.ram):
				print("WARNING: Flavor %s has %.1f GiB RAM, only needs %.1f GiB" % \
					(flv.name, flvram, cpuram.ram), file=sys.stderr)
				warn += 1
			# DISK
			accdisk = (0, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000)
			# Disk could have been omitted
			if not disk.parsed:
				disk.disksize = 0
			# We have a recommendation for disk size steps
			if disk.disksize not in accdisk:
				print("WARNING: Flavor %s advertizes disk size %i, should have (5, 10, 20, 50, 100, 200, ...)" % \
					(flv.name, disk.disksize), file=sys.stderr)
				warn += 1
			if (flv.disk < disk.disksize):
				print("ERROR: Flavor %s has only %i GB root disk, should have >= %i GB" % \
					(flv.name, flv.disk, disk.disksize), file=sys.stderr)
				err += 1
			elif (flv.disk > disk.disksize):
				print("WARNING: Flavor %s has %i GB root disk, only needs %i GB" % \
					(flv.name, flv.disk, disk.disksize), file=sys.stderr)
				warn += 1
			# Ev'thing checked, react to errors by putting the bad flavors in the bad bucket
			if err:
				wrongFlv.append(flv.name)
				errors += 1
			else:
				if flv.name in scsMandatory:
					scsMandatory.remove(flv.name)
					MSCSFlv.append(flv.name)
				else:
					SCSFlv.append(flv.name)
				if warn:
					warnFlv.append(flv.name)
		# Parser error
		except NameError as e:
			errors += 1
			wrongFlv.append(flv.name)
			print("Wrong flavor \"%s\": %s" % (flv.name, e), file=sys.stderr)
	# This makes the output more readable
	MSCSFlv.sort()
	SCSFlv.sort()
	nonSCSFlv.sort()
	wrongFlv.sort()
	warnFlv.sort()
	# We have counted errors on the fly, add missing flavors to the final result
	if (scsMandatory):
		errors += len(scsMandatory)
	# Produce dict for YAML reporting
	flvRep = {"MandatoryFlavors": MSCSFlv,
			"GoodSCSFlavors": SCSFlv,
			"WrongSCSFlavors": wrongFlv,
			"nonSCSFlavors": nonSCSFlv,
			"WarnSCSFlavors": warnFlv,
			"MissingFlavors": scsMandatory}
	flvSum = {"MandatoryFlavors": len(MSCSFlv),
			"GoodSCSFlavors": len(SCSFlv),
			"WrongSCSFlavors": len(wrongFlv),
			"nonSCSFlavors": len(nonSCSFlv),
			"MissingFlavors": len(scsMandatory),
			"warnings": len(warnFlv),
			"errors": errors} 
	if verbose:
		Report = {cloud: {"FlavorReport": flvRep, "FlavorSummary": flvSum}}
	else:
		Report = {cloud: {"FlavorSummary": flvSum}}
	if not quiet:
		print("%s" % yaml.dump(Report, default_flow_style=False))
	return errors


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))

