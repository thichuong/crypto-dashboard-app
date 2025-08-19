from setuptools import setup, find_packages

setup(
    name="crypto-dashboard-ai-report-generator",
    version="0.1.0",
    author="thichuong",
    description="A crypto dashboard and AI report generator application",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="Apache-2.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        line.strip() 
        for line in open("requirements.txt").readlines() 
        if line.strip() and not line.startswith("#")
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
