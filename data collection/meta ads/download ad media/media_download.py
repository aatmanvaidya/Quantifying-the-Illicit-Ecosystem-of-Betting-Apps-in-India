import json
import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple

import ijson
import requests
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm


class FacebookAdMediaDownloader:
    """
    A class to download media from Facebook ad snapshots based on JSON data.
    """

    def __init__(
        self, json_folder_path: str, output_folder_path: str, log_level=logging.INFO
    ):
        self.json_folder_path = Path(json_folder_path)
        self.output_folder_path = Path(output_folder_path)
        self.output_folder_path.mkdir(exist_ok=True)

        # Setup logging
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("media_downloader.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # XPaths for different media types
        self.media_xpaths = [
            # Multiple images
            '//*[@id="content"]/div/div/div/div/div/div/div[3]/div/div[2]/div/div/div[1]/div/div/a/div[1]/img',
            # Single images
            '//*[@id="content"]/div/div/div/div/div/div/div[2]/a/div[1]/img',
            '//*[@id="content"]/div/div/div/div/div/div/div[2]/div[2]/img',
            # Videos
            '//*[@id="content"]/div/div/div/div/div/div/div[2]/div[2]/video',
            '//*[@id="content"]/div/div/div/div/div/div/div[2]/div[2]/div/div/div/div/video',
        ]

        self.driver = None

    def setup_driver(self) -> bool:
        """Setup Chrome WebDriver with options."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in background
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Chrome driver: {e}")
            return False

    def close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
            except Exception as e:
                self.logger.error(f"Error closing driver: {e}")

    def find_media_element(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Find media element on the Facebook ad page."""
        try:
            self.driver.get(url)

            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Additional wait to ensure dynamic content loads
            # time.sleep(2)

            # Try each XPath to find media
            for xpath in self.media_xpaths:
                try:
                    element = self.driver.find_element(By.XPATH, xpath)
                    media_url = element.get_attribute("src")
                    if media_url:
                        # Determine media type based on element tag
                        media_type = (
                            "video" if element.tag_name.lower() == "video" else "image"
                        )
                        return media_url, media_type
                except NoSuchElementException:
                    continue

            return None, None

        except TimeoutException:
            raise Exception("Page load timeout")
        except WebDriverException as e:
            raise Exception(f"WebDriver error: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")

    def download_media(self, media_url: str, file_path: Path) -> bool:
        """Download media from URL and save to file."""
        try:
            response = requests.get(media_url, stream=True)
            response.raise_for_status()

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            return True
        except requests.exceptions.RequestException as e:
            raise Exception(f"Download failed: {str(e)}")

    def process_json_element(self, element: dict, output_dir: Path) -> dict:
        """Process a single JSON element to download media."""
        element_id = element.get("id", "unknown")
        ad_snapshot_url = element.get("ad_snapshot_url")

        # Initialize status fields if they don't exist
        if "download_media_status" not in element:
            element["download_media_status"] = "none"
        if "media_error_message" not in element:
            element["media_error_message"] = "none"
        if "media_type" not in element:
            element["media_type"] = "unknown"

        if not ad_snapshot_url:
            element["media_error_message"] = "No ad_snapshot_url found"
            return element

        try:
            # Find media on the page
            media_url, media_type = self.find_media_element(ad_snapshot_url)

            if not media_url:
                element["media_error_message"] = "no_media_element"
                return element

            # Set media type
            element["media_type"] = media_type

            # Determine file extension and name
            extension = ".mp4" if media_type == "video" else ".png"
            filename = f"{element_id}{extension}"
            file_path = output_dir / filename

            # Download media
            if self.download_media(media_url, file_path):
                element["download_media_status"] = "success"
                element["media_error_message"] = "none"
                self.logger.info(f"Successfully downloaded: {filename}")
            else:
                element["media_error_message"] = "Download failed"

        except Exception as e:
            element["media_error_message"] = str(e)
            self.logger.error(f"Error processing element {element_id}: {e}")

        return element

    def should_download_element(self, element: dict) -> bool:
        """Check if element should be downloaded based on flags."""
        is_downloadable = element.get("is_downloadable")
        is_spam = element.get("is_spam")

        return is_downloadable and not is_spam

    def get_downloadable_count(self, json_file_path: Path) -> int:
        """Count downloadable elements in a JSON file using ijson."""
        try:
            count = 0
            with open(json_file_path, "rb") as file:
                # Parse JSON objects in the array
                objects = ijson.items(file, "item")
                for obj in objects:
                    if self.should_download_element(obj):
                        count += 1
            return count
        except Exception as e:
            self.logger.error(
                f"Error counting downloadable elements in {json_file_path}: {e}"
            )
            return 0

    def load_json_elements(self, json_file_path: Path):
        """Generator to load JSON elements one by one using ijson."""
        try:
            with open(json_file_path, "rb") as file:
                # Parse JSON objects in the array
                objects = ijson.items(file, "item")
                for obj in objects:
                    yield obj
        except Exception as e:
            self.logger.error(f"Error loading JSON elements from {json_file_path}: {e}")
            return

    def save_updated_json(self, json_file_path: Path, updated_elements: List[dict]):
        """Save updated elements back to JSON file."""
        try:
            with open(json_file_path, "w", encoding="utf-8") as file:
                json.dump(updated_elements, file, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving updated JSON file {json_file_path}: {e}")
            raise

    def process_json_file(self, json_file_path: Path) -> bool:
        """Process a single JSON file."""
        self.logger.info(f"Processing file: {json_file_path.name}")

        # Create output directory for this JSON file
        output_dir = self.output_folder_path / json_file_path.stem
        output_dir.mkdir(exist_ok=True)

        try:
            updated_elements = []
            processed_count = 0
            total_elements = 0

            # Get total element count for progress bar
            with open(json_file_path, "rb") as file:
                objects = ijson.items(file, "item")
                total_elements = sum(1 for _ in objects)

            # Process elements with progress bar
            with tqdm(
                total=total_elements, desc=f"Processing {json_file_path.name}"
            ) as pbar:
                for element in self.load_json_elements(json_file_path):
                    if self.should_download_element(element):
                        # Process downloadable element
                        element = self.process_json_element(element, output_dir)
                        processed_count += 1
                    else:
                        # Skip non-downloadable elements but still add status fields
                        if "download_media_status" not in element:
                            element["download_media_status"] = "skipped"
                        if "media_error_message" not in element:
                            element["media_error_message"] = (
                                "not_downloadable_or_marked_spam"
                            )
                        if "media_type" not in element:
                            element["media_type"] = "unknown"

                    updated_elements.append(element)
                    pbar.update(1)

                    # Small delay to avoid overwhelming the server
                    if self.should_download_element(element):
                        time.sleep(0.5)

            # Save updated JSON file
            self.save_updated_json(json_file_path, updated_elements)

            self.logger.info(f"Completed processing {json_file_path.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error processing file {json_file_path.name}: {e}")
            return False

    def process_files(self, json_file_paths: List[Path]) -> None:
        """Process multiple JSON files."""
        self.logger.info(f"Starting processing of {len(json_file_paths)} files")

        # Setup WebDriver
        if not self.setup_driver():
            self.logger.error("Failed to setup WebDriver. Exiting.")
            return

        try:
            successful_files = 0
            for json_file in json_file_paths:
                if self.process_json_file(json_file):
                    successful_files += 1
                else:
                    self.logger.warning(f"Failed to process {json_file.name}")

            self.logger.info(
                f"Processing completed. {successful_files}/{len(json_file_paths)} files processed successfully."
            )

        except KeyboardInterrupt:
            self.logger.info("Process interrupted by user")
        except Exception as e:
            self.logger.error(f"Unexpected error during processing: {e}")
        finally:
            self.close_driver()

    def process_single_file(self, filename: str) -> bool:
        """Process a single specific JSON file."""
        json_file_path = self.json_folder_path / filename

        if not json_file_path.exists():
            self.logger.error(f"File {filename} not found in {self.json_folder_path}")
            return False

        self.logger.info(f"Processing single file: {filename}")

        # Setup WebDriver
        if not self.setup_driver():
            self.logger.error("Failed to setup WebDriver. Exiting.")
            return False

        try:
            result = self.process_json_file(json_file_path)
            self.logger.info(
                f"Single file processing {'completed successfully' if result else 'failed'}"
            )
            return result
        except Exception as e:
            self.logger.error(f"Error processing single file {filename}: {e}")
            return False
        finally:
            self.close_driver()
