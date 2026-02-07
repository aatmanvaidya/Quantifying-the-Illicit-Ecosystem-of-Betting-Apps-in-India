import json
import logging
import time
from typing import Dict, List

import requests

from logging_utils import ColorFormatter

logger = logging.getLogger("MetaAdsFetcher")
handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

API_ERROR_CODES = {
    1009: "Failed to pass parameter validation.",
    613: "Calls to this api have exceeded the rate limit.",
    100: "Invalid parameter.",
    200: "Permissions error.",
    2500: "Error parsing graph query.",
    190: "Invalid OAuth 2.0 Access Token.",
}


class MetaAdsFetcher:
    def __init__(self, access_token: str, api_version: str = "v23.0"):
        self.access_token = access_token
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{self.api_version}/ads_archive"

    def fetch_ads(
        self,
        search_terms: str,
        ad_type: str,
        ad_reached_countries: List[str],
        fields: str,
        ad_delivery_date_max: str = None,
    ) -> List[Dict]:
        params = {
            "search_terms": search_terms,
            "ad_type": ad_type,
            "ad_reached_countries": json.dumps(ad_reached_countries),
            "fields": fields,
            "access_token": self.access_token,
        }

        if ad_delivery_date_max:
            params["ad_delivery_date_max"] = ad_delivery_date_max

        all_ads = []
        url = self.base_url
        while url:
            try:
                response = requests.get(url, params=params)
                data = response.json()
            except Exception as e:
                logger.error(f"Request or JSON decode failed: {e}")
                break
            if "error" in data:
                error = data["error"]
                code = error.get("code")
                message = error.get("message", "Unknown error")
                user_msg = error.get("error_user_msg", "")
                log_msg = (
                    f"API Error {code}: {API_ERROR_CODES.get(code, message)} {user_msg}"
                )
                if code == 613:
                    logger.warning(
                        "Rate limit hit (code 613). Sleeping for 15 minutes..."
                    )
                    time.sleep(1)
                    # sys.exit(1)
                    return all_ads
                elif code == 190:
                    logger.critical("Invalid OAuth token. Stopping.")
                    break
                elif code in API_ERROR_CODES:
                    logger.error(log_msg)
                    break
                else:
                    logger.error(f"Unhandled API error: {data['error']}")
                    break
            if "data" in data:
                all_ads.extend(data["data"])
            else:
                logger.warning("No 'data' field in response. Stopping.")
                break
            url = data.get("paging", {}).get("next")
            params = {}  # After the first page, next is a full URL
        return all_ads
