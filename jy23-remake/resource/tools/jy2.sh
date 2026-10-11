#!/bin/sh
# Phase 2 用。Linux/macOS: 把對應平台 ruffle 放到 resource/engine/ 後執行。
DIR="$(dirname "$0")"
exec "$DIR/../engine/ruffle" "$DIR/../assets/jy2/jy2.swf" --save-directory "$DIR/../../save"
