#! /usr/bin/env python3

import json
import logging
import os
import appdirs
import bsdl_parser.bsdl2json

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

def load_bsdl(bsdl_file, bsdl_cache=None):
    try:
        # Try to open as bsdl-json-file:
        with open(bsdl_file) as json_file:
            data = json.load(json_file)
    except json.decoder.JSONDecodeError:
        # bsdl_file is an original BSDL file. Let's find in the cache:
        logging.info(f"{bsdl_file} is not a json file... Lets's find in the cache")
        bname = os.path.basename(bsdl_file)
        cachedir = appdirs.user_cache_dir("bscan_proc") 
        if bsdl_cache:
            cachedir = bsdl_cache
        try:
            os.mkdir(cachedir)
        except FileExistsError:
            pass
        cached_bsdl_json_file = os.path.abspath(os.path.join(cachedir, f'{bname}.json'))
        if not os.path.isfile(cached_bsdl_json_file):
            logging.info(f"{cached_bsdl_json_file} not found in cache... Lets's parse original.")
            logging.info(f"Calling bsdl2json({bsdl_file}, {cached_bsdl_json_file})")
            bsdl_parser.bsdl2json.bsdl2json(bsdl_file, cached_bsdl_json_file)
            
        with open(cached_bsdl_json_file) as json_file:
            logging.info(f"{cached_bsdl_json_file} json has found in the cace.")
            data = json.load(json_file)
    return data
