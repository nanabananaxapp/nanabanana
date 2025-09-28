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

# Custom CSS for a dark, minimalist look
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
    
    /* Ensure good button styling */
    .stButton>button {
        font-weight: bold;
    }
    
    /* Full-page loading spinner */
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.85);
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
        border: 8px solid rgba(255, 255, 255, 0.3);
        border-top: 8px solid #4169E1; /* Royal Blue */
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

# Set the Fal key globally for fal_client.run() - FIX FOR ATTRIBUTE ERROR
fal_client.key = FAL_KEY

# --- Cloudflare R2 Configuration and File Management ---
# R2 bucket name - you can change this or keep it in secrets
R2_BUCKET_NAME = get_secret("R2_BUCKET_NAME", "app-generations")

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
            return None

        # Create S3 client configured for R2
        s3_client = boto3.client(
            's3',
            endpoint_url=st.secrets["R2_ENDPOINT_URL"],
            aws_access_key_id=st.secrets["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["R2_SECRET_ACCESS_KEY"],
            region_name='auto' # R2 uses 'auto' for region
        )
        
        # Test connection by listing buckets
        s3_client.list_buckets()
        return s3_client
        
    except ClientError:
        return None
    except Exception:
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
                return True
            except ClientError:
                return False
        else:
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
    except ClientError:
        return None


def save_generation(s3_client, uploaded_files, generated_image_data, generation_params, folder_prefix="generation"):
    """Saves image generation data (Seedream) to R2."""
    if not s3_client or not R2_BUCKET_NAME:
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
        
    except Exception:
        pass # Silently fail R2 errors

def save_video_generation(s3_client, uploaded_files, generated_video_data, generation_params, folder_prefix="video_generation"):
    """Saves video generation data (Wan-I2V) to R2."""
    if not s3_client or not R2_BUCKET_NAME:
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
        
    except Exception:
        pass # Silently fail R2 errors

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
        # Use tempfile to handle file bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.type.split('/')[-1]}") as temp_file:
            temp_file.write(uploaded_file.getvalue())
            fal_image_url = fal_client.upload_file(temp_file.name)
            uploaded_image_urls[file_id] = fal_image_url
        os.unlink(temp_file.name)
    
    # Update the session state cache for next rerun/generation
    st.session_state.uploaded_image_urls.update(uploaded_image_urls)
    return uploaded_image_urls

# --- Session State Initialization ---
# Seedream (Image-to-Image) Defaults
if 'generated_images' not in st.session_state: st.session_state.generated_images = {}
if 'strength' not in st.session_state: st.session_state.strength = 0.95
if 'guidance_scale' not in st.session_state: st.session_state.guidance_scale = 4.5
if 'num_images' not in st.session_state: st.session_state.num_images = 1
if 'num_inference_steps' not in st.session_state: st.session_state.num_inference_steps = 40
if 'seed' not in st.session_state: st.session_state.seed = None
if 'enable_safety_checker' not in st.session_state: st.session_state.enable_safety_checker = False
if 'width' not in st.session_state: st.session_state.width = 1024 # Default to 1024
if 'height' not in st.session_state: st.session_state.height = 1024 # Default to 1024
if 'is_generating_clicked' not in st.session_state: st.session_state.is_generating_clicked = False
if 'prompt' not in st.session_state: st.session_state.prompt = ""
if 'negative_prompt' not in st.session_state: st.session_state.negative_prompt = "low quality, bad anatomy, bad hands, low resolution, worst quality, watermark"

# Wan-I2V (Image-to-Video) Defaults
if 'video_generated_data' not in st.session_state: st.session_state.video_generated_data = None
if 'video_prompt' not in st.session_state: st.session_state.video_prompt = ""
if 'video_negative_prompt' not in st.session_state: st.session_state.video_negative_prompt = "" 
if 'video_strength' not in st.session_state: st.session_state.video_strength = 0.95
if 'motion_bucket_id' not in st.session_state: st.session_state.motion_bucket_id = 127
if 'cond_aug' not in st.session_state: st.session_state.cond_aug = 0.02
if 'video_width' not in st.session_state: st.session_state.video_width = 832  
if 'video_height' not in st.session_state: st.session_state.video_height = 480 
if 'video_num_inference_steps' not in st.session_state: st.session_state.video_num_inference_steps = 50 
if 'video_fps' not in st.session_state: st.session_state.video_fps = 12 
if 'video_num_frames' not in st.session_state: st.session_state.video_num_frames = 16 
if 'video_lora_weight' not in st.session_state: st.session_state.video_lora_weight = 0.7 
if 'video_safety_checker' not in st.session_state: st.session_state.video_safety_checker = False 
if 'video_is_generating_clicked' not in st.session_state: st.session_state.video_is_generating_clicked = False
if 'video_seed' not in st.session_state: st.session_state.video_seed = None
if 'video_authenticated' not in st.session_state: st.session_state.video_authenticated = False 

# Common Session State
if 'uploaded_file_objects' not in st.session_state: st.session_state.uploaded_file_objects = None
if 'uploaded_image_urls' not in st.session_state: st.session_state.uploaded_image_urls = {}

# --- Authentication Logic ---
def authenticate_video_tab(password_attempt):
    """Checks the password and updates session state."""
    if password_attempt == VIDEO_PASSWORD:
        st.session_state.video_authenticated = True
        st.success("✅ Access Granted!")
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
        
        # Base prompt for Seedream
        base_prompt = ", Do not change the face appearance, the person's body structure is always like the original!!! But pose and the scene and moment and can be different when relevant. change outfit only when asked to. amazing details, detailed real skin-texture, body parts are always very detailed, perfect, and realistic. top camera quality, refine details, enhanced quality!! 8k, very detailed,high-definition, high-fidelity, high-resolution, DSLR quality."
        
        final_prompt = current_prompt + base_prompt

        arguments = {
            "image_urls": list(uploaded_file_urls.values()),
            "prompt": final_prompt,
            "negative_prompt": st.session_state.negative_prompt,
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

        # Using fal_client.run directly
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
                "negative_prompt": st.session_state.negative_prompt,
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
            # Subtle warning, not disruptive
            st.sidebar.warning("⚠️ Video model uses only the first uploaded image.")

        current_prompt = st.session_state.get('video_prompt', '').strip()
        if not current_prompt:
            st.error("❌ Please enter a prompt before generating.")
            st.session_state.video_is_generating_clicked = False
            return
        
        # Upload image to Fal (or use cached URLs)
        uploaded_file_urls = upload_files_to_fal(uploaded_files)
        image_url_to_use = list(uploaded_file_urls.values())[0]

        arguments = {
            "image_url": image_url_to_use,
            "prompt": current_prompt,
            "negative_prompt": st.session_state.video_negative_prompt, 
            "strength": st.session_state.video_strength,
            "motion_bucket_id": st.session_state.motion_bucket_id,
            "cond_aug": st.session_state.cond_aug,
            "width": st.session_state.video_width,
            "height": st.session_state.video_height,
            "num_inference_steps": st.session_state.video_num_inference_steps, 
            "fps": st.session_state.video_fps, 
            "num_frames": st.session_state.video_num_frames, 
            "lora_weight": st.session_state.video_lora_weight, 
            "enable_safety_checker": st.session_state.video_safety_checker
        }
        
        if st.session_state.video_seed is not None:
            arguments["seed"] = int(st.session_state.video_seed)

        # Use st.spinner for in-line feedback
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
                "prompt": current_prompt,
                "negative_prompt": st.session_state.video_negative_prompt,
                "strength": st.session_state.video_strength,
                "motion_bucket_id": st.session_state.motion_bucket_id,
                "cond_aug": st.session_state.cond_aug,
                "num_inference_steps": st.session_state.video_num_inference_steps,
                "fps": st.session_state.video_fps,
                "num_frames": st.session_state.video_num_frames,
                "lora_weight": st.session_state.video_lora_weight,
                "enable_safety_checker": st.session_state.video_safety_checker,
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


st.title("NANO BANANA X AI")
st.subheader("Image and Video Generator")

st.markdown("---")

# --- Tabs Implementation ---
tab_image, tab_video = st.tabs(["🖼️ Image to Image (Seedream)", "🎥 Image to Video (Wan-I2V)"])


# --- Common File Uploader Section ---
st.subheader("Source Image Uploader")
uploaded_files = st.file_uploader("Upload one or more images (JPG, PNG, WebP)", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key="main_uploader")

if uploaded_files:
    st.session_state.uploaded_file_objects = uploaded_files

if st.session_state.uploaded_file_objects:
    st.markdown("**Your Current Uploads**")
    
    # Display thumbnails (simpler display)
    cols = st.columns(min(len(st.session_state.uploaded_file_objects), 4))
    for i, uploaded_file in enumerate(st.session_state.uploaded_file_objects):
        if i < 4: # Limit displayed thumbnails to 4 for simplicity
            try:
                # Use st.image for cleaner display
                caption = f"Image {i+1}"
                if i == 0:
                    caption += " (Used for Video)"
                cols[i].image(uploaded_file, caption=caption, use_column_width="always")
            except Exception:
                # Fallback for display if file type is problematic
                cols[i].text(f"{uploaded_file.name}")
st.markdown("---")


# ----------------------------------------------------
# TAB 1: Image to Image (Seedream) - Unprotected
# ----------------------------------------------------
with tab_image:
    
    st.markdown("### **Image Generation Parameters**")
    
    col_controls, col_output = st.columns([1, 1])

    with col_controls:
        # Prompt and Negative Prompt
        prompt = st.text_area("🖊 Prompt", placeholder="e.g., A fantastical creature made of crystals, surrounded by a swirling nebula.", height=100, key="image_prompt_input")
        st.session_state.prompt = prompt

        negative_prompt = st.text_area("🚫 Negative Prompt", placeholder="e.g., low quality, blurry, bad hands.", height=70, key="image_negative_prompt_input")
        st.session_state.negative_prompt = negative_prompt

        # Advanced Settings
        st.markdown("---")
        with st.expander("⚙️ Advanced Settings"):
            
            resolution_options = {
                "512x512": (512, 512),
                "768x768": (768, 768),
                "1024x1024": (1024, 1024),
                "2048x2048 (2K)": (2048, 2048),
                "4096x4096 (4K)": (4096, 4096),
            }
            # Find the correct default index based on current state (1024x1024)
            current_res = f"{st.session_state.width}x{st.session_state.height}"
            # Ensure the key exists before indexing
            default_key = next((k for k, v in resolution_options.items() if v == (st.session_state.width, st.session_state.height)), "1024x1024")
            default_index = list(resolution_options.keys()).index(default_key)

            selected_resolution = st.selectbox("Resolution", list(resolution_options.keys()), index=default_index, key="img_resolution_select")
            st.session_state.width, st.session_state.height = resolution_options[selected_resolution]

            st.session_state.strength = st.slider("Strength (Image Fidelity)", min_value=0.0, max_value=1.0, value=st.session_state.strength, step=0.01, key="img_strength_slider")
            st.session_state.guidance_scale = st.slider("Guidance Scale (CFG)", min_value=1.0, max_value=15.0, value=st.session_state.guidance_scale, step=0.1, key="img_guidance_slider")
            st.session_state.num_images = st.slider("Number of Images", min_value=1, max_value=4, value=st.session_state.num_images, step=1, key="img_num_images_slider")
            st.session_state.num_inference_steps = st.slider("Inference Steps", min_value=10, max_value=150, value=st.session_state.num_inference_steps, step=1, key="img_steps_slider")
            seed_input = st.number_input("Seed (0 for random)", value=st.session_state.seed if st.session_state.seed is not None else 0, step=1, format="%d", key="img_seed_input")
            st.session_state.seed = seed_input if seed_input != 0 else None
            st.session_state.enable_safety_checker = st.checkbox("Enable Safety Checker", value=st.session_state.enable_safety_checker, key="img_safety_check")

        st.button("🚀 Generate Image", key="generate_image_btn", type="primary", use_container_width=True)
        if st.session_state.generate_image_btn:
            st.session_state.is_generating_clicked = True
            st.rerun()
        
    with col_output:
        st.subheader("Generated Images")
        
        if st.session_state.get('generated_images', {}).get('seedream'):
            num_results = len(st.session_state.generated_images['seedream'])
            cols_output = st.columns(min(num_results, 2))
            
            for i, image_data in enumerate(st.session_state.generated_images['seedream']):
                # Cycle through 2 columns for layout
                with cols_output[i % 2]:
                    st.image(image_data['url'], caption=f"Result {i+1}", use_container_width=True)
                    
                    st.download_button(
                        label="Download",
                        data=image_data['bytes'],
                        file_name=f"fal-image_{i+1}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png",
                        mime="image/png",
                        use_container_width=True
                    )
        else:
            st.info("Your generated image(s) will appear here.")
            st.image("https://placehold.co/1024x1024/2f2f2f/cccccc?text=Output+Preview", use_column_width="auto")

# ----------------------------------------------------
# TAB 2: Image to Video (Wan-I2V) - Protected
# ----------------------------------------------------
with tab_video:
    
    if st.session_state.video_authenticated:
        # --- Authenticated Content ---
        st.markdown("### **Video Generation Parameters**")
        
        col_v_controls, col_v_output = st.columns([1, 1])

        with col_v_controls:
            # Prompts
            video_prompt = st.text_area("🖊 Video Prompt", placeholder="e.g., A majestic dragon flying over a cyberpunk city at night.", height=100, key="video_prompt_input")
            st.session_state.video_prompt = video_prompt
            
            video_negative_prompt = st.text_area("🚫 Negative Prompt", placeholder="e.g., blurry, out of focus, poor quality, watermark, text.", height=70, key="video_negative_prompt_input")
            st.session_state.video_negative_prompt = video_negative_prompt
            
            # Advanced Settings (All features included)
            st.markdown("---")
            with st.expander("⚙️ Advanced Settings (Wan-I2V)"):
                
                col_res, col_frames = st.columns(2)
                with col_res:
                    video_resolution_options = {
                        "832x480": (832, 480),
                        "1280x720 (720P)": (1280, 720),
                    }
                    selected_video_resolution = st.selectbox("Resolution", list(video_resolution_options.keys()), index=0, key="vid_resolution_select")
                    st.session_state.video_width, st.session_state.video_height = video_resolution_options[selected_video_resolution]

                with col_frames:
                    st.session_state.video_num_frames = st.slider("Number of Frames (16 to 64)", min_value=16, max_value=64, value=st.session_state.video_num_frames, step=16, key="vid_num_frames_slider")
                    
                col_steps, col_fps = st.columns(2)
                with col_steps:
                    st.session_state.video_num_inference_steps = st.slider("Inference Steps", min_value=10, max_value=100, value=st.session_state.video_num_inference_steps, step=1, key="vid_steps_slider")
                with col_fps:
                    st.session_state.video_fps = st.slider("FPS (Max 12)", min_value=1, max_value=12, value=st.session_state.video_fps, step=1, key="vid_fps_slider")


                st.session_state.video_strength = st.slider("Strength (Deviation from Image)", min_value=0.0, max_value=1.0, value=st.session_state.video_strength, step=0.01, key="vid_strength_slider")
                st.session_state.motion_bucket_id = st.slider("Motion Bucket ID (Movement amount)", min_value=1, max_value=255, value=st.session_state.motion_bucket_id, step=1, key="vid_motion_bucket_slider")
                st.session_state.cond_aug = st.slider("Conditioning Augmentation (Fidelity/Creativity)", min_value=0.0, max_value=0.1, value=st.session_state.cond_aug, step=0.01, format="%.2f", key="vid_cond_aug_slider")
                st.session_state.video_lora_weight = st.slider("LoRA Weight", min_value=0.0, max_value=1.0, value=st.session_state.video_lora_weight, step=0.01, key="vid_lora_weight_slider")
                
                col_seed, col_safety = st.columns(2)
                with col_seed:
                    video_seed_input = st.number_input("Seed (0 for random)", value=st.session_state.video_seed if st.session_state.video_seed is not None else 0, step=1, format="%d", key="vid_seed_input")
                    st.session_state.video_seed = video_seed_input if video_seed_input != 0 else None
                with col_safety:
                    st.session_state.video_safety_checker = st.checkbox("Enable Safety Checker", value=st.session_state.video_safety_checker, key="vid_safety_check")

            st.button("🎥 Generate Video", key="generate_video_btn", type="primary", use_container_width=True)
            if st.session_state.generate_video_btn:
                st.session_state.video_is_generating_clicked = True
                st.rerun()
            
        with col_v_output:
            st.subheader("Generated Video")
            
            if st.session_state.get('video_generated_data'):
                video_data = st.session_state.video_generated_data
                
                st.video(video_data['bytes'], format='video/mp4')
                
                st.download_button(
                    label="Download Video (MP4)",
                    data=video_data['bytes'],
                    file_name=f"fal-video_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
            else:
                st.info("Your generated video will appear here.")
                st.image("https://placehold.co/832x480/2f2f2f/cccccc?text=Video+Output+Preview", use_column_width="auto")
            
    else:
        # --- Authentication Form ---
        st.markdown("### 🔒 Video Generation is Password Protected")
        st.warning("Please enter the password to access this feature.")
        
        with st.form("video_login_form"):
            password_input = st.text_input("Enter Password", type="password")
            submitted = st.form_submit_button("Unlock Tab", type="primary")
            
            if submitted:
                authenticate_video_tab(password_input)
