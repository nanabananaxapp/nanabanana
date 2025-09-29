import streamlit as st
import fal_client # Required for video generation call
import requests   # Required for downloading/R2 staging

# --- 1. CORE CONSTANTS AND MODEL ---
VIDEO_PASSWORD = "f6676kwp"
WANI2V_MODEL = "fal-ai/wan-i2v" 
DEFAULT_NEGATIVE_PROMPT = "bright colors, overexposed, static, blurred details, subtitles, style, artwork, painting, picture, still, overall gray, worst quality, low quality, etc." 
IS_FAL_READY = True # Assumed True for logic flow, actual check happens elsewhere

# --- 2. PLACEHOLDERS FOR EXTERNAL DEPENDENCIES ---
# NOTE: These functions must exist in your main application environment.

def upload_file_to_r2(content_url, file_extension):
    """Placeholder for R2/S3 upload logic."""
    # In a real app, this stages the FAL URL to a permanent storage URL.
    return content_url 

def display_image_uploader_with_thumbnail(session_state_key, label_text):
    """Placeholder for image uploader. Returns base64 image URL or None."""
    # This simulates the I2V image upload logic from the main app.
    return None # Placeholder always returns None for simplicity here

# --- 3. SESSION STATE INITIALIZATION (Default Settings) ---

def initialize_video_session_state():
    """Initializes all video-related session state variables with default values."""
    defaults = {
        'video_upload_img_data': None,
        'video_result_url': None,
        'video_password_input': "",
        'video_authenticated': False, 
        'password_error': None, 
        'video_prompt': "A majestic banana riding a futuristic, glowing skateboard in space, cinematic.",
        'video_width': 832, # Default Resolution
        'video_height': 480, # Default Resolution
        'video_strength': 0.7, # Default Strength (I2V)
        'motion_bucket_id': 127, # Default Motion
        'cond_aug': 0.02, # Default Conditioning Augmentation
        'video_num_inference_steps': 50, # Default Steps
        'video_fps': 16, # Default FPS
        'video_num_frames': 81, # Default Frames
        'video_lora_weight': 0.7, # Default LoRA Weight
        'video_safety_checker': False, # Default Safety Checker
        'negative_prompt': DEFAULT_NEGATIVE_PROMPT # Shared negative prompt
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- 4. CORE VIDEO LOGIC FUNCTIONS ---

def fal_generate_video(fal_client_instance, prompt, negative_prompt, input_image_url=None):
    """Handles the communication with the FAL Wan-I2V model."""
    
    # fal_client_instance must be the instantiated fal_client object from the main app
    # This logic assumes the main app handles the spinner/toasts/error reporting
    
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
        "enable_safety_checker": st.session_state.video_safety_checker,
        "seed": None
    }
    
    if input_image_url:
        params["image_url"] = input_image_url
    
    try:
        handler = fal_client_instance.submit(WANI2V_MODEL, arguments=params)
        result = handler.get_response(stream=True)
            
        fal_url = result['video']['url']
        staged_url = upload_file_to_r2(fal_url, ".mp4")
        return staged_url

    except Exception:
        # The main app should catch and display the detailed error
        return None

def check_video_password_callback():
    """Checks the password and updates authentication state."""
    password_attempt = st.session_state.video_password_input
    
    if password_attempt == VIDEO_PASSWORD:
        st.session_state.video_authenticated = True
        st.session_state.password_error = None
    else:
        st.session_state.password_error = "INCORRECT_PASSWORD"
        st.session_state.video_authenticated = False


# --- 5. PURE STREAMLIT UI RENDERER ---
def render_pure_video_ui(fal_client_instance):
    """
    Renders the Video Generator UI with minimal text, focusing on controls.
    NOTE: initialize_video_session_state() must be called first.
    """
    
    if not st.session_state.video_authenticated:
        # Password Gate UI
        st.text_input("PASSWORD", type="password", key="video_password_input")
        st.button("UNLOCK", key="video_unlock_button", on_click=check_video_password_callback, type="primary")

    else:
        # Main Video Generation UI
        col_input_video, col_output_video = st.columns([1.3, 1.7])

        with col_input_video:
            # I2V Image Upload
            input_video_image_url = display_image_uploader_with_thumbnail(
                'video_upload_img_data',
                "Initial image (I2V Optional)"
            )

            st.session_state.video_prompt = st.text_area(
                "Video Prompt",
                value=st.session_state.video_prompt,
                key="video_prompt_area_pure"
            )
            
            st.session_state.negative_prompt = st.text_area(
                "Negative Prompt",
                value=st.session_state.negative_prompt,
                key="video_negative_prompt_area_pure"
            )
                
            if st.button(
                "Generate Video", 
                key="generate_video_button_pure", 
                type="primary", 
                disabled=(not IS_FAL_READY) 
            ):
                if st.session_state.video_prompt:
                    st.session_state.video_result_url = fal_generate_video(
                        fal_client_instance,
                        st.session_state.video_prompt, 
                        st.session_state.negative_prompt, 
                        input_video_image_url
                    )

            # Advanced Settings UI (Sliders and Selectboxes)
            with st.expander("Settings"):
                resolution_video_options = {
                    "512x512": (512, 512),
                    "832x480": (832, 480),
                }
                current_res_key = next((k for k, v in resolution_video_options.items() if v == (st.session_state.video_width, st.session_state.video_height)), "832x480")
                
                selected_resolution_video = st.selectbox("Resolution", list(resolution_video_options.keys()), index=list(resolution_video_options.keys()).index(current_res_key), key="video_res_select_pure")
                st.session_state.video_width, st.session_state.video_height = resolution_video_options[selected_resolution_video]

                st.session_state.video_strength = st.slider("Strength (I2V)", min_value=0.0, max_value=1.0, value=st.session_state.video_strength, step=0.01)
                st.session_state.video_num_frames = st.slider("Frames (16-250)", min_value=16, max_value=250, value=st.session_state.video_num_frames, step=1)
                st.session_state.video_fps = st.slider("FPS (8-30)", min_value=8, max_value=30, value=st.session_state.video_fps, step=1)
                st.session_state.motion_bucket_id = st.slider("Motion ID (0-1024)", min_value=0, max_value=1024, value=st.session_state.motion_bucket_id, step=1)
                st.session_state.cond_aug = st.slider("Cond Aug (0.0-0.2)", min_value=0.0, max_value=0.2, value=st.session_state.cond_aug, step=0.01)
                st.session_state.video_lora_weight = st.slider("LoRA Weight (0.0-1.0)", min_value=0.0, max_value=1.0, value=st.session_state.video_lora_weight, step=0.01)
                st.session_state.video_num_inference_steps = st.slider("Inference Steps (10-100)", min_value=10, max_value=100, value=st.session_state.video_num_inference_steps, step=5)
                st.session_state.video_safety_checker = st.checkbox("Safety Filter", value=st.session_state.video_safety_checker, key="video_safety_check_pure")
                
        # Video Output Display
        with col_output_video:
            if st.session_state.video_result_url:
                st.video(st.session_state.video_result_url)
                
                st.download_button(
                    label="DOWNLOAD",
                    data=requests.get(st.session_state.video_result_url).content,
                    file_name=f"video.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
