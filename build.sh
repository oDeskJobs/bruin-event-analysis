currentdir=`pwd`
rm BruinEventAnalysis-0.1-debug.apk
pushd ~/libraries/python-for-android/dist/default/
rm -rf ./bin/*
./build.py --package org.test.bruinevents --name "Bruin Event Analysis" --version 0.1 --dir "$currentdir" debug
popd
cp ~/libraries/python-for-android/dist/default/bin/BruinEventAnalysis-0.1-debug.apk ./
