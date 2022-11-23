from clldutils import licenses

for license in licenses._LICENSES:
    if "CC" in license.id:
        print(license.id)