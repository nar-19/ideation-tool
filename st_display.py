import streamlit as st
import os
import pandas as pd
from google import genai
from google.genai import types
import streamlit as st
from modules import generate_trend, generate_ideas, store_ideas, create_or_clear_folder, generate_images

# Initialize the API key from secrets file
client = genai.Client(api_key = st.secrets["API_KEY"])

# # --- Data Loading ---
# df_idea = pd.read_csv("output/llm-output.csv")
# df_idea = df_idea.sort_values('created_date', ascending=False).reset_index(drop=True)

# --- Function to generate UI using Native Streamlit Components ---
def display_native_storyboard(idea_data, selected_influencer_type):
    try:
        # 1. Validation: Check if idea_data is valid before proceeding
        if not idea_data or not isinstance(idea_data, list):
            st.error("❌ No data received or data format is incorrect.")
            return

        # Data extraction
        idea_data = idea_data[0]
        
        # Using .get() is safer than square brackets to avoid KeyErrors
        trend_name = idea_data.get('trend_name', 'Unknown Trend')
        trend_description = idea_data.get('trend_description', 'No description available.')
        idea_title = idea_data.get('idea_title', 'Untitled Idea')
        idea_steps = idea_data.get('idea_steps', {})
        content_note = idea_data.get('content_note', {})

        with st.container(border=True):
            st.subheader(f"💡 Ideation for {selected_influencer_type}")
            st.title(idea_title)
            
            with st.expander("📌 View Trend Context", expanded=True):
                st.markdown(f"**Trend Name:** {trend_name}")
                st.markdown(f"**Description:** {trend_description}")

            st.divider()

            st.header("🎬 Storyboard Steps")
            
            # 2. Logic Protection: Ensure idea_steps is iterable
            if not idea_steps:
                st.info("No storyboard steps found for this idea.")
            else:
                for shot_key, shot_description in idea_steps.items():
                    try:
                        # Parsing the shot number can be fragile (e.g., if key is "Shot1" instead of "Shot 1")
                        parts = shot_key.split(' ')
                        shot_number = parts[1] if len(parts) > 1 else "X"
                        image_filename = f"image/image_{str(shot_number)}.png"

                        with st.container(border=True):
                            col_text, col_img = st.columns([1, 1])
                            
                            with col_text:
                                st.markdown(f"### {shot_key.capitalize()}")
                                st.write(shot_description)
                            
                            with col_img:
                                if os.path.exists(image_filename):
                                    st.image(image_filename, use_container_width=True, caption=f"Visual for {shot_key}")
                                else:
                                    st.warning(f"Image for {shot_key} is missing.")
                    except Exception as shot_error:
                        st.error(f"Error rendering {shot_key}: {shot_error}")

            st.divider()

            # 3. Final block check
            st.header("📝 Production Notes")
            if content_note:
                n_col1, n_col2 = st.columns(2)
                with n_col1:
                    st.info(f"**Format:** {content_note.get('📝content_format', 'N/A')}")
                    st.info(f"**Visual:** {content_note.get('🎨visual_concept', 'N/A')}")
                with n_col2:
                    st.success(f"**Overlay:** {content_note.get('🔤overlay_text', 'N/A')}")
                    st.success(f"**Caption:** {content_note.get('💬caption_suggestion', 'N/A')}")
            else:
                st.warning("Production notes are missing.")

    except IndexError:
        st.error("🚨 **Error:** The idea list is empty. Please generate ideas first.")
    except KeyError as e:
        st.error(f"🚨 **Data Error:** Missing expected information: {e}")
    except Exception as e:
        # General catch-all with a detailed expansion for debugging
        st.error("🚨 An unexpected error occurred while building the UI.")
        with st.expander("Show Technical Details"):
            st.code(traceback.format_exc())
            

# --- Streamlit App Layout ---
st.set_page_config(page_title="Content Ideation Tool", layout="wide")

st.title('🎥 Content Ideation Tool ✨')
st.markdown("Extracts TikTok trends and generates storyboards.")
st.write('---')

# Session State Initialization
if 'trend_data' not in st.session_state: st.session_state.trend_data = None
if 'content_ideas' not in st.session_state: st.session_state.content_ideas = None
if 'selected_influencer' not in st.session_state: st.session_state.selected_influencer = "Beauty Influencer"

# Step 1: Discover Trend
st.header("Step 1: Discover the Trend")
if st.button('1. Get Current Trend'):
    st.session_state.trend_data = generate_trend()
    st.session_state.content_ideas = None # Reset previous ideas

if st.session_state.trend_data:
    trend = st.session_state.trend_data[0]
    st.success(f"Trend fetched: {trend['trend_name']}")
    st.info(trend['trend_description'])

    # Step 2: Choose Influencer
    st.header("Step 2: Choose Your Influencer Type")
    st.session_state.selected_influencer = st.radio(
        "Select target profile:",
        ['Beauty Influencer', 'Fitness Influencer', 'Educational Influencer', 'Lifestyle Influencer']
    )

    # Step 3: Generate Storyboard
    st.header("Step 3: Generate Storyboard")
    if st.button('3. Generate Content Idea & Storyboard'):
        with st.status("Baking ideas... 🧑🏼‍🍳 This takes a few minutes", expanded=True) as status:
            st.write("Generating text content...")

            # Function (1)
            # st.session_state.content_ideas = generate_ideas(st.session_state.trend_data, st.session_state.selected_influencer)
            content_ideas = generate_ideas(st.session_state.trend_data, st.session_state.selected_influencer)
            store_ideas(content_ideas)
            st.session_state.content_ideas = content_ideas
            
            st.write("Creating storyboard visuals...")

            # Note: ensure generate_images saves to 'image/' folder
            # generate_images(st.session_state.content_ideas)
            # Function (2)
            # Create new directory 'image'. If it already exists, clear the folder and recreate.
            directory_name = "image"
            create_or_clear_folder(directory_name)

            # Function (3)
            # Generate images per shot and display output
            generate_images(content_ideas)
            
            status.update(label="Storyboard Complete!", state="complete", expanded=False)

# Display Output
if st.session_state.content_ideas:
    st.write('---')

    display_native_storyboard(st.session_state.content_ideas, st.session_state.selected_influencer)



# def display_native_storyboard(idea_data, selected_influencer_type):
#     # Data extraction
#     idea_data = idea_data[0]
#     trend_name = idea_data['trend_name']
#     trend_description = idea_data['trend_description']
#     idea_title = idea_data['idea_title']
#     idea_steps = idea_data['idea_steps']
#     content_note = idea_data['content_note']

#     # 1. Main Container (Replacing .idea-card)
#     with st.container(border=True):
#         st.subheader(f"💡 Ideation for {selected_influencer_type}")
#         st.title(idea_title)
        
#         # Trend Context
#         with st.expander("📌 View Trend Context", expanded=True):
#             st.markdown(f"**Trend Name:** {trend_name}")
#             st.markdown(f"**Description:** {trend_description}")

#         st.divider()

#         # 2. Idea Steps (Replacing .shot-item)
#         st.header("🎬 Storyboard Steps")
        
#         for shot_key, shot_description in idea_steps.items():
#             # Extract shot number for image filename
#             shot_number = shot_key.split(' ')[1]
#             image_filename = f"image/image_{str(shot_number)}.png"

#             # Create a nested container for each shot
#             with st.container(border=True):
#                 col_text, col_img = st.columns([1, 1])
                
#                 with col_text:
#                     st.markdown(f"### {shot_key.capitalize()}")
#                     st.write(shot_description)
                
#                 with col_img:
#                     if os.path.exists(image_filename):
#                         # Native st.image handles local paths automatically
#                         st.image(image_filename, width='stretch', caption=f"Visual for {shot_key}")
#                     else:
#                         st.warning(f"Image_{shot_number}.png not found.")

#         st.divider()

#         # 3. Content Notes (Replacing .content-note-list)
#         st.header("📝 Production Notes")
        
#         # Using columns for a cleaner "Note" layout
#         n_col1, n_col2 = st.columns(2)
#         with n_col1:
#             st.info(f"**Format:** {content_note['📝content_format']}")
#             st.info(f"**Visual:** {content_note['🎨visual_concept']}")
#         with n_col2:
#             st.success(f"**Overlay:** {content_note['🔤overlay_text']}")
#             st.success(f"**Caption:** {content_note['💬caption_suggestion']}")











