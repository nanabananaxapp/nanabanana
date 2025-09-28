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
import time # Used for mocking video generation delay

# --- App Configuration and Styling ---
st.set_page_config(
    page_title="NANO BANANA X AI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a dark, professional look, exactly matching the color scheme
st.markdown("""
<style>
    /* Hide Streamlit UI elements */
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
    
</style>
""", unsafe_allow_html=True)


# --- Session State Initialization ---
if 'prompt' not in st.session_state:
    st.session_state.prompt = "A hyper-realistic portrait of a golden retriever wearing a banana helmet, 8k cinematic lighting"
if 'negative_prompt' not in st.session_state:
    st.session_state.negative_prompt = "blurry, bad hands, low quality, cartoon, watermark"
if 'image_result_urls' not in st.session_state:
    st.session_state.image_result_urls = []
if 'width' not in st.session_state:
    st.session_state.width = 2048
if 'height' not in st.session_state:
    st.session_state.height = 2048
if 'strength' not in st.session_state:
    st.session_state.strength = 0.7
if 'guidance_scale' not in st.session_state:
    st.session_state.guidance_scale = 9.0
if 'num_images' not in st.session_state:
    st.session_state.num_images = 1
if 'num_inference_steps' not in st.session_state:
    st.session_state.num_inference_steps = 50
if 'seed' not in st.session_state:
    st.session_state.seed = 42
if 'video_prompt' not in st.session_state:
    st.session_state.video_prompt = "A majestic banana riding a futuristic, glowing skateboard in space, cinematic."
if 'video_result_url' not in st.session_state:
    st.session_state.video_result_url = None

# --- FAL Client Setup and Helpers (Reusing Existing Logic) ---
# NOTE: The client setup assumes the FAL_KEY and FAL_SECRET environment variables are set.
# If not, the following line will fail and need to be adapted for your specific environment.
# try:
#     fal = fal_client.client()
# except Exception as e:
#     st.error(f"FAL Client initialization failed: {e}")
#     st.stop()


def fal_generate_image(prompt, negative_prompt, width, height, num_images, strength, guidance_scale, num_steps, seed, input_image_url=None):
    """
    Simulates calling the Image-to-Image FAL endpoint (or text-to-image if input_image_url is None).
    """
    
    # --- MOCK API CALL START ---
    # Since we cannot guarantee the FAL client is configured in this environment, 
    # we simulate the generation and return a placeholder image URL for the UI demonstration.
    
    # In a real application, you would uncomment the actual fal_client call here:
    # try:
    #     result = fal.submit(
    #         "fal-ai/anything-v5", 
    #         arguments={
    #             "prompt": prompt,
    #             "negative_prompt": negative_prompt,
    #             "width": width,
    #             "height": height,
    #             "num_images": num_images,
    #             "strength": strength,
    #             "guidance_scale": guidance_scale,
    #             "num_steps": num_steps,
    #             "seed": seed,
    #             "image_url": input_image_url if input_image_url else None
    #         }
    #     )
    #     # Poll for results and return the list of image URLs
    #     result = result.get()
    #     return result['images']
    # except Exception as e:
    #     st.error(f"Image generation failed: {e}")
    #     return []
    
    # Placeholder for the generated image URLs (single golden retriever image placeholder)
    mock_url = f"https://placehold.co/{width}x{height}/4169E1/FFD700?text=NANO+BANANA+X+AI+{width}x{height}"
    return [mock_url] * num_images
    # --- MOCK API CALL END ---


def fal_generate_video(prompt, negative_prompt):
    """
    MOCK function to simulate calling a Video Generation model via fal_client.
    Returns a publicly available video URL for UI demonstration purposes.
    """
    
    # --- MOCK API CALL START ---
    # Simulating a successful, long-running process for UI demonstration
    # In a real application, this call would submit a job to a video model (e.g., Stable Video Diffusion)
    # and poll until a video URL is returned.
    time.sleep(3) # Simulate processing time for UI update
    
    # Public domain video for preview
    return "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    # --- MOCK API CALL END ---


# --- Main Application Layout ---

# Logo/Title
st.markdown('<h1 style="text-align: center; color: var(--primary-color); font-size: 2.5rem;">NANO BANANA X AI 🍌</h1>', unsafe_allow_html=True)

# Tabs for switching modes, with Video as the first tab
tab_video, tab_image = st.tabs(["🎥 Video Generation", "🖼️ Image Generation"])

# --------------------------------------------------
# 🎥 VIDEO GENERATION TAB (The primary, new section)
# --------------------------------------------------
with tab_video:
    st.markdown("---")
    # Use columns for Controls (Input) and Preview (Output)
    col_input, col_output = st.columns([1, 2]) # Input column slightly narrower than output

    with col_input:
        st.markdown("## Video Input Controls")
        
        # Prompt Input
        st.session_state.video_prompt = st.text_area(
            "Enter your **video prompt** (e.g., 'An epic slow-motion shot of a futuristic sports car driving through a neon city at night')", 
            value=st.session_state.video_prompt,
            height=150,
            key="video_prompt_area"
        )
        
        # Negative Prompt for Video
        st.session_state.negative_prompt = st.text_area(
            "Negative Prompt (What you *don't* want in the video)",
            value=st.session_state.negative_prompt,
            key="video_negative_prompt_area"
        )
        
        st.markdown("---")
        
        # Generate Button
        if st.button("🚀 Generate Video", key="generate_video_button", type="primary", use_container_width=True):
            if st.session_state.video_prompt:
                with st.spinner('Generating video... this can take a few minutes.'):
                    # NOTE: This calls the MOCK function for UI demonstration.
                    video_url = fal_generate_video(
                        st.session_state.video_prompt, 
                        st.session_state.negative_prompt
                    )
                    st.session_state.video_result_url = video_url
                    st.success("Video generation complete! Check the preview on the right.")
            else:
                st.error("Please enter a prompt to generate a video.")
        
        st.markdown("---")
        
        # Video-specific Settings
        with st.expander("⚙️ Video Advanced Settings", expanded=False):
            st.markdown("Model parameters for video output.")
            st.slider("Frames per Second (FPS)", min_value=1, max_value=30, value=15, step=1, key="video_fps")
            st.slider("Video Length (Seconds)", min_value=1, max_value=8, value=4, step=1, key="video_length")
            st.number_input("Seed", min_value=0, max_value=99999999, value=st.session_state.seed, step=1, key="video_seed")

    with col_output:
        st.markdown("## Video Output Preview")
        if st.session_state.video_result_url:
            st.video(st.session_state.video_result_url)
            st.markdown(f'<p style="text-align:center; color: var(--text-color); font-size: 0.9rem;">Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>', unsafe_allow_html=True)
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
                <p style="font-size: 0.9rem; color: #888;">Your generated video will appear here after clicking 'Generate Video'.</p>
            </div>
            """, unsafe_allow_html=True)


# --------------------------------------------------
# 🖼️ IMAGE GENERATION TAB (Original functionality)
# --------------------------------------------------
with tab_image:
    st.markdown("---")
    # Use columns for Controls (Input) and Preview (Output)
    col_input_img, col_output_img = st.columns([1, 2])

    with col_input_img:
        st.markdown("## Image Input Controls")
        
        # --- Image Upload Section ---
        uploaded_file = st.file_uploader(
            "Upload an **initial image** for Image-to-Image Generation (Optional)",
            type=["png", "jpg", "jpeg"],
            key="image_upload_img"
        )
        
        # Determine image URL from upload (MOCK S3 upload function removed for simplicity)
        input_image_url = None
        if uploaded_file is not None:
             st.success("Image uploaded. Using Image-to-Image mode.")
             # In a real app, this would be uploaded to S3 and input_image_url set.
             # For UI testing, we'll just check if it's present.
             input_image_url = "mock-uploaded-image-url"


        st.session_state.prompt = st.text_area(
            "Enter your **image prompt** (e.g., 'A hyper-realistic portrait of a golden retriever wearing a banana helmet, 8k cinematic lighting')",
            value=st.session_state.prompt,
            height=150,
            key="image_prompt_area"
        )
        
        # Negative Prompt
        st.session_state.negative_prompt = st.text_area(
            "Negative Prompt (What you *don't* want to see, e.g., blurry, bad hands)",
            value=st.session_state.negative_prompt,
            key="image_negative_prompt_area"
        )
        
        st.markdown("---")
        
        # Generate Button
        if st.button("✨ Generate Image", key="generate_image_button", type="primary", use_container_width=True):
            if st.session_state.prompt:
                with st.spinner('Generating image(s)...'):
                    st.session_state.image_result_urls = fal_generate_image(
                        st.session_state.prompt, 
                        st.session_state.negative_prompt, 
                        st.session_state.width, 
                        st.session_state.height, 
                        st.session_state.num_images, 
                        st.session_state.strength, 
                        st.session_state.guidance_scale, 
                        st.session_state.num_inference_steps, 
                        st.session_state.seed,
                        input_image_url
                    )
                    if st.session_state.image_result_urls:
                        st.success(f"Successfully generated {len(st.session_state.image_result_urls)} image(s)!")
                    else:
                        st.error("Image generation failed. Check your API configuration.")
            else:
                st.error("Please enter a prompt to generate an image.")

        st.markdown("---")

        # Advanced Settings for Image (Replicated from original file)
        with st.expander("⚙️ Advanced Settings", expanded=False):
            st.markdown("Customize how the model generates your image.")
            
            resolution_options = {
                "512x512": (512, 512),
                "768x768": (768, 768),
                "1024x1024": (1024, 1024),
                "2048x2048 (2K)": (2048, 2048),
                "4096x4096 (4K)": (4096, 4096),
            }
            # The original file set index=3 for 2048x2048, so we keep that default
            selected_resolution = st.selectbox("Select Resolution", list(resolution_options.keys()), index=3, key="img_resolution")
            st.session_state.width, st.session_state.height = resolution_options[selected_resolution]

            st.session_state.strength = st.slider("Strength (For Img2Img)", min_value=0.0, max_value=1.0, value=st.session_state.strength, step=0.01, key="img_strength")
            st.session_state.guidance_scale = st.slider("Guidance Scale", min_value=1.0, max_value=15.0, value=st.session_state.guidance_scale, step=0.1, key="img_guidance_scale")
            st.session_state.num_images = st.slider("Number of Images", min_value=1, max_value=4, value=st.session_state.num_images, step=1, key="img_num_images")
            st.session_state.num_inference_steps = st.slider("Inference Steps", min_value=10, max_value=100, value=st.session_state.num_inference_steps, step=10, key="img_steps")
            st.session_state.seed = st.number_input("Seed (Keep consistent for similar results)", min_value=0, max_value=99999999, value=st.session_state.seed, step=1, key="img_seed")


    with col_output_img:
        st.markdown("## Image Output Gallery")
        if st.session_state.image_result_urls:
            num_cols = 2
            cols = st.columns(num_cols)
            for i, image_url in enumerate(st.session_state.image_result_urls):
                with cols[i % num_cols]:
                    # Use the same style for image output
                    st.image(image_url, caption=f"Result {i+1}", use_column_width="always")
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
