# Quantifying the Illicit Ecosystem of Betting Apps in India

Online betting and gambling apps in India have expanded rapidly, alongside growing concern about financial loss, debt stress, and addictive use patterns. Yet the ecosystem is difficult to quantify because recruitment and harm are observed in different places: users are often acquired through social media promotion, while harms become visible later inside apps and in user complaints. We address this measurement gap with a mixed-method, multi-source study that links promotion to downstream experience. We compile three complementary datasets. First, we collect and analyze tens of thousands of betting-related advertisements from Meta’s Ad Library using an extensive keyword strategy to measure scale and characterize persuasive frames. Second, we gather a purposive sample of organic Instagram posts from ten betting-linked hashtags to study how similar narratives circulate outside formal advertising, including through surrogate sports pages and influencer-style content. Third, we analyze over 300{,}000 Google Play reviews for a set of betting apps, using topic modeling to extract recurring user-reported problems that reflect a harm surface including financial loss, withdrawal friction, and customer support failure. We connect these layers by constructing a shared narrative codebook for paid and organic promotion and mapping those recruitment narratives to review topics. Across sources, we find a consistent mismatch between what is promised at recruitment and what users report after adoption. Paid ads frequently frame betting as simple, quick, and highly winnable, while reviews repeatedly describe difficulty winning, blocked or delayed withdrawals, unclear rules, and perceived extractive design. Organic promotion often uses more coded and informal presentation than official ads, potentially reducing detectability while funneling users toward the same apps and referral pathways. Together, these results provide one of the first large-scale, cross-source measurements of India’s online betting promotion ecosystem and its associated user-reported harms, and they offer a general approach for studying how potentially harmful digital services sustain growth through mainstream platforms even under evolving regulation.

## Project Structure

- `data/`: Contains the datasets used in the study (Meta ads, Instagram posts, Google Play Store reviews). All data is publicly available, except for media items from Meta Ads. Access to these can be requested by contacting us at [aatmanvaidya@gmail.com](mailto:aatmanvaidya@gmail.com).
- `data collection/`: Scripts and notebooks for collecting/scraping data from various sources.
- `data analysis/`: Code for analyzing the collected data, including topic modeling, qualitative annotation and few-shot classification.
- `pyproject.toml`: Project metadata and dependencies.

## Getting Started

### Prerequisites

This project uses [uv](https://github.com/astral-sh/uv) for Python package management.

### Installing uv

You can install `uv` with the following command:

```bash
pip install uv
```

For other installation methods, please refer to the [official documentation](https://github.com/astral-sh/uv#installation).

### Setup and Installation

This command will create a virtual environment and install all necessary dependencies as specified in `pyproject.toml`.

```bash
uv venv
source .venv/bin/activate
uv sync
```

## Usage

Refer to the `README.md` files in `data collection/` and `data analysis/` for specific instructions on how to run the data gathering and analysis pipelines.
