import re, pathlib, requests, json
from collections import defaultdict
import mimetypes
from urllib.parse import urlparse
from pathlib import Path
from loguru import logger

data = [1809165574,]
logger.info(f'downloading mods {data}')
response = requests.post('https://backend-02-prd.steamworkshopdownloader.io/api/details/file',data=json.dumps(data))

def handle_generic(modroot, item):
    raise NotImplementedError

def handle_generic_warning(modroot,item):
    appname = item['app_name']
    logging.warning(f"Using generic downloader for {appname}")
    handle_generic(modroot,item)

from handlers.tabletopSim import handle as handle_tabletopSim
#Mapping of consumer appids to handlers
appHandlers = defaultdict(lambda: handle_generic_warning)
appHandlers.update({
    286160: handle_tabletopSim,
})

for item in response.json():
    #The folder to download the mod to.
    modroot=(Path('data')/item['app_name']/(item['publishedfileid']+"-"+item['title']).replace("/","|"))
    modroot.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving data to '{modroot}'")
    (modroot/"mod_metadata_workshopdownloader.json").write_text(json.dumps(item))

    if item.get('preview_url',None):
        preview_image = requests.get(item['preview_url'])
        content_type = preview_image.headers['content-type']
        extension = mimetypes.guess_extension(content_type)
        (modroot/("mod_preview_workshopdownloader"+extension)).write_bytes(preview_image.content)

    appHandlers[item['consumer_appid']](modroot,item)
