import argparse
import sys
import os
import soundfile as sf
from kokoro_onnx import Kokoro

# Available Voices (from VOICES.md):
# American English (lang_code='a'):
#   af_heart, af_alloy, af_aoede, af_bella, af_jessica, af_kore, af_nicole, af_nova, af_river, af_sarah, af_sky
#   am_adam, am_echo, am_eric, am_fenrir, am_liam, am_michael, am_onyx, am_puck, am_santa
# British English (lang_code='b'):
#   bf_alice, bf_emma, bf_isabella, bf_lily
#   bm_daniel, bm_fable, bm_george, bm_lewis
# Japanese (lang_code='j'):
#   jf_alpha, jf_gongitsune, jf_nezumi, jf_tebukuro
#   jm_kumo
# Mandarin Chinese (lang_code='z'):
#   zf_xiaobei, zf_xiaoni, zf_xiaoxiao, zf_xiaoyi
#   zm_yunjian, zm_yunxi, zm_yunxia, zm_yunyang
# Spanish (lang_code='e'):
#   ef_dora
#   em_alex, em_santa
# French (lang_code='f'):
#   ff_siwis
# Hindi (lang_code='h'):
#   hf_alpha, hf_beta
#   hm_omega, hm_psi
# Italian (lang_code='i'):
#   if_sara
#   im_nicola
# Brazilian Portuguese (lang_code='p'):
#   pf_dora
#   pm_alex, pm_santa

# Define English voices for the test flag
AMERICAN_ENGLISH_VOICES = [
    "af_heart", "af_alloy", "af_aoede", "af_bella", "af_jessica", "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky",
    "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael", "am_onyx", "am_puck", "am_santa"
]
BRITISH_ENGLISH_VOICES = [
    "bf_alice", "bf_emma", "bf_isabella", "bf_lily",
    "bm_daniel", "bm_fable", "bm_george", "bm_lewis"
]
ALL_ENGLISH_VOICES = AMERICAN_ENGLISH_VOICES + BRITISH_ENGLISH_VOICES
DEFAULT_TEST_SENTENCE = "The quick brown fox jumps over the lazy dog."

def synthesize_audio(kokoro, text, voice, lang, speed, output_path):
    """Generates and saves audio for a single voice."""
    try:
        print(f"\nSynthesizing text: '{text}'")
        print(f"Using voice: {voice}")
        print(f"Using language: {lang}")
        print(f"Speed: {speed}")
        print(f"Output path: {output_path}")

        # Generate audio samples
        samples, sample_rate = kokoro.create(
            text,
            voice=voice,
            speed=speed,
            lang=lang
        )
        print(f"Audio generated with sample rate: {sample_rate}")

        # Save the audio to a WAV file
        sf.write(output_path, samples, sample_rate)
        print(f"Audio saved to '{output_path}'")
        return True

    except ValueError as e:
        print(f"Error during synthesis for voice {voice}: {e}", file=sys.stderr)
        print("Check if the voice ID and language code are valid.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred during synthesis for voice {voice}: {e}", file=sys.stderr)
        return False


def main():
    """Parses command-line arguments and generates audio using Kokoro ONNX."""

    parser = argparse.ArgumentParser(description="Generate audio from text using Kokoro ONNX. Use --test to generate samples for all English voices.")
    parser.add_argument("--text", help=f"Text to synthesize. Required unless --test is used (default for test: '{DEFAULT_TEST_SENTENCE}').")
    parser.add_argument("--voice", default="af_sarah", help="Voice ID to use (default: af_sarah). Ignored if --test is used.")
    parser.add_argument("--lang", default="en-us", help="Language code (default: en-us). Ignored if --test is used.")
    parser.add_argument("--speed", type=float, default=1.0, help="Synthesis speed (default: 1.0).")
    parser.add_argument("--test", action="store_true", help="Generate audio for all English voices using the default test sentence or provided text.")
    parser.add_argument("--output-dir", required=True, help="Directory to save the output audio file(s).")
    parser.add_argument("--output-filename", default="output.wav", help="Name for the output audio file (default: output.wav). Ignored if --test is used; filenames will be based on voice ID.")
    parser.add_argument("--model", default="kokoro-v1.0.onnx", help="Path to the Kokoro model file (default: kokoro-v1.0.onnx).")
    parser.add_argument("--voices", default="voices-v1.0.bin", help="Path to the voices file (default: voices-v1.0.bin).")

    args = parser.parse_args()

    # Validate arguments
    if not args.test and not args.text:
        parser.error("--text is required unless --test is specified.")
    if args.test and not args.text:
        args.text = DEFAULT_TEST_SENTENCE
        print(f"Using default test sentence: '{args.text}'")

    print(f"Loading Kokoro model: {args.model}")
    print(f"Loading voices: {args.voices}")

    try:
        # Initialize Kokoro
        kokoro = Kokoro(args.model, args.voices)
        print("Kokoro model loaded successfully.")

    except FileNotFoundError:
        print(f"Error: Model file '{args.model}' or voices file '{args.voices}' not found.", file=sys.stderr)
        print("Please ensure the paths are correct or download them from https://github.com/thewh1teagle/kokoro-onnx/releases", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error initializing Kokoro: {e}", file=sys.stderr)
        sys.exit(1)

    # Ensure output directory exists
    try:
        os.makedirs(args.output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating output directory '{args.output_dir}': {e}", file=sys.stderr)
        sys.exit(1)

    if args.test:
        print("\n--- Running in Test Mode: Generating samples for all English voices ---")
        success_count = 0
        fail_count = 0
        for voice_id in ALL_ENGLISH_VOICES:
            # Determine language code based on voice prefix (though 'en-us' might work for both)
            lang_code = "en-us" # Defaulting to en-us as per comments and common usage
            # if voice_id.startswith("bf_") or voice_id.startswith("bm_"):
            #     lang_code = "en-gb" # Potentially use en-gb for British voices if needed
            # else:
            #     lang_code = "en-us"

            output_filename = f"{voice_id}.wav"
            output_path = os.path.join(args.output_dir, output_filename)

            if synthesize_audio(kokoro, args.text, voice_id, lang_code, args.speed, output_path):
                success_count += 1
            else:
                fail_count += 1
        print(f"\n--- Test Mode Complete: {success_count} succeeded, {fail_count} failed ---")

    else:
        # Original single synthesis logic
        output_path = os.path.join(args.output_dir, args.output_filename)
        synthesize_audio(kokoro, args.text, args.voice, args.lang, args.speed, output_path)


if __name__ == "__main__":
    main()
