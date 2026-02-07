import yaml
from pathlib import Path
from media_download import FacebookAdMediaDownloader

def main():
    json_folder_path = Path(r"/path/to/ads json folder")

    with open("file_order.yml", "r") as f:
        data = yaml.safe_load(f)

    ascending_files = data["ascending_order"]

    json_files = [json_folder_path / file_info["filename"] for file_info in ascending_files]
    # print(json_files)

    # Initialize downloader
    downloader = FacebookAdMediaDownloader(
        json_folder_path=json_folder_path,
        output_folder_path=r"/path/to/download media folder"
    )
    downloader.process_files(json_files)

if __name__ == "__main__":
    main()
