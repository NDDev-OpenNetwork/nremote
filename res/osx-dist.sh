#!/usr/bin/env bash

echo $MACOS_CODESIGN_IDENTITY
cargo install flutter_rust_bridge_codegen --version 1.80.1 --features uuid --locked
cd flutter; flutter pub get; cd -
~/.cargo/bin/flutter_rust_bridge_codegen --rust-input ./src/flutter_ffi.rs --dart-output ./flutter/lib/generated_bridge.dart --c-output ./flutter/macos/Runner/bridge_generated.h
./build.py --flutter
rm nremote-$VERSION.dmg
# security find-identity -v
codesign --force --options runtime -s $MACOS_CODESIGN_IDENTITY --deep --strict ./flutter/build/macos/Build/Products/Release/NRemote.app -vvv
create-dmg --icon "NRemote.app" 200 190 --hide-extension "NRemote.app" --window-size 800 400 --app-drop-link 600 185 nremote-$VERSION.dmg ./flutter/build/macos/Build/Products/Release/NRemote.app
codesign --force --options runtime -s $MACOS_CODESIGN_IDENTITY --deep --strict nremote-$VERSION.dmg -vvv
# notarize the nremote-${{ env.VERSION }}.dmg
rcodesign notary-submit --api-key-path ~/.p12/api-key.json  --staple nremote-$VERSION.dmg
