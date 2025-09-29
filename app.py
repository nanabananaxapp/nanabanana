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
import requests # ADDED: Required for robust R2/URL handling
from PIL import Image # ADDED: Required for robust thumbnail handling

# --- Constants and Configuration ---
# CRITICAL: Re-checked from user's expected parameters
VIDEO_PASSWORD = "f6676kwp" # NEW: Video Password
# CRITICAL: Streamlit File ID for the user's uploaded logo file
UPLOADED_LOGO_ID = "uploaded:Clipboard01.jpg-e0b3072d-9dd7-4283-81d8-bb2162171654" 

# FAL Models
SDXL_MODEL = "fal-ai/stable-diffusion-xl-lightning"
SDXL_I2I_MODEL = "fal-ai/stable-diffusion-xl-lightning-sdedit"
WANI2V_MODEL = "fal-ai/wan-i2v" # NEW: Video Model

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


# --- Session State Initialization (Updated for Video) ---
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
    
    # NEW: Video Settings
    'video_upload_img_data': None,
    'video_result_url': None,
    'video_password_input': "",
    'video_authenticated': False, 
    'password_error': None, 
    'video_prompt': "A majestic banana riding a futuristic, glowing skateboard in space, cinematic.",
    'video_width': 832, 
    'video_height': 480, 
    'video_strength': 0.7, 
    'motion_bucket_id': 127, 
    'cond_aug': 0.02, 
    'video_num_inference_steps': 50, 
    'video_fps': 16, 
    'video_num_frames': 81, 
    'video_lora_weight': 0.7, 
    'video_safety_checker': False
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --- Helper Functions (Updated/New) ---
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
    """Handles image upload and displays thumbnail. Logic restored/fixed."""
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
            
            # Check if valid image
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


def fal_generate_video(prompt, negative_prompt, input_image_url=None):
    """NEW: Video generation function using Wan-I2V. Uses the existing FAL client/logic."""
    if not IS_FAL_READY:
        st.error("FAL client is not ready. Check FAL_KEY in secrets.")
        return None
        
    st.toast("Submitting Video Generation Request... This will take a moment.", icon="🎬")
    
    params = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": st.session_state.video_width,
        "height": st.session_state.video_height,
        "num_frames": st.session_state.video_num_frames,
        "fps": st.session_state.video_fps,
        "num_inference_steps": st.session_state.video_num_inference_steps,
        "strength": st.session_state.video_strength,
        "motion_bucket_id": st.session_state.motion_bucket_id,
        "cond_aug": st.session_state.cond_aug,
        "lora_weight": st.session_state.video_lora_weight,
        "enable_safety_checker": st.session_state.video_safety_checker,
        "seed": None
    }
    
    if input_image_url:
        params["image_url"] = input_image_url
    
    try:
        handler = fal.submit(WANI2V_MODEL, arguments=params)
        with st.spinner("Processing... This can take up to 5 minutes."):
            result = handler.get_response(stream=True)
            
        # The result for video will contain a 'video' field with the URL
        fal_url = result['video']['url']
        staged_url = upload_file_to_r2(fal_url, ".mp4")
        st.toast("Video generation complete!", icon="🎥")
        return staged_url

    except Exception:
        st.error("Video generation failed. Check the console for error details.")
        return None

def check_video_password_callback():
    """Checks the password and updates state."""
    password_attempt = st.session_state.video_password_input
    
    if password_attempt == VIDEO_PASSWORD:
        st.session_state.video_authenticated = True
        st.session_state.password_error = None
        st.balloons()
        st.rerun() 
    else:
        st.session_state.password_error = "INCORRECT PASSWORD. ACCESS DENIED."
        st.session_state.video_authenticated = False


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
    1.  This feature is **password protected**. The required password is: `f6676kwp`.
    2.  Enter a descriptive **Video Prompt**.
    3.  **Optional:** Upload an image for **Image-to-Video** (I2V) generation.
    4.  Video generation can take several minutes.
    
    ---
    
    ⚠️ **Button Status:** If the "Generate" buttons are **disabled (grayed out)**, the FAL AI key (`FAL_KEY`) is missing from the application environment secrets. **The application requires a valid FAL_KEY set in the environment.**
    """)
st.markdown("---")
# --- END INSTRUCTIONS LIST ---

# NEW: Tab structure added here
tab_image, tab_video = st.tabs(["🖼️ Image Generation (SDXL Lightning)", "🎥 Video Generation (Wan-I2V)"])


# --------------------------------------------------
# 🖼️ IMAGE GENERATION TAB (Original content restored here)
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
# 🎥 VIDEO GENERATION TAB (NEW FEATURE - FULLY FUNCTIONAL)
# --------------------------------------------------
with tab_video:
    
    if not st.session_state.video_authenticated:
        st.markdown("## 🔐 Video Generation Access")
        st.error("VIDEO GENERATION IS LOCKED. ENTER THE AUTHORIZED PASSWORD.")
        
        st.text_input("ENTER PASSWORD", type="password", key="video_password_input")
        st.button("UNLOCK VIDEO GENERATOR", key="video_unlock_button", on_click=check_video_password_callback, type="primary")
        
        if st.session_state.password_error:
            st.error(st.session_state.password_error)
            st.session_state.password_error = None

    else:
        st.success("ACCESS GRANTED. PROCEED WITH VIDEO GENERATION.")
        
        col_input_video, col_output_video = st.columns([1.3, 1.7])

        with col_input_video:
            st.markdown("## Video Input Controls")
            
            # --- Image Upload Section for Video I2V ---
            input_video_image_url = display_image_uploader_with_thumbnail(
                'video_upload_img_data',
                "Initial image for **Image-to-Video** Generation (Optional)"
            )

            st.markdown("---")

            # --- Prompts ---
            st.markdown("### Enter Prompts")
            
            st.session_state.video_prompt = st.text_area(
                "Enter your **video prompt**",
                value=st.session_state.video_prompt,
                height=150,
                key="video_prompt_area"
            )
            
            # Use the same negative prompt session state but ensure a unique key to prevent clash in this tab
            st.session_state.negative_prompt = st.text_area(
                "Negative Prompt (What to avoid)",
                value=st.session_state.negative_prompt,
                key="video_negative_prompt_area_2"
            )
            
            # --- GENERATE BUTTON ---
            st.markdown('<div style="margin-top: 20px; margin-bottom: 20px;">', unsafe_allow_html=True)
                
            if st.button(
                "🎬 Generate Video (Longer wait time)", 
                key="generate_video_button", 
                type="primary", 
                disabled=(not IS_FAL_READY) 
            ):
                if st.session_state.video_prompt:
                    st.session_state.video_result_url = fal_generate_video(
                        st.session_state.video_prompt, 
                        st.session_state.negative_prompt, 
                        input_video_image_url
                    )
                else:
                    st.toast("ENTER A PROMPT.", icon="✍️") 

            if not IS_FAL_READY:
                st.error("**FATAL ERROR: FAL AI Key is MISSING or INVALID.** Please check the FAL_KEY secret as per the instructions above. The button is currently disabled.")
            
            st.markdown('</div>', unsafe_allow_html=True) 


            # --- Advanced Settings Expander ---
            with st.expander("⚙️ Video Advanced Settings"):
                st.markdown("Customize Wan-I2V generation.")
                
                resolution_video_options = {
                    "512x512": (512, 512),
                    "832x480 (Recommended)": (832, 480),
                }
                
                current_res_key = next((k for k, v in resolution_video_options.items() if v == (st.session_state.video_width, st.session_state.video_height)), "832x480 (Recommended)")
                
                selected_resolution_video = st.selectbox("Select Resolution", list(resolution_video_options.keys()), index=list(resolution_video_options.keys()).index(current_res_key), key="video_res_select")
                st.session_state.video_width, st.session_state.video_height = resolution_video_options[selected_resolution_video]

                st.session_state.video_strength = st.slider("Strength (I2V only: 1.0=Full Change, 0.0=Original)", min_value=0.0, max_value=1.0, value=st.session_state.video_strength, step=0.01)
                st.session_state.video_num_frames = st.slider("Number of Frames (Affects length, Max 250)", min_value=16, max_value=250, value=st.session_state.video_num_frames, step=1)
                st.session_state.video_fps = st.slider("Frames Per Second (FPS)", min_value=8, max_value=30, value=st.session_state.video_fps, step=1)
                st.session_state.motion_bucket_id = st.slider("Motion Bucket ID (Controls motion style)", min_value=0, max_value=1024, value=st.session_state.motion_bucket_id, step=1)
                st.session_state.cond_aug = st.slider("Conditioning Augmentation", min_value=0.0, max_value=0.2, value=st.session_state.cond_aug, step=0.01)
                st.session_state.video_lora_weight = st.slider("LoRA Weight", min_value=0.0, max_value=1.0, value=st.session_state.video_lora_weight, step=0.01)
                st.session_state.video_num_inference_steps = st.slider("Inference Steps", min_value=10, max_value=100, value=st.session_state.video_num_inference_steps, step=5)
                st.session_state.video_safety_checker = st.checkbox("Enable Safety Filter", value=st.session_state.video_safety_checker, key="video_safety_check")
                
        # --- Output Video Display (Right Column) ---
        with col_output_video:
            st.markdown("## Generated Video")
            if st.session_state.video_result_url:
                st.video(st.session_state.video_result_url)
                
                st.download_button(
                    label="⬇️ DOWNLOAD VIDEO",
                    data=requests.get(st.session_state.video_result_url).content,
                    file_name=f"nano_banana_x_ai_video_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
