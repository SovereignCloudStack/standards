#!/bin/bash

unset OS_SYSTEM_SCOPE
CLOUD_NAME="scs-test"
HYPERVISOR="qemu"
INSTALL_RECOMMENDED=true
INSTALL_FROM_LOCAL=true

echo ""
echo "Checking requirements..."

if ! [[ "$(python3 -V)" =~ "Python 3" ]]; then
    echo "\033[0;31m'python' needs to be available on the install node!\033[0m"
    exit 1
fi
if ! [ -x "$(command -v python3 -m venv .test)" ]; then
    echo "\033[0;31m'python-venv' needs to be available on the install node!\033[0m" >&2
    exit 1
fi
if ! [ -x "$(command -v wget)" ]; then
    echo "\033[0;31m'wget' needs to be available on the install node!\033[0m" >&2
    exit 1
fi
if ! [ -x "$(command -v git)" ]; then
    echo "\033[0;31m'git' needs to be available on the install node!\033[0m" >&2
    exit 1
fi


if [ ! -f "clouds.yaml" ]; then
    echo "Please provide a clouds.yaml in the working directory!"
    exit 1
fi

if [ ! -f "images.yaml" ]; then
    echo "Please provide a images.yaml in the base directory!"
    exit 1
fi

if [ "$INSTALL_FROM_LOCAL" = true ]; then
    image_sources=("https://cloud-images.ubuntu.com/releases/focal/release/ubuntu-20.04-server-cloudimg-amd64.img" "https://cloud-images.ubuntu.com/releases/jammy/release/ubuntu-22.04-server-cloudimg-amd64.img" "https://swift.services.a.regiocloud.tech/swift/v1/AUTH_b182637428444b9aa302bb8d5a5a418c/openstack-k8s-capi-images/ubuntu-2204-kube-v1.29/ubuntu-2204-kube-v1.29.3.qcow2" "https://cloud.debian.org/images/cloud/buster/latest/debian-10-generic-amd64.raw" "https://cloud.debian.org/images/cloud/bullseye/latest/debian-11-generic-amd64.raw" "https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-amd64.raw")

    cp images.yaml images-local.yaml
    for i in "${!image_sources[@]}"; do
        image=${image_sources[i]}
        name=${image##*/}
        file="file://$PWD$name"
        sed -i 's#'"$image"'#'"$file"'#g' images-local.yaml
        if [ -f "$name" ]; then
            echo "File $name already exists..."
        else
            wget -O $name $image
        fi
    done
fi

echo "Creating OIM virtual environment..."
python3 -m venv .scs-venv-oim
source .scs-venv-oim/bin/activate
echo "Installing required pip packages..."
python3 -m pip install openstack-image-manager

echo "Fixing openstack-image-manager..."
sed -i 's/import\sDict/import Union, Dict/g' .scs-venv-oim/lib/python3.9/site-packages/openstack_image_manager/manage.py
sed -i 's/Image\s|\sNone/ Union\[Image, None\]/g' .scs-venv-oim/lib/python3.9/site-packages/openstack_image_manager/manage.py

if [ "$INSTALL_FROM_LOCAL" = true ]; then
    openstack-image-manager --cloud $CLOUD_NAME --images images-local.yaml --hypervisor $HYPERVISOR

    image_names=("Ubuntu 20.04" "Ubuntu 22.04" "ubuntu-capi-image v1.29.3" "Debian 10" "Debian 11" "Debian 12")
    for i in "${!image_names[@]}"; do
        openstack image set --property image_source="${image_sources[i]}" "${image_names[i]}"
    done

else
    openstack-image-manager --cloud $CLOUD_NAME --images images.yaml --hypervisor $HYPERVISOR
fi

echo "Removing OIM virtual environment..."
deactivate
rm -rf .scs-venv-oim

echo "Creating OFM virtual environment..."
python3 -m venv .scs-venv-ofm
source .scs-venv-ofm/bin/activate
echo "Installing required pip packages..."
python3 -m pip install openstack-flavor-manager

echo "Fixing openstack-flavor-manager..."
sed -i '10s/^/from typing import Union\\n/' .scs-venv-ofm/lib/python3.9/site-packages/openstack_flavor_manager/main.py
sed -i 's/Flavor\s|\sNone/ Union\[Flavor, None\]/g' .scs-venv-ofm/lib/python3.9/site-packages/openstack_flavor_manager/main.py

openstack-flavor-manager --cloud $CLOUD_NAME
if [ "$INSTALL_RECOMMENDED" = true ]; then
    openstack-flavor-manager --cloud $CLOUD_NAME --recommended
fi

echo "Removing OFM virtual environment..."
deactivate
rm -rf .scs-venv-ofm

echo "Cloning SCS standards repository..."
git clone https://github.com/SovereignCloudStack/standards


echo "Creating testing virtual environment..."
python3 -m venv .scs-venv-test
source .scs-venv-test/bin/activate
pip install fabric openstacksdk PyYAML
export OS_CLOUD="scs-test"

echo "Executing SCS tests..."
cp clouds.yaml ./standards/Tests/
python3 ./standards/Tests/scs-compliance-check.py ./standards/Tests/scs-compatible-iaas.yaml -s $CLOUD_NAME -a os_cloud=$CLOUD_NAME -o $CLOUD_NAME-iaas.yaml -C

cat $CLOUD_NAME-iaas.yaml

echo "Removing testing virtual environment..."
deactivate
rm -rf .scs-venv-test

rm -rf standards
