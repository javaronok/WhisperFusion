# Fix SIGSERV - https://github.com/KoljaB/RealtimeSTT/issues/33

# Remove
rm .venv/lib/python3.11/site-packages/functorch/.dylibs/libiomp5.dylib
rm .venv/lib/python3.11/site-packages/torch/lib/libiomp5.dylib

# Replace with symlinks
ln .venv/lib/python3.11/site-packages/ctranslate2/.dylibs/libiomp5.dylib .venv/lib/python3.11/site-packages/functorch/.dylibs/libiomp5.dylib
ln .venv/lib/python3.11/site-packages/ctranslate2/.dylibs/libiomp5.dylib .venv/lib/python3.11/site-packages/torch/lib/libiomp5.dylib
