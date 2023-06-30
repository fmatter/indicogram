from setuptools import setup, find_packages


setup(
    name="indicogram",
    version="0.0.1.dev",
    description="indicogram",
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author="Florian Matter",
    author_email="fmatter@mailbox.org",
    url="",
    keywords="linguistics, digital grammaticography, clld",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "clld>=9.0.0",
        "clld_corpus_plugin>=0.0.8",
        "clld_document_plugin>=0.0.5",
        "clld_morphology_plugin>=0.0.10",
        "clld_markdown_plugin>=0.2.0",
        "waitress>=2.1.2",
        "cldf-ldd",
    ],
    extras_require={
        "dev": ["flake8"],
        "test": [
            "mock",
            "pytest>=5.4",
            "pytest-clld",
            "pytest-mock",
            "pytest-cov",
            "coverage>=4.2",
            "selenium",
            "zope.component>=3.11.0",
        ],
    },
    test_suite="indicogram",
    entry_points="""\
    [paste.app_factory]
    main = indicogram:main
""",
)
