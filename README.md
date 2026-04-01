Creative Automation Pipeline (PoC)

Overview
This is a lightweight proof-of-concept that automates creative asset generation for social ad campaigns. It reads a campaign brief, reuses input assets when available, generates missing assets, overlays the campaign message, and exports creatives for multiple aspect ratios organized by product.

Note on AI/agents: The intended backend is an agentic flow orchestrated with CrewAI using Google Gemini Pro for logo extraction and image generation. In this PoC, those calls are stubbed locally. The logo is not composited with Pillow; instead, its path would be provided to the image generation call.

Key Features
- Accepts a campaign brief (JSON only) with: products (>=2), target region, audience, and campaign message.
- Reuses assets from a local assets directory if present (e.g., Coffee Pods.png).
- Generates placeholder hero images when assets are missing (uses brand colors + gradient).
- Produces creatives for multiple aspect ratios: 1:1, 9:16, 16:9.
- Displays the campaign message on final images (English; localized support can be added via the brief).
- Organizes outputs by product and aspect ratio.
- Bonus (basic):
  - Brand compliance checks: detects if logo was present and notes brand color usage.
  - Simple legal content checks: flags prohibited words (e.g., “guaranteed”, “cure”, “free beer”).
  - JSON report summarizing generated assets and checks.

Requirements
- Python 3.12+
- Dependencies listed in requirements.txt

Install
1. (Optional) Create and activate a virtual environment.
2. Install dependencies:
   pip install -r requirements.txt

Project Layout
- main.py — CLI entry point and pipeline implementation.
- streamlit_app.py — Streamlit frontend for editing campaigns, CRUD, generation, and preview.
- campaign.json — Example campaign brief.
- campaigns/ — (Optional) Folder where additional campaign JSON files are stored/managed by the UI.
- assets/ — Place optional input assets here (created automatically on first run if missing).
  - Example filenames it will look for per product: Coffee Pods.png, Coffee Pods.jpg, Coffee Pods.jpeg
  - Optional logo file name: logo.png (or .jpg/.jpeg). If present, its path is passed to the image generation step (e.g., Gemini Pro). It is not composited locally by Pillow.
- images/ — Generated creatives organized by campaign and aspect ratio (created on run).

Usage
Basic run (uses campaign.json in project root):
  python main.py --brief campaign.json --assets-dir assets --out-dir outputs --ratios "1:1,9:16,16:9"

Quick start (Streamlit UI in your browser)
1. Install dependencies (once):
   pip install -r requirements.txt
2. From the project root, launch the UI:
   streamlit run streamlit_app.py
   - This typically opens your default browser automatically. If it doesn't, open:
     http://localhost:8501
3. Alternative launch (if streamlit isn’t on PATH):
   python -m streamlit run streamlit_app.py
4. Change the port (if 8501 is busy):
   streamlit run streamlit_app.py --server.port 8502

Interactive UI (Streamlit):
  streamlit run streamlit_app.py

What the UI provides:
- Edit the campaign brief via a form (products, region, audience, message).
- Choose aspect ratios, assets directory, and output directory.
- Basic CRUD over campaigns: create new, duplicate, delete. Files are saved under campaigns/ (plus the default campaign.json in root).
- Generate or regenerate creatives and preview the resulting images inline.

Hugging Face image generation (optional)
- You can use the Hugging Face Inference API to generate higher-quality base images when local assets are missing.
- This is available both via CLI flags and in the Streamlit UI (toggle in the form).

Setup a Hugging Face token
1. Create a free account at https://huggingface.co (if you don't have one).
2. Create an access token at https://huggingface.co/settings/tokens (read access is enough for public models).
3. Set the token in your environment (recommended) so the app can pick it up:
   - Windows PowerShell:
     setx HUGGINGFACEHUB_API_TOKEN "<YOUR_TOKEN>"
     (Then open a new terminal so the variable is available.)
   - macOS/Linux (bash/zsh):
     export HUGGINGFACEHUB_API_TOKEN="<YOUR_TOKEN>"

CLI usage with Hugging Face
- Example using Stable Diffusion 2.1 (falls back to local placeholder on any HF error):
  python main.py --brief campaign.json --assets-dir assets --out-dir outputs --ratios "1:1,9:16,16:9" \
    --use-hf --hf-model-id stabilityai/stable-diffusion-2-1 --hf-num-steps 30 --hf-guidance 7.5
- You may also pass the token explicitly (env var preferred):
  python main.py --use-hf --hf-token YOUR_TOKEN_HERE
- Other useful flags:
  --hf-negative-prompt "blurry, low quality" --hf-seed 123

Streamlit UI usage with Hugging Face
1. Launch the UI: streamlit run streamlit_app.py
2. In the form, expand the "Hugging Face (optional)" section.
3. Enable "Use Hugging Face Inference API" and choose a model (e.g., stabilityai/stable-diffusion-2-1 or stabilityai/sdxl-turbo).
4. Enter your token (or rely on the HUGGINGFACEHUB_API_TOKEN env var), then click Generate Images.
5. The pipeline will try HF first (when no local product image exists); on failure it falls back to a branded placeholder.

Arguments
- --brief        Path to campaign brief (JSON). Default: campaign.json
- --assets-dir   Input assets directory. Default: assets
- --out-dir      Output directory. Default: outputs
- --ratios       Comma-separated list of aspect ratios (supported: 1:1,9:16,16:9). Default: 1:1,9:16,16:9

Campaign Brief Format (JSON example)
{
  "products": ["Coffee Pods", "Cold Brew Bottle"],
  "target_region": "US",
  "target_audience": "Busy young professionals",
  "campaign_message": "Fuel your day with bold flavor."
}

Note: YAML is not supported. Use JSON only for campaign briefs.

Outputs
When using the Streamlit app provided in this repo, generated creatives are saved per campaign in the following structure: images/campaign{campaignId}/{ratio}.png, where ratio is one of 1x1, 9x16, 16x9. For example: images/campaign3/1x1.png. This matches the requested layout.

Example Output Tree (abbreviated)
images/
  campaign1/
    1x1.png
    9x16.png
    16x9.png
  campaign2/
    1x1.png
    9x16.png
    16x9.png

Design Decisions
- Simplicity: A single Python script (main.py) provides a clear, minimal PoC without external services.
- Placeholder generation: When assets are missing, the app can either call the Hugging Face Inference API to generate a product hero image (if enabled), or locally generate a gradient placeholder with brand colors.
- Brand checks: Lightweight, focusing on detectable items locally (logo presence and brand palette usage assumed by generator).
- Legal checks: String-based term flags for demo purposes only (not a substitute for legal review).
- Extensibility: The find_or_generate_base_asset function can be extended to call an external GenAI image API when desired.

Assumptions & Limitations
- Fonts: Uses Pillow’s default font to avoid OS-specific font path issues.
- Localization: Only English text is rendered by default. Localization can be added by augmenting the brief per locale.
- Asset matching: Product-to-file match is based on exact product name + common file extensions in the assets directory.
- Brand rules: Simplified; in real scenarios, enforce specific typography, safe areas, contrast ratios, etc.
- Legal rules: Very limited keyword checks—intended only to demonstrate the concept.

Demo Tips (for recording)
1. Show the campaign.json or create a new campaign in the UI.
2. (Optional) Place a logo.png into assets/ to demonstrate brand detection.
3. Run the CLI (see command above) or the UI (streamlit run streamlit_app.py).
4. In the UI, click Generate Images to produce creatives, and preview them directly in the browser.
5. Alternatively, open the outputs/ directory and preview generated images and report.json.

Troubleshooting
- If you see an error about PIL/Pillow not found, ensure you ran: pip install -r requirements.txt
 - If Streamlit isn’t found, install requirements (streamlit is included): pip install -r requirements.txt
  - If the browser doesn’t open automatically, copy the local URL shown in the terminal (e.g., http://localhost:8501) and paste it into your browser.
  - If you see “port already in use,” run with a different port, e.g.: streamlit run streamlit_app.py --server.port 8502
  - On first run, Windows may prompt for firewall permission; allow access so your browser can connect to the local app.
  - If Hugging Face generation fails: ensure your token is valid, the model id exists and is public/you have access, and try fewer steps. The app will automatically fall back to local placeholder generation so your run still completes.

License
This PoC is provided for interview/demo purposes.
