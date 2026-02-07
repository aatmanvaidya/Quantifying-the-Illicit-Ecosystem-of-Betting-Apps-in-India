# Data Analysis

This directory contains tools and scripts for analyzing the collected datasets.

## Modules

### 1. Annotation UI (`annotation ui/`)
A custom web-based interface for manual annotation and validation of the collected data.
- `server.py`: A FastAPI server that serves the UI and handles data persistence.
- `index.html`, `gallery.html`, `validate_gemini.html`: Frontend components for different annotation tasks.

### 2. Few-Shot Classification (`few shot classification/`)
Scripts for automated classification of recruitment narratives and user-reported harms.
- `classify.py`: Implements few-shot classification using Gemini to categorize ads and reviews.

### 3. Topic Modeling (`topic modelling/`)
Analysis of user reviews to identify recurring themes and harm surfaces.
- `bert_topic_modelling.ipynb`: Uses BERTopic to extract topics from the Google Play Store reviews.