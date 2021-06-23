import re, pathlib, requests, json
import mimetypes
from urllib.parse import urlparse
from pathlib import Path
import bson
import cgi
from loguru import logger
import shutil, functools
from tqdm.auto import tqdm
import csv

urlRegex = re.compile("(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")

def handle(modroot, item):
    #Keep track of files that we've already seen, so we don't accidently download them
    # more than once.
    #We don't want to download a few common urls that aren't actually relevent to anything.
    seen = {"http://berserk-games.com/knowledgebase/scripting/",
            "https://api.tabletopsimulator.com/",
            }
    #Sometimes we can't name a file. If we can't, it gets a number.
    unknown_files = 0

    content = None
    with requests.get(item['file_url']) as r:
        dump = bson.loads(r.content)
        dump.pop('DrawImage',None)
        content = json.dumps(dump,indent=2)
        (modroot/Path("mod.json")).write_text(content)
    urlmapping = csv.writer((modroot/"mod_file_mapping.csv").open("w"))
    urlmapping.writerow(("url","filename"))

    urls = urlRegex.finditer(content)
    for item in urls:
        url = item[0]
        #Don't download files more than once
        if url in seen: continue
        seen.add(url)

        #Streaming download with guessed file name and content type
        download = requests.get(url, stream=True, allow_redirects=True)
        fname = ''
        if 'content-disposition' in download.headers:
            value, params = cgi.parse_header(download.headers['content-disposition'])
            fname = params.get('filename','')
        if not fname:
            fname = urlparse(url).path

        fname = Path(fname).name
        #Handle files who's name we can't auto discover
        if not fname:
            extention = mimetypes.guess_extension(download.headers.get('content-type',""))
            fname = "Unknown_file-"+str(unkown_files)+ extention
            unkown_files+=1

        fpath = modroot/fname
        urlmapping.writerow((url,fname))
        logger.info(f'Downloading "{fpath}" from "{url}"')

        file_size = int(download.headers.get('Content-Length', 0))
        desc = "(Unknown total file size)" if file_size == 0 else ""
        download.raw.read = functools.partial(download.raw.read, decode_content=True)  # Decompress if needed
        with tqdm.wrapattr(download.raw, "read", total=file_size, desc=desc, leave=False) as download_raw:
            with fpath.open("wb") as f:
                shutil.copyfileobj(download_raw, f)
