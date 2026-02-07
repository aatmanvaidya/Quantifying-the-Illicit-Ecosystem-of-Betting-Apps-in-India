import csv
import datetime
import json
import os
import glob
import random
from typing import List, Optional, Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

PORT = 8000
BASE_PATH = r"/path/to/downloaded media"
JSON_FOLDER = os.path.join(BASE_PATH, r"/path/to/meta ads metadata json")
ANNOTATION_FOLDER = r"/path/to/store annotation csv"

VALIDATION_MEDIA_ROOT = "/path/to/instagram posts"
VALIDATION_JSON_DIR = os.path.join(VALIDATION_MEDIA_ROOT, "output_result_jsons")
VALIDATION_CSV_PATH = os.path.join(VALIDATION_JSON_DIR, "validation_results.csv")

app = FastAPI(title="Annotation UI", version="0.0.1")


class AnnotationPayload(BaseModel):
    jsonFileName: str
    id: str
    is_spam: str
    ad_category: List[str]
    ad_category_other: Optional[str] = ""
    app_name: List[str]
    app_name_other: Optional[str] = ""
    primary_messaging_strategy: List[str]
    potentially_harmful_narratives: List[str]
    media_authenticity: List[str]
    sexual_content: str
    ad_notes: Optional[str] = ""


class GetDataPayload(BaseModel):
    json_file: str


class QueryPayload(BaseModel):
    field_name: str
    field_value: str


class GalleryQueryPayload(BaseModel):
    ad_category: str
    media_authenticity: str
    media_type: str


class ValidationPayload(BaseModel):
    file_name: str
    source_json: str
    validation_status: str  # 'Correct' or 'Incorrect'
    # We keep this field to maintain CSV structure compatibility,
    # but the frontend will now send empty strings.
    correction_notes: Optional[str] = ""


@app.post("/api/get_data")
async def get_data(payload: GetDataPayload):
    json_path = os.path.join(JSON_FOLDER, payload.json_file)
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="JSON file not found")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@app.post("/api/get_remaining_data")
async def get_remaining_data(payload: GetDataPayload):
    json_path = os.path.join(JSON_FOLDER, payload.json_file)
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="JSON file not found")

    with open(json_path, "r", encoding="utf-8") as f:
        full_data = json.load(f)

    csv_file_name = payload.json_file.replace(".json", ".csv")
    csv_path = os.path.join(ANNOTATION_FOLDER, csv_file_name)

    annotated_ids = set()
    if os.path.exists(csv_path):
        try:
            with open(csv_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "id" in row:
                        annotated_ids.add(row["id"])
        except Exception:
            pass

    remaining_data = [item for item in full_data if item.get("id") not in annotated_ids]
    return remaining_data


@app.get("/api/get_item_by_id")
async def get_item_by_id(item_id: str, json_file: str):
    json_path = os.path.join(JSON_FOLDER, json_file)
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="JSON file not found")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        if item.get("id") == item_id:
            return [item]

    raise HTTPException(status_code=404, detail=f"Item with ID '{item_id}' not found")


@app.get("/api/get_annotations")
async def get_annotations(json_file: str):
    csv_file_name = json_file.replace(".json", ".csv")
    csv_path = os.path.join(ANNOTATION_FOLDER, csv_file_name)

    annotations = {}
    if os.path.exists(csv_path):
        try:
            with open(csv_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "id" in row:
                        annotations[row["id"]] = row
        except Exception:
            return {}

    return JSONResponse(content=annotations)


@app.post("/api/query_annotations")
async def query_annotations(payload: QueryPayload):
    target_field = payload.field_name
    target_value = payload.field_value

    results = []
    json_cache = {}

    if not os.path.exists(ANNOTATION_FOLDER):
        return []

    for csv_file in os.listdir(ANNOTATION_FOLDER):
        if not csv_file.endswith(".csv"):
            continue

        csv_path = os.path.join(ANNOTATION_FOLDER, csv_file)
        json_file_name = csv_file.replace(".csv", ".json")
        json_path = os.path.join(JSON_FOLDER, json_file_name)

        if not os.path.exists(json_path):
            continue

        try:
            with open(csv_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames and target_field not in reader.fieldnames:
                    continue

                for row in reader:
                    row_value = row.get(target_field, "")
                    values_list = row_value.split(";")

                    if target_value in values_list:
                        item_id = row.get("id")

                        if json_file_name not in json_cache:
                            with open(json_path, "r", encoding="utf-8") as jf:
                                json_cache[json_file_name] = json.load(jf)

                        original_item = next(
                            (
                                item
                                for item in json_cache[json_file_name]
                                if item["id"] == item_id
                            ),
                            None,
                        )

                        if original_item:
                            original_item["jsonFileName"] = json_file_name
                            original_item["existing_annotation"] = row
                            results.append(original_item)

        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
            continue

    return results


@app.post("/api/get_gallery_items")
async def get_gallery_items(payload: GalleryQueryPayload):
    target_category = payload.ad_category
    target_auth = payload.media_authenticity
    target_media_type = payload.media_type

    results = []
    json_cache = {}

    if not os.path.exists(ANNOTATION_FOLDER):
        return []

    for csv_file in os.listdir(ANNOTATION_FOLDER):
        if not csv_file.endswith(".csv"):
            continue

        csv_path = os.path.join(ANNOTATION_FOLDER, csv_file)
        json_file_name = csv_file.replace(".csv", ".json")
        json_path = os.path.join(JSON_FOLDER, json_file_name)

        if not os.path.exists(json_path):
            continue

        try:
            with open(csv_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    if row.get("is_spam") == "True":
                        continue

                    row_categories = row.get("ad_category", "").split(";")
                    if (
                        target_category != "All"
                        and target_category not in row_categories
                    ):
                        continue

                    row_auth = row.get("media_authenticity", "").split(";")
                    if target_auth != "All" and target_auth not in row_auth:
                        continue

                    item_id = row.get("id")

                    if json_file_name not in json_cache:
                        with open(json_path, "r", encoding="utf-8") as jf:
                            json_cache[json_file_name] = json.load(jf)

                    original_item = next(
                        (
                            item
                            for item in json_cache[json_file_name]
                            if item["id"] == item_id
                        ),
                        None,
                    )

                    if original_item:
                        item_media_type = original_item.get("media_type", "image")
                        if (
                            target_media_type != "All"
                            and item_media_type != target_media_type
                        ):
                            continue

                        original_item["jsonFileName"] = json_file_name
                        results.append(original_item)

        except Exception as e:
            print(f"Error processing gallery scan for {csv_file}: {e}")
            continue

    return results


@app.post("/api/save_annotation")
async def save_annotation(annotation: AnnotationPayload):
    annotation_data = annotation.dict()
    item_id = annotation_data["id"]
    json_file_name = annotation_data["jsonFileName"]

    for key, value in annotation_data.items():
        if isinstance(value, list):
            annotation_data[key] = ";".join(map(str, value))

    all_headers = [
        "jsonFileName",
        "id",
        "is_spam",
        "ad_category",
        "ad_category_other",
        "app_name",
        "app_name_other",
        "primary_messaging_strategy",
        "potentially_harmful_narratives",
        "media_authenticity",
        "sexual_content",
        "ad_notes",
        "timestamp",
    ]

    os.makedirs(ANNOTATION_FOLDER, exist_ok=True)
    csv_file_name = json_file_name.replace(".json", ".csv")
    csv_path = os.path.join(ANNOTATION_FOLDER, csv_file_name)

    annotation_data["timestamp"] = datetime.datetime.now().isoformat()

    existing_data = []
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        with open(csv_path, "r", newline="", encoding="utf-8") as rf:
            reader = csv.DictReader(rf)
            existing_data = list(reader)

    found = False
    for i, row in enumerate(existing_data):
        if row.get("id") == item_id:
            existing_data[i] = annotation_data
            found = True
            break

    if not found:
        existing_data.append(annotation_data)

    with open(csv_path, "w", newline="", encoding="utf-8") as wf:
        writer = csv.DictWriter(wf, fieldnames=all_headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(existing_data)

    return {"status": "success", "message": "Annotation saved."}


@app.get("/api/get_validation_batch")
async def get_validation_batch():
    """
    Returns the same 300 random items (seeded) every time.
    It checks the CSV to see if an item has ALREADY been validated,
    and if so, attaches that data to the response so the frontend can populate it.
    """
    all_items = []

    # 1. Gather all items
    json_files = glob.glob(os.path.join(VALIDATION_JSON_DIR, "*.json"))
    for j_file in json_files:
        try:
            with open(j_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                source_name = os.path.basename(j_file)
                if isinstance(data, list):
                    for item in data:
                        if item.get("status") == "success":
                            item["_source_json"] = source_name
                            all_items.append(item)
        except Exception as e:
            print(f"Skipping bad JSON {j_file}: {e}")

    # 2. Select 300 Random Items (Fixed Seed)
    all_items.sort(key=lambda x: x.get("file_path", ""))
    random.seed(42)
    sample_size = min(300, len(all_items))
    selected_batch = random.sample(all_items, sample_size)

    # 3. Load existing validations into a Lookup Dict
    validation_map = {}
    if os.path.exists(VALIDATION_CSV_PATH):
        try:
            with open(VALIDATION_CSV_PATH, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = f"{row['source_json']}_{row['file_name']}"
                    validation_map[key] = row
        except Exception:
            pass

    # 4. Attach validation status and web URL
    for item in selected_batch:
        # Resolve Web URL
        abs_path = item.get("file_path", "")
        if abs_path.startswith(VALIDATION_MEDIA_ROOT):
            relative_part = abs_path.replace(VALIDATION_MEDIA_ROOT, "")
            if relative_part.startswith("/"):
                relative_part = relative_part[1:]
            item["web_url"] = f"/validation-media/{relative_part}"
        else:
            item["web_url"] = ""

        # Attach existing validation if present
        key = f"{item['_source_json']}_{item['file_name']}"
        if key in validation_map:
            item["existing_validation"] = validation_map[key]
        else:
            item["existing_validation"] = None

    return {"total_batch_size": len(selected_batch), "items": selected_batch}


@app.post("/api/save_validation_result")
async def save_validation_result(payload: ValidationPayload):
    """
    Saves or Updates a validation result in the CSV.
    """
    fieldnames = [
        "source_json",
        "file_name",
        "validation_status",
        "correction_notes",
        "timestamp",
    ]

    new_row = {
        "source_json": payload.source_json,
        "file_name": payload.file_name,
        "validation_status": payload.validation_status,
        "correction_notes": payload.correction_notes,
        "timestamp": datetime.datetime.now().isoformat(),
    }

    # Read all existing data
    rows = []
    file_exists = os.path.exists(VALIDATION_CSV_PATH)
    found = False

    if file_exists:
        try:
            with open(VALIDATION_CSV_PATH, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception:
            rows = []

    # Check if we need to update an existing row
    for i, row in enumerate(rows):
        if (
            row["source_json"] == payload.source_json
            and row["file_name"] == payload.file_name
        ):
            rows[i] = new_row
            found = True
            break

    if not found:
        rows.append(new_row)

    # Write back completely
    with open(VALIDATION_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {"status": "success"}


app.mount("/scams-media", StaticFiles(directory=BASE_PATH), name="scams-media")

if os.path.exists(VALIDATION_MEDIA_ROOT):
    app.mount(
        "/validation-media",
        StaticFiles(directory=VALIDATION_MEDIA_ROOT),
        name="validation-media",
    )
else:
    print(f"WARNING: Validation media root not found at {VALIDATION_MEDIA_ROOT}")


# --- PAGE ROUTES ---
@app.get("/")
async def read_index():
    return FileResponse("index.html")


@app.get("/remaining")
async def read_remaining_index():
    return FileResponse("index.html")


@app.get("/filter")
async def read_filter_index():
    return FileResponse("index.html")


@app.get("/gallery")
async def read_gallery_index():
    return (
        FileResponse("gallery.html")
        if os.path.exists("gallery.html")
        else JSONResponse({"error": "gallery.html not found"}, 404)
    )


@app.get("/validate_gemini")
async def read_validate_gemini():
    return (
        FileResponse("validate_gemini.html")
        if os.path.exists("validate_gemini.html")
        else JSONResponse({"error": "validate_gemini.html not found"}, 404)
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
