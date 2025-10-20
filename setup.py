import sys
import pathlib
import subprocess
from setuptools import find_packages, setup
from setuptools.command.install import install

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()


def link_libiomp():
    # путь к вашему файлу
    script_path = "fix_libomp.sh"
    print(f"[post-install] Execute: {script_path} ")
    subprocess.run(["/bin/sh", script_path], check=True)

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        # 1. стандартная установка пакета и зависимостей
        install.run(self)

        print(f"[post-install] Platform: {sys.platform}")
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
    cmdclass={"install": PostInstallCommand},
)
