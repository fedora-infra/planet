#!/bin/sh

set -eu -o pipefail

GALAXY='./build'

build_dir="../../site"

pushd ${GALAXY}
pluto -c ../ build people.ini -o ${build_dir} -d ${build_dir} -t planet
for PLANET in design desktop edited quality security ; do # TODO: add summer-coding once it works
    mkdir -p ${build_dir}/${PLANET}
    cp -r ${build_dir}/css-v2 ${build_dir}/${PLANET}/css-v2
    cp -r ${build_dir}/images-v2 ${build_dir}/${PLANET}/images-v2
    pluto -c ../ build ${PLANET}.ini -o ${build_dir}/${PLANET} -d ${build_dir}/${PLANET} -t planet
done
popd
