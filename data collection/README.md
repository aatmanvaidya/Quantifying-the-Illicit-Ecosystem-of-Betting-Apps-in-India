# Data Collection

This directory contains scripts and notebooks used to collect data from various sources including Meta Ad Library, Instagram, and Google Play Store.

## Modules

### 1. Meta Ad Library (`meta ads/`)
This module is responsible for fetching ads related to betting apps from Meta's Ad Library.
- **`collect ads/`**: Contains scripts to query the Meta Ad Library API.
  - `meta_ads_fetcher.py`: Core logic for interacting with the API.
  - `run_fetch_ads.py`: Entry point for starting the collection process.
- **`download ad media/`**: Contains scripts to download images and videos from the collected ads.
  - `media_download.py`: Utility to download and save media files.

### 2. Instagram (`instagram/`)
This module collects organic posts from Instagram.
- `collect_posts_per_hashtag.ipynb`: Notebook for scraping posts based on specific betting-related hashtags.
- `download_images.ipynb`: Notebook for downloading images from the collected Instagram posts.

### 3. Google Play Store Reviews (`google playstore reviews/`)
This module identifies and collects user reviews for betting apps.
- `collect_reviews.py`: Uses the `google-play-scraper` library to fetch reviews for a predefined set of app IDs.

## Requirements
Most scripts require specific environment variables (e.g., Meta AD Library Access token). Ensure you have a `.env` file in the root directory if required by the scripts.
