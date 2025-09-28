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
    
    /* General Text and Background */
    body {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* Input Fields and Text Areas */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: var(--card-background);
        border: 1px solid var(--border-color);
        color: var(--text-color);
        border-radius: 8px;
        padding: 10px;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        transition: background-color 0.2s;
    }
    .stButton>button:hover {
        background-color: #3a5bbd; /* Slightly darker blue */
    }
    
    /* Expander/Container */
    .stExpander, [data-testid="stVerticalBlock"] {
        background-color: var(--card-background);
        border-radius: 12px;
        padding: 10px 20px;
        margin-bottom: 15px;
        border: 1px solid var(--border-color);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: var(--card-background);
        border-radius: 8px 8px 0 0;
        padding: 10px 15px;
        color: var(--text-color);
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--primary-color);
        color: white;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background-color: var(--card-background);
        border-radius: 0 0 12px 12px;
        padding: 20px;
    }
    
    /* Sliders */
    .stSlider>div>div>div:nth-child(2) {
        background-color: var(--primary-color);
    }
    
    /* Output Image Styling */
    .image-container img {
        border-radius: 12px;
        border: 3px solid var(--primary-color);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# --- Firebase/Auth Setup (Mocked for context, using fal_client for API calls) ---
# Assuming fal_client is set up via environment variables or secrets
client = fal_client.DurableClient()


# --- Session State Initialization ---

# General Image Settings
if "prompt" not in st.session_state:
    st.session_state.prompt = "A majestic wolf howling at a full moon, cinematic lighting, hyper detailed, 8k, photorealistic"
if "negative_prompt" not in st.session_state:
    st.session_state.negative_prompt = "low quality, bad anatomy, bad hands, low resolution, worst quality"
if "model_name" not in st.session_state:
    st.session_state.model_name = "stable-diffusion-xl"
if "width" not in st.session_state:
    st.session_state.width = 1024 # Default width for Txt2Img and Img2Img (as requested)
if "height" not in st.session_state:
    st.session_state.height = 1024 # Default height for Txt2Img and Img2Img (as requested)
if "strength" not in st.session_state:
    st.session_state.strength = 0.7
if "guidance_scale" not in st.session_state:
    st.session_state.guidance_scale = 9.0
if "num_images" not in st.session_state:
    st.session_state.num_images = 1
if "seed" not in st.session_state:
    st.session_state.seed = 42
if "image_uploaded" not in st.session_state:
    st.session_state.image_uploaded = None

# Video Generation Settings (NEW)
if "video_frames" not in st.session_state:
    st.session_state.video_frames = 14
if "video_steps" not in st.session_state:
    st.session_state.video_steps = 25
if "video_fps" not in st.session_state:
    st.session_state.video_fps = 6
if "video_motion_bucket_id" not in st.session_state:
    st.session_state.video_motion_bucket_id = 127
if "video_cond_aug" not in st.session_state:
    st.session_state.video_cond_aug = 0.02
if "video_safety_checker" not in st.session_state:
    st.session_state.video_safety_checker = False # Set to False as requested
if "video_seed" not in st.session_state:
    st.session_state.video_seed = 42
if "video_input_image" not in st.session_state:
    st.session_state.video_input_image = None
if "video_model_name" not in st.session_state:
    st.session_state.video_model_name = "svd"


# --- Utility Functions (Mocked) ---
def generate_image(mode, image_url=None):
    """
    Placeholder for the fal_client image generation call.
    Uses current session state parameters.
    """
    st.info(f"Generating image with {mode}...")
    
    # Mocking the output structure for the UI
    mock_output_url = "https://placehold.co/1024x1024/4169E1/FFD700?text=Result+Mock"
    
    # In a real app, this would be a fal_client call:
    # response = client.run(
    #     st.session_state.model_name,
    #     arguments={...}
    # )
    # return response['images'][0]['url']
    
    # Mock return
    return mock_output_url

def generate_video():
    """
    Placeholder for the fal_client video generation call.
    Uses current session state parameters.
    """
    if not st.session_state.video_input_image:
        st.error("Please upload a starting image for video generation.")
        return None
        
    st.info(f"Generating video using model: {st.session_state.video_model_name}...")
    
    # Mocking the output structure for the UI
    mock_video_url = "https://storage.googleapis.com/test-bucket/sample.mp4" # Placeholder URL
    
    # In a real app, this would be a fal_client call:
    # response = client.run(
    #     st.session_state.video_model_name,
    #     arguments={...}
    # )
    # return response['video']['url']
    
    # Mock return
    return mock_video_url


# --- Main Application UI ---
st.title("🍌 NANO BANANA X AI")
st.caption("Text-to-Image, Image-to-Image, and Video Generation powered by cutting-edge models.")

# --- Tab Definitions ---
tab_txt2img, tab_img2img, tab_video, tab_settings = st.tabs(
    ["🖼️ Text-to-Image", "🔄 Image-to-Image", "🎥 Video Generation", "⚙️ Settings"]
)

# --- 1. Text-to-Image Tab ---
with tab_txt2img:
    st.header("🖼️ Text-to-Image Generation")
    
    col_input, col_output = st.columns([1, 1])

    with col_input:
        st.subheader("Your Imagination")
        st.session_state.prompt = st.text_area(
            "Prompt", 
            value=st.session_state.prompt, 
            height=150,
            key="txt2img_prompt"
        )
        st.session_state.negative_prompt = st.text_area(
            "Negative Prompt (Things to Avoid)",
            value=st.session_state.negative_prompt,
            height=75,
            key="txt2img_negative_prompt"
        )
        
        # Advanced Settings (Used by Txt2Img and Img2Img)
        st.markdown("---")
        with st.expander("⚙️ Advanced Settings (Image)"):
            st.markdown("Customize image size and other parameters.")
            
            resolution_options = {
                "512x512": (512, 512),
                "768x768": (768, 768),
                "1024x1024": (1024, 1024),
                "2048x2048 (2K)": (2048, 2048),
                "4096x4096 (4K)": (4096, 4096),
            }
            # Find the current resolution key
            current_resolution_key = next((k for k, v in resolution_options.items() if v == (st.session_state.width, st.session_state.height)), "1024x1024")
            default_index = list(resolution_options.keys()).index(current_resolution_key)

            selected_resolution_key = st.selectbox(
                "Select Resolution", 
                list(resolution_options.keys()), 
                index=default_index,
                key="txt2img_resolution_selector"
            )
            st.session_state.width, st.session_state.height = resolution_options[selected_resolution_key]

            st.session_state.guidance_scale = st.slider(
                "Guidance Scale (CFG)", 
                min_value=1.0, 
                max_value=15.0, 
                value=st.session_state.guidance_scale, 
                step=0.1,
                key="txt2img_guidance"
            )
            st.session_state.num_images = st.slider(
                "Number of Images to Generate", 
                min_value=1, 
                max_value=4, 
                value=st.session_state.num_images, 
                step=1,
                key="txt2img_num_images"
            )
            st.session_state.seed = st.number_input(
                "Seed (Leave at 0 for random)",
                min_value=0, 
                value=st.session_state.seed, 
                step=1, 
                key="txt2img_seed"
            )
            
        st.markdown("---")
        if st.button("✨ Generate Image", type="primary", use_container_width=True):
            st.session_state.result_url = generate_image("txt2img")

    with col_output:
        st.subheader("Results")
        if "result_url" in st.session_state and st.session_state.result_url:
            st.image(st.session_state.result_url, caption="Generated Image", use_column_width="auto")
            # Using the same download logic as provided in the snippet
            try:
                img_data = urlopen(st.session_state.result_url).read()
                st.download_button(
                    "Download Image",
                    data=img_data,
                    file_name=f"txt2img_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png",
                    mime="image/png",
                )
            except Exception as e:
                st.warning(f"Could not prepare download: {e}")
        else:
            st.info("Your generated image will appear here.")
            st.image("https://placehold.co/1024x1024/1e1e1e/3a3a3a?text=Output+Preview", use_column_width="auto")
            
# --- 2. Image-to-Image Tab ---
with tab_img2img:
    st.header("🔄 Image-to-Image / Inpainting")

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Input Image & Settings")
        uploaded_file = st.file_uploader(
            "Upload an image to use as a base or mask", 
            type=["png", "jpg", "jpeg"],
            key="img2img_uploader"
        )

        if uploaded_file is not None:
            # Save uploaded file to session state for persistence
            file_bytes = uploaded_file.read()
            st.session_state.image_uploaded = base64.b64encode(file_bytes).decode('utf-8')
            st.image(uploaded_file, caption="Input Image", use_column_width="always")
            
            st.markdown("---")
            st.subheader("Transformation Parameters")
            
            # The global width/height state is set in the Txt2Img tab/Settings tab, which defaults to 1024x1024.
            # This satisfies the requirement to have a 1024x1024 default for Image-to-Image.
            st.caption(f"Current Resolution: **{st.session_state.width}x{st.session_state.height}** (Set in Text-to-Image/Settings tab)")

            st.session_state.strength = st.slider(
                "Denoising Strength", 
                min_value=0.0, 
                max_value=1.0, 
                value=st.session_state.strength, 
                step=0.01,
                help="How much the generated image can deviate from the input image. Low value = small changes. High value = large changes.",
                key="img2img_strength"
            )
            
            st.session_state.prompt = st.text_area(
                "Prompt for Transformation", 
                value=st.session_state.prompt, 
                height=100,
                key="img2img_prompt"
            )
            st.session_state.negative_prompt = st.text_area(
                "Negative Prompt",
                value=st.session_state.negative_prompt,
                height=70,
                key="img2img_negative_prompt"
            )
            
            if st.button("🔄 Transform Image", type="primary", use_container_width=True):
                st.session_state.result_url_img2img = generate_image("img2img", image_url=st.session_state.image_uploaded)
        else:
            st.warning("Upload an image to begin Image-to-Image generation.")

    with col2:
        st.subheader("Transformed Result")
        if "result_url_img2img" in st.session_state and st.session_state.result_url_img2img:
            st.image(st.session_state.result_url_img2img, caption="Transformed Image", use_column_width="auto")
            try:
                img_data = urlopen(st.session_state.result_url_img2img).read()
                st.download_button(
                    "Download Image",
                    data=img_data,
                    file_name=f"img2img_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png",
                    mime="image/png",
                )
            except Exception as e:
                st.warning(f"Could not prepare download: {e}")
        else:
            st.info("Your transformed image will appear here.")
            st.image("https://placehold.co/1024x1024/1e1e1e/3a3a3a?text=Output+Preview", use_column_width="auto")

# --- 3. Video Generation Tab (NEW) ---
with tab_video:
    st.header("🎥 Image-to-Video Generation")
    st.markdown("Use a high-quality image and a prompt to generate a short, dynamic video clip.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Input Image & Prompts")
        
        video_uploaded_file = st.file_uploader(
            "Upload an image to animate (Square input is recommended)", 
            type=["png", "jpg", "jpeg"],
            key="video_uploader"
        )
        
        if video_uploaded_file is not None:
            file_bytes_video = video_uploaded_file.read()
            st.session_state.video_input_image = base64.b64encode(file_bytes_video).decode('utf-8')
            st.image(video_uploaded_file, caption="Input Image", use_column_width="always")
        else:
            st.session_state.video_input_image = None
            st.warning("Upload an image to enable video generation.")
        
        st.markdown("---")
        st.subheader("Motion Guidance")
        st.session_state.prompt = st.text_area(
            "Prompt (Guiding the motion/style)", 
            value=st.session_state.prompt, 
            height=100,
            key="video_prompt"
        )
        st.session_state.negative_prompt = st.text_area(
            "Negative Prompt",
            value=st.session_state.negative_prompt,
            height=70,
            key="video_negative_prompt"
        )
        
        st.markdown("---")
        st.subheader("Quick Parameters")
        st.caption("Detailed settings are in the 'Settings' tab.")
        
        st.session_state.video_motion_bucket_id = st.slider(
            "Motion Intensity",
            min_value=1, max_value=255, value=st.session_state.video_motion_bucket_id, step=1,
            help="Higher values result in more intense motion (currently: 127 default).",
            key="video_motion_bucket_display"
        )
        
        st.session_state.video_frames = st.slider(
            "Video Length (Frames)",
            min_value=10, max_value=25, value=st.session_state.video_frames, step=1,
            key="video_frames_display"
        )
        
        if st.session_state.video_input_image:
            if st.button("▶️ Generate Video", type="primary", use_container_width=True):
                st.session_state.video_result_url = generate_video()
        else:
            st.button("▶️ Generate Video", disabled=True, use_container_width=True)


    with col2:
        st.subheader("Generated Video")
        if "video_result_url" in st.session_state and st.session_state.video_result_url:
            st.video(st.session_state.video_result_url, format="video/mp4")
            try:
                video_data = urlopen(st.session_state.video_result_url).read()
                st.download_button(
                    "Download Video",
                    data=video_data,
                    file_name=f"video_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp4",
                    mime="video/mp4",
                )
            except Exception as e:
                st.warning(f"Could not prepare download: {e}")
        else:
            st.info("Your generated video will appear here. Video generation can take longer.")
            st.image("https://placehold.co/1600x900/1e1e1e/3a3a3a?text=Video+Output+Preview+(16:9)", use_column_width="auto")

# --- 4. Settings Tab ---
with tab_settings:
    st.header("⚙️ Application Settings")

    # --- Video Generation Settings (FULL FEATURE SET AS REQUESTED) ---
    st.subheader("Video Generation Parameters (SVD)")
    st.markdown("Customize all parameters for the **Video Generation** tab.")
    
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        st.session_state.video_model_name = st.selectbox(
            "Video Model",
            ["svd", "svd-xt"],
            index=0 if st.session_state.video_model_name == "svd" else 1,
            key="settings_video_model"
        )
        
        st.session_state.video_frames = st.slider(
            "Number of Frames (Length)",
            min_value=10, max_value=25, value=st.session_state.video_frames, step=1,
            key="settings_video_frames"
        )
        st.session_state.video_steps = st.slider(
            "Inference Steps (Quality)",
            min_value=10, max_value=50, value=st.session_state.video_steps, step=1,
            key="settings_video_steps"
        )
        
        # Safety Checker (Set to False as requested)
        st.session_state.video_safety_checker = st.toggle(
            "Enable Safety Checker",
            value=st.session_state.video_safety_checker,
            key="settings_video_safety_checker"
        )
        st.caption(f"Current Value: **{st.session_state.video_safety_checker}** (Toggles removal of NSFW content)")

    with col_v2:
        st.session_state.video_fps = st.slider(
            "Frames Per Second (Playback Speed)",
            min_value=3, max_value=12, value=st.session_state.video_fps, step=1,
            key="settings_video_fps"
        )
        st.session_state.video_motion_bucket_id = st.slider(
            "Motion Bucket ID (Intensity)",
            min_value=1, max_value=255, value=st.session_state.video_motion_bucket_id, step=1,
            help="Higher values result in more intense motion.",
            key="settings_video_motion_bucket"
        )
        st.session_state.video_cond_aug = st.slider(
            "Conditional Augmentation (Noise)",
            min_value=0.0, max_value=0.1, value=st.session_state.video_cond_aug, step=0.005,
            help="Controls initial noise level, affecting how much the video deviates from the image.",
            key="settings_video_cond_aug"
        )
        
        st.session_state.video_seed = st.number_input(
            "Video Seed (0 for random)",
            min_value=0, 
            value=st.session_state.video_seed, 
            step=1, 
            key="settings_video_seed"
        )

    st.markdown("---")

    # --- Image Generation Settings (Existing Section) ---
    st.subheader("Image Generation Parameters (SDXL)")
    st.markdown("These settings apply to the **Text-to-Image** and **Image-to-Image** tabs.")
    
    col_i1, col_i2 = st.columns(2)
    
    with col_i1:
        st.session_state.model_name = st.selectbox(
            "Image Model",
            ["stable-diffusion-xl", "dall-e-3"],
            index=0 if st.session_state.model_name == "stable-diffusion-xl" else 1,
            key="settings_image_model"
        )

        st.session_state.guidance_scale = st.slider(
            "Guidance Scale (CFG)", 
            min_value=1.0, 
            max_value=15.0, 
            value=st.session_state.guidance_scale, 
            step=0.1,
            key="settings_guidance"
        )

    with col_i2:
        st.session_state.num_images = st.slider(
            "Number of Images to Generate", 
            min_value=1, 
            max_value=4, 
            value=st.session_state.num_images, 
            step=1,
            key="settings_num_images"
        )
        st.session_state.seed = st.number_input(
            "Image Seed (0 for random)",
            min_value=0, 
            value=st.session_state.seed, 
            step=1, 
            key="settings_image_seed"
        )

    # Resolution (Shared state)
    st.markdown("---")
    st.subheader("Shared Resolution")
    
    resolution_options_settings = {
        "512x512": (512, 512),
        "768x768": (768, 768),
        "1024x1024": (1024, 1024),
        "2048x2048 (2K)": (2048, 2048),
        "4096x4096 (4K)": (4096, 4096),
    }
    
    # Determine current selected key based on session state width/height
    current_resolution_key = next((k for k, v in resolution_options_settings.items() if v == (st.session_state.width, st.session_state.height)), "1024x1024")
    default_index = list(resolution_options_settings.keys()).index(current_resolution_key)
    
    selected_resolution_key_settings = st.selectbox(
        "Select Resolution for Image Generation (Txt2Img & Img2Img)", 
        list(resolution_options_settings.keys()), 
        index=default_index,
        key="settings_resolution_selector"
    )
    st.session_state.width, st.session_state.height = resolution_options_settings[selected_resolution_key_settings]

    st.markdown("---")

    # --- Authentication (Removed Password Info) ---
    st.subheader("Authentication")
    st.markdown("This application requires API keys (e.g., FAL_KEY_ID, FAL_KEY_SECRET) to be set up in your environment or secrets management for the generation services to run.")
