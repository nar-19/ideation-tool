import pandas as pd
import numpy as np
# from dotenv import load_dotenv
from datetime import datetime
from google import genai
from google.genai import types
from PIL import Image as pilImage
import os, json, random, string, time, io, shutil

# from dotenv import load_dotenv # Load env
# # Load environment variables from .env file
# load_dotenv()
# # Get the API key from the .env file
# # client = genai.Client(api_key=os.environ.get('API_KEY'))
# client = genai.Client(api_key=os.getenv("API_KEY"))


def generate_llm_output(prompt):
    response_json = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents = prompt
    )

    json_output = (response_json.text)
    # print(json_output)
    json_text = json_output.split("json")[1].replace("```","")
    # Convert string type LLM outputs to a dictionary type
    json_object = json.loads(json_text)

    return json_object


def generate_trend():
    prompt_trend = """
    1) Persona: You are a creative, young, lively content strategist from a boutique marketing agency.

    2) Purpose and goal:
    Get 1 latest Tiktok trends in Malaysia. The trends must be the specific trend that includes specific description such as the name of the trend or challenge and the relatable background sound or music.

    3) Output items:
    trend_name: (The TikToktrend name.)
    trend_description: (The TikTok trend description.)

    4) Output format:
    Return the answer in Json format with the following structure.
    [{"trend_name": "string", "trend_description": "string"}]
    """

    trend_data = generate_llm_output(prompt_trend)
    print(trend_data)
    return trend_data


def generate_ideas(trend_data, influencer_type):
  prompt_ideas = f"""
  1) Persona: You are a creative, young, lively content strategist from a boutique marketing agency.

  2) Purpose and goal:
  Create 1 unique content idea based on the following TikTok trend for a {influencer_type} in Malaysia.
  Trend name: {trend_data[0]['trend_name']}
  Trend description: {trend_data[0]['trend_description']}

  3) Content ideas:
  - The ideas need to apply creative elements, with some fun and lively concepts inspired by modern cultures, and may have some plot twists elements.
  - Detail the output either to be formed in static image or videos in a way where it helps the content creator to create the content.
  - Add a Content Note detailing the content format, visual concept with overlay text if any, and caption suggestions or guidance. 
  If it is a video, add the details of the acts or shots recommended.
  - Do use many emojis in the outputs, including in the trend name and trend description.

  4) Output items:
  trend_name: (The TikToktrend name.)
  trend_description: (The TikTok trend description.)
  idea_title: (The concise title or concept of the content idea)
  idea_steps: (Steps to execute either the static image or video idea, suitable for content production. Maximum of 4 steps.)
  content_note: (Content format, overlay text if any, and caption suggestions or guidance.)
  """ + """
  5) Output format:
  Return the answer in Json format with the following structure.
  [{"trend_name": "string", 
    "trend_description": "string",
    "idea_title":"string",
    "idea_steps":{"🎬shot 1":"string","🎬shot 2":"string","🎬shot 3":"string"},
    "content_note":{"📝content_format":"string","🎨visual_concept":"string","🔤overlay_text":"string","💬caption_suggestion":"string"}
    }]
  """

  content_ideas = generate_llm_output(prompt_ideas)
  print(content_ideas)

  return content_ideas


# Define a function to generate the unique idea ID
def generate_idea_id(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))


def store_ideas(content_ideas):
    # Convert the outputs in Json format into a dataframe format for storage
    df_idea = pd.DataFrame.from_dict(content_ideas)

    # Renaming columns for a more self-describing column name
    df_idea = df_idea.assign(idea_id = np.nan)

    # Generate a random alphanumeric idea ID
    df_idea.idea_id = df_idea.idea_id.apply(lambda x: str(generate_idea_id()) if pd.isnull(x) else x)

    # Generate a created_date column
    df_idea = df_idea.assign(created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Re-arrange columns
    cols = ['trend_name', 'trend_description', 'idea_title', 'idea_steps', 'content_note', 'created_date']
    df_idea = df_idea[cols]

    # Check if the file exists
    csv_file_path = 'output/llm-output.csv'
    file_exists = os.path.exists(csv_file_path)

    df_llm_output = df_idea.copy()

    # Append to csv
    if file_exists:
        # Append without header if file already exists
        df_llm_output.to_csv(csv_file_path, mode='a', header=False, index=False, encoding='utf-8-sig')
        print(f"Data appended to '{csv_file_path}'.")

    else:
        # Append with header if file does not exist
        df_llm_output.to_csv(csv_file_path, mode='w', header=True, index=False, encoding='utf-8-sig')
        print(f"New file '{csv_file_path}' created with header and data.")


def create_or_clear_folder(folder_path):
    # Check if the folder already exists
    if os.path.exists(folder_path):
        print(f"Folder '{folder_path}' already exists. Clearing its contents...")
        # Remove the directory and all its contents recursively
        shutil.rmtree(folder_path)
        print(f"Folder '{folder_path}' cleared.")
    
    # Create a new, empty directory (and any necessary parent directories)
    os.makedirs(folder_path)
    print(f"Folder '{folder_path}' is ready.")


def generate_images(content_ideas):
    # Create shot-by-shot images for the generated ideas
    # Store the shots by incremental numbering generated_image_n.png

    for idea in content_ideas:
        i = 1 # File naming counter
        # print("idea no:", idea['idea_no'])
        for shot in idea['idea_steps']:
            
            if i == 1:
                print(idea['idea_steps'][shot])
                print("")
                prompt = (
                    f'''{idea['idea_steps'][shot]}.
                    
                    Additional instructions:
                    - The character in the image must be a Malaysian character from any race in Malaysia.
                    - Add in overlay texts where relevant and applicable, for example to introduce things.
                    '''
                )

                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=[prompt],
                )

            else:    
                print(idea['idea_steps'][shot])
                print("")
                prompt = (
                    f'''
                    Main input instruction:
                    {idea['idea_steps'][shot]}.

                    Additional instructions:
                    - Use the main person from the attached image as the character in the generated image, drop the initial speech bubble if any.
                    - Remove the overlay texts from the reference image to prevent redundancy.
                    - Use the setting from the attached image as the background in the generated image. The setting can change depending on the suitability and creativeness of the earlier main input instruction, but the similarity should be retained where it is applicable. For example, when a person is cooking, the setting should be the same kitchen as in the reference image. But the setting can change, for example to outside area or other area to fit the main input instruction.
                    - Generate new speech bubbles if this is relevant, and add in overlay texts where relevant and applicable, for example to introduce certain things.
                    '''
                )
                # Read the reference person image Created earlier to be included in the prompting
                reference_image = pilImage.open("image/image_" + str(1) + ".png")

                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=[prompt, reference_image],
                )

            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    print(part.text)
                elif part.inline_data is not None:
                    # image = part.as_image()
                    img_data = part.inline_data.data
                    image = pilImage.open(io.BytesIO(img_data))
                    image_resized = image.resize((300, 300), pilImage.Resampling.LANCZOS)

                    image_resized.save("image/image_" + str(i) + ".png")
            
            i = i+1
            time.sleep(30)

