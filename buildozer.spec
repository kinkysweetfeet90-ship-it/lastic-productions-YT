[app]
title = Lastic Productions Mobile
package.name = lasticproductions
package.domain = com.lasticproductions
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0
requirements = python3,kivy==2.2.1,yt-dlp,ffmpeg-python
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

[app:android]
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25c
android.gradle_dependencies = androidx.core:core:1.9.0
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True
android.wakelock = True
android.window_soft_input_mode = adjustResize
