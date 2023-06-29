import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setuptools.setup(
    name="pg_tuna",
    version="0.1.1",
    author="Josip Delic",
    description="pg_tuna",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/delijati/py-tuna",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    zip_safe=False,
    include_package_data=True,
    package_dir={"": "src"},
    packages=setuptools.find_namespace_packages(where="src"),
    install_requires=[],
    extras_require={"tests": ["pytest", "pytest-cov", "flake8"]},
    entry_points={"console_scripts": ["pg-tuna = pg_tuna.wizard:main"]},
)
