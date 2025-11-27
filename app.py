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
    page_title="NANO BANANA PRO X AI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for fal.ai playground-inspired design
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

    /* Color Palette - fal.ai inspired */
    :root {
        --primary-color: #6366f1; /* Indigo */
        --primary-hover: #4f46e5;
        --secondary-color: #8b5cf6; /* Purple accent */
        --background-color: #0a0a0a; /* Very dark background */
        --card-background: #121212; /* Slightly lighter for containers */
        --border-color: #1f1f1f;
        --text-color: #e5e5e5;
        --text-muted: #a3a3a3;
        --success-color: #10b981;
        --input-bg: #1a1a1a;
    }
    
    /* Main App Container Styling */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", "Helvetica Neue", Arial, sans-serif;
    }
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Button Styling - fal.ai style */
    .stButton>button {
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 8px;
        transition: all 0.2s ease;
        font-weight: 500;
        padding: 0.625rem 1.25rem;
        font-size: 0.95rem;
        width: 100%;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    }
    .stButton>button:hover {
        background: var(--primary-hover);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        transform: translateY(-1px);
    }
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Input Field Styling */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea, 
    .stNumberInput>div>input,
    .stSelectbox>div>div>div {
        background-color: var(--input-bg);
        color: var(--text-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 0.625rem 0.875rem;
        transition: all 0.2s ease;
        font-size: 0.95rem;
    }
    .stTextInput>div>div>input:focus, 
    .stTextArea>div>div>textarea:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        outline: none;
    }
    
    /* Header Styling */
    h1 {
        color: var(--text-color);
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    h2 {
        color: var(--text-color);
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    h3 {
        color: var(--text-muted);
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.75rem;
    }
    
    /* Card/Container Styling */
    .upload-section {
        background-color: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    /* Thumbnail Grid */
    .thumbnail-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-top: 1rem;
    }
    
    .thumbnail-container {
        position: relative;
        width: 100px;
        height: 100px;
        border-radius: 8px;
        overflow: hidden;
        border: 2px solid var(--border-color);
        transition: all 0.2s ease;
        background-color: var(--input-bg);
    }
    
    .thumbnail-container:hover {
        border-color: var(--primary-color);
        transform: scale(1.05);
    }
    
    .thumbnail-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    .remove-thumbnail {
        position: absolute;
        top: 4px;
        right: 4px;
        background-color: rgba(239, 68, 68, 0.9);
        color: white;
        border: none;
        border-radius: 4px;
        width: 24px;
        height: 24px;
        font-size: 14px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
    }
    
    .remove-thumbnail:hover {
        background-color: rgba(220, 38, 38, 1);
    }
    
    /* Output Image Styling */
    .output-container {
        background-color: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 2rem;
    }
    
    .stImage img {
        border-radius: 8px;
        width: 100%;
        height: auto;
    }
    
    /* Divider */
    hr {
        border: none;
        border-top: 1px solid var(--border-color);
        margin: 2rem 0;
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background-color: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-color);
        font-weight: 500;
    }
    
    /* Slider Styling */
    .stSlider>div>div>div>div {
        background-color: var(--primary-color);
    }
    
    /* File Uploader Styling */
    [data-testid="stFileUploader"] {
        background-color: var(--input-bg);
        border: 2px dashed var(--border-color);
        border-radius: 8px;
        padding: 1.5rem;
        transition: all 0.2s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: var(--primary-color);
    }
    
    /* Loading Spinner */
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(10, 10, 10, 0.95);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    }
    
    .spinner-icon {
        width: 60px;
        height: 60px;
        border: 4px solid var(--border-color);
        border-top: 4px solid var(--primary-color);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .spinner-text {
        margin-top: 1.5rem;
        font-size: 1.1rem;
        color: var(--text-muted);
        font-weight: 500;
    }
    
    /* Info/Success Messages */
    .stAlert {
        background-color: var(--card-background);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-color);
    }
    
    /* Download Button Styling */
    .stDownloadButton>button {
        background-color: var(--success-color);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.625rem 1.25rem;
        font-weight: 500;
        transition: all 0.2s ease;
        width: 100%;
    }
    
    .stDownloadButton>button:hover {
        background-color: #059669;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--card-background);
        border-radius: 8px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 6px;
        color: var(--text-muted);
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color);
        color: white;
    }
    
    /* Selectbox Styling */
    .stSelectbox>div>div {
        background-color: var(--input-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }
    
    /* Checkbox Styling */
    .stCheckbox {
        color: var(--text-color);
    }
</style>
""", unsafe_allow_html=True)

# --- Login Configuration ---
LOGIN_USERNAME = "nofar"
LOGIN_PASSWORD = "Nofar123!"

# --- Session State Initialization ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'uploaded_file_objects' not in st.session_state:
    st.session_state.uploaded_file_objects = []
if 'prompt' not in st.session_state:
    st.session_state.prompt = ""
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = []
if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False

# T2I Parameters (Nano Banana Pro) - Fixed to 1 image
if 'num_images' not in st.session_state:
    st.session_state.num_images = 1
if 'aspect_ratio' not in st.session_state:
    st.session_state.aspect_ratio = "1:1"
if 'output_format' not in st.session_state:
    st.session_state.output_format = "png"

# I2I Parameters (Nano Banana Pro Edit) - Fixed to 1 image
if 'num_images_i2i' not in st.session_state:
    st.session_state.num_images_i2i = 1
if 'aspect_ratio_i2i' not in st.session_state:
    st.session_state.aspect_ratio_i2i = "auto"

# --- R2 Configuration ---
R2_ACCOUNT_ID = st.secrets.get("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = st.secrets.get("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = st.secrets.get("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = st.secrets.get("R2_BUCKET_NAME", "")
R2_PUBLIC_URL = st.secrets.get("R2_PUBLIC_URL", "")

# --- Helper Functions ---
def upload_to_r2(image_bytes, filename):
    """Upload image to Cloudflare R2 and return public URL"""
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name='auto'
        )
        
        s3_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=filename,
            Body=image_bytes,
            ContentType='image/png'
        )
        
        public_url = f"{R2_PUBLIC_URL}/{filename}"
        return public_url
    except Exception as e:
        st.error(f"Error uploading to R2: {str(e)}")
        return None

def upload_image_to_fal(uploaded_file):
    """Upload image to fal.ai and return URL"""
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp_file.write(uploaded_file.getvalue())
        temp_file.close()
        
        image_url = fal_client.upload_file(temp_file.name)
        os.unlink(temp_file.name)
        return image_url
    except Exception as e:
        st.error(f"Error uploading to fal.ai: {str(e)}")
        return None

def generate_t2i():
    """Generate images using Nano Banana Pro (Text-to-Image)"""
    if not st.session_state.prompt:
        st.error("Please enter a prompt!")
        return
    
    try:
        # Prepare arguments
        arguments = {
            "prompt": st.session_state.prompt,
            "num_images": st.session_state.num_images,
            "aspect_ratio": st.session_state.aspect_ratio,
            "output_format": st.session_state.output_format
        }
        
        # Call fal.ai API
        result = fal_client.subscribe(
            "fal-ai/nano-banana-pro",
            arguments=arguments
        )
        
        # Process results
        generated_images = []
        if result and 'images' in result:
            for i, img_data in enumerate(result['images']):
                img_url = img_data['url']
                img_bytes = BytesIO(urlopen(img_url).read())
                
                # Upload to R2
                filename = f"nanobananapro_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1}.png"
                r2_url = upload_to_r2(img_bytes.getvalue(), filename)
                
                generated_images.append({
                    'url': img_url,
                    'r2_url': r2_url,
                    'bytes': img_bytes.getvalue()
                })
        
        st.session_state.generated_images = generated_images
        
    except Exception as e:
        st.error(f"Error generating images: {str(e)}")
    finally:
        st.session_state.is_generating = False

def generate_i2i():
    """Generate images using Nano Banana Pro Edit (Image-to-Image)"""
    if not st.session_state.prompt:
        st.error("Please enter a prompt!")
        return
    
    if not st.session_state.uploaded_file_objects:
        st.error("Please upload at least one image!")
        return
    
    try:
        # Upload images to fal.ai
        image_urls = []
        for uploaded_file in st.session_state.uploaded_file_objects:
            fal_url = upload_image_to_fal(uploaded_file)
            if fal_url:
                image_urls.append(fal_url)
        
        if not image_urls:
            st.error("Failed to upload images to fal.ai")
            return
        
        # Prepare arguments
        arguments = {
            "prompt": st.session_state.prompt,
            "image_urls": image_urls,
            "num_images": st.session_state.num_images_i2i,
            "aspect_ratio": st.session_state.aspect_ratio_i2i,
            "output_format": st.session_state.output_format
        }
        
        # Call fal.ai API
        result = fal_client.subscribe(
            "fal-ai/nano-banana-pro/edit",
            arguments=arguments
        )
        
        # Process results
        generated_images = []
        if result and 'images' in result:
            for i, img_data in enumerate(result['images']):
                img_url = img_data['url']
                img_bytes = BytesIO(urlopen(img_url).read())
                
                # Upload to R2
                filename = f"nanobananapro_edit_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1}.png"
                r2_url = upload_to_r2(img_bytes.getvalue(), filename)
                
                generated_images.append({
                    'url': img_url,
                    'r2_url': r2_url,
                    'bytes': img_bytes.getvalue()
                })
        
        st.session_state.generated_images = generated_images
        
    except Exception as e:
        st.error(f"Error generating images: {str(e)}")
    finally:
        st.session_state.is_generating = False

# --- Handle Generation ---
if st.session_state.is_generating:
    st.markdown("""
    <div class="loading-overlay">
        <div class="spinner-icon"></div>
        <div class="spinner-text">Generating your masterpiece...</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Determine which generation to run
    if st.session_state.uploaded_file_objects:
        generate_i2i()
    else:
        generate_t2i()
    st.rerun()

# --- Login Screen ---
if not st.session_state.authenticated:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1>🍌 NANO BANANA PRO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: var(--text-muted); font-size: 1.1rem; margin-top: -0.5rem; margin-bottom: 2rem;'>Advanced AI Image Generation & Editing</p>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='
            background-color: var(--card-background);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        '>
        """, unsafe_allow_html=True)
        
        st.markdown("<h2 style='text-align: center; margin-top: 0;'>🔐 Login</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: var(--text-muted); margin-bottom: 1.5rem;'>Enter your credentials to access the app</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username", key="login_username")
            password = st.text_input("Password", type="password", placeholder="Enter password", key="login_password")
            
            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if username == LOGIN_USERNAME and password == LOGIN_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.stop()

# --- Main App (Only shown after authentication) ---
col_header_left, col_header_right = st.columns([4, 1])

with col_header_left:
    st.markdown("<h1>🍌 NANO BANANA PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: var(--text-muted); font-size: 1.1rem; margin-top: -0.5rem;'>Advanced AI Image Generation & Editing</p>", unsafe_allow_html=True)

with col_header_right:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state.authenticated = False
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# --- Main Layout ---
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    # --- Prompt Input ---
    st.markdown("<h3>✍️ PROMPT</h3>", unsafe_allow_html=True)
    prompt = st.text_area(
        "Describe what you want to create or edit",
        placeholder="An action shot of a black lab swimming in a pool, camera on water line...",
        height=120,
        key="prompt_input",
        label_visibility="collapsed"
    )
    st.session_state.prompt = prompt
    
    # --- Image Upload ---
    st.markdown("<h3>📸 IMAGES (OPTIONAL)</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: var(--text-muted); font-size: 0.875rem; margin-top: -0.5rem;'>Upload images for Image-to-Image editing. Leave empty for Text-to-Image generation.</p>", unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Upload images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="file_uploader",
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        st.session_state.uploaded_file_objects = uploaded_files
    
    # Display thumbnails
    if st.session_state.uploaded_file_objects:
        st.markdown("<div class='thumbnail-grid'>", unsafe_allow_html=True)
        thumbnail_html = ""
        for idx, uploaded_file in enumerate(st.session_state.uploaded_file_objects):
            encoded_image = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
            thumbnail_html += f"""
            <div class='thumbnail-container'>
                <img src='data:{uploaded_file.type};base64,{encoded_image}' class='thumbnail-image'/>
            </div>
            """
        st.markdown(thumbnail_html + "</div>", unsafe_allow_html=True)
        
        if st.button("🗑️ Clear All Images", key="clear_images"):
            st.session_state.uploaded_file_objects = []
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- Settings Expander ---
    with st.expander("⚙️ Advanced Settings", expanded=False):
        if st.session_state.uploaded_file_objects:
            st.markdown("**Image-to-Image Settings**")
            st.session_state.aspect_ratio_i2i = st.selectbox(
                "Aspect Ratio",
                ["auto", "1:1", "16:9", "9:16", "4:3", "3:4"],
                index=0,
                key="aspect_ratio_i2i_select"
            )
        else:
            st.markdown("**Text-to-Image Settings**")
            st.session_state.aspect_ratio = st.selectbox(
                "Aspect Ratio",
                ["1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "9:21"],
                index=0,
                key="aspect_ratio_select"
            )
        
        st.session_state.output_format = st.selectbox(
            "Output Format",
            ["png", "jpeg", "webp"],
            index=0,
            key="output_format_select"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- Generate Button ---
    if st.button("🚀 Generate", key="generate_btn", use_container_width=True):
        st.session_state.is_generating = True
        st.rerun()

with col_right:
    # --- Output Section ---
    st.markdown("<h3>🎨 OUTPUT</h3>", unsafe_allow_html=True)
    
    if st.session_state.generated_images:
        # Display generated images
        for idx, img_data in enumerate(st.session_state.generated_images):
            st.image(img_data['url'], use_container_width=True)
            
            col_download, col_r2 = st.columns(2)
            with col_download:
                st.download_button(
                    label="⬇️ Download",
                    data=img_data['bytes'],
                    file_name=f"nanobananapro_{idx+1}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png",
                    mime="image/png",
                    key=f"download_{idx}",
                    use_container_width=True
                )
            with col_r2:
                if img_data['r2_url']:
                    st.markdown(f"[🔗 View on R2]({img_data['r2_url']})", unsafe_allow_html=True)
            
            if idx < len(st.session_state.generated_images) - 1:
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        # Placeholder
        st.markdown("""
        <div style='
            background-color: var(--card-background);
            border: 2px dashed var(--border-color);
            border-radius: 12px;
            padding: 3rem;
            text-align: center;
            color: var(--text-muted);
            min-height: 400px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        '>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>🎨</div>
            <div style='font-size: 1.1rem; font-weight: 500;'>Your generated images will appear here</div>
            <div style='font-size: 0.9rem; margin-top: 0.5rem;'>Enter a prompt and click Generate to start creating</div>
        </div>
        """, unsafe_allow_html=True)

# --- Footer ---
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: var(--text-muted); font-size: 0.875rem;'>
    <p>Powered by <strong>Nano Banana Pro</strong> (Gemini 3 Pro Image) via fal.ai</p>
    <p style='margin-top: 0.5rem;'>⚡ Lightning-fast AI image generation & editing | 🎯 Perfect text rendering | 🌟 Character consistency</p>
</div>
""", unsafe_allow_html=True)
