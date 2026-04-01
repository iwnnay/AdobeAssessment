import json
import os
import io
import sys
from typing import List, Optional, Dict

# Enforce Python version requirement early
if sys.version_info < (3, 12):
    raise SystemExit(
        f"Python 3.12+ is required to run this app. Detected: {sys.version.split()[0]}.\n"
        "Please upgrade your Python interpreter to 3.12 or newer."
    )

import streamlit as st

from models import Campaign
from database import Database
from utils import slugify, save_uploaded_images
from generator import ImageGenerator


# ---------------------- Frontend (Streamlit) ----------------------

st.set_page_config(page_title="Campaign Generator", layout="wide")

db = Database()
generator = ImageGenerator()


def create_campaign_from_form(name: str, products_csv: str, region: str, audience: str, message: str) -> Campaign:
    products = [p.strip() for p in products_csv.split(",") if p.strip()]
    new_id = db.next_id()
    campaign = Campaign(
        id=new_id,
        name=name.strip(),
        products=products,
        target_region=region.strip(),
        target_audience=audience.strip(),
        campaign_message=message.strip(),
    )
    return campaign


def create_campaign_from_brief(brief: Dict) -> Campaign:
    new_id = db.next_id()
    campaign = Campaign(
        id=new_id,
        name=brief.get("name") or f"Campaign {new_id}",
        products=brief["products"],
        target_region=brief["target_region"],
        target_audience=brief["target_audience"],
        campaign_message=brief["campaign_message"],
        language=brief.get("language", "US_en"),
    )
    return campaign


def show_campaign(campaign: Campaign):
    col_left, col_right = st.columns([4, 1])
    with col_left:
        st.markdown(f"## {campaign.name}")
        st.write(
            {
                "Products": campaign.products,
                "Region": campaign.target_region,
                "Audience": campaign.target_audience,
                "Message": campaign.campaign_message,
                "Language": campaign.language,
            }
        )
    with col_right:
        # Shareable link
        share_key = f"{slugify(campaign.name)}-{campaign.id}"
        st.text_input("Share link", value=f"?c={share_key}", help="Copy and share this suffix.")
        # Approval toggle
        color = "green" if campaign.approved else "red"
        label = "Approved" if campaign.approved else "Needs Approval"
        if st.button(label, type="secondary"):
            campaign.approved = not campaign.approved
            db.update(campaign)
            st.experimental_rerun()

    # Images grid
    st.markdown("### Images")
    imgs = campaign.generatedImages + campaign.initialImages
    if imgs:
        cols = st.columns(3)
        for i, rec in enumerate(sorted(imgs, key=lambda r: r.aspectRatio)):
            with cols[i % 3]:
                try:
                    st.image(os.path.abspath(rec.path), caption=f"{rec.aspectRatio}")
                except Exception:
                    st.write(rec.path)
    else:
        st.info("No images yet.")

    st.markdown("### Branding Report")
    st.write(campaign.brandingReport or "No report yet.")

    st.markdown("### Future Campaigns")
    st.write(campaign.futureCampaigns or "No plans yet.")

    with st.expander("Branding Details"):
        st.write(campaign.brandingDetails or "-")
    with st.expander("Marketing Details"):
        st.write(campaign.marketingDetails or "-")


def run_generation_flow(campaign: Campaign, uploaded_images: List[io.BytesIO]) -> Campaign:
    # persist initial record first
    db.add(campaign)
    # save images
    saved = save_uploaded_images(campaign.id, uploaded_images)
    campaign.initialImages = saved
    # Execute the complete CrewAI flow (all steps: extraction, generation, evaluation)
    campaign = generator.process_campaign(campaign)
    db.update(campaign)
    return campaign


def sidebar_nav() -> Optional[int]:
    st.sidebar.markdown("## Navigation")
    # Create new campaign shortcut
    if st.sidebar.button("Generate Campaign +"):
        st.session_state["page"] = "new"
    # Existing campaigns
    st.sidebar.markdown("### Previously Generated")
    for c in db.all():
        if st.sidebar.button(c.name, key=f"nav_{c.id}"):
            st.session_state["page"] = f"view:{c.id}"
    # Handle share link param
    qp = st.query_params
    if "c" in qp:
        key = qp["c"][0]
        try:
            cid = int(key.split("-")[-1])
            st.session_state["page"] = f"view:{cid}"
        except Exception:
            pass
    return None


def page_new_campaign():
    new_id = db.next_id()
    st.markdown("## Generate Campaign")
    st.text_input("Campaign Name", value=f"Campaign {new_id}")

    # Toggle between file upload and manual form
    use_upload = st.checkbox("Upload brief (JSON)?", value=True)

    uploaded_images = st.file_uploader(
        "Upload images (optional)", type=["png", "jpg", "jpeg"], accept_multiple_files=True
    )

    error_msgs = {}
    campaign: Optional[Campaign] = None

    if use_upload:
        uploaded_brief = st.file_uploader("Brief file (JSON only)", type=["json"], accept_multiple_files=False)
        if uploaded_brief is not None:
            try:
                data = uploaded_brief.read()
                text = data.decode("utf-8")
                brief = json.loads(text)
                if "name" not in brief:
                    brief["name"] = os.path.splitext(uploaded_brief.name)[0]
                campaign = create_campaign_from_brief(brief)
            except Exception as e:
                st.error(f"Failed to parse brief: {e}")
    else:
        with st.form("manual_form"):
            products = st.text_input("Products (comma-separated)", value="")
            region = st.text_input("Target Region/Market", value="")
            audience = st.text_input("Target Audience", value="")
            message = st.text_input("Campaign Message", value="")

            submitted = st.form_submit_button("Generate Campaign")
            if submitted:
                # validations
                if not name.strip():
                    error_msgs["name"] = "Name is required"
                prod_list = [p.strip() for p in products.split(",") if p.strip()]
                if len(set(prod_list)) < 2:
                    error_msgs["products"] = "Please enter at least two different products"
                if not region.strip():
                    error_msgs["region"] = "Region is required"
                if not audience.strip():
                    error_msgs["audience"] = "Audience is required"
                if not message.strip():
                    error_msgs["message"] = "Message is required"

                if error_msgs:
                    for k, v in error_msgs.items():
                        st.warning(f"{k}: {v}")
                else:
                    campaign = create_campaign_from_form(name, products, region, audience, message)

    # Separate generate button when using upload path
    if use_upload:
        if st.button("Generate Campaign"):
            if campaign is None:
                st.warning("Please provide a valid brief file first.")
            else:
                with st.spinner("Generating..."):
                    files = [io.BytesIO(f.read()) for f in uploaded_images] if uploaded_images else []
                    campaign = run_generation_flow(campaign, files)
                st.success("Campaign generated!")
                st.session_state["page"] = f"view:{campaign.id}"
                st.experimental_rerun()
    else:
        # Manual form handles its own submit
        if campaign is not None and not error_msgs:
            with st.spinner("Generating..."):
                files = [io.BytesIO(f.read()) for f in uploaded_images] if uploaded_images else []
                campaign = run_generation_flow(campaign, files)
            st.success("Campaign generated!")
            st.session_state["page"] = f"view:{campaign.id}"
            st.experimental_rerun()


def page_view_campaign(cid: int):
    campaign = db.get(cid)
    if not campaign:
        st.error("Campaign not found")
        return
    show_campaign(campaign)


def main():
    sidebar_nav()
    page = st.session_state.get("page", "new")
    if page == "new":
        page_new_campaign()
    elif page.startswith("view:"):
        try:
            cid = int(page.split(":")[1])
            page_view_campaign(cid)
        except Exception:
            page_new_campaign()
    else:
        page_new_campaign()


if __name__ == "__main__":
    main()
