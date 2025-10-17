import os
import sys
import pathlib
import site
from setuptools import find_packages, setup
from setuptools.command.install import install


# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()


def link_libiomp():
    dylib = "libiomp5.dylib"
    site_packages = pathlib.Path(sys.prefix) / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"

    lib_dst_functorch = site_packages / "functorch" / ".dylibs" / dylib
    lib_dst_torch = site_packages / "torch" / "lib" / dylib
    lib_src = site_packages / "ctranslate2" / ".dylibs" / dylib

    # если ctranslate2 ещё не установлен – пропускаем
    if not lib_src.exists():
        print(f"[post-install] {lib_src} not found – skip fix.")
        return

    for lib in (lib_dst_functorch, lib_dst_torch):
        if not lib.exists():
            continue
        # удаляем оригинал
        lib.unlink()
        # создаём жёсткую ссылку
        lib.hardlink_to(os.path.relpath(lib_src, lib.parent))
        print(f"[post-install] replaced {lib} with symlink to {lib_src}")

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        # 1. стандартная установка пакета и зависимостей
        install.run(self)

        # 2. выполняем фикс только на Darwin (macOS)
        if sys.platform == "darwin":
            link_libiomp()


# This call to setup() does all the work
setup(
    name="whisper_fusion",
    version="0.1",
    description="A nearly-live implementation of OpenAI's Whisper.",
    long_description=README,
    long_description_content_type="text/markdown",
    include_package_data=True,
    url="https://github.com/collabora/WhisperFusion",
    author="Collabora Ltd",
    author_email="vineet.suryan@collabora.com",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    packages=find_packages(
        exclude=(
            "requirements",
            "whisper-finetuning"
        )
    ),
    install_requires=[
        "PyAudio",
        "faster-whisper==1.1.0",
        "torch",
        "torchaudio",
        "websockets",
        "onnxruntime==1.17.0",
        "scipy",
        "websocket-client",
        "numba",
        "openai-whisper==20240930",
        "kaldialign",
        "soundfile",
        "tokenizers==0.20.3",
        "librosa",
        "numpy==1.26.4",
        "openvino",
        "openvino-genai",
        "openvino-tokenizers",
        "optimum", 
        "optimum-intel",
        "sentencepiece",
        "sacremoses",
        "kokoro"
    ],
    python_requires=">=3.11",
    cmdclass={"install": PostInstallCommand,},
)
