
from pathlib import Path
import config

def text_to_speech_file(text: str, folder: str) -> str:
    if not config.ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY is not configured")
    if not text.strip():
        raise RuntimeError("Narration text is empty")
    try:
        from elevenlabs import VoiceSettings
        from elevenlabs.client import ElevenLabs
    except ImportError as exc:
        raise RuntimeError("The elevenlabs package is not installed") from exc

    client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
    # Calling the text_to_speech conversion API with detailed parameters
    response = client.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB", # Adam pre-made voice
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2_5", # use the turbo model for low latency
        # Optional voice settings that allow you to customize the output
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    # uncomment the line below to play the audio back
    # play(response)

    # Generating a unique file name for the output MP3 file
    save_file_path = Path(config.UPLOAD_FOLDER) / folder / "audio.mp3"

    # Writing the audio to a file
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"{save_file_path}: A new audio file was saved successfully!")

    # Return the path of the saved audio file
    return save_file_path


# text_to_speech_file("Hey I am a good boy and its the python course", "ac9a7034-2bf9-11f0-b9c0-ad551e1c593a")
