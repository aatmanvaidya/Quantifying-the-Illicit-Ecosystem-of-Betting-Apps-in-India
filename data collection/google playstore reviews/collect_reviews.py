import json
import os
import re
import time
import csv

import pandas as pd
from google_play_scraper import Sort, reviews_all
from tqdm import tqdm

# json file has app metadata like id, name etc (can be any datatype/file)
INPUT_JSON = r"/path/to/input json"
output_dir = r"/path/to/download folder"
os.makedirs(output_dir, exist_ok=True)

def clean_filename(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9\s]", "", title)
    title = re.sub(r"\s+", "_", title)
    return title.strip("_")

st = time.time()

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    apps = json.load(f)

for app in tqdm(apps, desc="Fetching reviews"):
    app_id = app["id"]
    app_title = app["title"]
    safe_title = clean_filename(app_title)
    output_file = os.path.join(output_dir, f"{safe_title}.csv")

    try:
        reviews = reviews_all(
            app_id,
            country="in",
            sort=Sort.MOST_RELEVANT,
            filter_score_with=1,  # defaults to None(means all score)
        )

        df = pd.DataFrame(reviews)

        # df.to_csv(output_file, index=False, encoding="utf-8")
        df.to_csv(output_file, index=False, encoding="utf-8", quoting=csv.QUOTE_ALL)
    except Exception as e:
        print(f"Error fetching {app_title}: {e}")

et = time.time()
print(f"Total Time: {et - st} secs")
