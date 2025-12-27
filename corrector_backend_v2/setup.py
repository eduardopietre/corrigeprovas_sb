from setuptools import setup, find_packages

setup(
    name="corrector_backend_v2",
    version="1.0",
    description="Backend Logic of Corrector",
    author="Eduardo Pietre",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "opencv-python"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
