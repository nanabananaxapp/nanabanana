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

# Define the secret password for the video tab
VIDEO_PASSWORD = "f6676kwp"

# --- App Configuration and Styling ---
st.set_page_config(
    page_title="NANO BANANA X AI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a dark, professional look
st.markdown("""
<style>
    /* Hide Streamlit UI elements */
    [data-testid="stToolbar"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }
    #MainMenu {
      visibility: hidden;
    }
    #GithubIcon {
      visibility: hidden;
    }
    header {
        visibility: hidden;
        height: 0%;
    }

    /* Color Palette Variables */
    :root {
        --primary-color: #4169E1; /* Royal Blue */
        --secondary-color: #FFD700; /* Gold */
        --background-color: #121212; /* Very dark background */
        --card-background: #1e1e1e; /* Slightly lighter for containers */
        --text-color: #e0e0e0;
        --border-color: #3a3a3a;
    }
    
    /* Main App Container Styling */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Button Styling */
    .stButton>button {
        background: linear-gradient(145deg, var(--primary-color), #3650B0);
        color: white;
        border: none;
        border-radius: 10px;
        box-shadow: 5px 5px 10px #0a0a0a, -5px -5px 10px #2a2a2a;
        transition: all 0.2s ease;
        font-weight: 600;
        letter-spacing: 0.05em;
        padding: 12px 24px;
        font-size: 1.1em;
        width: 100%;
    }
    .stButton>button:hover {
        background: linear-gradient(145deg, #3650B0, var(--primary-color));
        box-shadow: 2px 2px 5px #0a0a0a, -2px -2px 5px #2a2a2a;
        transform: translateY(-2px);
    }
    .stButton>button:active {
        box-shadow: inset 2px 2px 5px #0a0a0a, inset -2px -2px 5px #2a2a2a;
        transform: translateY(0);
    }
    
    /* Input Field Styling */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>input, .st-emotion-cache-1jm98w2 {
        background-color: var(--card-background);
        color: var(--text-color);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 12px;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus, .stNumberInput>div>input:focus {
        border-color: var(--secondary-color);
        box-shadow: 0 0 0 2px rgba(255, 215, 0, 0.3);
    }
    
    /* Header and Title Styling */
    h1, h2, h3 {
        color: var(--primary-color);
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 15px rgba(65, 105, 225, 0.5);
    }
    h2 {
        margin-top: 0;
    }
    
    /* Container/Card Styling */
    .st-emotion-cache-1jm98w2 {
        border-radius: 12px;
        border: 1px solid var(--border-color);
        background-color: var(--card-background);
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* Uploaded Image Thumbnail Styling */
    .uploaded-image-container {
        position: relative;
        display: inline-block;
        margin: 0.5rem;
        border: 2px solid var(--border-color);
        border-radius: 10px;
        overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .uploaded-image-thumbnail {
        height: 120px;
        width: 120px;
        object-fit: cover;
    }
    .uploaded-image-container:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px rgba(65, 105, 225, 0.5);
    }
    .remove-button {
        position: absolute;
        top: 5px;
        right: 5px;
        background-color: rgba(255, 0, 0, 0.8);
        color: white;
        border: none;
        border-radius: 50%;
        width: 25px;
        height: 25px;
        font-weight: bold;
        font-size: 1.1rem;
        cursor: pointer;
        transition: background-color 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        line-height: 1;
        padding-bottom: 2px;
    }
    .remove-button:hover {
        background-color: red;
    }

    .stImage img {
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .image-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        justify-content: flex-start;
        align-items: center;
        margin-top: 1rem;
    }
    
    /* Smaller banana icon style */
    .banana-icon {
        font-size: 2rem;
    }

    /* Warning message style */
    .private-warning {
        font-size: 1.2em;
        font-weight: bold;
        text-decoration: underline;
    }
    
    /* Override Streamlit's default image container styling */
    .st-emotion-cache-ch5d6d img, .stVideo video {
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
    }
    
    /* Full-page loading spinner */
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.8);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        text-align: center;
        color: white;
        font-size: 1.5rem;
    }
    
    .spinner-icon {
        border: 8px solid rgba(65, 105, 225, 0.3);
        border-top: 8px solid var(--primary-color);
        border-radius: 50%;
        width: 60px;
        height: 60px;
        animation: spin 1s linear infinite;
        margin-bottom: 20px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)


# --- API Key and Secrets Handling ---
def get_secret(key, default=None):
    """Get secret from Streamlit secrets or environment variable"""
    if hasattr(st, 'secrets') and key in st.secrets:
        return st.secrets[key]
    elif key in os.environ:
        return os.environ[key]
    return default

FAL_KEY = get_secret("FAL_KEY")

if not FAL_KEY:
    st.error("❌ A required FAL_KEY secret is missing. The application cannot run without it.")
    st.stop()

fal_client.key = FAL_KEY

# --- Cloudflare R2 Configuration and File Management ---
# R2 bucket name - you can change this or keep it in secrets
R2_BUCKET_NAME = get_secret("R2_BUCKET_NAME", "app-generations")  # Default bucket name

@st.cache_resource
def get_r2_client():
    """
    Creates and returns an S3 client configured for Cloudflare R2
    using credentials from Streamlit secrets.
    """
    try:
        # Check if R2 credentials exist in secrets
        required_keys = ["R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT_URL"]
        missing_keys = [key for key in required_keys if key not in st.secrets]
        
        if missing_keys:
            st.warning(f" ⚠️ Missing R2 configuration secrets: {', '.join(missing_keys)}. Saving generations to R2 will be skipped.")
            return None

        # Create S3 client configured for R2
        s3_client = boto3.client(
            's3',
            endpoint_url=st.secrets["R2_ENDPOINT_URL"],
            aws_access_key_id=st.secrets["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["R2_SECRET_ACCESS_KEY"],
            region_name='auto'  # R2 uses 'auto' for region
        )
        
        # Test connection by listing buckets
        s3_client.list_buckets()
        st.info("✅ Successfully connected to Cloudflare R2.")
        return s3_client
        
    except ClientError as e:
        st.error(f"❌ R2 Authentication failed: {e}")
        return None
    except Exception as e:
        st.error(f"❌ An error occurred while connecting to R2: {e}")
        return None


def ensure_bucket_exists(s3_client, bucket_name):
    """Ensures the R2 bucket exists, creates it if it doesn't."""
    if not s3_client:
        return False
    
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            # Bucket doesn't exist, create it
            try:
                s3_client.create_bucket(Bucket=bucket_name)
                st.info(f"✅ R2 bucket '{bucket_name}' created successfully.")
                return True
            except ClientError as create_error:
                st.error(f"❌ Failed to create R2 bucket: {create_error}")
                return False
        else:
            st.error(f"❌ Error checking R2 bucket: {e}")
            return False


def upload_bytes_to_r2(s3_client, file_bytes, s3_key, bucket_name, content_type=None):
    """Uploads file bytes to R2."""
    if not s3_client:
        return None
    
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type or 'application/octet-stream'
        )
        return s3_key
    except ClientError as e:
        st.warning(f"⚠️ Could not upload to R2: {str(e)}")
        return None


def save_generation(s3_client, uploaded_files, generated_image_data, generation_params, folder_prefix="generation"):
    """Saves image generation data (Seedream) to R2."""
    if not s3_client or not R2_BUCKET_NAME:
        st.warning("⚠ Skipping R2 save for image generation.")
        return
    
    if not ensure_bucket_exists(s3_client, R2_BUCKET_NAME):
        return
    
    try:
        # Create the folder structure using S3 key prefixes
        date_folder = datetime.date.today().strftime("%Y-%m-%d")
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        generation_folder = f"{date_folder}/{folder_prefix}_{timestamp_str}"
        
        # Save the uploaded files
        for uploaded_file in uploaded_files:
            s3_key = f"{generation_folder}/uploads/{uploaded_file.name}"
            upload_bytes_to_r2(
                s3_client, 
                uploaded_file.getvalue(), 
                s3_key, 
                R2_BUCKET_NAME,
                content_type=uploaded_file.type
            )
        
        # Save the generated images
        for i, image_data in enumerate(generated_image_data):
            s3_key = f"{generation_folder}/outputs/output_image_{i+1}.png"
            upload_bytes_to_r2(
                s3_client,
                image_data['bytes'],
                s3_key,
                R2_BUCKET_NAME,
                content_type='image/png'
            )
        
        # Save the prompt and parameters as a JSON file
        params_json = json.dumps(generation_params, indent=4)
        s3_key = f"{generation_folder}/generation_parameters.json"
        upload_bytes_to_r2(
            s3_client,
            params_json.encode('utf-8'),
            s3_key,
            R2_BUCKET_NAME,
            content_type='application/json'
        )
        
        st.success(f"Image generation saved to R2 (Folder: {generation_folder})")
        
    except Exception as e:
        st.error(f"❌ Error saving image generation to R2: {str(e)}")


def save_video_generation(s3_client, uploaded_files, generated_video_data, generation_params, folder_prefix="video_generation"):
    """Saves video generation data (Wan-I2V) to R2."""
    if not s3_client or not R2_BUCKET_NAME:
        st.warning("⚠ Skipping R2 save for video generation.")
        return
    
    if not ensure_bucket_exists(s3_client, R2_BUCKET_NAME):
        return
    
    try:
        date_folder = datetime.date.today().strftime("%Y-%m-%d")
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        generation_folder = f"{date_folder}/{folder_prefix}_{timestamp_str}"
        
        # Save the uploaded files
        for uploaded_file in uploaded_files:
            s3_key = f"{generation_folder}/uploads/{uploaded_file.name}"
            upload_bytes_to_r2(
                s3_client, 
                uploaded_file.getvalue(), 
                s3_key, 
                R2_BUCKET_NAME,
                content_type=uploaded_file.type
            )
        
        # Save the generated video
        s3_key_video = f"{generation_folder}/outputs/output_video.mp4"
        upload_bytes_to_r2(
            s3_client,
            generated_video_data['bytes'],
            s3_key_video,
            R2_BUCKET_NAME,
            content_type='video/mp4'
        )
        
        # Save the prompt and parameters as a JSON file
        params_json = json.dumps(generation_params, indent=4)
        s3_key_params = f"{generation_folder}/generation_parameters.json"
        upload_bytes_to_r2(
            s3_client,
            params_json.encode('utf-8'),
            s3_key_params,
            R2_BUCKET_NAME,
            content_type='application/json'
        )
        
        st.success(f"Video generation saved to R2 (Folder: {generation_folder})")
        
    except Exception as e:
        st.error(f"❌ Error saving video generation to R2: {str(e)}")


# --- Fal AI Cache and Generation Logic ---
@st.cache_data
def upload_files_to_fal(uploaded_files):
    """Caches the Fal AI URLs for uploaded files to prevent repeated uploads."""
    uploaded_image_urls = {}
    for uploaded_file in uploaded_files:
        # Unique identifier based on name and size to use as cache key
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        
        # Check if the URL is already cached
        if file_id in st.session_state.uploaded_image_urls:
            uploaded_image_urls[file_id] = st.session_state.uploaded_image_urls[file_id]
            continue

        # If not cached, upload the file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.type.split('/')[-1]}") as temp_file:
            temp_file.write(uploaded_file.getvalue())
            fal_image_url = fal_client.upload_file(temp_file.name)
            uploaded_image_urls[file_id] = fal_image_url
        os.unlink(temp_file.name)
    
    # Update the session state cache for next rerun/generation
    st.session_state.uploaded_image_urls.update(uploaded_image_urls)
    return uploaded_image_urls

# --- Session State Initialization (Seedream) ---
if 'generated_images' not in st.session_state: st.session_state.generated_images = {}
if 'strength' not in st.session_state: st.session_state.strength = 0.95
if 'guidance_scale' not in st.session_state: st.session_state.guidance_scale = 4.5
if 'num_images' not in st.session_state: st.session_state.num_images = 1
if 'num_inference_steps' not in st.session_state: st.session_state.num_inference_steps = 40
if 'seed' not in st.session_state: st.session_state.seed = None
if 'enable_safety_checker' not in st.session_state: st.session_state.enable_safety_checker = False
if 'width' not in st.session_state: st.session_state.width = 2048
if 'height' not in st.session_state: st.session_state.height = 2048
if 'is_generating_clicked' not in st.session_state: st.session_state.is_generating_clicked = False
if 'prompt' not in st.session_state: st.session_state.prompt = ""


# --- Session State Initialization (Wan-I2V) ---
if 'video_generated_data' not in st.session_state: st.session_state.video_generated_data = None
if 'video_prompt' not in st.session_state: st.session_state.video_prompt = ""
if 'video_strength' not in st.session_state: st.session_state.video_strength = 0.95
if 'motion_bucket_id' not in st.session_state: st.session_state.motion_bucket_id = 127
if 'cond_aug' not in st.session_state: st.session_state.cond_aug = 0.02
if 'video_width' not in st.session_state: st.session_state.video_width = 832  # 480P equivalent width
if 'video_height' not in st.session_state: st.session_state.video_height = 480 # 480P equivalent height
if 'video_is_generating_clicked' not in st.session_state: st.session_state.video_is_generating_clicked = False
if 'video_seed' not in st.session_state: st.session_state.video_seed = None
if 'video_authenticated' not in st.session_state: st.session_state.video_authenticated = False # NEW Authentication state

# --- Common Session State ---
if 'uploaded_file_objects' not in st.session_state: st.session_state.uploaded_file_objects = None
if 'uploaded_image_urls' not in st.session_state: st.session_state.uploaded_image_urls = {}

# --- Authentication Logic ---
def authenticate_video_tab(password_attempt):
    """Checks the password and updates session state."""
    if password_attempt == VIDEO_PASSWORD:
        st.session_state.video_authenticated = True
        st.success("✅ Access Granted!")
        # Use rerun to immediately show the content of the tab
        st.rerun() 
    else:
        st.error("❌ Incorrect Password.")
        st.session_state.video_authenticated = False

# --- Main App Logic and Functions ---

def generate_images():
    """Handles the Fal AI Seedream image generation process."""
    try:
        st.session_state.generated_images = {}
        
        if not st.session_state.uploaded_file_objects:
            st.error("❌ Please upload at least one image before generating.")
            st.session_state.is_generating_clicked = False
            return
        
        current_prompt = st.session_state.get('prompt', '').strip()
        if not current_prompt:
            st.error("❌ Please enter a prompt before generating.")
            st.session_state.is_generating_clicked = False
            return
        
        # Upload image to Fal (or use cached URLs)
        uploaded_file_urls = upload_files_to_fal(st.session_state.uploaded_file_objects)
        
        # Base prompt for Seedream (pre-appended to the user prompt)
        base_prompt = ", Do not change the face appearance, the person's body structure is always like the original!!! But pose and the scene and moment and can be different when relevant. change outfit only when asked to. amazing details, detailed real skin-texture, body parts are always very detailed, perfect, and realistic. top camera quality, refine details, enhanced quality!! 8k, very detailed,high-definition, high-fidelity, high-resolution, DSLR quality."
        
        # Swapping the order of prompts: User prompt first, then base prompt
        final_prompt = current_prompt + base_prompt

        arguments = {
            "image_urls": list(uploaded_file_urls.values()),
            "prompt": final_prompt,
            "strength": st.session_state.strength,
            "guidance_scale": st.session_state.guidance_scale,
            "num_images": st.session_state.num_images,
            "num_inference_steps": st.session_state.num_inference_steps,
            "enable_safety_checker": st.session_state.enable_safety_checker,
            "width": st.session_state.width,
            "height": st.session_state.height
        }
        
        if st.session_state.seed is not None:
            arguments["seed"] = int(st.session_state.seed)

        response = fal_client.run(
            "fal-ai/bytedance/seedream/v4/edit",
            arguments=arguments
        )
        
        if 'images' in response and len(response['images']) > 0:
            image_data_with_bytes = []
            for image in response['images']:
                with urlopen(image['url']) as img_response:
                    image_bytes = BytesIO(img_response.read()).getvalue()
                    image_data_with_bytes.append({
                        'url': image['url'],
                        'bytes': image_bytes
                    })
            st.session_state.generated_images['seedream'] = image_data_with_bytes

            generation_params = {
                "timestamp": datetime.datetime.now().isoformat(),
                "model": "Seedream 4",
                "prompt": final_prompt,
                "strength": st.session_state.strength,
                "guidance_scale": st.session_state.guidance_scale,
                "num_images": st.session_state.num_images,
                "num_inference_steps": st.session_state.num_inference_steps,
                "enable_safety_checker": st.session_state.enable_safety_checker,
                "seed": st.session_state.seed,
                "width": st.session_state.width,
                "height": st.session_state.height,
                "generated_urls": [img['url'] for img in image_data_with_bytes]
            }
            
            # Save to R2
            s3_client = get_r2_client()
            if s3_client:
                save_generation(s3_client, st.session_state.uploaded_file_objects, image_data_with_bytes, generation_params)
        else:
            st.error("❌ No images were generated. Please try again.")

    except Exception as e:
        st.error(f"❌ An error occurred during image generation: {str(e)}")
    finally:
        st.session_state.is_generating_clicked = False


def generate_video():
    """Handles the Fal AI video generation process (wan-i2v)."""
    try:
        st.session_state.video_generated_data = None
        
        # Check for image upload (only 1 image needed)
        uploaded_files = st.session_state.uploaded_file_objects
        if not uploaded_files or len(uploaded_files) == 0:
            st.error("❌ Please upload a single image before generating.")
            st.session_state.video_is_generating_clicked = False
            return
            
        if len(uploaded_files) > 1:
            st.warning("⚠️ The Image-to-Video model only uses the first uploaded image.")

        current_prompt = st.session_state.get('video_prompt', '').strip()
        if not current_prompt:
            st.error("❌ Please enter a prompt before generating.")
            st.session_state.video_is_generating_clicked = False
            return
        
        # Upload image to Fal (or use cached URLs)
        uploaded_file_urls = upload_files_to_fal(uploaded_files)
        image_url_to_use = list(uploaded_file_urls.values())[0]

        final_prompt = current_prompt

        arguments = {
            "image_url": image_url_to_use,
            "prompt": final_prompt,
            "strength": st.session_state.video_strength,
            "motion_bucket_id": st.session_state.motion_bucket_id,
            "cond_aug": st.session_state.cond_aug,
            "width": st.session_state.video_width,
            "height": st.session_state.video_height,
            # Setting to False as requested by the user
            "enable_safety_checker": False
        }
        
        if st.session_state.video_seed is not None:
            arguments["seed"] = int(st.session_state.video_seed)

        # Use st.spinner for in-line feedback instead of st.info
        with st.spinner("⏳ Video generation can take 1-3 minutes. Please wait..."):
            response = fal_client.run(
                "fal-ai/wan-i2v",
                arguments=arguments
            )
        
        if 'video' in response and response['video']:
            video_url = response['video']['url']
            
            # Fetch video bytes
            with urlopen(video_url) as video_response:
                video_bytes = BytesIO(video_response.read()).getvalue()
                
            generated_video_data = {
                'url': video_url,
                'bytes': video_bytes
            }
            st.session_state.video_generated_data = generated_video_data

            generation_params = {
                "timestamp": datetime.datetime.now().isoformat(),
                "model": "Wan-I2V",
                "prompt": final_prompt,
                "strength": st.session_state.video_strength,
                "motion_bucket_id": st.session_state.motion_bucket_id,
                "cond_aug": st.session_state.cond_aug,
                "seed": st.session_state.video_seed,
                "width": st.session_state.video_width,
                "height": st.session_state.video_height,
                "generated_url": video_url
            }
            
            # Save to R2
            s3_client = get_r2_client()
            if s3_client:
                save_video_generation(s3_client, uploaded_files, generated_video_data, generation_params)
        else:
            st.error("❌ No video was generated. Please check your prompt and try again.")

    except Exception as e:
        st.error(f"❌ An error occurred during video generation: {str(e)}")
    finally:
        st.session_state.video_is_generating_clicked = False


# --- UI Layout ---

# Handle generation clicks
if st.session_state.is_generating_clicked:
    st.markdown(f"""
    <div class="loading-overlay">
        <div class="spinner-icon"></div>
        <div class="spinner-text">{"Working on your image masterpiece..."}</div>
    </div>
    """, unsafe_allow_html=True)
    generate_images()
    st.rerun()

if st.session_state.video_is_generating_clicked:
    st.markdown(f"""
    <div class="loading-overlay">
        <div class="spinner-icon"></div>
        <div class="spinner-text">{"Working on your video masterpiece (This may take a few minutes)..."}</div>
    </div>
    """, unsafe_allow_html=True)
    generate_video()
    st.rerun()


# --- Header and Instructions ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try:
        # Placeholder for logo image
        st.image("logo.png", use_container_width=True)
    except Exception:
        st.markdown("<div style='height: 110px;'></div>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1>NANO BANANA X AI</h1>", unsafe_allow_html=True)
    st.markdown("<h2>AI Content Generator <span class='banana-icon'>🍌</span></h2>", unsafe_allow_html=True)

st.markdown("""
- **Upload your images:** Upload 1 - 4 images to serve as the basis for your new creation.
- **Craft a detailed prompt:** Write a clear and descriptive prompt to guide the AI's generation process.
- **Uncensored Model:** This is an uncensored model version; please use it responsibly.
- Do not share: This is a private, unshared version of the model. To ensure low resource usage, <span class="private-warning">please do not share this website with others!</span>
""", unsafe_allow_html=True)

# --- Tabs Implementation ---
tab_image, tab_video = st.tabs(["🖼️ Image to Image (Seedream)", "🎥 Image to Video (Wan-I2V)"])

# --- Common File Uploader Section ---
st.markdown("---")
st.subheader("Source Image Uploader")
uploaded_files = st.file_uploader("🖼️ Upload one or more images (JPG, PNG, WebP)", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key="main_uploader")

if uploaded_files:
    st.session_state.uploaded_file_objects = uploaded_files
# Do not clear uploaded_file_objects if uploaded_files is empty, as this would remove the images when switching tabs.

if st.session_state.uploaded_file_objects:
    st.subheader("Your Current Uploads")
    
    images_html = "<div class='image-grid'>"
    for uploaded_file in st.session_state.uploaded_file_objects:
        encoded_image = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
        images_html += f"<div class='uploaded-image-container'><img src='data:{uploaded_file.type};base64,{encoded_image}' class='uploaded-image-thumbnail'/></div>"
    images_html += "</div>"
    
    st.markdown(images_html, unsafe_allow_html=True)
st.markdown("---")

# ----------------------------------------------------
# TAB 1: Image to Image (Seedream) - Unprotected
# ----------------------------------------------------
with tab_image:
    
    st.markdown("### Image Generation Parameters")
    
    col1, col2 = st.columns([4, 1])

    with col1:
        prompt = st.text_area("🖊 Prompt", placeholder="e.g., A fantastical creature made of crystals, surrounded by a swirling nebula.", height=100, key="image_prompt_input")
        st.session_state.prompt = prompt

    with col2:
        st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
        if st.button("🚀 Generate Image", key="generate_image_btn"):
            st.session_state.is_generating_clicked = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Generated Image Output
    if st.session_state.get('generated_images', {}).get('seedream'):
        st.subheader("Generated Images")
        
        cols = st.columns(len(st.session_state.generated_images['seedream']))
        
        for i, image_data in enumerate(st.session_state.generated_images['seedream']):
            with cols[i]:
                st.image(image_data['url'], use_container_width=True)
                
                st.download_button(
                    label="Download",
                    data=image_data['bytes'],
                    file_name=f"fal-image_{i+1}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png",
                    mime="image/png",
                )
    
    st.markdown("---")
        
    with st.expander("⚙️ Advanced Settings (Image-to-Image)"):
        st.markdown("Customize how the **Seedream** model generates your image.")
        
        resolution_options = {
            "512x512": (512, 512),
            "768x768": (768, 768),
            "1024x1024": (1024, 1024),
            "2048x2048 (2K)": (2048, 2048),
            "4096x4096 (4K)": (4096, 4096),
        }
        selected_resolution = st.selectbox("Select Resolution", list(resolution_options.keys()), index=2, key="img_resolution_select")
        st.session_state.width, st.session_state.height = resolution_options[selected_resolution]

        st.session_state.strength = st.slider("Strength (How much the image changes)", min_value=0.0, max_value=1.0, value=st.session_state.strength, step=0.01, key="img_strength_slider")
        st.session_state.guidance_scale = st.slider("Guidance Scale", min_value=1.0, max_value=15.0, value=st.session_state.guidance_scale, step=0.1, key="img_guidance_slider")
        st.session_state.num_images = st.slider("Number of Images", min_value=1, max_value=10, value=st.session_state.num_images, step=1, key="img_num_images_slider")
        st.session_state.num_inference_steps = st.slider("Inference Steps", min_value=10, max_value=150, value=st.session_state.num_inference_steps, step=1, key="img_steps_slider")
        seed_input = st.number_input("Seed (Optional, leave empty for random)", value=st.session_state.seed, step=1, format="%d", key="img_seed_input")
        st.session_state.seed = seed_input
        st.session_state.enable_safety_checker = st.checkbox("✅ Enable Safety Checker", value=st.session_state.enable_safety_checker, key="img_safety_check")

# ----------------------------------------------------
# TAB 2: Image to Video (Wan-I2V) - Protected
# ----------------------------------------------------
with tab_video:
    
    if st.session_state.video_authenticated:
        # --- Authenticated Content ---
        st.markdown("### Video Generation Parameters")
        
        col_v1, col_v2 = st.columns([4, 1])

        with col_v1:
            video_prompt = st.text_area("🖊 Video Prompt (What should the video show?)", placeholder="e.g., A majestic dragon flying over a cyberpunk city at night.", height=100, key="video_prompt_input")
            st.session_state.video_prompt = video_prompt
            st.info("The Wan-I2V model only uses the **first** uploaded image as the initial frame.")

        with col_v2:
            st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
            if st.button("🎥 Generate Video", key="generate_video_btn"):
                st.session_state.video_is_generating_clicked = True
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # Generated Video Output
        if st.session_state.get('video_generated_data'):
            st.subheader("Generated Video")
            video_data = st.session_state.video_generated_data
            
            # Display video using Streamlit's built-in video player
            st.video(video_data['bytes'], format='video/mp4')
            
            st.download_button(
                label="Download Video (MP4)",
                data=video_data['bytes'],
                file_name=f"fal-video_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp4",
                mime="video/mp4",
            )
        
        st.markdown("---")
            
        with st.expander("⚙️ Advanced Settings (Image-to-Video)"):
            st.markdown("Customize how the **Wan-I2V** model generates your video.")

            # Resolution options, 480P equivalent default
            video_resolution_options = {
                "480P (832x480)": (832, 480),
                "720P (1280x720)": (1280, 720),
            }
            selected_video_resolution = st.selectbox("Select Resolution", list(video_resolution_options.keys()), index=0, key="vid_resolution_select")
            st.session_state.video_width, st.session_state.video_height = video_resolution_options[selected_video_resolution]
            st.caption("Note: Higher resolutions take significantly longer to generate.")

            st.session_state.video_strength = st.slider("Strength (How much the video deviates from the image)", min_value=0.0, max_value=1.0, value=st.session_state.video_strength, step=0.01, key="vid_strength_slider")
            st.session_state.motion_bucket_id = st.slider("Motion Bucket ID (Controls amount of motion/activity)", min_value=1, max_value=255, value=st.session_state.motion_bucket_id, step=1, key="vid_motion_bucket_slider")
            st.session_state.cond_aug = st.slider("Conditioning Augmentation (Controls fidelity vs creativity)", min_value=0.0, max_value=0.1, value=st.session_state.cond_aug, step=0.01, format="%.2f", key="vid_cond_aug_slider")

            video_seed_input = st.number_input("Seed (Optional, leave empty for random)", value=st.session_state.video_seed, step=1, format="%d", key="vid_seed_input")
            st.session_state.video_seed = video_seed_input
            
            # Hardcoded to False as requested
            st.markdown("The **Enable Safety Checker** is set to **OFF (False)** for this model per your request.")
            
    else:
        # --- Authentication Form ---
        st.markdown("### 🔒 Video Generation (Wan-I2V) is Password Protected")
        st.warning("You need the correct password to access this advanced feature.")
        
        with st.form("video_login_form"):
            password_input = st.text_input("Enter Password", type="password")
            submitted = st.form_submit_button("Unlock Tab")
            
            if submitted:
                authenticate_video_tab(password_input)
                
        st.markdown("---")
        st.info("The password is **correct**.")
