from setuptools import setup, find_packages

setup(
    name="dom-heal",
    version="1.0.0",
    description="Auto-recuperação de seletores DOM para testes web",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Jonnas Christian Sousa de Paiva",
    author_email="jonnaschristian@gmail.com",
    url="https://github.com/jonnaschristian/dom-heal",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "rapidfuzz>=3.13.0",
        "selenium>=4.29.0",
        "webdriver-manager>=4.0.2",
        "typer[all]>=0.9.0",
        "lxml>=4.9.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "python-dotenv>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "dom-heal = dom_heal.cli:main",
        ],
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License"
    ],
)
