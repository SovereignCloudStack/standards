#!/bin/sh

###############################################################################
##### HELPERS                                                             #####
###############################################################################

set -x

# This is the entrypoint for the image and meant to wrap the
# logic of gathering/reporting results to the Sonobuoy worker.

results_dir="${RESULTS_DIR:-/tmp/results}"
mkdir -p ${results_dir}

# saveResults prepares the results for handoff to the Sonobuoy worker.
# See: https://github.com/vmware-tanzu/sonobuoy/blob/main/site/content/docs/main/plugins.md
saveResults() {
	cd ${results_dir}
	echo ${results_dir}

	# Sonobuoy worker expects a tar file.
	tar czf results.tar.gz *

	# Signal to the worker that we are done and where to find the results.
	printf ${results_dir}/results.tar.gz > ${results_dir}/done
}

# Ensure that we tell the Sonobuoy worker we are done regardless of results.
trap saveResults EXIT


###############################################################################
##### RUN TEST SCRIPTS                                                    #####
###############################################################################

# Each script name is expected to be given as an arg. If no args, error out
# but print one result file for clarity in the results.
if [ "$#" -eq "0" ]; then
	echo "No arguments; expects each argument to be script name" > ${results_dir}/out
	exit 1
fi

# Iterate through the python tests passed as arguments
i=0
while [ "$1" != "" ]; do
	# Run each arg as a command and save the output in the results directory.
	echo "run testscript: [$1.py]"

	python $1.py > ${results_dir}/out_$1
	cp $1.result.yaml ${results_dir}
	i=$((i + 1))

	# Shift all the parameters down by one
	shift
done
