"""
Few-shot image classification using Gemini 2.0 Flash.
Includes example images with annotations to improve model consistency.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from tqdm import tqdm

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Configuration
keyword = "instagram key word name"
image_folder = Path(
    f"/path/to/instagram posts downloaded/{keyword}"
)
examples_folder = Path(
    "/path/to/few_shot_examples"
)
output_file = rf"/path/to/output annotations/{keyword}.json"
token_log_file = "gemini_token_log.jsonl"
MODEL = "gemini-2.5-pro"
SAVE_INTERVAL = 10  # Save every N images

# Few-shot examples with their expected annotations
FEW_SHOT_EXAMPLES = [
    {"image_file": "ex1-spam.png", "annotation": {"is_spam": True}},
    {"image_file": "ex2-spam.png", "annotation": {"is_spam": True}},
    {"image_file": "ex3-spam.png", "annotation": {"is_spam": True}},
    {
        "image_file": "ex4.png",
        "annotation": {
            "is_spam": False,
            "ad_category": ["Casino Games", "Trading / Crypto"],
            "app_name": ["BC Game"],
            "primary_messaging_strategy": ["User Acquisition", "General Promotion"],
            "potentially_harmful_narratives": [
                "Easy Money Narrative",
                "Risk Minimization",
            ],
            "media_authenticity": ["Authentic"],
            "sexual_content": "no",
            "ad_notes": "The ad promotes BC.Game, an online casino, with a 300% deposit bonus. This is harmful because it promotes easy money narrative and risk minimization by offering a large bonus.",
        },
    },
    {
        "image_file": "ex5.png",
        "annotation": {
            "is_spam": False,
            "ad_category": ["Sports Betting", "Prediction Games"],
            "app_name": ["Betway", "1xBet", "Parimatch", "1win", "Aviator"],
            "primary_messaging_strategy": ["User Acquisition", "General Promotion"],
            "potentially_harmful_narratives": [
                "Easy Money Narrative",
                "Risk Minimization",
            ],
            "media_authenticity": ["Authentic"],
            "sexual_content": "no",
            "ad_notes": "The image promotes an 'Aviator Predictor' app version 6.0 and various betting platforms. The easy money narrative and potential misleading claims of predicting outcomes in betting games are harmful, as they can lead to financial losses and addiction.",
        },
    },
    {
        "image_file": "ex6.jpg",
        "annotation": {
            "is_spam": False,
            "ad_category": ["Sports Betting"],
            "app_name": ["Betway", "1xBet", "Parimatch", "1win", "Aviator"],
            "primary_messaging_strategy": ["User Acquisition", "General Promotion"],
            "potentially_harmful_narratives": [
                "Easy Money Narrative",
                "Risk Minimization",
            ],
            "media_authenticity": ["Authentic"],
            "sexual_content": "no",
            "ad_notes": "The image promotes an 'Aviator Predictor' app version 6.0 and various betting platforms. The easy money narrative and potential misleading claims of predicting outcomes in betting games are harmful, as they can lead to financial losses and addiction.",
        },
    },
    {
        "image_file": "ex7.jpg",
        "annotation": {
            "is_spam": False,
            "ad_category": ["Lottery / Jackpots", "Prediction Games"],
            "app_name": [],
            "primary_messaging_strategy": [
                "Misleading or Deceptive",
                "General Promotion",
            ],
            "potentially_harmful_narratives": ["Easy Money Narrative"],
            "media_authenticity": ["Authentic"],
            "sexual_content": "no",
            "ad_notes": 'The image shows a lottery game winning announcement, showing a bonus of Rs294,000.00. It promotes an "easy money" narrative, implying winning is easy and the amount is substantial, which can be misleading for users as most people are statistically likely to lose their bets and even get addicted to the game.',
        },
    },
]


def build_base_instructions():
    """Build the base annotation instructions."""
    return """Analyze this image and answer the following questions. Provide your response in JSON format.

IMPORTANT: First determine if the image is spam. For the image to be spam the content should NOT be related to gambling, betting, or similar activities. 
If the image is spam, then you don't have to answer the other questions.

1. Is Spam: Is this image spam/advertising content? (true/false)

IF AND ONLY IF "is_spam" is FALSE, answer the following questions. Otherwise, skip them:

2. Ad Category: Select all that apply from:
   - Sports Betting
   - Fantasy Sports
   - Casino Games
   - Card Games
   - Prediction Games
   - Lottery / Jackpots
   - Trading / Crypto
   - Other (specify)

3. App Name: Identify any of these apps mentioned or shown:
   - Parimatch, Betway, 1xBet, 22Bet, 20Bet, Stake, Junglee Rummy, Aviator, Bet365, 
     Lucky Casino, 91Club, Melbet, Sportsbet_io, Dafabet, PokerStars, Megapari, 
     Roobet, Jackpot City Casino, 1win, BC Game
   - Other (specify)

4. Primary Messaging Strategy: Select all that apply:
   - User Acquisition
   - Promoting a New Feature
   - Celebrity Endorsement
   - Misleading or Deceptive
   - Emotional Appeal
   - Social Proof / Testimonials
   - General Promotion

5. Potentially Harmful Narratives: Select all that apply:
   - Easy Money Narrative
   - Risk Minimization
   - Income Source Framing
   - Addiction Normalization
   - Debt Solution Marketing
   - Success Story Manipulation
   - Time Pressure Tactics
   - Other (specify)

6. Media Authenticity & Manipulation: Select all that apply:
   - Authentic
   - AI-Generated (Synthetic Media)
   - Deepfake (Celebrity)
   - Deepfake (Non-Celebrity)

7. Sexual Content: Does the image contain sexual content? (yes/no)

8. Ad Notes: Write 1-2 sentences describing the image. Write what you think are harmful things in this image for the user. Write any additional information about the image if useful.

---

Here are some examples to guide you:"""


def build_output_format_instructions():
    """Build the output format instructions."""
    return """
---

Now analyze the NEW IMAGE below and provide your annotation.

Respond ONLY with a valid JSON object in this format:

If is_spam is TRUE:
{
  "is_spam": true
}

If is_spam is FALSE:
{
  "is_spam": false,
  "ad_category": ["category1", "category2"],
  "app_name": ["app1", "app2"],
  "primary_messaging_strategy": ["strategy1"],
  "potentially_harmful_narratives": ["narrative1"],
  "media_authenticity": ["type1"],
  "sexual_content": "yes"/"no",
  "ad_notes": "text"
}
"""


def load_existing_results():
    """Load existing results from output file if it exists."""
    if Path(output_file).exists():
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_results(results):
    """Save results to JSON file."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def get_processed_files(results):
    """Get set of already processed file names."""
    return {r["file_name"] for r in results}


def annotate_images():
    """Main annotation function with few-shot prompting and incremental saving."""

    # Load existing results if resuming
    results = load_existing_results()
    processed_files = get_processed_files(results)

    if results:
        print(f"Resuming from previous run. Already processed: {len(results)} images\n")

    image_paths = (
        list(image_folder.glob("*.png"))
        + list(image_folder.glob("*.jpg"))
        + list(image_folder.glob("*.jpeg"))
    )

    # Filter out already processed images
    image_paths = [p for p in image_paths if p.name not in processed_files]

    # Count available examples
    available_examples = 0
    for example in FEW_SHOT_EXAMPLES:
        example_path = examples_folder / example["image_file"]
        if example_path.exists():
            available_examples += 1

    print(f"Found {available_examples} out of {len(FEW_SHOT_EXAMPLES)} example images")
    print(f"Processing {len(image_paths)} remaining images\n")

    if not image_paths:
        print("No new images to process!")
        return

    for idx, image_path in enumerate(tqdm(image_paths, desc="Annotating images"), 1):
        mime_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"

        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            # Build interleaved content with examples
            contents = [build_base_instructions()]

            # Add few-shot examples with their annotations
            examples_added = 0
            for i, example in enumerate(FEW_SHOT_EXAMPLES, 1):
                example_path = examples_folder / example["image_file"]
                if not example_path.exists():
                    continue

                try:
                    with open(example_path, "rb") as f:
                        ex_bytes = f.read()
                    ex_mime = (
                        "image/png"
                        if example_path.suffix.lower() == ".png"
                        else "image/jpeg"
                    )

                    # Add example with clear labeling
                    contents.append(f"\n\nEXAMPLE {i}:")
                    contents.append(
                        types.Part.from_bytes(data=ex_bytes, mime_type=ex_mime)
                    )
                    contents.append(
                        f"\nExpected JSON output:\n{json.dumps(example['annotation'], indent=2)}"
                    )
                    examples_added += 1
                except Exception as e:
                    print(f"\n⚠️  Error loading example {example_path}: {e}")
                    continue

            # Add output format instructions and target image
            contents.append(build_output_format_instructions())
            contents.append(
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            )

            # Make API call
            response = client.models.generate_content(
                model=MODEL,
                contents=contents,
            )

            response_text = response.text.strip()

            # Clean markdown code blocks
            if response_text.startswith("```json"):
                response_text = (
                    response_text.split("```json")[1].split("```")[0].strip()
                )
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()

            annotation_data = json.loads(response_text)

            results.append(
                {
                    "file_name": image_path.name,
                    "file_path": str(image_path),
                    "annotations": annotation_data,
                    "status": "success",
                }
            )

            # Log token usage
            usage = response.usage_metadata
            timestamp_utc = datetime.now(timezone.utc).isoformat()

            token_log_entry = {
                "timestamp_utc": timestamp_utc,
                "file_name": image_path.name,
                "model": MODEL,
                "prompt_tokens": usage.prompt_token_count,
                "output_tokens": usage.candidates_token_count,
                "total_tokens": usage.total_token_count,
                "prompt_tokens_text": next(
                    (
                        d.token_count
                        for d in usage.prompt_tokens_details
                        if d.modality.name == "TEXT"
                    ),
                    None,
                ),
                "prompt_tokens_image": next(
                    (
                        d.token_count
                        for d in usage.prompt_tokens_details
                        if d.modality.name == "IMAGE"
                    ),
                    None,
                ),
                "few_shot_mode": True,
                "num_examples": examples_added,
            }

            with open(token_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(token_log_entry) + "\n")

        except json.JSONDecodeError as e:
            results.append(
                {
                    "file_name": image_path.name,
                    "file_path": str(image_path),
                    "annotations": None,
                    "status": "json_error",
                    "error": str(e),
                    "raw_response": response_text
                    if "response_text" in locals()
                    else None,
                }
            )
            print(f"\n⚠️  JSON error for {image_path.name}: {e}")

        except Exception as e:
            results.append(
                {
                    "file_name": image_path.name,
                    "file_path": str(image_path),
                    "annotations": None,
                    "status": "error",
                    "error": str(e),
                }
            )
            print(f"\n⚠️  Error processing {image_path.name}: {e}")

        # Save results every SAVE_INTERVAL images
        if idx % SAVE_INTERVAL == 0:
            save_results(results)
            print(f"\nProgress saved: {len(results)} images processed")

    # Final save
    save_results(results)

    # Print summary
    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - successful

    print(f"\n{'=' * 50}")
    print(f"✓ Annotations saved to {output_file}")
    print(f"✓ Token logs saved to {token_log_file}")
    print("\nSummary:")
    print(f"  Total images: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")

    if failed > 0:
        print("\nFailed images:")
        for r in results:
            if r["status"] != "success":
                print(f"  - {r['file_name']}: {r['status']}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    annotate_images()
