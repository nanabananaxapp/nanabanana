import streamlit as st
import fal_client
import os
import tempfile
import json
import datetime
import base64
from io import BytesIO
from urllib.request import urlopen
import boto3
from botocore.exceptions import ClientError
import requests # ADDED: Required for robust R2/URL handling by existing upload_file_to_r2 function
from PIL import Image # ADDED: Required for robust thumbnail handling by existing display_image_uploader_with_thumbnail function

# --- Constants and Configuration ---
# CRITICAL: Re-checked from user's expected parameters
# CRITICAL: Streamlit File ID for the user's uploaded logo file
UPLOADED_LOGO_ID = "uploaded:Clipboard01.jpg-e0b3072d-9dd7-4283-81d8-bb2162171654" 

# FAL Models
SDXL_MODEL = "fal-ai/stable-diffusion-xl-lightning"
SDXL_I2I_MODEL = "fal-ai/stable-diffusion-xl-lightning-sdedit"

# Comprehensive Negative Prompt
DEFAULT_NEGATIVE_PROMPT = "bright colors, overexposed, static, blurred details, subtitles, style, artwork, painting, picture, still, overall gray, worst quality, low quality, JPEG compression compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, malformed limbs, fused fingers, still picture, cluttered background, three legs, many people in the background, walking backwards"


# --- App Configuration and Styling (Professional Dark Theme) ---
st.set_page_config(
    page_title="NANO BANANA X AI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a dark, professional look
st.markdown("""
<style>
    /* Hide Streamlit UI elements */
    [data-testid="stToolbar"], #MainMenu, #GithubIcon, header {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }

    /* Color Palette Variables */
    :root {
        --primary-color: #4169E1; /* Royal Blue */
        --secondary-color: #FFD700; /* Gold */
        --background-color: #121212; /* Very dark background */
        --card-background: #1e1e1e; /* Slightly lighter for containers */
        --text-color: #e0e0e0;
        --border-color: #3a3a3a;
        --success-color: #3CB371; 
        --error-color: #dc3545; 
    }

    /* General App Styling */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* CRITICAL LOGO POSITIONING (TOP LEFT) - FIXED */
    .logo-container {
        position: fixed;
        top: 10px;
        left: 10px; 
        right: auto; 
        width: 100px; 
        height: 100px;
        z-index: 1000;
        border-radius: 8px; 
        overflow: hidden; 
        background-color: var(--background-color);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5); 
    }
    .logo-container img {
        width: 100%;
        height: 100%;
        object-fit: contain;
    }

    /* Card/Container Styling */
    [data-testid*="stVerticalBlock"], [data-testid*="stExpander"] > div:first-child, [data-testid*="stForm"] {
        background-color: var(--card-background);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid var(--border-color);
        margin-bottom: 15px;
    }
    
    /* Button Styles (Refined) */
    .stButton[data-testid="stButton-primary"] > button {
        background-color: var(--primary-color);
        color: #ffffff;
        border-radius: 6px; 
        border: none;
        padding: 12px 20px; 
        font-size: 1.1rem; 
        font-weight: 700; 
        transition: background-color 0.3s;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4);
        max-width: fit-content; 
    }
    .stButton[data-testid="stButton-primary"] > button:hover {
        background-color: #3457c7; 
    }
    /* Disabled primary button style - CRITICAL FOR FEEDBACK */
    .stButton[data-testid="stButton-primary"] > button:disabled {
        background-color: #2a3c74 !important; 
        cursor: not-allowed;
        box-shadow: none;
    }
    
    /* Uploaded Thumbnail Styling */
    .uploaded-thumbnail-wrapper {
        margin-top: 10px;
        margin-bottom: 5px;
        width: 100px !important; 
        height: 100px !important; 
        overflow: hidden;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        display: block !important; 
    }
    .uploaded-thumbnail-wrapper img {
        width: 100px !important; 
        height: 100px !important; 
        object-fit: cover !important; 
        border-radius: 8px !important; 
        display: block !important;
        margin: 0 !important;
    }

</style>
""", unsafe_allow_html=True)


# --- R2/S3 Client Setup (Preserved 1:1) ---
R2_ENDPOINT_URL = os.environ.get('R2_ENDPOINT_URL')
R2_ACCESS_KEY_ID = os.environ.get('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME')

r2_client = None
STAGING_ENABLED = False
try:
    if all([R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME]):
        r2_client = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY
        )
        STAGING_ENABLED = True
except Exception:
    pass 

# --- FAL Client Initialization (Preserved 1:1) ---
fal = None
IS_FAL_READY = False
try:
    fal_key = st.secrets.get("FAL_KEY")
    
    if fal_key:
        fal = fal_client.client(key=fal_key)
        IS_FAL_READY = True
except Exception:
    fal = None
    IS_FAL_READY = False


# --- Session State Initialization (Preserved 1:1) ---
defaults = {
    'prompt': "A hyper-realistic portrait of a golden retriever wearing a banana helmet, 8k cinematic lighting",
    'negative_prompt': DEFAULT_NEGATIVE_PROMPT,
    'image_upload_img_data': None,
    'image_result_urls': [],
    
    # Image Settings 
    'width': 1024,
    'height': 1024,
    'strength': 0.95, 
    'guidance_scale': 4.5, 
    'num_images': 1,
    'num_inference_steps': 50, 
    'enable_safety_checker': False, 
    'remove_index': None, 
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --- Helper Functions (Preserved 1:1) ---
def upload_file_to_r2(content_url, file_extension):
    """Uploads content from a URL to R2 if enabled. Preserved logic."""
    if not STAGING_ENABLED:
        return content_url
    try:
        response = requests.get(content_url)
        response.raise_for_status() 
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        file_key = f"fal_assets/{timestamp}_{os.urandom(4).hex()}{file_extension}"
        content_type = response.headers.get('Content-Type') or (
            'video/mp4' if file_extension == '.mp4' else 'image/jpeg'
        )
        r2_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=file_key,
            Body=response.content,
            ContentType=content_type
        )
        public_url = f"{R2_ENDPOINT_URL}/{R2_BUCKET_NAME}/{file_key}"
        return public_url
    except Exception:
        return content_url

def display_image_uploader_with_thumbnail(session_state_key, label_text):
    """Handles image upload and displays thumbnail. Preserved logic."""
    input_image_url = None
    
    uploaded_file = st.file_uploader(
        label_text, 
        type=["png", "jpg", "jpeg"],
        key=f"uploader_{session_state_key}",
        accept_multiple_files=False
    )
    
    # Sync Session State: Update state only if a new file is uploaded
    if uploaded_file is not None:
        file_data = BytesIO(uploaded_file.getvalue())
        st.session_state[session_state_key] = file_data
    
    current_file_data = st.session_state.get(session_state_key)
    
    if current_file_data is not None:
        try:
            current_file_data.seek(0)
            img_bytes = current_file_data.getvalue()
            
            Image.open(BytesIO(img_bytes)).verify()
            
            # Create base64 URL
            input_image_url = f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode()}"
            
            st.markdown(f"""
                <div class="uploaded-thumbnail-wrapper">
                    <img src="{input_image_url}" alt="Uploaded Thumbnail" />
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f'<p style="font-size: 0.8rem; color: var(--success-color); margin-top: 0px;">Image ready for generation.</p>', unsafe_allow_html=True)

        except Exception:
            st.error("Uploaded file is corrupted or not a valid image. Please re-upload.")
            input_image_url = None 
            st.session_state[session_state_key] = None
        
        if current_file_data is not None:
            current_file_data.seek(0) 

    return input_image_url

def fal_generate_image(prompt, negative_prompt, width, height, num_images, strength, guidance_scale, num_steps, input_image_url=None):
    """Image generation function. Preserved logic."""
    if not IS_FAL_READY:
        st.error("FAL client is not ready. Check FAL_KEY in secrets.")
        return []

    st.toast("Submitting Image Generation Request...", icon="🚀")
    
    model = SDXL_I2I_MODEL if input_image_url else SDXL_MODEL
    
    params = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "num_images": num_images,
        "guidance_scale": guidance_scale,
        "num_inference_steps": num_steps,
        "enable_safety_checker": st.session_state.enable_safety_checker,
        "seed": None
    }
    
    if input_image_url:
        params["image_url"] = input_image_url
        params["strength"] = strength
    
    try:
        handler = fal.submit(model, arguments=params)
        with st.spinner("Processing... waiting for the model to finish."):
            result = handler.get_response(stream=True) 
            
        final_urls = []
        for image_data in result.get('images', []):
            fal_url = image_data['url']
            staged_url = upload_file_to_r2(fal_url, ".jpg")
            final_urls.append(staged_url)
        
        st.toast(f"Generated {len(final_urls)} image(s) successfully!", icon="✅")
        return final_urls

    except Exception:
        st.error("Image generation failed. Ensure your prompt is safe and try again.")
        return []

# --- Main Application Layout ---

# CRITICAL LOGO BLOCK (Top Left)
st.markdown(f"""
<div class="logo-container">
    <img src="{UPLOADED_LOGO_ID}" alt="NANO BANANA X AI Logo"/>
</div>
""", unsafe_allow_html=True)

st.title("NANO BANANA X AI Unified Generator")

# --- Instructions List ---
st.markdown("---")
with st.expander("📝 **PROJECT INSTRUCTIONS & USAGE GUIDE**"):
    st.markdown("""
    This application allows you to generate high-quality images and videos using the FAL AI platform.
    
    ### 🖼️ Image Generation
    1.  **Enter your prompt** (what you want to see).
    2.  Use the **Negative Prompt** field to describe what you *don't* want.
    3.  **Optional:** Upload an image for **Image-to-Image** (I2I) generation. Adjust the **Strength** slider in Advanced Settings to control how much the image changes (lower strength = closer to original image).
    4.  Adjust **Advanced Settings** for resolution, quality, and quantity.
    5.  Click **"✨ Generate Image"** to submit the request.

    ### 🎥 Video Generation
    1.  This feature is **under development** and is currently a placeholder.
    
    ---
    
    ⚠️ **Button Status:** If the "Generate" buttons are **disabled (grayed out)**, the FAL AI key (`FAL_KEY`) is missing from the application environment secrets. **The application requires a valid FAL_KEY set in the environment.**
    """)
st.markdown("---")
# --- END INSTRUCTIONS LIST ---

# NEW: Tab structure added here (THIS IS THE ONLY MODIFICATION TO THE UI FLOW)
tab_image, tab_video = st.tabs(["🖼️ Image Generation (SDXL Lightning)", "🎥 Video Generation (Placeholder)"])


# --------------------------------------------------
# 🖼️ IMAGE GENERATION TAB (Original content wrapped here)
# --------------------------------------------------
with tab_image:
    
    col_input_img, col_output_img = st.columns([1.3, 1.7])

    with col_input_img:
        st.markdown("## Image Input Controls")
        
        # --- Image Upload Section ---
        input_image_url = display_image_uploader_with_thumbnail(
            'image_upload_img_data',
            "Initial image for **Image-to-Image** Generation (Optional)"
        )
        
        st.markdown("---") 
        
        # --- Prompts ---
        st.markdown("### Enter Prompts")

        st.session_state.prompt = st.text_area(
            "Enter your **image prompt**",
            value=st.session_state.prompt,
            height=150,
            key="image_prompt_area"
        )
        
        st.session_state.negative_prompt = st.text_area(
            "Negative Prompt (What to avoid)",
            value=st.session_state.negative_prompt,
            key="image_negative_prompt_area"
        )
        
        # --- GENERATE BUTTON ---
        st.markdown('<div style="margin-top: 20px; margin-bottom: 20px;">', unsafe_allow_html=True)
            
        if st.button(
            "✨ Generate Image", 
            key="generate_image_button", 
            type="primary", 
            disabled=(not IS_FAL_READY) 
        ):
            if st.session_state.prompt:
                st.session_state.image_result_urls = fal_generate_image(
                    st.session_state.prompt, 
                    st.session_state.negative_prompt, 
                    st.session_state.width, 
                    st.session_state.height, 
                    st.session_state.num_images, 
                    st.session_state.strength, 
                    st.session_state.guidance_scale, 
                    st.session_state.num_inference_steps, 
                    input_image_url
                )
            else:
                st.toast("ENTER A PROMPT.", icon="✍️") 

        if not IS_FAL_READY:
            # FATAL ERROR message restored
            st.error("**FATAL ERROR: FAL AI Key is MISSING or INVALID.** Please check the FAL_KEY secret as per the instructions above. The button is currently disabled.")

        st.markdown('</div>', unsafe_allow_html=True) 


        # --- Advanced Settings Expander ---
        with st.expander("⚙️ Advanced Settings"):
            st.markdown("Customize how the model generates your image.")
            
            resolution_options = {
                "512x512": (512, 512),
                "768x768": (768, 768),
                "1024x1024 (Default)": (1024, 1024),
                "2048x2048 (2K)": (2048, 2048),
                "4096x4096 (4K)": (4096, 4096),
            }
            # Handle index setting based on current state, defaulting to 1024x1024
            current_res_key = next((k for k, v in resolution_options.items() if v == (st.session_state.width, st.session_state.height)), "1024x1024 (Default)")
            
            selected_resolution = st.selectbox("Select Resolution", list(resolution_options.keys()), index=list(resolution_options.keys()).index(current_res_key))
            st.session_state.width, st.session_state.height = resolution_options[selected_resolution]

            st.session_state.strength = st.slider("Strength (I2I only: 1.0=Full Change, 0.0=Original)", min_value=0.0, max_value=1.0, value=st.session_state.strength, step=0.01)
            st.session_state.guidance_scale = st.slider("Guidance Scale (CFG: How closely to follow prompt)", min_value=1.0, max_value=15.0, value=st.session_state.guidance_scale, step=0.1)
            st.session_state.num_images = st.slider("Number of Images to Generate", min_value=1, max_value=4, value=st.session_state.num_images)
            st.session_state.num_inference_steps = st.slider("Inference Steps (Higher=Better quality, Slower)", min_value=10, max_value=100, value=st.session_state.num_inference_steps, step=5)
            st.session_state.enable_safety_checker = st.checkbox("Enable Safety Filter", value=st.session_state.enable_safety_checker)
            

    # --- Output Gallery (Right Column) ---
    with col_output_img:
        st.markdown("## Generated Images Gallery")
        
        # --- Image Removal Logic ---
        if st.session_state.remove_index is not None:
            if 0 <= st.session_state.remove_index < len(st.session_state.image_result_urls):
                st.session_state.image_result_urls.pop(st.session_state.remove_index)
            st.session_state.remove_index = None 
            st.rerun() 

        # --- Gallery Display ---
        if st.session_state.image_result_urls:
            cols = st.columns(3) 
            
            for i, url in enumerate(st.session_state.image_result_urls):
                with cols[i % 3]: 
                    st.markdown('<div class="generated-image-result">', unsafe_allow_html=True)
                    st.image(url, use_column_width=False) 
                    
                    st.markdown(f'<a href="{url}" target="_blank" style="font-size: 0.85rem; color: var(--secondary-color);">VIEW FULL SIZE</a>', unsafe_allow_html=True)

                    st.button(
                        "❌ REMOVE",
                        key=f"remove_gallery_img_btn_{i}",
                        help="Remove this generated image from the gallery.",
                        type="secondary",
                        on_click=lambda index=i: st.session_state.__setitem__('remove_index', index),
                        use_container_width=True
                    )
                        
                    st.download_button(
                        label="⬇️ DOWNLOAD",
                        data=requests.get(url).content,
                        file_name=f"nano_banana_x_ai_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{i}.jpg",
                        mime="image/jpeg",
                        use_container_width=True
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------
# 🎥 VIDEO GENERATION TAB (NEW PLACEHOLDER ONLY)
# --------------------------------------------------
with tab_video:
    st.markdown("## 🎥 Video Generation")
    st.info("This feature is currently under development. The Video Generation model (Wan-I2V) will be integrated here soon. Thank you for your patience!")
    st.image("https://placehold.co/800x400/1e1e1e/8c8c8c?text=Video+Generator+Coming+Soon", use_column_width=True)
