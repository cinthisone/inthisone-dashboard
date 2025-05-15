from setuptools import setup, find_packages

setup(
    name="inthisone-dashboard",
    version="1.0.0",
    description="Inthisone Dashboard - A customizable desktop dashboard application",
    author="StackBlitz",
    packages=find_packages(),
    install_requires=[
        "PySide6>=6.5.0",
        "markdown2>=2.4.0",
        "pdfminer.six>=20221105",
        "beautifulsoup4>=4.12.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "dashboard=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
        "Topic :: Desktop Environment",
    ],
    python_requires=">=3.8",
)