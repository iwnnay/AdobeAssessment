import os
import json
from typing import Dict, List

import streamlit as st

from main import (
    ASPECT_RATIOS,
    generate_creatives,
)


APP_TITLE = "Creative Automation Pipeline — Streamlit UI"
DEFAULT_CAMPAIGN_FILE = "campaign.json"
CAMPAIGNS_DIR = "campaigns"


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def list_campaign_files() -> List[str]:
    files: List[str] = []
    # Include default root campaign file if present
    if os.path.isfile(DEFAULT_CAMPAIGN_FILE):
        files.append(DEFAULT_CAMPAIGN_FILE)
    # Include campaigns directory files
    if os.path.isdir(CAMPAIGNS_DIR):
        for name in sorted(os.listdir(CAMPAIGNS_DIR)):
            if name.lower().endswith((".json", ".yaml", ".yml")):
                files.append(os.path.join(CAMPAIGNS_DIR, name))
    return files


def read_campaign(path: str) -> Dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Fall back to a sensible blank
        return {
            "products": ["Coffee Pods", "Cold Brew Bottle"],
            "target_region": "US",
            "target_audience": "Busy young professionals",
            "campaign_message": "Fuel your day with bold flavor.",
        }


def write_campaign(path: str, data: Dict) -> None:
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def display_generated_images(report: Dict):
    st.subheader("Generated Creatives")
    products = report.get("products", {})
    if not products:
        st.info("No creatives generated yet. Use the Generate button above.")
        return
    for product, entries in products.items():
        st.markdown(f"#### {product}")
        # Group by ratio for consistent display
        by_ratio = {}
        for e in entries:
            by_ratio.setdefault(e.get("ratio", ""), []).append(e)
        cols = st.columns(max(1, min(3, len(by_ratio))))
        idx = 0
        for ratio, items in by_ratio.items():
            with cols[idx % len(cols)]:
                st.caption(f"Aspect {ratio}")
                for it in items:
                    p = it.get("path")
                    if p and os.path.isfile(p):
                        st.image(p, use_column_width=True)
            idx += 1


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)

    # Sidebar: Campaign selection & CRUD
    with st.sidebar:
        st.header("Campaigns")
        ensure_dir(CAMPAIGNS_DIR)
        campaign_files = list_campaign_files()
        if not campaign_files:
            # Seed default file if nothing exists
            default_data = read_campaign(DEFAULT_CAMPAIGN_FILE)
            write_campaign(DEFAULT_CAMPAIGN_FILE, default_data)
            campaign_files = list_campaign_files()

        selected_path = st.selectbox("Select campaign", options=campaign_files, index=0)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            new_name = st.text_input("New name", value="new_campaign")
            if st.button("New"):
                fname = new_name.strip()
                if not fname:
                    st.warning("Enter a name for the new campaign.")
                else:
                    if not fname.lower().endswith(".json"):
                        fname += ".json"
                    new_path = os.path.join(CAMPAIGNS_DIR, fname)
                    if os.path.exists(new_path):
                        st.error("A campaign with that name already exists.")
                    else:
                        write_campaign(new_path, read_campaign(DEFAULT_CAMPAIGN_FILE))
                        st.success(f"Created {new_path}")
                        st.rerun()
        with col_b:
            if st.button("Duplicate"):
                base = os.path.basename(selected_path)
                name, ext = os.path.splitext(base)
                dup_name = f"{name}_copy{ext or '.json'}"
                dup_path = os.path.join(CAMPAIGNS_DIR, dup_name)
                data = read_campaign(selected_path)
                write_campaign(dup_path, data)
                st.success(f"Duplicated to {dup_path}")
                st.rerun()
        with col_c:
            if st.button("Delete"):
                try:
                    os.remove(selected_path)
                    st.success(f"Deleted {selected_path}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete: {e}")

    # Load selected campaign data
    brief = read_campaign(selected_path)

    # Main form for editing the brief
    with st.form("campaign_form"):
        st.subheader("Campaign Brief")
        products_text = st.text_area(
            "Products (one per line)",
            value="\n".join(brief.get("products") or []),
            height=120,
        )
        col1, col2 = st.columns(2)
        with col1:
            target_region = st.text_input("Target Region", value=brief.get("target_region", ""))
        with col2:
            target_audience = st.text_input("Target Audience", value=brief.get("target_audience", ""))
        campaign_message = st.text_area("Campaign Message", value=brief.get("campaign_message", ""), height=80)

        st.subheader("Generation Settings")
        supported = list(ASPECT_RATIOS.keys())
        default_ratios = brief.get("ratios") or supported
        ratios = st.multiselect("Aspect Ratios", options=supported, default=default_ratios)

        col3, col4 = st.columns(2)
        with col3:
            assets_dir = st.text_input("Assets Directory", value=brief.get("assets_dir", "assets"))
        with col4:
            out_dir = st.text_input("Output Directory", value=brief.get("out_dir", "outputs"))

        save_clicked = st.form_submit_button("Save Campaign")

    # Persist changes if requested
    products = [p.strip() for p in (products_text or "").splitlines() if p.strip()]
    updated_brief = {
        "products": products,
        "target_region": target_region,
        "target_audience": target_audience,
        "campaign_message": campaign_message,
        "ratios": ratios,
        "assets_dir": assets_dir,
        "out_dir": out_dir,
    }
    if save_clicked:
        write_campaign(selected_path, updated_brief)
        st.success("Campaign saved.")

    # Action buttons (Generate / Regenerate)
    gen_col1, gen_col2 = st.columns([1, 1])
    with gen_col1:
        gen_clicked = st.button("Generate Images", type="primary")
    with gen_col2:
        regen_clicked = st.button("Regenerate Images")

    # Keep a report in session state to display without re-reading files
    if "last_report" not in st.session_state:
        st.session_state["last_report"] = None

    if gen_clicked or regen_clicked:
        # Use the generation pipeline
        try:
            report = generate_creatives(
                {
                    "products": products,
                    "target_region": target_region,
                    "target_audience": target_audience,
                    "campaign_message": campaign_message,
                },
                assets_dir=assets_dir,
                out_dir=out_dir,
                ratios=ratios or list(ASPECT_RATIOS.keys()),
            )
            st.session_state["last_report"] = report
            st.success("Generation complete.")
        except Exception as e:
            st.error(f"Generation failed: {e}")

    # Display images from the latest report (from this session) or attempt to load from disk
    if st.session_state.get("last_report"):
        display_generated_images(st.session_state["last_report"])
    else:
        # If an outputs/report.json exists in chosen out_dir, try loading it
        report_path = os.path.join(out_dir, "report.json")
        if os.path.isfile(report_path):
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    display_generated_images(json.load(f))
            except Exception:
                st.info("No recent generation report to display.")


if __name__ == "__main__":
    main()
