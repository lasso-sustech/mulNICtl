#!/usr/bin/bash

cargo build --target aarch64-linux-android --release
mkdir -p ../app/src/main/jniLibs/arm64-v8a
cp -f target/aarch64-linux-android/release/libmulnictl.so ../app/src/main/jniLibs/arm64-v8a/libmulnictl.so
