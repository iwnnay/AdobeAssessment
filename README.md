# Campaign Image Generation App

## Overview
This application generates campaign ideas and images for social media marketing campaigns using CrewAI and Google Gemini AI. It takes a campaign brief and automatically generates professional marketing images in multiple aspect ratios with AI-powered branding analysis and future campaign recommendations.

## Requirements
- **Python 3.12** (tested and verified)
  - **Note**: This application will NOT work with Python 3.15 or newer
- Google Gemini API key
- Dependencies listed in `requirements.txt`

## Setup

[![Watch the video](./setup.png)](https://youtu.be/ojfHK_pGCI0)

### Configure API Key
Copy the example environment file and add your Gemini API key:

```bash
cp .env.example .env
```

Edit `.env` and replace `your_gemini_api_key_here` with your actual Gemini API key:

```
GEMINI_API_KEY=your_actual_api_key_here
```

## Running the Application

You have two options to run the application:

### Option 1: Docker (Recommended)

```bash
docker compose up -d
```

Then visit [http://localhost:8501](http://localhost:8501) in your browser.

To stop the application:
```bash
docker compose down
```

### Option 2: Local Development

Install dependencies using `uv`:

```bash
uv pip install -r requirements.txt
```

Run the Streamlit application:

```bash
uv run streamlit run streamlit_app.py
```

The application will open in your browser at [http://localhost:8501](http://localhost:8501)

## Usage

### Add Your Logo
Place your company logo at `inputs/logo.png`. This logo will be incorporated into all generated campaign images. Note that the Keurig logo is the example logo used in this application. If you wonder why everything is Keurig related, it's because this file needs to be swapped out.

1. **Create a Campaign**: Enter campaign details including (manually in the web app or in a JSON file):
   - Campaign name
   - At least 2 products (comma-separated)
   - Target region/market
   - Target audience
   - Campaign message

2. **Generate Images**: The AI will:
   - Analyze your brand and logo
   - Research your target market
   - Translate your message to the target language
   - Generate 3 images (1:1, 9:16, 16:9 aspect ratios)
   - Evaluate each image for brand compliance
   - Suggest future campaign ideas

3. **Review Results**: View generated images, branding reports, and future campaign recommendations

## Project Structure

- `streamlit_app.py` - Main Streamlit web application
- `src/flows/` - CrewAI agents and workflow orchestration
- `src/models.py` - Pydantic data models
- `src/database.py` - Simple JSON file-based database
- `inputs/logo.png` - Your company logo (you provide this)
- `storage/` - Generated campaign images and data
- `database.json` - Campaign database

## Campaign Brief Format (JSON)

```json
{
  "name": "Summer Campaign",
  "products": ["Product A", "Product B"],
  "target_region": "US",
  "target_audience": "Young professionals",
  "campaign_message": "Elevate your summer experience"
}
```

## Outputs

Generated images are saved in: `storage/campaign{ID}/`
- `1x1.png` - Square format (1:1)
- `9x16.png` - Vertical format (9:16)
- `16x9.png` - Horizontal format (16:9)

Each image includes a branding report evaluating logo inclusion and brand alignment.
