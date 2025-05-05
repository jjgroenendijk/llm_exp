# Simple Kokoro TTS ONNX Inference using kokoro-onnx

This project provides a simple Python script to run inference using the Kokoro TTS ONNX model via the `kokoro-onnx` package. This package simplifies the process and handles ONNX Runtime session management, including attempting hardware acceleration (like Core ML on Apple Silicon Macs) automatically.

This implementation is based on the [thewh1teagle/kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) repository.

## Features

*   Uses the `kokoro-onnx` package for easy TTS inference.
*   Loads the required `kokoro-v1.0.onnx` model and `voices-v1.0.bin` voice data.
*   Handles ONNX Runtime setup internally, attempting hardware acceleration where available.
*   Generates audio and saves it to a WAV file using `soundfile`.
*   Includes `inference.py` for simple, hardcoded synthesis.
*   Includes `cli.py` for flexible command-line synthesis with various options.

## Setup

1.  **Clone or Download:** Get the files from this project.
2.  **Create Virtual Environment:**
    ```bash
    # Using standard venv
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install Dependencies:**
    ```bash
    # Using pip
    pip install -r requirements.txt
    ```
    This installs `kokoro-onnx` and `soundfile`. `onnxruntime` is installed as a dependency of `kokoro-onnx`.
4.  **Download Model Files:**
    *   Download `kokoro-v1.0.onnx` from [here](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx).
    *   Download `voices-v1.0.bin` from [here](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin).
    *   Place both downloaded files (`kokoro-v1.0.onnx` and `voices-v1.0.bin`) in the project's root directory (alongside `inference.py` and `cli.py`).

## Usage (Simple Script - inference.py)

1.  **Activate Environment:**
    ```bash
    source venv/bin/activate
    ```
2.  **(Optional) Modify `inference.py`:** You can change the hardcoded text, voice, language, or output filename directly within the `inference.py` script:
    *   `TEXT_TO_SYNTHESIZE`: The text you want to convert to speech.
    *   `VOICE_ID`: The desired voice (see available voices [here](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) or listed in `cli.py`).
    *   `LANGUAGE_CODE`: The language code corresponding to the text/voice.
    *   `OUTPUT_FILENAME`: The name of the output WAV file.
3.  **Run `inference.py`:**
    ```bash
    python inference.py
    ```
    The script will load the model, generate the audio, and save it to `output_audio.wav` (or the filename specified in `OUTPUT_FILENAME`). This script is useful for quick tests with predefined settings.

## Usage (Command-Line Interface - cli.py)

The `cli.py` script offers more flexibility through command-line arguments.

1.  **Activate Environment:**
    ```bash
    source venv/bin/activate
    ```
2.  **Run `cli.py` with Options:**
    ```bash
    python cli.py --text "Your text here" --output-dir <output_directory> [options]
    ```

    **Required Arguments:**
    *   `--text TEXT`: The text to synthesize (required unless `--test` is used).
    *   `--output-dir OUTPUT_DIR`: The directory where the output `.wav` file(s) will be saved.

    **Optional Arguments:**
    *   `--voice VOICE_ID`: Specify the voice ID (default: `af_sarah`). See the list in `cli.py` or [here](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md). Ignored if `--test` is used.
    *   `--lang LANG_CODE`: Specify the language code (default: `en-us`). Ignored if `--test` is used.
    *   `--speed SPEED`: Set the synthesis speed (default: `1.0`).
    *   `--output-filename FILENAME`: Set the name for the output file (default: `output.wav`). Ignored if `--test` is used.
    *   `--model MODEL_PATH`: Path to the `.onnx` model file (default: `kokoro-v1.0.onnx`).
    *   `--voices VOICES_PATH`: Path to the `.bin` voices file (default: `voices-v1.0.bin`).
    *   `--test`: Generate audio samples for **all English voices** (American and British). Uses the text provided via `--text` or a default sentence if `--text` is omitted. Output filenames will be `<voice_id>.wav`.

    **Examples:**

    *   Generate audio with a specific voice:
        ```bash
        mkdir audio_output
        python cli.py --text "Hello from the command line." --voice "af_heart" --output-dir audio_output --output-filename hello.wav
        ```
    *   Generate samples for all English voices using the default sentence:
        ```bash
        mkdir all_english_samples
        python cli.py --test --output-dir all_english_samples
        ```
    *   Generate samples for all English voices using custom text:
        ```bash
        mkdir custom_test_samples
        python cli.py --test --text "Testing all the different English voices." --output-dir custom_test_samples
        ```

## Notes

*   **Hardware Acceleration:** The `kokoro-onnx` package should automatically detect and use available ONNX Runtime execution providers like Core ML on macOS or CUDA/DirectML on other platforms if `onnxruntime` was installed with the appropriate support.
*   **G2P:** For best results, especially with non-English languages, the underlying `kokoro-onnx` package might rely on external Grapheme-to-Phoneme (G2P) tools or packages like `misaki`. Ensure you have any necessary G2P dependencies installed if required for your chosen language (refer to `kokoro-onnx` or original Kokoro documentation if issues arise).
