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
    st.error("❌.")
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
            st.warning(f" {', '.join(missing_keys)}. .")
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
        st.info("")
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
                st.info(f"{bucket_name}")
                return True
            except ClientError as create_error:
                st.error(f"❌ Failed to create bucket: {create_error}")
                return False
        else:
            st.error(f"❌ Error checking bucket: {e}")
            return False


def upload_to_r2(s3_client, file_path, s3_key, bucket_name, content_type=None):
    """Uploads a file to Cloudflare R2."""
    if not s3_client:
        return None
    
    try:
        if content_type is None:
            import mimetypes
            content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        
        with open(file_path, 'rb') as f:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=f,
                ContentType=content_type
            )
        return s3_key
    except ClientError as e:
        st.warning(f"{str(e)}")
        return None


def upload_bytes_to_r2(s3_client, file_bytes, s3_key, bucket_name, content_type=None):
    """R2."""
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


def save_generation(s3_client, uploaded_files, generated_image_data, generation_params):
    """R2."""
    if not s3_client:
        return
    
    if not R2_BUCKET_NAME:
        st.warning("⚠")
        return
    
    # Ensure bucket exists
    if not ensure_bucket_exists(s3_client, R2_BUCKET_NAME):
        return
    
    try:
        # Create the folder structure using S3 key prefixes
        date_folder = datetime.date.today().strftime("%Y-%m-%d")
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        generation_folder = f"{date_folder}/generation_{timestamp_str}"
        
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
        
        st.success(f"(Folder: {generation_folder})")
        
    except Exception as e:
        st.error(f"{str(e)}")


# --- Fal AI Cache and Generation Logic ---
@st.cache_data
def upload_files_to_fal(uploaded_files):
    """Caches the Fal AI URLs for uploaded files to prevent repeated uploads."""
    uploaded_image_urls = {}
    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.type.split('/')[-1]}") as temp_file:
            temp_file.write(uploaded_file.getvalue())
            fal_image_url = fal_client.upload_file(temp_file.name)
            uploaded_image_urls[f"{uploaded_file.name}_{uploaded_file.size}"] = fal_image_url
        os.unlink(temp_file.name)
    return uploaded_image_urls

# --- Session State Initialization ---
if 'generated_images' not in st.session_state: st.session_state.generated_images = {}
if 'uploaded_file_objects' not in st.session_state: st.session_state.uploaded_file_objects = None
if 'uploaded_image_urls' not in st.session_state: st.session_state.uploaded_image_urls = {}
if 'strength' not in st.session_state: st.session_state.strength = 0.95
if 'guidance_scale' not in st.session_state: st.session_state.guidance_scale = 4.5
if 'num_images' not in st.session_state: st.session_state.num_images = 1
if 'num_inference_steps' not in st.session_state: st.session_state.num_inference_steps = 40
if 'seed' not in st.session_state: st.session_state.seed = None
if 'enable_safety_checker' not in st.session_state: st.session_state.enable_safety_checker = False
if 'width' not in st.session_state: st.session_state.width = 2048
if 'height' not in st.session_state: st.session_state.height = 2048
if 'is_generating_clicked' not in st.session_state: st.session_state.is_generating_clicked = False

# --- Main App Logic and Functions ---

def generate_images():
    """Handles the Fal AI generation process."""
    try:
        st.session_state.generated_images = {}
        
        if not st.session_state.uploaded_file_objects:
            st.error("❌ Please upload at least one image before generating.")
            st.session_state.is_generating_clicked = False
            return
        
        if not st.session_state.get('prompt', '').strip():
            st.error("❌ Please enter a prompt before generating.")
            st.session_state.is_generating_clicked = False
            return
        
        st.session_state.uploaded_image_urls = upload_files_to_fal(st.session_state.uploaded_file_objects)
        
        base_prompt = " . Do not change the face appearance, the person's body structure is always like the original!!! But pose and the scene and moment and can be different when relevant. change outfit only when asked to. amazing details, detailed real skin-texture, body parts are always very detailed, perfect, and realistic. top camera quality, refine details, enhanced quality!! 8k, very detailed,high-definition, high-fidelity, high-resolution, DSLR quality. image feels like a genuine high-end professional photo or candid capture."
        
        # Swapping the order of prompts
        final_prompt = st.session_state.prompt + base_prompt

        arguments = {
            "image_urls": list(st.session_state.uploaded_image_urls.values()),
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
        st.error(f"❌ An error occurred during generation: {str(e)}")
    finally:
        st.session_state.is_generating_clicked = False


# --- UI Layout ---

if st.session_state.is_generating_clicked:
    st.markdown(f"""
    <div class="loading-overlay">
        <div class="spinner-icon"></div>
        <div class="spinner-text">{"Working on your masterpiece..."}</div>
    </div>
    """, unsafe_allow_html=True)
    generate_images()
    st.rerun()


col_logo, col_title = st.columns([1, 5])
with col_logo:
    try:
        st.image("logo.png", use_container_width=True)
    except Exception:
        st.markdown("<div style='height: 110px;'></div>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1>NANO BANANA X AI</h1>", unsafe_allow_html=True)
    st.markdown("<h2>Image to Image Generator <span class='banana-icon'>🍌</span></h2>", unsafe_allow_html=True)

st.markdown("""
- **Upload your images:** Upload 1 - 4 images to serve as the basis for your new creation.
- **Craft a detailed prompt:** Write a clear and descriptive prompt to guide the AI's generation process.
- **Generate your image:** Click the 'Generate' button to begin the AI transformation.
- **Optimize results:** For the best quality, we recommend using the default settings.
- **Uncensored Model:** This is an uncensored model version; please use it responsibly.
- Do not share: This is a private, unshared version of the model. To ensure low resource usage, <span class="private-warning">please do not share this website with others!</span>
""", unsafe_allow_html=True)

col1, col2 = st.columns([4, 1])

with col1:
    prompt = st.text_area("🖊 Prompt", placeholder="e.g., A fantastical creature made of crystals, surrounded by a swirling nebula.", height=100)
    st.session_state.prompt = prompt

with col2:
    st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
    if st.button("🚀 Generate"):
        st.session_state.is_generating_clicked = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    
image_cols = st.columns([1, 1])

with image_cols[0]:
    uploaded_files = st.file_uploader("🖼️ Upload one or more images", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
    
    if uploaded_files:
        st.session_state.uploaded_file_objects = uploaded_files
    # The fix: Do not clear uploaded_file_objects if uploaded_files is empty,
    # as this would remove the images after the first generation.
    # The line `st.session_state.uploaded_file_objects = []` when `uploaded_files` is empty is removed.
    # This keeps the images visible.
    
    if st.session_state.uploaded_file_objects:
        st.subheader("Your Uploaded Images")
        
        images_html = "<div class='image-grid'>"
        for uploaded_file in st.session_state.uploaded_file_objects:
            encoded_image = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
            images_html += f"<div class='uploaded-image-container'><img src='data:{uploaded_file.type};base64,{encoded_image}' class='uploaded-image-thumbnail'/></div>"
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
                    label="Download",
                    data=image_data['bytes'],
                    file_name=f"fal-image_{i+1}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png",
                    mime="image/png",
                )
            
st.markdown("---")
    
with st.expander("⚙️ Advanced Settings"):
    st.markdown("Customize how the model generates your image.")
    
    resolution_options = {
        "512x512": (512, 512),
        "768x768": (768, 768),
        "1024x1024": (1024, 1024),
        "2048x2048 (2K)": (2048, 2048),
        "4096x4096 (4K)": (4096, 4096),
    }
    selected_resolution = st.selectbox("Select Resolution", list(resolution_options.keys()), index=2)
    st.session_state.width, st.session_state.height = resolution_options[selected_resolution]

    st.session_state.strength = st.slider("Strength", min_value=0.0, max_value=1.0, value=st.session_state.strength, step=0.01)
    st.session_state.guidance_scale = st.slider("Guidance Scale", min_value=1.0, max_value=15.0, value=st.session_state.guidance_scale, step=0.1)
    st.session_state.num_images = st.slider("Number of Images", min_value=1, max_value=10, value=st.session_state.num_images, step=1)
    st.session_state.num_inference_steps = st.slider("Inference Steps", min_value=10, max_value=150, value=st.session_state.num_inference_steps, step=1)
    seed_input = st.number_input("Seed (Optional, leave empty for random)", value=None, step=1, format="%d")
    st.session_state.seed = seed_input
    st.session_state.enable_safety_checker = st.checkbox("✅ Enable Safety Checker", value=st.session_state.enable_safety_checker)



























