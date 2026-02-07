import json
import logging
import os
import time

import yaml
from dotenv import load_dotenv

from logging_utils import ColorFormatter
from meta_ads_fetcher import MetaAdsFetcher

load_dotenv()

logger = logging.getLogger("RunFetchAds")
handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

FIELDS = "id,page_id,page_name,ad_snapshot_url,ad_creation_time,ad_delivery_start_time,ad_delivery_stop_time,ad_creative_bodies,ad_creative_link_captions,ad_creative_link_descriptions,ad_creative_link_titles,demographic_distribution,delivery_by_region,impressions,spend,currency,estimated_audience_size,bylines,publisher_platforms,languages"
DATE_CUTOFF = "2025-12-31"

fetcher = MetaAdsFetcher(ACCESS_TOKEN)

yaml_path = os.path.join(os.path.dirname(__file__), r"path/to/keywords.yml")
with open(yaml_path, "r") as f:
    keywords_data = yaml.safe_load(f)

KEYWORDS = keywords_data["keywords"]

# Create download_ads directory if it doesn't exist
download_dir = os.path.join(os.path.dirname(__file__), r"path/to/download/folder")
os.makedirs(download_dir, exist_ok=True)


def sanitize_filename(keyword):
    return "".join([c if c.isalnum() else "_" for c in keyword])


for keyword in KEYWORDS:
    safe_name = sanitize_filename(keyword)
    output_file = os.path.join(download_dir, f"{safe_name}.json")

    if os.path.exists(output_file):
        logger.warning(f"Skipping {keyword} – file already exists")
        continue

    start_time = time.time()
    logger.info(f"Fetching ads for keyword: {keyword}")
    ads = fetcher.fetch_ads(
        search_terms=keyword,
        ad_type="ALL",
        ad_reached_countries=["IN"],
        fields=FIELDS,
        ad_delivery_date_max=DATE_CUTOFF,
    )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(ads, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    logger.info(f"Fetched {len(ads)} ads for '{keyword}' in {elapsed:.2f} seconds.")
