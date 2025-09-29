import streamlit as st
import fal_client
import os
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
# ID for the user's uploaded logo file
UPLOADED_LOGO_ID = "uploaded:Clipboard01.jpg-e0b3072d-9dd7-4283-81d8-bb2162171654" 

# Comprehensive Negative Prompt
DEFAULT_NEGATIVE_PROMPT = "bright colors, overexposed, static, blurred details, subtitles, style, artwork, painting, picture, still, overall gray, worst quality, low quality, JPEG compression compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, malformed limbs, fused fingers, still picture, cluttered background, three legs, many people in the background, walking backwards"

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
    
    /* Color Palette Variables - NANO BANANA X AI Theme */
    :root {
        --primary-color: #4169E1; /* Royal Blue */
        --secondary-color: #FFD700; /* Gold */
        --background-color: #121212; /* Very dark background */
        --card-background: #1e1e1e; /* Slightly lighter for containers */
        --text-color: #e0e0e0;
        --border-color: #3a3a3a;
        --success-color: #3CB371; /* Medium Sea Green */
        --error-color: #dc3545; /* Bootstrap Red */
    }

    /* General App Styling */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* Logo positioning (TOP RIGHT, as requested) */
    .logo-container {
        position: fixed;
        top: 10px;
        right: 10px;
        width: 100px; 
        height: 100px;
        z-index: 1000;
        border-radius: 8px; /* Added for aesthetic */
        overflow: hidden; /* Ensure image doesn't bleed */
    }
    .logo-container img {
        width: 100%;
        height: 100%;
        object-fit: contain;
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
    
    /* ======================================================= */
    /* *** BUTTON SIZING FIXES *** */
    /* ======================================================= */

    /* Primary Button Style (GENERATE) - MADE SMALLER AND MORE COMPACT */
    .stButton[data-testid="stButton-primary"] > button {
        background-color: var(--primary-color);
        color: #ffffff;
        border-radius: 6px; /* slightly smaller radius */
        border: none;
        padding: 10px 15px; /* Reduced padding for smaller size */
        font-size: 1.0rem; /* Slightly smaller font */
        font-weight: 600; 
        transition: background-color 0.3s;
        box-shadow: 0 3px 5px rgba(0, 0, 0, 0.3);
        /* Ensure it's not full width if use_container_width=False */
        max-width: fit-content; 
    }
    .stButton[data-testid="stButton-primary"] > button:hover {
        background-color: #3457c7; /* Darker royal blue on hover */
    }
    /* Disabled primary button style */
    .stButton[data-testid="stButton-primary"] > button:disabled {
        background-color: #2a3c74; /* Darker, desaturated blue for disabled */
        cursor: not-allowed;
        box-shadow: none;
    }
    
    /* Secondary Button Style (Download/Remove) */
    .stButton > button {
        background-color: #333; /* Dark gray for secondary buttons */
        color: var(--text-color);
        border-radius: 6px;
        border: none;
        padding: 8px 10px;
        font-weight: 500;
        transition: background-color 0.3s;
    }
    .stButton > button:hover {
        background-color: #555;
    }
    
    /* ======================================================= */
    /* *** FORCE SMALL UPLOADED THUMBNAIL (100x100) *** */
    /* ======================================================= */
    
    /* Wrapper for the single uploaded file thumbnail (Using pure HTML/base64) */
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
    /* The actual <img> tag inside the wrapper */
    .uploaded-thumbnail-wrapper img {
        width: 100px !important; 
        height: 100px !important; 
        object-fit: cover !important; 
        border-radius: 8px !important; 
        display: block !important;
        margin: 0 !important;
    }

    /* ======================================================= */
    /* *** GENERATED IMAGE GALLERY STYLING (MODIFIED FOR SMALLER OUTPUT) *** */
    /* ======================================================= */
    
    /* Container for generated image results */
    .generated-image-result {
        margin-bottom: 20px;
        display: flex;
        flex-direction: column;
        align-items: center; /* Center image block */
    }
    
    /* Generated image itself - Target the Streamlit image element wrapper*/
    .generated-image-result [data-testid="stImage"] {
        max-width: 200px; /* Max size for the thumbnail block, making images smaller */
        height: auto;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 5px; /* Spacing between image and buttons */
    }

    /* Actual <img> tag inside the result */
    .generated-image-result [data-testid="stImage"] img {
        border-radius: 8px;
        width: 100%; /* Fill the max-width of its container (200px) */
        height: auto;
        object-fit: cover;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5); 
        cursor: pointer; 
    }
    
</style>
""", unsafe_allow_html=True)

# Initialize R2/S3 client 
try:
    # R2 keys MUST be read from environment variables for the current environment
    R2_ENDPOINT_URL = os.environ.get('R2_ENDPOINT_URL')
    R2_ACCESS_KEY_ID = os.environ.get('R2_ACCESS_KEY_ID')
    R2_SECRET_ACCESS_KEY = os.environ.get('R2_SECRET_ACCESS_KEY')
    R2_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME')
    
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
except Exception as e:
    # Log the R2 error, but don't show it in the UI
    print(f"R2 Setup Failed: {e}")
    r2_client = None
    STAGING_ENABLED = False

# Initialize FAL Client (FIXED LOGIC: ONLY using st.secrets for FAL, as per the working backup file)
fal = None
IS_FAL_READY = False
try:
    # ONLY check Streamlit secrets for FAL Key, as per user's working backup file logic
    fal_key = st.secrets.get("FAL_KEY")
    
    if fal_key:
        # Connect using the single key
        fal = fal_client.client(key=fal_key)
        IS_FAL_READY = True
        print("FAL AI connection status: SUCCESS. Buttons enabled.") 
    else:
        # Check environment as a final fallback if st.secrets is not available or empty
        fal_key = os.environ.get("FAL_KEY")
        if fal_key:
            fal = fal_client.client(key=fal_key)
            IS_FAL_READY = True
        else:
            print("FAL AI connection status: FAL_KEY not found in secrets or environment. Buttons disabled.") 
        
except Exception as e:
    # Connection failed for another reason
    print(f"FAL AI Service connection failed during initialization: {e}")


# --- Session State Initialization ---
if 'negative_prompt' not in st.session_state: st.session_state.negative_prompt = DEFAULT_NEGATIVE_PROMPT
if 'seed' not in st.session_state: st.session_state.seed = None 
if 'video_password_input' not in st.session_state: st.session_state.video_password_input = "" 
if 'video_authenticated' not in st.session_state: st.session_state.video_authenticated = False 
if 'image_upload_img_data' not in st.session_state: st.session_state.image_upload_img_data = None 
if 'video_upload_img_data' not in st.session_state: st.session_state.video_upload_img_data = None
if 'prompt' not in st.session_state: st.session_state.prompt = "A hyper-realistic portrait of a golden retriever wearing a banana helmet, 8k cinematic lighting"
if 'image_result_urls' not in st.session_state: st.session_state.image_result_urls = []
if 'width' not in st.session_state: st.session_state.width = 1024
if 'height' not in st.session_state: st.session_state.height = 1024
if 'strength' not in st.session_state: st.session_state.strength = 0.95 
if 'guidance_scale' not in st.session_state: st.session_state.guidance_scale = 4.5 
if 'num_images' not in st.session_state: st.session_state.num_images = 1
if 'num_inference_steps' not in st.session_state: st.session_state.num_inference_steps = 50 
if 'enable_safety_checker' not in st.session_state: st.session_state.enable_safety_checker = False 
if 'remove_index' not in st.session_state: st.session_state.remove_index = None 
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
if 'password_error' not in st.session_state: st.session_state.password_error = None 


# --- Helper Functions (Staging remains the same as it was correct) ---

def upload_file_to_r2(content_url, file_extension):
    """Uploads content from a URL to R2 (Cloudflare's S3-compatible storage) if enabled."""
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
        # Construct the public URL using the endpoint and bucket name
        public_url = f"{R2_ENDPOINT_URL}/{R2_BUCKET_NAME}/{file_key}"
        return public_url
    except Exception as e:
        print(f"R2 Upload Failed: {e}") 
        return content_url

def display_image_uploader_with_thumbnail(session_state_key, label_text):
    """
    Handles the UI for image upload using a single-file uploader.
    """
    input_image_url = None
    
    # 1. Always show the uploader widget
    uploaded_file = st.file_uploader(
        label_text, 
        type=["png", "jpg", "jpeg"],
        key=f"uploader_{session_state_key}",
        accept_multiple_files=False
    )
    
    # 2. Sync Session State (our persistent data storage) with Uploader State
    if uploaded_file is not None:
        file_data = BytesIO(uploaded_file.getvalue())
        st.session_state[session_state_key] = file_data
    else:
        st.session_state[session_state_key] = None

    # 3. Check persistent state to draw the tiny, forced thumbnail
    current_file_data = st.session_state.get(session_state_key)
    
    if current_file_data is not None:
        try:
            current_file_data.seek(0)
            img_bytes = current_file_data.getvalue()
            # Use Image.open to validate the image is not corrupted
            Image.open(BytesIO(img_bytes))
            
            input_image_url = f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode()}"
            
            # Use ultra-aggressive HTML/CSS to force the 100x100 thumbnail
            st.markdown(f"""
                <div class="uploaded-thumbnail-wrapper">
                    <img src="{input_image_url}" alt="Uploaded Thumbnail" />
                </div>
            """, unsafe_allow_html=True)
            
            # Using simple text for status, not a banner
            st.markdown(f'<p style="font-size: 0.8rem; color: var(--success-color); margin-top: 0px;">Image ready for I2I Generation.</p>', unsafe_allow_html=True)

        except Exception as e:
            # We must keep this error message because it relates to USER UPLOADED file corruption.
            st.error("Uploaded file is corrupted or not a valid image. Please use the 'Clear file' button above to remove it.")
            print(f"User uploaded corrupted file: {e}")
            input_image_url = None 
            st.session_state[session_state_key] = None
        
        current_file_data.seek(0) # Reset BytesIO after use

    return input_image_url

def fal_generate_image(prompt, negative_prompt, width, height, num_images, strength, guidance_scale, num_steps, seed, input_image_url=None):
    """Submits the image generation request to the FAL API."""
    if fal is None:
        # Silently fail generation if FAL is not ready (disabled button handles the UI)
        print("Attempted generation while FAL client was not ready.")
        return []

    st.toast("Submitting Image Generation Request...")
    
    if input_image_url:
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
            "seed": seed, 
            "enable_safety_checker": st.session_state.enable_safety_checker
        }
    else:
        model = SDXL_MODEL
        params = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "num_images": num_images,
            "guidance_scale": guidance_scale,
            "num_inference_steps": num_steps,
            "seed": seed, 
            "enable_safety_checker": st.session_state.enable_safety_checker
        }
    
    try:
        handler = fal.submit(model, arguments=params)
        with st.spinner("Processing... waiting for the model to finish."):
            # Stream=True is safe for synchronous calls, it just gives a progress indicator
            result = handler.get_response(stream=True) 
            
        final_urls = []
        for i, image_data in enumerate(result['images']):
            fal_url = image_data['url']
            staged_url = upload_file_to_r2(fal_url, ".jpg")
            final_urls.append(staged_url)
        
        st.toast(f"Generated {len(final_urls)} image(s) successfully!")
        return final_urls

    except Exception as e:
        # Log the generation failure, but don't use st.error on the UI
        print(f"Image Generation Failed (FAL API Call Error): {e}")
        st.toast("Generation failed. Check the console for error details.", icon="⚠️")
        return []


def fal_generate_video(prompt, negative_prompt, input_image_url=None, seed=None):
    """Submits the video generation request to the FAL API (Wan-I2V)."""
    if fal is None:
        # Silently fail generation if FAL is not ready (disabled button handles the UI)
        print("Attempted video generation while FAL client was not ready.")
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
        "seed": seed,
        "enable_safety_checker": st.session_state.video_safety_checker,
        "image_url": input_image_url # Note: passed as function argument
    }
    
    try:
        handler = fal.submit(WANI2V_MODEL, arguments=params)
        with st.spinner("Processing... This can take a few minutes."):
            result = handler.get_response(stream=True)
            
        fal_url = result['video']['url']
        staged_url = upload_file_to_r2(fal_url, ".mp4")
        st.toast("Video generation complete!")
        return staged_url

    except Exception as e:
        # Log the generation failure, but don't use st.error on the UI
        print(f"Video Generation Failed (FAL API Call Error): {e}")
        st.toast("Video generation failed. Check the console for error details.", icon="⚠️")
        return None

# --- Authentication Logic ---
def check_video_password_callback():
    """Checks the password, updates state, and triggers a rerun if successful."""
    password_attempt = st.session_state.video_password_input
    
    if password_attempt == VIDEO_PASSWORD:
        st.session_state.video_authenticated = True
        st.session_state.password_error = None
        st.balloons()
        st.rerun() 
    else:
        # Using a password error message, as this is an explicit security check
        st.session_state.password_error = "Incorrect password. Try again."
        st.session_state.video_authenticated = False


# --- Main Application Layout ---

# --- LOGO/TITLE BLOCK (Restored EXACTLY as requested: Top Right Logo) ---
st.markdown(f"""
<div class="logo-container">
    <img src="{UPLOADED_LOGO_ID}" alt="NANO BANANA X AI Logo"/>
</div>
""", unsafe_allow_html=True)
# --- END LOGO/TITLE BLOCK ---


tab_image, tab_video = st.tabs(["🖼️ Image Generation", "🎥 Video Generation"])

st.markdown("---")

# --------------------------------------------------
# 🖼️ IMAGE GENERATION TAB (First Tab)
# --------------------------------------------------
with tab_image:
    
    # 1. COLUMN WIDTH: [1.3, 1.7] for wider input area
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
            "Negative Prompt",
            value=st.session_state.negative_prompt,
            key="image_negative_prompt_area"
        )
        
        # --- GENERATE BUTTON (FIXED PLACEMENT & SIZING) ---
        # The button is disabled if IS_FAL_READY is False, silencing the error.
        st.markdown('<div style="margin-top: 20px; margin-bottom: 20px;">', unsafe_allow_html=True)
            
        if st.button("✨ Generate Image", key="generate_image_button", type="primary", disabled=(not IS_FAL_READY)):
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
                    None, # Seed
                    input_image_url
                )
            else:
                st.toast("Please enter a prompt to generate an image.") 

        st.markdown('</div>', unsafe_allow_html=True) 


        # --- Advanced Settings Expander ---
        with st.expander("⚙️ Advanced Settings"):
            st.markdown("Customize how the model generates your image.")
            
            resolution_options = {
                "512x512": (512, 512),
                "768x768": (768, 768),
                "1024x1024": (1024, 1024),
                "2048x2048 (2K)": (2048, 2048),
            }
            current_res_key = next((k for k, v in resolution_options.items() if v == (st.session_state.width, st.session_state.height)), "1024x1024")
            
            selected_resolution = st.selectbox("Select Resolution", list(resolution_options.keys()), index=list(resolution_options.keys()).index(current_res_key))
            st.session_state.width, st.session_state.height = resolution_options[selected_resolution]

            st.session_state.strength = st.slider("Strength (Image-to-Image only)", min_value=0.0, max_value=1.0, value=st.session_state.strength, step=0.01)
            st.session_state.guidance_scale = st.slider("Guidance Scale (CFG)", min_value=1.0, max_value=15.0, value=st.session_state.guidance_scale, step=0.1)
            st.session_state.num_images = st.slider("Number of Images to Generate", min_value=1, max_value=4, value=st.session_state.num_images)
            st.session_state.num_inference_steps = st.slider("Inference Steps (Quality/Speed)", min_value=10, max_value=100, value=st.session_state.num_inference_steps, step=5)
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
            # Displays generated images in a 3-column grid
            cols = st.columns(3) 
            
            for i, url in enumerate(st.session_state.image_result_urls):
                with cols[i % 3]: 
                    
                    st.markdown('<div class="generated-image-result">', unsafe_allow_html=True)
                    st.image(url, use_column_width=False) 
                    
                    st.markdown(f'<a href="{url}" target="_blank" style="font-size: 0.85rem; color: var(--secondary-color);">View Full Size</a>', unsafe_allow_html=True)

                    st.button(
                        "❌ Remove",
                        key=f"remove_gallery_img_btn_{i}",
                        help="Remove this generated image from the gallery.",
                        type="secondary",
                        on_click=lambda index=i: st.session_state.__setitem__('remove_index', index),
                        use_container_width=True
                    )
                        
                    st.download_button(
                        label="⬇️ Download",
                        data=requests.get(url).content,
                        file_name=f"nano_banana_x_ai_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{i}.jpg",
                        mime="image/jpeg",
                        use_container_width=True
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
        # NO BANNER / INFO TEXT HERE
            
# --------------------------------------------------
# 🎥 VIDEO GENERATION TAB (Second Tab)
# --------------------------------------------------
with tab_video:
    
    if not st.session_state.video_authenticated:
        st.markdown("## 🔐 Video Generation Access")
        st.warning("Video Generation is currently restricted. Please enter the password to access.")
        
        st.text_input("Enter Password", type="password", key="video_password_input")
        st.button("Unlock Video Generator", key="video_unlock_button", on_click=check_video_password_callback, type="primary")
        
        if st.session_state.password_error:
            # Only showing this error because it relates to a USER INPUT (password), not a backend API issue.
            st.error(st.session_state.password_error)
            st.session_state.password_error = None

    else:
        # If authenticated, show the video generation interface
        st.success("Access Granted! Generating videos with Wan-I2V.")
        
        # 1. COLUMN WIDTH: [1.3, 1.7] for wider input area
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
            
            st.session_state.negative_prompt = st.text_area(
                "Negative Prompt",
                value=st.session_state.negative_prompt,
                key="video_negative_prompt_area"
            )
            
            # --- GENERATE BUTTON (FIXED PLACEMENT & SIZING) ---
            # The button is disabled if IS_FAL_READY is False, silencing the error.
            st.markdown('<div style="margin-top: 20px; margin-bottom: 20px;">', unsafe_allow_html=True)
                
            if st.button("🎬 Generate Video", key="generate_video_button", type="primary", disabled=(not IS_FAL_READY)):
                if st.session_state.video_prompt:
                    st.session_state.video_result_url = fal_generate_video(
                        st.session_state.video_prompt, 
                        st.session_state.negative_prompt, 
                        input_video_image_url, 
                        None # Seed
                    )
                else:
                    st.toast("Please enter a prompt to generate a video.") 
            
            st.markdown('</div>', unsafe_allow_html=True) 


            # --- Advanced Settings Expander ---
            with st.expander("⚙️ Video Advanced Settings"):
                st.markdown("Customize Wan-I2V generation.")
                
                resolution_video_options = {
                    "512x512": (512, 512),
                    "832x480": (832, 480), # Recommended landscape
                }
                
                current_res_key = next((k for k, v in resolution_video_options.items() if v == (st.session_state.video_width, st.session_state.video_height)), "832x480")
                
                selected_resolution_video = st.selectbox("Select Resolution", list(resolution_video_options.keys()), index=list(resolution_video_options.keys()).index(current_res_key), key="video_res_select")
                st.session_state.video_width, st.session_state.video_height = resolution_video_options[selected_resolution_video]

                st.session_state.video_strength = st.slider("Strength (Image-to-Video only)", min_value=0.0, max_value=1.0, value=st.session_state.video_strength, step=0.01)
                st.session_state.video_num_frames = st.slider("Number of Frames", min_value=16, max_value=250, value=st.session_state.video_num_frames, step=1)
                st.session_state.video_fps = st.slider("Frames Per Second (FPS)", min_value=8, max_value=30, value=st.session_state.video_fps, step=1)
                st.session_state.motion_bucket_id = st.slider("Motion Bucket ID (Controls motion strength/style)", min_value=0, max_value=1024, value=st.session_state.motion_bucket_id, step=1)
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
                    label="⬇️ Download Video",
                    data=requests.get(st.session_state.video_result_url).content,
                    file_name=f"nano_banana_x_ai_video_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
            else:
                st.info("Your generated video will appear here.")
                
            st.markdown("---")
            st.warning("Video generation can be slow and may take several minutes.")
