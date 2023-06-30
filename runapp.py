import os

from paste.deploy import loadapp
from waitress import serve
import pandas as pd
from pathlib import Path
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

if __name__ == "__main__":
    AUDIO_PATH = Path("audio")
    AUDIO_PATH.mkdir(exist_ok=True)
    df = pd.read_csv(
        "https://raw.githubusercontent.com/caribank/yawarana-corpus-cldf/main/cldf/media.csv"
    )
    for rec in df.to_dict("records"):
        if not Path(rec["Download_URL"]).is_file():
            print(rec["Download_URL"], "not found, downloading update")
            zipurl = (
                "https://www.dropbox.com/sh/9nrrnn5n0gzkjpi/AABQC_7h2CpCiY0lK6BG-igra?dl=1"
            )
            with urlopen(zipurl) as zipresp:
                with ZipFile(BytesIO(zipresp.read())) as zfile:
                    zfile.extractall(AUDIO_PATH)
            print("Success")
            break


    port = int(os.environ.get("PORT", 5000))
    app = loadapp("config:development.ini", relative_to=".")

    serve(app, host="0.0.0.0", port=port)
