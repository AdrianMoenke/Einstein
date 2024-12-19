# Einstein
An AI Assistant for your home

Testing the capabilities of open source tools

# Current Version
- Simple AI Assistant without integrations and without memory
- Currently only german is supported

# Installation Guide
As there are a lot of problems with all the python packages, Apple Silicon (M1/2/3 Chips) and so on, I will provide a guide on how to install all the necessary packages and what to fix to make it work.

1.  Optional: Install uv (https://astral.sh/blog/uv) -> curl -LsSf https://astral.sh/uv/install.sh | sh
2.  Install necessary Python Packages using pip or uv pip
3.  Install rust with curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -> If you have trouble using or installing Rust try and install or reinstall gcc
4.  Optional if you are using Apple Silicon:

          1. xcode-select --install
          2. /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
          3. brew install cmake
          4. git clone https://github.com/rhasspy/piper.git
          5. cd piper
          6. git clone https://github.com/rhasspy/piper-phonemize.git pp
          7. cd pp
          8. git checkout fccd4f335aa68ac0b72600822f34d84363daa2bf -b my
          9. make
          10. export DYLD_LIBRARY_PATH=`pwd`/install/lib/
          11. patch -p1 <<EOF --- a/setup.py +++ b/setup.py @@ -9 +9 @@ _DIR = Path(__file__).parent -_ESPEAK_DIR = _DIR / "espeak-ng" / "build" +_ESPEAK_DIR = _DIR / "install" @@ -13 +13 @@ _ONNXRUNTIME_DIR = _LIB_DIR / "onnxruntime" -__version__ = "1.2.0" +__version__ = "1.1.0" EOF
          12. pip install .
          13. cp -rp ./install/share/espeak-ng-data venv/lib/python3.12/site-packages/piper_phonemize/espeak-ng-data
          14. pip install piper-tts
    
5.  Optional if you have trouble with make on Apple Silicon: Update your Makefile in the pp folder to this

          .PHONY: clean
          
          all:
          	cmake -Bbuild -DCMAKE_INSTALL_PREFIX=install -DCMAKE_BUILD_TYPE=Release
          	cmake --build build
          	cd build && ctest
          	cmake --install build
          
          clean:
          	rm -rf build install
6.  Download the german voice model Thorsten and the config (as this is the best german model available): https://github.com/rhasspy/piper/blob/master/VOICES.md
7.  Rename the voice model to voice_model.onnx and the config to voice_model.onnx.json and put it in the utilities folder
