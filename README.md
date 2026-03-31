Creative Automation Pipeline (PoC)

Overview
This is a lightweight proof-of-concept that automates creative asset generation for social ad campaigns. It reads a campaign brief, reuses input assets when available, generates missing assets, overlays the campaign message, and exports creatives for multiple aspect ratios organized by product.

Key Features
- Accepts a campaign brief (JSON or YAML) with: products (>=2), target region, audience, and campaign message.
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
- Python 3.8+
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
  - Optional logo file name: logo.png (or .jpg/.jpeg). If present, it will be overlaid automatically.
- outputs/ — Generated creatives and report (created on run).

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

Arguments
- --brief        Path to campaign brief (JSON or YAML). Default: campaign.json
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

YAML is also supported if PyYAML is installed (it is included in requirements.txt on Python 3.8+).

Outputs
On successful run, outputs/ will contain one folder per product, and inside that, one folder per aspect ratio (e.g., 1x1, 9x16, 16x9). A report.json file is also written at outputs/report.json summarizing generated files, brand checks, and legal flags.

Example Output Tree (abbreviated)
outputs/
  report.json
  coffee_pods/
    1x1/
      coffee_pods_1x1.png
    9x16/
      coffee_pods_9x16.png
    16x9/
      coffee_pods_16x9.png
  cold_brew_bottle/
    1x1/
      cold_brew_bottle_1x1.png
    ...

Design Decisions
- Simplicity: A single Python script (main.py) provides a clear, minimal PoC without external services.
- Placeholder generation: When assets are missing, Pillow generates gradient backgrounds with brand colors, ensuring consistent visual identity.
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
- If brief parsing fails and you’re using YAML, ensure PyYAML is installed (it is in requirements.txt) and the file is valid YAML.
 - If Streamlit isn’t found, install requirements (streamlit is included): pip install -r requirements.txt
 - If the browser doesn’t open automatically, copy the local URL shown in the terminal (e.g., http://localhost:8501) and paste it into your browser.
 - If you see “port already in use,” run with a different port, e.g.: streamlit run streamlit_app.py --server.port 8502
 - On first run, Windows may prompt for firewall permission; allow access so your browser can connect to the local app.

License
This PoC is provided for interview/demo purposes.
