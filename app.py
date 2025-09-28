import streamlit as st
import fal_client
import os
import tempfile
import json
import datetime
import time # Used for mock generation delay

# Define Constants
VIDEO_PASSWORD = "f6676kwp"

# Comprehensive Negative Prompt (as requested)
DEFAULT_NEGATIVE_PROMPT = "bright colors, overexposed, static, blurred details, subtitles, style, artwork, painting, picture, still, overall gray, worst quality, low quality, JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn faces, deformed, disfigured, malformed limbs, fused fingers, still picture, cluttered background, three legs, many people in the background, walking backwards"


# --- App Configuration and Styling ---
st.set_page_config(
    page_title="NANO BANANA X AI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for the precise dark, professional look
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


# --- Session State Initialization (Updated for Wan-I2V defaults and Random Seed) ---

# --- GENERAL DEFAULTS ---
if 'negative_prompt' not in st.session_state: st.session_state.negative_prompt = DEFAULT_NEGATIVE_PROMPT
if 'seed' not in st.session_state: st.session_state.seed = None # Always Random (no value)
if 'video_authenticated' not in st.session_state: st.session_state.video_authenticated = False 

# --- IMAGE DEFAULTS (Seedream/SDXL) ---
if 'prompt' not in st.session_state: st.session_state.prompt = "A hyper-realistic portrait of a golden retriever wearing a banana helmet, 8k cinematic lighting"
if 'image_result_urls' not in st.session_state: st.session_state.image_result_urls = []
if 'width' not in st.session_state: st.session_state.width = 1024
if 'height' not in st.session_state: st.session_state.height = 1024
if 'strength' not in st.session_state: st.session_state.strength = 0.95 # Retained: 0.95
if 'guidance_scale' not in st.session_state: st.session_state.guidance_scale = 4.5 # Retained: 4.5
if 'num_images' not in st.session_state: st.session_state.num_images = 1
if 'num_inference_steps' not in st.session_state: st.session_state.num_inference_steps = 50 
if 'enable_safety_checker' not in st.session_state: st.session_state.enable_safety_checker = False 

# --- VIDEO DEFAULTS (Wan-I2V / SVD-like - Matched to fal.ai site defaults) ---
if 'video_prompt' not in st.session_state: st.session_state.video_prompt = "A majestic banana riding a futuristic, glowing skateboard in space, cinematic."
if 'video_result_url' not in st.session_state: st.session_state.video_result_url = None
if 'video_width' not in st.session_state: st.session_state.video_width = 832 # Wan-I2V Default
if 'video_height' not in st.session_state: st.session_state.video_height = 480 # Wan-I2V Default
if 'video_strength' not in st.session_state: st.session_state.video_strength = 0.7 # Wan-I2V Default
if 'motion_bucket_id' not in st.session_state: st.session_state.motion_bucket_id = 127 # Wan-I2V Default
if 'cond_aug' not in st.session_state: st.session_state.cond_aug = 0.02 # Wan-I2V Default
if 'video_num_inference_steps' not in st.session_state: st.session_state.video_num_inference_steps = 40 # Wan-I2V Default
if 'video_fps' not in st.session_state: st.session_state.video_fps = 16 # Wan-I2V Default (Updated to 16)
if 'video_num_frames' not in st.session_state: st.session_state.video_num_frames = 81 # Wan-I2V Default (Updated to 81)
if 'video_lora_weight' not in st.session_state: st.session_state.video_lora_weight = 0.7 # Wan-I2V Default (0.7 is common for video strength)
if 'video_safety_checker' not in st.session_state: st.session_state.video_safety_checker = False 
if 'video_seed' not in st.session_state: st.session_state.video_seed = None # Always Random (no value)

# --- Authentication Logic ---
def authenticate_video_tab(password_attempt):
    """Checks the password and updates session state."""
    if password_attempt == VIDEO_PASSWORD:
        st.session_state.video_authenticated = True
        st.success("✅ Access Granted!")
    else:
        st.session_state.video_authenticated = False
        st.error("❌ Incorrect Password.")

# --- Mock Generation Functions (Kept for UI demonstration) ---
def fal_generate_image(prompt, negative_prompt, width, height, num_images, strength, guidance_scale, num_steps, seed, input_image_url=None):
    """MOCK function to simulate image generation. Seed will be None."""
    # Placeholder for the generated image URLs (single golden retriever image placeholder)
    mock_url = f"https://placehold.co/{width}x{height}/4169E1/FFD700?text=NANO+BANANA+X+AI+{width}x{height}"
    return [mock_url] * num_images


def fal_generate_video(prompt, negative_prompt, input_image_url=None, seed=None):
    """MOCK function to simulate video generation with delay. Seed will be None."""
    time.sleep(3) # Simulate processing time
    if input_image_url:
        st.toast(f"Starting Video-from-Image generation with prompt: {prompt}")
    # Public domain video for preview
    return "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"


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
        
        input_image_url = None
        if uploaded_file is not None:
             st.success("Image uploaded. Using Image-to-Image mode.")
             input_image_url = "mock-uploaded-image-url"

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
        # The actual seed passed is always None (random) as requested
        final_image_seed = None 
        
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
                        final_image_seed, # Always None
                        input_image_url
                    )
                    if st.session_state.image_result_urls:
                        st.toast(f"Generated {len(st.session_state.image_result_urls)} image(s)!")
            else:
                st.error("Please enter a prompt to generate an image.")

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
            
            # Seed input displayed for UI completeness, but the generation logic forces None (random)
            st.number_input("Seed (Policy: Always Random)", min_value=0, max_value=0, value=0, step=1, disabled=True, key="img_seed_input_display")
            
            st.session_state.enable_safety_checker = st.checkbox("Enable Safety Checker", value=st.session_state.enable_safety_checker, key="img_safety_check")

    with col_output_img:
        st.markdown("## Image Output Gallery")
        if st.session_state.image_result_urls:
            num_cols = 2
            cols = st.columns(num_cols)
            for i, image_url in enumerate(st.session_state.image_result_urls):
                with cols[i % num_cols]:
                    st.image(image_url, caption=f"Result {i+1}", use_column_width="always")
                    # Mock download button
                    st.download_button(
                        label="Download",
                        data="Mock image data",
                        file_name=f"fal-image_{i+1}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png",
                        mime="image/png",
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
            
            # --- Image Upload Section for Video Source ---
            video_uploaded_file = st.file_uploader(
                "Upload **source image** for Image-to-Video Generation (Optional)",
                type=["png", "jpg", "jpeg"],
                key="video_upload_img"
            )
            
            input_video_image_url = None
            if video_uploaded_file is not None:
                 st.success("Image uploaded. Ready for Video Generation.")
                 input_video_image_url = "mock-uploaded-image-url-for-video"
            else:
                 st.info("Upload an image to guide the starting frame and style of the video.")

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
            
            # The actual seed passed is always None (random) as requested
            final_video_seed = None 
            
            # --- Generate Button ---
            if st.button("🚀 Generate Video", key="generate_video_button", type="primary", use_container_width=True):
                if st.session_state.video_prompt:
                    with st.spinner('Generating video... this can take a few minutes.'):
                        video_url = fal_generate_video(
                            st.session_state.video_prompt, 
                            st.session_state.negative_prompt,
                            input_video_image_url,
                            final_video_seed # Always None
                        )
                        st.session_state.video_result_url = video_url
                        st.toast("Video generation complete!")
                else:
                    st.error("Please enter a prompt to generate a video.")
            
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
                selected_video_resolution = st.selectbox("Resolution", list(video_resolution_options.keys()), index=0, key="vid_resolution_select")
                st.session_state.video_width, st.session_state.video_height = video_resolution_options[selected_video_resolution]

                # Core Generation Parameters
                st.session_state.video_strength = st.slider("Strength (Image Fidelity)", min_value=0.0, max_value=1.0, value=st.session_state.video_strength, step=0.01, key="vid_strength_slider")
                st.session_state.motion_bucket_id = st.slider("Motion Bucket ID (Movement amount)", min_value=1, max_value=255, value=st.session_state.motion_bucket_id, step=1, key="vid_motion_bucket_slider")
                st.session_state.cond_aug = st.slider("Conditioning Augmentation", min_value=0.0, max_value=0.1, value=st.session_state.cond_aug, step=0.01, format="%.2f", key="vid_cond_aug_slider")
                st.session_state.video_lora_weight = st.slider("LoRA Weight (Style adaptation)", min_value=0.0, max_value=1.0, value=st.session_state.video_lora_weight, step=0.01, key="vid_lora_weight_slider")
                
                # Time/Quality Parameters (UPDATED)
                st.session_state.video_num_frames = st.slider("Number of Frames", min_value=16, max_value=100, value=st.session_state.video_num_frames, step=1, key="vid_num_frames_slider")
                st.session_state.video_fps = st.slider("FPS (Frames per Second)", min_value=1, max_value=24, value=st.session_state.video_fps, step=1, key="vid_fps_slider")
                st.session_state.video_num_inference_steps = st.slider("Inference Steps", min_value=10, max_value=100, value=st.session_state.video_num_inference_steps, step=1, key="vid_steps_slider")

                # Seed input displayed for UI completeness, but the generation logic forces None (random)
                st.number_input("Seed (Policy: Always Random)", min_value=0, max_value=0, value=0, step=1, disabled=True, key="vid_seed_input_display")
                
                st.session_state.video_safety_checker = st.checkbox("Enable Safety Checker", value=st.session_state.video_safety_checker, key="vid_safety_check")

        with col_output:
            st.markdown("## Video Output Preview")
            if st.session_state.video_result_url:
                st.video(st.session_state.video_result_url)
                st.markdown(f'<p style="text-align:center; color: var(--text-color); font-size: 0.9rem;">Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>', unsafe_allow_html=True)
                # Mock download button
                st.download_button(
                    label="Download Video (MP4)",
                    data="Mock video data",
                    file_name=f"fal-video_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp4",
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

