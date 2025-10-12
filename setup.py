"""Setup script for AI Job Candidate Reviewer."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="ai-job-candidate-reviewer",
    version="0.1.0",
    author="AI Job Candidate Reviewer Team",
    description="Automate first-pass resume screening with AI assistance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=[
        "candidate_reviewer",
        "config",
        "models",
        "open_api_test_connection",
        "file_processor",
        "output_generator",
    ],
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "candidate-reviewer=candidate_reviewer:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
