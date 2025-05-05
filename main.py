import os
import time
import pandas as pd
from dotenv import load_dotenv
import lyricsgenius
import openai

# Load environment variables
load_dotenv()
GENIUS_TOKEN = os.getenv("ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_KEY")

# Initialize clients
genius = lyricsgenius.Genius(
    GENIUS_TOKEN,
    timeout=15,
    retries=3,
    skip_non_songs=True,
    remove_section_headers=True
)
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

def fetch_lyrics(track: str, artist: str) -> str:
    song = genius.search_song(title=track, artist=artist)
    return song.lyrics if song and song.lyrics else None

def analyze_lyrics(lyrics: str) -> tuple[str, str]:
    prompt = f"""
Analyze the following song lyrics and identify:
- The most common theme. Give me only one theme. The most prominent one (e.g. love, success, sadness)
- The overall mood. (e.g. happy, aggressive, nostalgic)

In your response just give me the theme and the mood. Do not write anything else in your response.
Example:
Theme: Love
Mood: Sad

Lyrics:
{lyrics}
"""
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content
    theme = mood = "N/A"
    for line in content.splitlines():
        if "theme" in line.lower():
            theme = line.split(":")[-1].strip()
        elif "mood" in line.lower():
            mood = line.split(":")[-1].strip()
    return theme, mood

def process_dataframe(csv_path: str, output_path: str):
    df = pd.read_csv(csv_path)
    df["Lyrics"] = ""
    df["Theme"] = ""
    df["Mood"] = ""

    for index, row in df.iterrows():
        track, artist = row["Track"], row["Artists"]
        print(f"Processing: {track} by {artist}")
        try:
            lyrics = fetch_lyrics(track, artist)
            if lyrics:
                theme, mood = analyze_lyrics(lyrics)
                df.at[index, "Lyrics"] = lyrics
                df.at[index, "Theme"] = theme
                df.at[index, "Mood"] = mood
            else:
                df.at[index, "Lyrics"] = "Not found"
        except Exception as e:
            print(f"Error with {track} by {artist}: {e}")
            df.at[index, "Lyrics"] = "Error"
            df.at[index, "Theme"] = "Error"
            df.at[index, "Mood"] = "Error"
        time.sleep(1.5)

    df.to_excel(output_path, index=False)
    print(f"Analysis complete. File saved to {output_path}")

if __name__ == "__main__":
    INPUT_CSV = "Spotify Daily Global Chart - Top 50 (May 4, 2025) - 2025_05_05 - 09_51_06.csv"
    OUTPUT_FILE = "Top_50_Analysis.xlsx"
    process_dataframe(INPUT_CSV, OUTPUT_FILE)
