import streamlit as st
import fal_client
import os
import tempfile
import json
import datetime
import time
import base64
from io import BytesIO
import requests
import boto3
from botocore.exceptions import ClientError
from PIL import Image

# Define Constants
VIDEO_PASSWORD = "f6676kwp"

# Comprehensive Negative Prompt
DEFAULT_NEGATIVE_PROMPT = "bright colors, overexposed, static, blurred details, subtitles, style, artwork, painting, picture, still, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, malformed limbs, fused fingers, still picture, cluttered background, three legs, many people in the background, walking backwards"

# FAL Models
SDXL_MODEL = "fal-ai/stable-diffusion-xl-lightning"
WANI2V_MODEL = "fal-ai/wan-i2v"

# --- App Configuration and Styling ---
st.set_page_config(
    page_title="NANO BANANA X AI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for the precise dark, professional look
st.markdown("""
<style>
    /* Hide Streamlit UI elements (including headers and toolbars) */
    [data-testid="stToolbar"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }
    #MainMenu, #GithubIcon, header {
      visibility: hidden;
      height: 0%;
    }
    /* Hiding all Streamlit alert boxes/notices as requested (Success, Info, Warning, Error) */
    .stAlert, [data-testid="stNotification"], [data-testid="stSuccess"], [data-testid="stInfo"], [data-testid="stWarning"], [data-testid="stError"] {
        display: none !important;
    }

    /* Color Palette Variables - NANO BANANA X AI Theme */
    :root {
        --primary-color: #4169E1; /* Royal Blue */
        --secondary-color: #FFD700; /* Gold */
        --background-color: #121212; /* Very dark background */
        --card-background: #1e1e1e; /* Slightly lighter for containers */
        --text-color: #e0e0e0;
        --border-color: #3a3a3a;
        --success-color: #3CB371; /* Medium Sea Green */
    }

    /* General App Styling */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* Main Title/Logo Style */
    h1 {
        color: var(--primary-color);
        text-align: center;
        padding-top: 10px;
        margin-bottom: 20px;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: 1px;
    }
    
    /* Input Areas and Text */
    .stTextArea label, .stTextInput label, .stFileUploader label, .stSelectbox label {
        color: var(--text-color) !important;
        font-weight: 600;
    }
    
    /* Containers (Card Backgrounds) */
    [data-testid*="stVerticalBlock"], [data-testid*="stExpander"] > div:first-child, [data-testid*="stForm"] {
        background-color: var(--card-background);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid var(--border-color);
        margin-bottom: 15px;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: var(--primary-color);
        color: #ffffff;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: 700;
        transition: background-color 0.3s;
    }
    .stButton > button:hover {
        background-color: #3457c7; /* Darker royal blue on hover */
    }
    
    /* Tabs Styling */
    .stTabs [data-testid="stTab"] {
        background-color: var(--card-background);
        color: var(--text-color);
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        margin-right: 5px;
        font-weight: 600;
        border-bottom: 2px solid var(--border-color);
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 3px solid var(--primary-color);
        color: var(--primary-color) !important;
        background-color: var(--background-color);
    }
    .stTabs [data-testid="stTabContainer"] {
        background-color: var(--card-background);
        border-radius: 10px;
    }

    /* Custom styles for image upload thumbnail and removal button */
    .uploaded-thumbnail-container {
        display: flex;
        align-items: center;
        padding: 8px 12px;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        background-color: var(--card-background);
        margin-top: 10px;
    }
    .uploaded-thumbnail-image {
        width: 48px;
        height: 48px;
        object-fit: cover;
        border-radius: 4px;
        margin-right: 15px;
    }
    
    /* --- NEW STYLES FOR OUTPUT GALLERY THUMBNAILS --- */
    .gallery-thumbnail-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        background-color: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 5px;
        margin-bottom: 5px; /* Reduced margin for compact display */
    }
    .gallery-thumbnail-image {
        width: 100px; /* Fixed small size */
        height: 100px; 
        object-fit: cover;
        border-radius: 6px;
        margin-bottom: 5px;
    }
    
    /* Streamlit button specific styling for the small buttons below thumbnails */
    /* Ensure the buttons are aligned well */
    [data-testid*="stVerticalBlock"] > [data-testid*="stHorizontalBlock"] > div > [data-testid*="stButton"] button {
        padding: 5px 10px;
        font-size: 0.8rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# --- R2/S3 Configuration and Client Initialization (for saving generated files) ---
try:
    R2_ENDPOINT_URL = os.environ.get('R2_ENDPOINT_URL')
    R2_ACCESS_KEY_ID = os.environ.get('R2_ACCESS_KEY_ID')
    R2_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY')
    R2_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME')
    
    # Check if all necessary R2 variables are set
    if all([R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME]):
        r2_client = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY
        )
        STAGING_ENABLED = True
    else:
        r2_client = None
        STAGING_ENABLED = False
except Exception:
    r2_client = None
    STAGING_ENABLED = False

# Initialize FAL Client (FIX FOR TYPE ERROR)
try:
    # Explicitly load FAL credentials from Streamlit secrets
    FAL_KEY = st.secrets["FAL_KEY"]
    FAL_SECRET = st.secrets["FAL_SECRET"]
    
    # Initialize the client with explicit key/secret
    fal = fal_client.client(key=FAL_KEY, secret=FAL_SECRET)
except KeyError:
    st.error("FATAL ERROR: FAL_KEY or FAL_SECRET is missing from Streamlit secrets. Please configure them.")
    fal = None
except Exception as e:
    st.error(f"FATAL ERROR: Could not initialize the FAL AI Client. Details: {e}")
    fal = None


# --- Session State Initialization ---

# --- GENERAL DEFAULTS ---
if 'negative_prompt' not in st.session_state: st.session_state.negative_prompt = DEFAULT_NEGATIVE_PROMPT
if 'seed' not in st.session_state: st.session_state.seed = None 
if 'video_authenticated' not in st.session_state: st.session_state.video_authenticated = False 

# --- IMAGE UPLOADS (Stores BytesIO object) ---
if 'image_upload_img_data' not in st.session_state: st.session_state.image_upload_img_data = None
if 'video_upload_img_data' not in st.session_state: st.session_state.video_upload_img_data = None

# --- IMAGE DEFAULTS (SDXL) ---
if 'prompt' not in st.session_state: st.session_state.prompt = "A hyper-realistic portrait of a golden retriever wearing a banana helmet, 8k cinematic lighting"
if 'image_result_urls' not in st.session_state: st.session_state.image_result_urls = []
if 'width' not in st.session_state: st.session_state.width = 1024
if 'height' not in st.session_state: st.session_state.height = 1024
if 'strength' not in st.session_state: st.session_state.strength = 0.95 
if 'guidance_scale' not in st.session_state: st.session_state.guidance_scale = 4.5 
if 'num_images' not in st.session_state: st.session_state.num_images = 1
if 'num_inference_steps' not in st.session_state: st.session_state.num_inference_steps = 50 
if 'enable_safety_checker' not in st.session_state: st.session_state.enable_safety_checker = False 
if 'remove_index' not in st.session_state: st.session_state.remove_index = None # New state for image removal

# --- VIDEO DEFAULTS (Wan-I2V) ---
if 'video_prompt' not in st.session_state: st.session_state.video_prompt = "A majestic banana riding a futuristic, glowing skateboard in space, cinematic."
if 'video_result_url' not in st.session_state: st.session_state.video_result_url = None
if 'video_width' not in st.session_state: st.session_state.video_width = 832 
if 'video_height' not in st.session_state: st.session_state.video_height = 480 
if 'video_strength' not in st.session_state: st.session_state.video_strength = 0.7 
if 'motion_bucket_id' not in st.session_state: st.session_state.motion_bucket_id = 127 
if 'cond_aug' not in st.session_state: st.session_state.cond_aug = 0.02 
if 'video_num_inference_steps' not in st.session_state: st.session_state.video_num_inference_steps = 50 
if 'video_fps' not in st.session_state: st.session_state.video_fps = 16 
if 'video_num_frames' not in st.session_state: st.session_state.video_num_frames = 81 
if 'video_lora_weight' not in st.session_state: st.session_state.video_lora_weight = 0.7 
if 'video_safety_checker' not in st.session_state: st.session_state.video_safety_checker = False 
if 'video_seed' not in st.session_state: st.session_state.video_seed = None 

# --- Helper Functions ---

def upload_file_to_r2(content_url, file_extension):
    """
    Downloads content from a URL and uploads it to R2/S3, returning the public URL.
    Returns the original content_url if R2/S3 staging is disabled or fails.
    """
    if not STAGING_ENABLED:
        return content_url

    try:
        response = requests.get(content_url)
        response.raise_for_status() # Check for bad status codes
        
        # Determine file name and MIME type
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

        # Construct public URL (assumes public access bucket policy)
        public_url = f"{R2_ENDPOINT_URL}/{R2_BUCKET_NAME}/{file_key}"
        return public_url

    except Exception as e:
        # Errors are logged to console.
        print(f"R2 Upload Failed: {e}") 
        return content_url

def image_to_base64(uploaded_file_data):
    """Converts BytesIO file data to a base64 string for thumbnail display."""
    if uploaded_file_data:
        try:
            # Re-read the BytesIO object from the start
            uploaded_file_data.seek(0)
            img = Image.open(uploaded_file_data)
            img.thumbnail((128, 128)) # Resize for thumbnail
            
            buffered = BytesIO()
            # Save as JPEG to standardize output (smaller size)
            img.save(buffered, format="JPEG")
            
            # Reset BytesIO position after saving
            uploaded_file_data.seek(0) 
            
            return base64.b64encode(buffered.getvalue()).decode()
        except Exception:
            # Reset BytesIO position after failure
            uploaded_file_data.seek(0)
            return None
    return None

def display_image_uploader_with_thumbnail(session_state_key, label_text):
    """Handles the UI for image upload, thumbnail display, and removal."""
    
    # 1. Image Uploader
    uploaded_file = st.file_uploader(
        label_text,
        type=["png", "jpg", "jpeg"],
        key=f"uploader_{session_state_key}"
    )

    # If a new file is uploaded, update the session state with BytesIO data
    if uploaded_file is not None and getattr(st.session_state, session_state_key) is None:
        file_data = BytesIO(uploaded_file.getvalue())
        setattr(st.session_state, session_state_key, file_data)
    
    # 2. Thumbnail Display and Removal
    current_file_data = getattr(st.session_state, session_state_key)
    input_image_url = None
    
    if current_file_data is not None:
        
        b64_img = image_to_base64(current_file_data)
        
        if b64_img:
            # Get base64 URL for FAL client by re-reading the data
            current_file_data.seek(0)
            img_bytes = current_file_data.getvalue()
            current_file_data.seek(0) # Reset pointer
            input_image_url = f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode()}"

            # Use st.markdown for a custom thumbnail display with an inline X button
            st.markdown(f"""
                <div class="uploaded-thumbnail-container">
                    <img src="data:image/jpeg;base64,{b64_img}" class="uploaded-thumbnail-image" alt="Uploaded Image Thumbnail"/>
                    <span style="color: var(--text-color); font-size: 0.9rem; margin-right: auto;">Image Ready for Generation.</span>
                    <button class="remove-button" onclick="
                        // This uses a non-Streamlit way to signal state change via JS, 
                        // which relies on the environment supporting this cross-frame communication.
                        // However, using a Streamlit button is generally more reliable. 
                        // We keep the JS for the visual style but still rely on Streamlit Reruns for logic flow.
                        window.parent.postMessage({{
                            'type': 'set_session_state',
                            'key': '{session_state_key}',
                            'value': null
                        }}, '*');
                        window.parent.postMessage({{
                            'type': 'rerun'
                        }}, '*');
                    "><p>X</p></button>
                </div>
            """, unsafe_allow_html=True)
            
            # Ensure the BytesIO object is at the beginning for the generator call
            current_file_data.seek(0)
            
    return input_image_url

# --- FAL Generation Functions (Restored with actual logic) ---

def fal_generate_image(prompt, negative_prompt, width, height, num_images, strength, guidance_scale, num_steps, seed, input_image_url=None):
    """Generates images using fal-ai/stable-diffusion-xl-lightning and stages results."""
    
    if fal is None:
        st.error("Cannot generate image: FAL service is not initialized.")
        return []

    st.toast("Submitting Image Generation Request...")
    
    if input_image_url:
        # Image-to-Image mode
        model = "fal-ai/stable-diffusion-xl-lightning-sdedit"
        params = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "num_images": num_images,
            "image_url": input_image_url,
            "strength": strength,
            "guidance_scale": guidance_scale,
            "num_inference_steps": num_steps,
            "seed": seed, # None for random
            "enable_safety_checker": st.session_state.enable_safety_checker
        }
    else:
        # Text-to-Image mode
        model = SDXL_MODEL
        params = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "num_images": num_images,
            "guidance_scale": guidance_scale,
            "num_inference_steps": num_steps,
            "seed": seed, # None for random
            "enable_safety_checker": st.session_state.enable_safety_checker
        }
    
    try:
        handler = fal.submit(model, arguments=params)
        
        # Streamlit poll loop
        with st.spinner("Processing... waiting for the model to finish."):
            result = handler.get_response(stream=True)
            
        final_urls = []
        
        # Stage results to R2 if enabled
        for i, image_data in enumerate(result['images']):
            fal_url = image_data['url']
            staged_url = upload_file_to_r2(fal_url, ".jpg")
            final_urls.append(staged_url)
        
        st.toast(f"Generated {len(final_urls)} image(s) successfully!")
        return final_urls

    except Exception as e:
        # Use st.exception for robust error display without a notice bar
        st.error("Image Generation Failed. Check the console for details.")
        print(f"Image Generation Failed: {e}")
        return []


def fal_generate_video(prompt, negative_prompt, input_image_url=None, seed=None):
    """Generates video using fal-ai/wan-i2v and stages result."""
    
    if fal is None:
        st.error("Cannot generate video: FAL service is not initialized.")
        return None
        
    st.toast("Submitting Video Generation Request...")
    
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
        "seed": seed, # None for random
        "enable_safety_checker": st.session_state.video_safety_checker,
        "image_url": input_image_url # Used for I2V, None for T2V
    }
    
    try:
        handler = fal.submit(WANI2V_MODEL, arguments=params)
        
        # Streamlit poll loop
        with st.spinner("Processing... This can take a few minutes."):
            result = handler.get_response(stream=True)
            
        fal_url = result['video']['url']
        
        # Stage result to R2 if enabled
        staged_url = upload_file_to_r2(fal_url, ".mp4")
        
        st.toast("Video generation complete!")
        return staged_url

    except Exception as e:
        # Use st.exception for robust error display without a notice bar
        st.error("Video Generation Failed. Check the console for details.")
        print(f"Video Generation Failed: {e}")
        return None

# --- Authentication Logic ---
def authenticate_video_tab(password_attempt):
    """Checks the password and updates session state."""
    if password_attempt == VIDEO_PASSWORD:
        st.session_state.video_authenticated = True
        st.balloons()
        st.experimental_rerun()
    # Note: st.error is kept here as it's the only way to communicate a failed login attempt.


# --- Main Application Layout ---

# Logo/Title
st.markdown('<h1 style="text-align: center; color: var(--primary-color); font-size: 2.5rem;">NANO BANANA X AI 🍌</h1>', unsafe_allow_html=True)

# Tabs: Image first, Video second
tab_image, tab_video = st.tabs(["🖼️ Image Generation", "🎥 Video Generation"])

st.markdown("---")

# --------------------------------------------------
# 🖼️ IMAGE GENERATION TAB (First Tab)
# --------------------------------------------------
with tab_image:
    
    col_input_img, col_output_img = st.columns([1, 2])

    with col_input_img:
        st.markdown("## Image Input Controls")
        
        # --- Image Upload Section (Using custom component) ---
        input_image_url = display_image_uploader_with_thumbnail(
            'image_upload_img_data',
            "Upload an **initial image** for Image-to-Image Generation (Optional)"
        )
        
        # --- Prompts ---
        st.session_state.prompt = st.text_area(
            "Enter your **image prompt**",
            value=st.session_state.prompt,
            height=150,
            key="image_prompt_area"
        )
        
        st.session_state.negative_prompt = st.text_area(
            "Negative Prompt",
            value=st.session_state.negative_prompt,
            key="image_negative_prompt_area"
        )
        
        st.markdown("---")
        
        # --- Generate Button ---
        final_image_seed = None # Always Random
        
        # Check if FAL is initialized before allowing generation
        if fal is None:
            st.warning("Please resolve the FATAL ERROR above before generating.")
        else:
            if st.button("✨ Generate Image", key="generate_image_button", type="primary", use_container_width=True):
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
                        final_image_seed, 
                        input_image_url
                    )
                else:
                    # Use a specific message if no prompt is entered
                    st.toast("Please enter a prompt to generate an image.") 

        st.markdown("---")

        # --- Advanced Settings (ALL FEATURES EXPOSED) ---
        with st.expander("⚙️ Advanced Settings (SDXL / Seedream)", expanded=False):
            st.markdown("Customize model parameters for creative control.")
            
            resolution_options = {
                "512x512": (512, 512),
                "768x768": (768, 768),
                "1024x1024": (1024, 1024),
                "2048x2048 (2K)": (2048, 2048),
                "4096x4096 (4K)": (4096, 4096),
            }
            # Default to 1024x1024 (index 2)
            selected_resolution = st.selectbox("Select Resolution", list(resolution_options.keys()), index=2, key="img_resolution")
            st.session_state.width, st.session_state.height = resolution_options[selected_resolution]

            # Sliders reflect specific defaults: 0.95 and 4.5
            st.session_state.strength = st.slider("Strength (Img2Img Only)", min_value=0.0, max_value=1.0, value=st.session_state.strength, step=0.01, key="img_strength")
            st.session_state.guidance_scale = st.slider("Guidance Scale (CFG)", min_value=1.0, max_value=15.0, value=st.session_state.guidance_scale, step=0.1, key="img_guidance_scale")
            st.session_state.num_images = st.slider("Number of Images", min_value=1, max_value=4, value=st.session_state.num_images, step=1, key="img_num_images")
            st.session_state.num_inference_steps = st.slider("Inference Steps", min_value=10, max_value=150, value=st.session_state.num_inference_steps, step=1, key="img_steps")
            
            st.number_input("Seed (Policy: Always Random)", min_value=0, max_value=0, value=0, step=1, disabled=True, key="img_seed_input_display")
            
            st.session_state.enable_safety_checker = st.checkbox("Enable Safety Checker", value=st.session_state.enable_safety_checker, key="img_safety_check")

    with col_output_img:
        st.markdown("## Image Output Gallery")
        
        # --- Image Removal Logic (Must run before display loop) ---
        # Checks if a removal was requested in the previous run and executes it
        if st.session_state.remove_index is not None:
            try:
                # Remove the item at the specified index
                del st.session_state.image_result_urls[st.session_state.remove_index]
                st.session_state.remove_index = None # Clear the flag
                st.experimental_rerun()
            except IndexError:
                st.session_state.remove_index = None # Safety clear
        
        # --- Image Display Logic (Small Thumbnails) ---
        if st.session_state.image_result_urls:
            
            # Use 3 columns to display small thumbnails side-by-side
            cols = st.columns(3) 
            
            for i, image_url in enumerate(st.session_state.image_result_urls):
                with cols[i % 3]: # Cycle through the 3 columns
                    
                    # Custom HTML for the small thumbnail container (using new CSS class)
                    st.markdown(f"""
                        <div class="gallery-thumbnail-container">
                            <img src="{image_url}" class="gallery-thumbnail-image" title="Result {i+1}"/>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Streamlit button for Removal (The functional 'X' requested)
                    # We set the remove_index state variable and trigger a rerun on click
                    if st.button("❌ Remove", key=f"remove_img_{i}", use_container_width=True):
                        st.session_state.remove_index = i
                        # The rerun is handled automatically by the button click
                        
                    # Download button
                    try:
                        image_content = requests.get(image_url).content
                    except Exception:
                        image_content = b"Error fetching image content."
                        
                    st.download_button(
                        label="⬇️ Download",
                        data=image_content,
                        file_name=f"nano_banana_img_{i+1}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.jpg",
                        mime="image/jpeg",
                        use_container_width=True
                    )
        else:
             st.markdown(f"""
            <div style="
                height: 400px; 
                border: 2px dashed var(--primary-color); 
                border-radius: 12px; 
                display: flex; 
                flex-direction: column;
                justify-content: center; 
                align-items: center; 
                color: var(--text-color);
                background-color: var(--card-background);
                text-align: center;
                margin-top: 15px;
            ">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 48px; height: 48px; color: var(--secondary-color);">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.58-1.58l1.593-1.593a2.25 2.25 0 013.182 0l2.25 2.25m-4.5 4.5l2.25 2.25m-4.5-4.5l5.159-5.159m-1.58-1.58l1.593-1.593a2.25 2.25 0 013.182 0l2.25 2.25M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
                </svg>
                <h4 style="color: var(--secondary-color); margin-top: 10px;">IMAGE GALLERY</h4>
                <p style="font-size: 0.9rem; color: #888;">Generated images will appear here.</p>
            </div>
            """, unsafe_allow_html=True)


# --------------------------------------------------
# 🎥 VIDEO GENERATION TAB (Second Tab, Protected)
# --------------------------------------------------
with tab_video:
    
    if st.session_state.video_authenticated:
        # --- Authenticated Content ---
        st.markdown("---")
        
        col_input, col_output = st.columns([1, 2])

        with col_input:
            st.markdown("## Video Input Controls")
            
            # --- Image Upload Section for Video Source (Using custom component) ---
            input_video_image_url = display_image_uploader_with_thumbnail(
                'video_upload_img_data',
                "Upload **source image** for Image-to-Video Generation (Optional)"
            )

            # --- Prompts ---
            st.session_state.video_prompt = st.text_area(
                "Enter your **video prompt**", 
                value=st.session_state.video_prompt,
                height=150,
                key="video_prompt_area"
            )
            
            st.session_state.negative_prompt = st.text_area(
                "Negative Prompt",
                value=st.session_state.negative_prompt,
                key="video_negative_prompt_area"
            )
            
            st.markdown("---")
            
            final_video_seed = None # Always Random
            
            # --- Generate Button ---
            # Check if FAL is initialized before allowing generation
            if fal is None:
                st.warning("Please resolve the FATAL ERROR above before generating.")
            else:
                if st.button("🚀 Generate Video", key="generate_video_button", type="primary", use_container_width=True):
                    if st.session_state.video_prompt:
                        st.session_state.video_result_url = fal_generate_video(
                            st.session_state.video_prompt, 
                            st.session_state.negative_prompt,
                            input_video_image_url,
                            final_video_seed # Always None
                        )
                    else:
                        st.toast("Please enter a prompt to generate a video.")
            
            st.markdown("---")
            
            # --- Advanced Settings (ALL FEATURES EXPOSED) ---
            with st.expander("⚙️ Advanced Settings (Wan-I2V / SVD)", expanded=False):
                st.markdown("Precise control over motion and video output, matching **fal-ai/wan-i2v** defaults.")
                
                # Resolution
                video_resolution_options = {
                    "832x480 (480P)": (832, 480), # Default
                    "1024x576 (576P)": (1024, 576),
                    "1280x720 (720P)": (1280, 720),
                }
                # Default to 832x480 (index 0)
                selected_video_resolution = st.selectbox("Resolution", list(video_resolution_options.keys()), index=0, key="vid_resolution_select")
                st.session_state.video_width, st.session_state.video_height = video_resolution_options[selected_video_resolution]

                # Core Generation Parameters
                st.session_state.video_strength = st.slider("Strength (Image Fidelity)", min_value=0.0, max_value=1.0, value=st.session_state.video_strength, step=0.01, key="vid_strength_slider")
                st.session_state.motion_bucket_id = st.slider("Motion Bucket ID (Movement amount)", min_value=1, max_value=255, value=st.session_state.motion_bucket_id, step=1, key="vid_motion_bucket_slider")
                st.session_state.cond_aug = st.slider("Conditioning Augmentation", min_value=0.0, max_value=0.1, value=st.session_state.cond_aug, step=0.01, format="%.2f", key="vid_cond_aug_slider")
                st.session_state.video_lora_weight = st.slider("LoRA Weight (Style adaptation)", min_value=0.0, max_value=1.0, value=st.session_state.video_lora_weight, step=0.01, key="vid_lora_weight_slider")
                
                # Time/Quality Parameters
                st.session_state.video_num_frames = st.slider("Number of Frames (Max 100)", min_value=16, max_value=100, value=st.session_state.video_num_frames, step=1, key="vid_num_frames_slider")
                st.session_state.video_fps = st.slider("FPS (Frames per Second)", min_value=1, max_value=24, value=st.session_state.video_fps, step=1, key="vid_fps_slider")
                st.session_state.video_num_inference_steps = st.slider("Inference Steps", min_value=10, max_value=100, value=st.session_state.video_num_inference_steps, step=1, key="vid_steps_slider")

                st.number_input("Seed (Policy: Always Random)", min_value=0, max_value=0, value=0, step=1, disabled=True, key="vid_seed_input_display")
                
                st.session_state.video_safety_checker = st.checkbox("Enable Safety Checker", value=st.session_state.video_safety_checker, key="vid_safety_check")

        with col_output:
            st.markdown("## Video Output Preview")
            if st.session_state.video_result_url:
                st.video(st.session_state.video_result_url, format="video/mp4", start_time=0, loop=True, autoplay=True, use_container_width=True)
                st.markdown(f'<p style="text-align:center; color: var(--text-color); font-size: 0.9rem;">Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>', unsafe_allow_html=True)
                
                # R2 Download button or link to original FAL URL
                download_label = "Download Video (Staged)" if STAGING_ENABLED else "Download Video (FAL URL)"
                
                # Download the content to serve the file directly to the user
                try:
                    video_content = requests.get(st.session_state.video_result_url).content
                except Exception:
                    video_content = b"Error fetching video content."

                st.download_button(
                    label=download_label,
                    data=video_content,
                    file_name=f"nano_banana_video_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
            else:
                st.markdown(f"""
                <div style="
                    height: 400px; 
                    border: 2px dashed var(--primary-color); 
                    border-radius: 12px; 
                    display: flex; 
                    flex-direction: column;
                    justify-content: center; 
                    align-items: center; 
                    color: var(--text-color);
                    background-color: var(--card-background);
                    text-align: center;
                    margin-top: 15px;
                ">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 48px; height: 48px; color: var(--secondary-color);">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9.75M4.5 5.25h9.75M4.5 12h9.75" />
                    </svg>
                    <h4 style="color: var(--secondary-color); margin-top: 10px;">VIDEO PREVIEW</h4>
                    <p style="font-size: 0.9rem; color: #888;">Your generated video will appear here.</p>
                </div>
                """, unsafe_allow_html=True)
                
    else:
        # --- Authentication Form ---
        st.markdown("## 🔒 Video Generation is Password Protected")
        st.warning("Please enter the password to access this feature.")
        
        with st.form("video_login_form"):
            password_input = st.text_input("Enter Password", type="password", key="password_input")
            submitted = st.form_submit_button("Unlock Tab", type="primary")
            
            if submitted:
                authenticate_video_tab(password_input)
