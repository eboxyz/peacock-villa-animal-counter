from setuptools import setup, find_packages

setup(
    name="animal-counter",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "ultralytics>=8.0.0",
        "torch>=2.0.0",
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "motor>=3.3.0",
        "pymongo>=4.6.0",
        "python-multipart>=0.0.6",
    ],
    python_requires=">=3.9",
)
