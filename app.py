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
import time

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
    .st-emotion-cache-ch5d6d img {
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
    st.error("❌ FAL_KEY not found. Please set it in Streamlit secrets.")
    st.stop()

# Set the key for the fal_client
fal_client.key = FAL_KEY

# --- Cloudflare R2 Configuration and File Management ---
R2_BUCKET_NAME = get_secret("R2_BUCKET_NAME", "app-generations")

@st.cache_resource
def get_r2_client():
    """Creates and returns an S3 client configured for Cloudflare R2."""
    try:
        required_keys = ["R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT_URL"]
        if any(key not in st.secrets for key in required_keys):
            st.warning("R2 credentials not found in secrets. R2 upload will be disabled.")
            return None

        s3_client = boto3.client(
            's3',
            endpoint_url=st.secrets["R2_ENDPOINT_URL"],
            aws_access_key_id=st.secrets["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["R2_SECRET_ACCESS_KEY"],
            region_name='auto'
        )
        s3_client.list_buckets() # Test connection
        return s3_client
    except Exception as e:
        st.error(f"❌ R2 connection failed: {e}")
        return None

def ensure_bucket_exists(s3_client, bucket_name):
    """Ensures the R2 bucket exists."""
    if not s3_client: return False
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError:
        try:
            s3_client.create_bucket(Bucket=bucket_name)
            st.info(f"Created R2 bucket: {bucket_name}")
            return True
        except ClientError as create_error:
            st.error(f"❌ Failed to create bucket: {create_error}")
            return False

def upload_bytes_to_r2(s3_client, file_bytes, s3_key, bucket_name, content_type=None):
    """Uploads bytes to R2."""
    if not s3_client: return None
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

# --- R2 Save Functions ---
def save_image_generation(s3_client, uploaded_files, generated_image_data, generation_params):
    """Saves image generation artifacts to R2."""
    if not s3_client or not R2_BUCKET_NAME or not ensure_bucket_exists(s3_client, R2_BUCKET_NAME):
        return
    try:
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        generation_folder = f"{datetime.date.today():%Y-%m-%d}/image_generation_{timestamp_str}"
        
        for uploaded_file in uploaded_files:
            s3_key = f"{generation_folder}/uploads/{uploaded_file.name}"
            upload_bytes_to_r2(s3_client, uploaded_file.getvalue(), s3_key, R2_BUCKET_NAME, uploaded_file.type)
        
        for i, image_data in enumerate(generated_image_data):
            s3_key = f"{generation_folder}/outputs/output_image_{i+1}.png"
            upload_bytes_to_r2(s3_client, image_data['bytes'], s3_key, R2_BUCKET_NAME, 'image/png')
        
        params_json = json.dumps(generation_params, indent=4)
        s3_key = f"{generation_folder}/generation_parameters.json"
        upload_bytes_to_r2(s3_client, params_json.encode('utf-8'), s3_key, R2_BUCKET_NAME, 'application/json')
        
        st.success(f"Image generation saved to R2 (Folder: {generation_folder})")
    except Exception as e:
        st.error(f"Error saving image generation to R2: {str(e)}")

def save_video_generation(s3_client, uploaded_file, generated_video_data, generation_params):
    """Saves video generation artifacts to R2."""
    if not s3_client or not R2_BUCKET_NAME or not ensure_bucket_exists(s3_client, R2_BUCKET_NAME):
        return
    try:
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        generation_folder = f"{datetime.date.today():%Y-%m-%d}/video_generation_{timestamp_str}"

        s3_key_upload = f"{generation_folder}/upload/{uploaded_file.name}"
        upload_bytes_to_r2(s3_client, uploaded_file.getvalue(), s3_key_upload, R2_BUCKET_NAME, uploaded_file.type)

        s3_key_output = f"{generation_folder}/output/output_video.mp4"
        upload_bytes_to_r2(s3_client, generated_video_data['bytes'], s3_key_output, R2_BUCKET_NAME, 'video/mp4')
        
        params_json = json.dumps(generation_params, indent=4)
        s3_key_params = f"{generation_folder}/generation_parameters.json"
        upload_bytes_to_r2(s3_client, params_json.encode('utf-8'), s3_key_params, R2_BUCKET_NAME, 'application/json')
        
        st.success(f"Video generation saved to R2 (Folder: {generation_folder})")
    except Exception as e:
        st.error(f"Error saving video generation to R2: {str(e)}")


# --- Fal AI Upload Logic ---
@st.cache_data(ttl=3600) # Cache for 1 hour
def upload_file_to_fal(uploaded_file):
    """Uploads a single file to Fal AI and returns its URL."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_path = temp_file.name
    
    try:
        fal_url = fal_client.upload_file(temp_path)
    finally:
        os.unlink(temp_path) # Clean up temp file
    return fal_url

# --- Session State Initialization ---
# General
if 'is_generating_image' not in st.session_state: st.session_state.is_generating_image = False
if 'is_generating_video' not in st.session_state: st.session_state.is_generating_video = False

# Image Generation State
if 'generated_images' not in st.session_state: st.session_state.generated_images = {}
if 'uploaded_file_objects' not in st.session_state: st.session_state.uploaded_file_objects = None
if 'strength' not in st.session_state: st.session_state.strength = 0.95
if 'guidance_scale' not in st.session_state: st.session_state.guidance_scale = 4.5
if 'num_images' not in st.session_state: st.session_state.num_images = 1
if 'num_inference_steps' not in st.session_state: st.session_state.num_inference_steps = 40
if 'seed' not in st.session_state: st.session_state.seed = None
if 'enable_safety_checker' not in st.session_state: st.session_state.enable_safety_checker = False
if 'width' not in st.session_state: st.session_state.width = 1024
if 'height' not in st.session_state: st.session_state.height = 1024

# Video Generation State
if 'video_auth_ok' not in st.session_state: st.session_state.video_auth_ok = False
if 'video_uploaded_file' not in st.session_state: st.session_state.video_uploaded_file = None
if 'generated_video' not in st.session_state: st.session_state.generated_video = None
if 'video_prompt' not in st.session_state: st.session_state.video_prompt = ""
if 'video_negative_prompt' not in st.session_state: st.session_state.video_negative_prompt = "bright colors, overexposed, static, blurred details, subtitles, style, artwork, painting, picture, still, overall gray, worst quality, low quality, etc."
if 'video_width' not in st.session_state: st.session_state.video_width = 832
if 'video_height' not in st.session_state: st.session_state.video_height = 480
if 'video_num_frames' not in st.session_state: st.session_state.video_num_frames = 81
if 'video_fps' not in st.session_state: st.session_state.video_fps = 16
if 'video_num_inference_steps' not in st.session_state: st.session_state.video_num_inference_steps = 50
if 'video_strength' not in st.session_state: st.session_state.video_strength = 0.7
if 'motion_bucket_id' not in st.session_state: st.session_state.motion_bucket_id = 127
if 'cond_aug' not in st.session_state: st.session_state.cond_aug = 0.02
if 'video_lora_weight' not in st.session_state: st.session_state.video_lora_weight = 0.7
if 'video_safety_checker' not in st.session_state: st.session_state.video_safety_checker = False
if 'video_seed' not in st.session_state: st.session_state.video_seed = None


# --- Main App Logic and Functions ---

def generate_images():
    """Handles the Fal AI image generation process."""
    try:
        st.session_state.generated_images = {}
        if not st.session_state.uploaded_file_objects:
            st.error("❌ Please upload at least one image before generating.")
            return
        if not st.session_state.get('prompt', '').strip():
            st.error("❌ Please enter a prompt before generating.")
            return

        uploaded_image_urls = [upload_file_to_fal(f) for f in st.session_state.uploaded_file_objects]
        
        base_prompt = " .same exact face from the original photo preserved realistically with full details. keep proportions. refine details, enhanced quality, high-definition, high-fidelity, high-resolution, DSLR quality."
        final_prompt = st.session_state.prompt + base_prompt

        arguments = {
            "image_urls": uploaded_image_urls,
            "prompt": final_prompt,
            "strength": st.session_state.strength,
            "guidance_scale": st.session_state.guidance_scale,
            "num_images": st.session_state.num_images,
            "num_inference_steps": st.session_state.num_inference_steps,
            "enable_safety_checker": st.session_state.enable_safety_checker,
            "width": st.session_state.width,
            "height": st.session_state.height,
            "seed": int(st.session_state.seed) if st.session_state.seed else None
        }

        response = fal_client.run("fal-ai/bytedance/seedream/v4/edit", arguments=arguments)
        
        if 'images' in response and response['images']:
            image_data_with_bytes = []
            for image in response['images']:
                with urlopen(image['url']) as img_response:
                    image_bytes = BytesIO(img_response.read()).getvalue()
                    image_data_with_bytes.append({'url': image['url'], 'bytes': image_bytes})
            st.session_state.generated_images['seedream'] = image_data_with_bytes

            generation_params = {k: v for k, v in arguments.items() if k != "image_urls"}
            generation_params.update({
                "timestamp": datetime.datetime.now().isoformat(),
                "model": "Seedream 4",
                "generated_urls": [img['url'] for img in image_data_with_bytes]
            })
            
            s3_client = get_r2_client()
            if s3_client:
                save_image_generation(s3_client, st.session_state.uploaded_file_objects, image_data_with_bytes, generation_params)
        else:
            st.error("❌ No images were generated. Please try again.")
    except Exception as e:
        st.error(f"❌ An error occurred during image generation: {str(e)}")
    finally:
        st.session_state.is_generating_image = False


def generate_video():
    """Handles the Fal AI video generation process."""
    try:
        st.session_state.generated_video = None
        if not st.session_state.video_uploaded_file:
            st.error("❌ Please upload an image for video generation.")
            return
        if not st.session_state.video_prompt.strip():
            st.error("❌ Please enter a prompt for video generation.")
            return

        image_url = upload_file_to_fal(st.session_state.video_uploaded_file)
        
        payload = {
            "prompt": st.session_state.video_prompt,
            "image_url": image_url,
            "negative_prompt": st.session_state.video_negative_prompt,
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
            "seed": int(st.session_state.video_seed) if st.session_state.video_seed else None
        }

        handler = fal_client.submit("fal-ai/wan-i2v", arguments=payload)
        
        # Stream logs while waiting
        progress_bar = st.progress(0, text="Job submitted... waiting for logs.")
        logs = []
        for i, log in enumerate(handler.iter_logs(stream=True)):
            if 'message' in log:
                logs.append(log['message'])
                progress_text = f"Generating... ({log['message']})"
                # Update progress bar - this is a rough estimation
                progress_value = min(i / (st.session_state.video_num_inference_steps * 1.5), 1.0) # Heuristic
                progress_bar.progress(progress_value, text=progress_text)
        
        progress_bar.progress(1.0, text="Finalizing video...")
        result = handler.get()
        progress_bar.empty()

        if result and result.get('video') and result['video'].get('url'):
            video_url = result['video']['url']
            with urlopen(video_url) as video_response:
                video_bytes = video_response.read()
            st.session_state.generated_video = {'url': video_url, 'bytes': video_bytes}

            generation_params = {k: v for k, v in payload.items() if k != "image_url"}
            generation_params.update({
                "timestamp": datetime.datetime.now().isoformat(),
                "model": "fal-ai/wan-i2v",
                "generated_url": video_url
            })

            s3_client = get_r2_client()
            if s3_client:
                save_video_generation(s3_client, st.session_state.video_uploaded_file, st.session_state.generated_video, generation_params)
        else:
            st.error("❌ Video generation failed or returned no result.")
            st.json(result) # Show the raw response for debugging

    except Exception as e:
        st.error(f"❌ An error occurred during video generation: {str(e)}")
    finally:
        st.session_state.is_generating_video = False

# --- UI Layout ---

# Handle loading overlays
if st.session_state.is_generating_image:
    st.markdown('<div class="loading-overlay"><div class="spinner-icon"></div><div>Generating your image...</div></div>', unsafe_allow_html=True)
    generate_images()
    st.rerun()

if st.session_state.is_generating_video:
    st.markdown('<div class="loading-overlay"><div class="spinner-icon"></div><div>Generating your video... this may take a moment.</div></div>', unsafe_allow_html=True)
    generate_video()
    st.rerun()

# Main Header
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try:
        st.image("logo.png", use_container_width=True)
    except Exception:
        st.markdown("<div style='height: 110px;'></div>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1>NANO BANANA X AI</h1>", unsafe_allow_html=True)
    st.markdown("<h2>Generative AI Suite <span class='banana-icon'>🍌</span></h2>", unsafe_allow_html=True)

# Tabs
tab1, tab2 = st.tabs(["Image Generation", "Video Generation"])

# --- Image Generation Tab ---
with tab1:
    st.markdown("""
    - **Upload your images:** Upload 1 - 4 images to serve as the basis for your new creation.
    - **Craft a detailed prompt:** Write a clear and descriptive prompt to guide the AI's generation process.
    - **Generate your image:** Click the 'Generate' button to begin the AI transformation.
    - **Uncensored Model:** This is an uncensored model version; please use it responsibly.
    - **Private Use:** <span class="private-warning">Please do not share this website with others!</span>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([4, 1])
    with col1:
        st.session_state.prompt = st.text_area("🖊 Prompt", placeholder="e.g., A fantastical creature made of crystals, surrounded by a swirling nebula.", height=100, key="image_prompt")
    with col2:
        st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
        if st.button("🚀 Generate Image"):
            st.session_state.is_generating_image = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    image_cols = st.columns(2)
    with image_cols[0]:
        uploaded_files = st.file_uploader("🖼️ Upload one or more images", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key="image_uploader")
        if uploaded_files:
            st.session_state.uploaded_file_objects = uploaded_files
        
        if st.session_state.uploaded_file_objects:
            st.subheader("Your Uploaded Images")
            images_html = "<div class='image-grid'>"
            for f in st.session_state.uploaded_file_objects:
                encoded_image = base64.b64encode(f.getvalue()).decode("utf-8")
                images_html += f"<div class='uploaded-image-container'><img src='data:{f.type};base64,{encoded_image}' class='uploaded-image-thumbnail'/></div>"
            images_html += "</div>"
            st.markdown(images_html, unsafe_allow_html=True)
    
    with image_cols[1]:
        if st.session_state.get('generated_images', {}).get('seedream'):
            st.subheader("Generated Images")
            cols = st.columns(len(st.session_state.generated_images['seedream']))
            for i, image_data in enumerate(st.session_state.generated_images['seedream']):
                with cols[i]:
                    st.image(image_data['url'], use_container_width=True)
                    st.download_button(
                        label="Download", data=image_data['bytes'],
                        file_name=f"fal-image_{i+1}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png", mime="image/png"
                    )
            
    st.markdown("---")
    with st.expander("⚙️ Advanced Image Settings"):
        resolution_options = {"512x512": (512, 512), "768x768": (768, 768), "1024x1024": (1024, 1024), "2048x2048 (2K)": (2048, 2048)}
        selected_resolution = st.selectbox("Select Resolution", list(resolution_options.keys()), index=2, key="image_res")
        st.session_state.width, st.session_state.height = resolution_options[selected_resolution]
        st.session_state.strength = st.slider("Strength", 0.0, 1.0, st.session_state.strength, 0.01, key="image_strength")
        st.session_state.guidance_scale = st.slider("Guidance Scale", 1.0, 15.0, st.session_state.guidance_scale, 0.1, key="image_guidance")
        st.session_state.num_images = st.slider("Number of Images", 1, 10, st.session_state.num_images, 1, key="image_num")
        st.session_state.num_inference_steps = st.slider("Inference Steps", 10, 150, st.session_state.num_inference_steps, 1, key="image_steps")
        st.session_state.seed = st.number_input("Seed (Optional)", value=None, step=1, format="%d", key="image_seed")
        st.session_state.enable_safety_checker = st.checkbox("✅ Enable Safety Checker", st.session_state.enable_safety_checker, key="image_safety")

# --- Video Generation Tab ---
with tab2:
    VIDEO_PASSWORD = get_secret("VIDEO_PASSWORD")

    if not VIDEO_PASSWORD:
        st.error("Video Password not set. Please configure the `VIDEO_PASSWORD` secret to enable this feature.")
    elif not st.session_state.video_auth_ok:
        st.subheader("🔒 Access Required")
        password = st.text_input("Enter password to access Video Generation:", type="password")
        if st.button("Unlock"):
            if password == VIDEO_PASSWORD:
                st.session_state.video_auth_ok = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    else:
        st.markdown("""
        - **Upload an image:** This will be the starting frame and guide for the video.
        - **Write a prompt:** Describe the motion or transformation you want to see.
        - **Generate:** Click the button to create your video. This can take several minutes.
        """, unsafe_allow_html=True)

        v_col1, v_col2 = st.columns([4, 1])
        with v_col1:
            st.session_state.video_prompt = st.text_area("🖊 Video Prompt", placeholder="e.g., A cinematic drone shot flying forward through the scene.", height=100, key="video_prompt_input")
            st.session_state.video_negative_prompt = st.text_area("🖊 Negative Prompt", value=st.session_state.video_negative_prompt, height=100, key="video_neg_prompt")
        with v_col2:
            st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
            if st.button("🎬 Generate Video"):
                st.session_state.is_generating_video = True
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        v_res_col1, v_res_col2 = st.columns(2)
        with v_res_col1:
            video_file = st.file_uploader("🖼️ Upload an image for the video", type=["png", "jpg", "jpeg", "webp"], key="video_uploader")
            if video_file:
                st.session_state.video_uploaded_file = video_file
            if st.session_state.video_uploaded_file:
                st.subheader("Your Uploaded Image")
                st.image(st.session_state.video_uploaded_file, use_container_width=True)

        with v_res_col2:
            if st.session_state.generated_video:
                st.subheader("Generated Video")
                st.video(st.session_state.generated_video['url'])
                st.download_button(
                    label="Download Video", data=st.session_state.generated_video['bytes'],
                    file_name=f"fal-video_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp4", mime="video/mp4"
                )
        
        st.markdown("---")
        with st.expander("⚙️ Advanced Video Settings"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.session_state.video_width = st.number_input("Width", value=st.session_state.video_width, key="vid_w")
                st.session_state.video_height = st.number_input("Height", value=st.session_state.video_height, key="vid_h")
                st.session_state.video_num_frames = st.slider("Number of Frames", 10, 150, st.session_state.video_num_frames, 1, key="vid_frames")
                st.session_state.video_fps = st.slider("FPS", 5, 30, st.session_state.video_fps, 1, key="vid_fps")
                st.session_state.motion_bucket_id = st.slider("Motion Bucket ID", 1, 255, st.session_state.motion_bucket_id, 1, key="vid_motion")
            with c2:
                st.session_state.video_num_inference_steps = st.slider("Inference Steps", 10, 100, st.session_state.video_num_inference_steps, 1, key="vid_steps")
                st.session_state.video_strength = st.slider("Strength (Image influence)", 0.0, 1.0, st.session_state.video_strength, 0.01, key="vid_strength")
                st.session_state.cond_aug = st.slider("Conditioning Augmentation", 0.0, 0.1, st.session_state.cond_aug, 0.001, format="%.3f", key="vid_cond")
                st.session_state.video_lora_weight = st.slider("LoRA Weight", 0.0, 1.0, st.session_state.video_lora_weight, 0.01, key="vid_lora")
            with c3:
                st.session_state.video_seed = st.number_input("Seed (Optional)", value=None, step=1, format="%d", key="vid_seed")
                st.session_state.video_safety_checker = st.checkbox("✅ Enable Safety Checker", st.session_state.video_safety_checker, key="vid_safety")

