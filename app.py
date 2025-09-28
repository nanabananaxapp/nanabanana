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
    
    /* Primary Button Style (GENERATE) */
    .stButton[data-testid="stButton-primary"] > button {
        background-color: var(--primary-color);
        color: #ffffff;
        border-radius: 8px;
        border: none;
        padding: 12px 20px;
        font-size: 1.1rem;
        font-weight: 700;
        transition: background-color 0.3s;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .stButton[data-testid="stButton-primary"] > button:hover {
        background-color: #3457c7; /* Darker royal blue on hover */
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
    /* *** CRITICAL FIX: TINY X BUTTON ON UPLOADED THUMBNAIL *** */
    /* ======================================================= */
    
    /* 1. Style the container around the image to allow relative positioning */
    .thumbnail-display-container {
        position: relative;
        display: inline-block; /* Makes the container wrap the image */
    }
    
    /* 2. Target the specific removal button and make it tiny, absolute positioned */
    [data-testid*="remove_upload_img_btn_"] > button { 
        position: absolute !important; 
        top: 0px !important;            /* Top right corner */
        right: -20px !important;        /* Pulls it slightly over the image boundary */
        
        /* Make it tiny */
        padding: 0px !important;
        font-size: 0.9rem !important; 
        line-height: 1 !important;
        width: 20px !important;
        height: 20px !important;
        
        background-color: #B22222 !important; /* Firebrick red */
        color: white !important;
        border-radius: 50% !important; /* Circular X */
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.5); /* Shadow for pop-out effect */
        z-index: 100;
    }
    [data-testid*="remove_upload_img_btn_"] > button:hover {
        background-color: #8B0000 !important; /* Darker red on hover */
    }
    
    /* Align the parent block to the top */
    [data-testid="stHorizontalBlock"] > div {
        align-items: flex-start !important;
    }
    
    /* 3. Style the image itself */
    .thumbnail-display-container img {
        border-radius: 8px;
        width: 100px;
        height: 100px;
        object-fit: cover;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
    }

</style>
""", unsafe_allow_html=True)

# Initialize R2/S3 client (rest of setup remains the same)
try:
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
if 'negative_prompt' not in st.session_state: st.session_state.negative_prompt = DEFAULT_NEGATIVE_PROMPT
if 'seed' not in st.session_state: st.session_state.seed = None 
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

# --- Helper Functions (No changes to R2/FAL logic) ---

def upload_file_to_r2(content_url, file_extension):
    # ... (function body remains unchanged) ...
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
    except Exception as e:
        print(f"R2 Upload Failed: {e}") 
        return content_url

def remove_uploaded_image_data(session_state_key):
    """Callback function to remove the uploaded image data from session state."""
    if session_state_key in st.session_state:
        st.session_state[session_state_key] = None
        st.toast("Uploaded image removed.")


def display_image_uploader_with_thumbnail(session_state_key, label_text):
    """
    Handles the UI for image upload, thumbnail display, and removal.
    Updated to use a visual overlay for the '❌' button and removes st.experimental_rerun.
    """
    input_image_url = None
    
    current_file_data = st.session_state.get(session_state_key)
    
    if current_file_data is None:
        # --- 1. Show Uploader (File Not Uploaded) ---
        uploaded_file = st.file_uploader(
            label_text,
            type=["png", "jpg", "jpeg"],
            key=f"uploader_{session_state_key}"
        )

        # If a new file is uploaded, update the session state with BytesIO data
        if uploaded_file is not None:
            file_data = BytesIO(uploaded_file.getvalue())
            st.session_state[session_state_key] = file_data
            # *** ERROR FIX: Removed st.experimental_rerun() ***
        
    else:
        # --- 2. Show Thumbnail and Removal Button (File Uploaded) ---
        
        # Prepare URL for FAL client (base64 encoded)
        current_file_data.seek(0)
        img_bytes = current_file_data.getvalue()
        input_image_url = f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode()}"
        
        st.markdown(f"**{label_text}**")
        
        # Use HTML/CSS to create the visual overlay effect for the tiny X
        st.markdown(
            f"""
            <div class="thumbnail-display-container">
                <img src="{input_image_url}" alt="Uploaded Image">
                <!-- The Streamlit button is placed right after this markdown block
                     but the CSS makes it look like it's part of the image container -->
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # The actual Streamlit button (used for the Python callback)
        st.button(
            "❌",
            key=f"remove_upload_img_btn_{session_state_key}", # Custom data-testid targetted by CSS
            help="Click to remove the uploaded image.",
            type="secondary",
            on_click=remove_uploaded_image_data,
            args=(session_state_key,),
        )
        
        # Add a subtle confirmation message below the thumbnail display area
        st.markdown(f'<p style="font-size: 0.8rem; color: var(--success-color);">Image ready for Image-to-Image Generation.</p>', unsafe_allow_html=True)
        current_file_data.seek(0) # Reset BytesIO after use

    if current_file_data is not None:
        current_file_data.seek(0)
        
    return input_image_url

def fal_generate_image(prompt, negative_prompt, width, height, num_images, strength, guidance_scale, num_steps, seed, input_image_url=None):
    # ... (function body remains unchanged) ...
    if fal is None:
        st.error("Cannot generate image: FAL service is not initialized.")
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
            result = handler.get_response(stream=True)
            
        final_urls = []
        for i, image_data in enumerate(result['images']):
            fal_url = image_data['url']
            staged_url = upload_file_to_r2(fal_url, ".jpg")
            final_urls.append(staged_url)
        
        st.toast(f"Generated {len(final_urls)} image(s) successfully!")
        return final_urls

    except Exception as e:
        st.error("Image Generation Failed. Check the console for details.")
        print(f"Image Generation Failed: {e}")
        return []


def fal_generate_video(prompt, negative_prompt, input_image_url=None, seed=None):
    # ... (function body remains unchanged) ...
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
        "seed": seed,
        "enable_safety_checker": st.session_state.video_safety_checker,
        "image_url": input_image_url
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
        st.error("Video Generation Failed. Check the console for details.")
        print(f"Video Generation Failed: {e}")
        return None

# --- Authentication Logic (Unchanged) ---
def authenticate_video_tab(password_attempt):
    """Checks the password and updates session state."""
    if password_attempt == VIDEO_PASSWORD:
        st.session_state.video_authenticated = True
        st.balloons()
        st.experimental_rerun()


# --- Main Application Layout ---

st.markdown('<h1 style="text-align: center; color: var(--primary-color); font-size: 2.5rem;">NANO BANANA X AI 🍌</h1>', unsafe_allow_html=True)

tab_image, tab_video = st.tabs(["🖼️ Image Generation", "🎥 Video Generation"])

st.markdown("---")

# --------------------------------------------------
# 🖼️ IMAGE GENERATION TAB (First Tab)
# --------------------------------------------------
with tab_image:
    
    col_input_img, col_output_img = st.columns([1, 2])

    with col_input_img:
        st.markdown("## Image Input Controls")
        
        # --- Image Upload Section ---
        input_image_url = display_image_uploader_with_thumbnail(
            'image_upload_img_data',
            "Initial image for **Image-to-Image** Generation (Optional)"
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
        
        # --- Generate Button (Max Visibility) ---
        final_image_seed = None 
        
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
                    st.toast("Please enter a prompt to generate an image.") 

    # --- Output Gallery (Right Column) ---
    with col_output_img:
        st.markdown("## Generated Images Gallery")
        
        # --- Image Removal Logic ---
        if st.session_state.remove_index is not None:
            if 0 <= st.session_state.remove_index < len(st.session_state.image_result_urls):
                st.session_state.image_result_urls.pop(st.session_state.remove_index)
            st.session_state.remove_index = None 
            st.experimental_rerun() 

        # --- Gallery Display ---
        if st.session_state.image_result_urls:
            cols = st.columns(3) 
            
            for i, url in enumerate(st.session_state.image_result_urls):
                with cols[i % 3]: 
                    
                    # Create a tiny overlay for generated images too (using the same structure)
                    st.markdown(
                        f"""
                        <div class="thumbnail-display-container" style="margin-bottom: 20px;">
                            <img src="{url}" alt="Generated Image {i+1}">
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Note: We reuse the CSS for the generated images' remove button by giving it a similar look
                    # but using a different key prefix.
                    st.button(
                        "❌",
                        key=f"remove_gallery_img_btn_{i}",
                        help="Remove this generated image from the gallery.",
                        type="secondary",
                        on_click=lambda index=i: st.session_state.__setitem__('remove_index', index)
                    )
                        
                    st.download_button(
                        label="⬇️ Download",
                        data=requests.get(url).content,
                        file_name=f"nano_banana_x_ai_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{i}.jpg",
                        mime="image/jpeg",
                        use_container_width=True
                    )
                    st.markdown("---")
        else:
            st.info("Your generated images will appear here as small thumbnails.")
            
    # --- Advanced Settings Expander ---
    with col_input_img:
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
            

# --------------------------------------------------
# 🎥 VIDEO GENERATION TAB (Second Tab)
# --------------------------------------------------
with tab_video:
    
    if not st.session_state.video_authenticated:
        st.markdown("## 🔐 Video Generation Access")
        st.warning("Video Generation is currently restricted. Please enter the password to access.")
        
        password_attempt = st.text_input("Enter Password", type="password", key="video_password_input")
        if st.button("Unlock Video Generator", key="video_unlock_button"):
            if password_attempt:
                authenticate_video_tab(password_attempt)
            else:
                st.error("Please enter a password.")
        
    else:
        st.success("Access Granted! Generating videos with Wan-I2V.")
        
        col_input_video, col_output_video = st.columns([1, 2])

        with col_input_video:
            st.markdown("## Video Input Controls")
            
            # --- Image Upload Section for Video I2V ---
            input_video_image_url = display_image_uploader_with_thumbnail(
                'video_upload_img_data',
                "Initial image for **Image-to-Video** Generation (Optional)"
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
            
            # --- Generate Button ---
            final_video_seed = None 
            
            if fal is None:
                st.warning("Please resolve the FATAL ERROR above before generating.")
            else:
                if st.button("🎬 Generate Video", key="generate_video_button", type="primary", use_container_width=True):
                    if st.session_state.video_prompt:
                        st.session_state.video_result_url = fal_generate_video(
                            st.session_state.video_prompt, 
                            st.session_state.negative_prompt, 
                            input_video_image_url, 
                            final_video_seed
                        )
                    else:
                        st.toast("Please enter a prompt to generate a video.") 

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
