import google.generativeai as genai
import argparse
import os
import math
import time
import ffmpeg # Replaced moviepy with ffmpeg-python

# Default model set as per user request.
# If "gemini-2.5-pro-latest" is not a valid identifier for the API,
# the script will error when initializing the model.
# The --model command-line argument can be used to specify an alternative.
DEFAULT_MODEL = "gemini-2.0-flash" # Changed default to the last working model
API_KEY_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "gemini-api-key.txt")
DEFAULT_MAX_CHUNK_DURATION_SECONDS = 1200 # 20 minutes
DEFAULT_OVERLAP_DURATION_SECONDS = 60   # 1 minute

# Default timeout for API calls per chunk.
DEFAULT_TIMEOUT_PER_CHUNK_SECONDS = 1200 # 20 minutes (remains suitable for 20-min chunks)

def summarize_single_video_file(video_path, model_name, timeout=DEFAULT_TIMEOUT_PER_CHUNK_SECONDS):
    """Uploads a single video file and returns its summary and the remote file resource."""
    video_file_resource = None
    try:
        print(f"Uploading video file: {video_path}...")
        # Initial upload call
        video_file_resource = genai.upload_file(path=video_path)
        print(f"File upload initiated. URI: {video_file_resource.uri}, Name: {video_file_resource.name}")

        # Wait for the file to become ACTIVE
        print(f"Waiting for file {video_file_resource.name} to become ACTIVE...")
        while video_file_resource.state.name != "ACTIVE":
            time.sleep(5) # Check every 5 seconds
            video_file_resource = genai.get_file(name=video_file_resource.name) # Refresh file state
            print(f"Current state of {video_file_resource.name}: {video_file_resource.state.name}")
            if video_file_resource.state.name == "FAILED":
                print(f"Error: File processing failed for {video_file_resource.name}.")
                # Attempt to delete the failed resource before returning
                try:
                    genai.delete_file(video_file_resource.name)
                    print(f"Deleted failed file resource {video_file_resource.name} from Gemini storage.")
                except Exception as del_e:
                    print(f"Warning: Could not delete failed file resource {video_file_resource.name}: {del_e}")
                return None, None # Return None for both summary and resource if processing failed

        print(f"File {video_file_resource.name} is now ACTIVE.")
        print(f"Generating summary using model: {model_name}...")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            ["Please summarize this video.", video_file_resource],
            request_options={"timeout": timeout}
        )
        return response.text, video_file_resource
    except Exception as e:
        print(f"An error occurred during processing {video_path}: {e}")
        # Return None for summary but still return resource if it exists, to attempt deletion
        return None, video_file_resource
    # No finally block here, deletion of individual chunks handled by caller or main finally block

def main():
    parser = argparse.ArgumentParser(description="Summarize a video using Google Gemini API. Splits long videos into chunks.")
    parser.add_argument("video_file", help="Path to the video file to summarize.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Gemini model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--max_chunk_duration", type=int, default=DEFAULT_MAX_CHUNK_DURATION_SECONDS, help=f"Maximum duration of video chunks in seconds (default: {DEFAULT_MAX_CHUNK_DURATION_SECONDS} - 20 minutes). Set to 0 to disable splitting. Adjust based on model token limits.")
    parser.add_argument("--overlap_duration", type=int, default=DEFAULT_OVERLAP_DURATION_SECONDS, help=f"Overlap duration between chunks in seconds (default: {DEFAULT_OVERLAP_DURATION_SECONDS} - 1 minute).")
    parser.add_argument("--timeout_per_chunk", type=int, default=DEFAULT_TIMEOUT_PER_CHUNK_SECONDS, help=f"Timeout in seconds for API call per chunk (default: {DEFAULT_TIMEOUT_PER_CHUNK_SECONDS} - 20 minutes).")
    
    args = parser.parse_args()

    if args.overlap_duration >= args.max_chunk_duration and args.max_chunk_duration > 0:
        print("Error: Overlap duration must be less than chunk duration. Disabling overlap.")
        args.overlap_duration = 0

    # 1. Read API Key
    try:
        with open(API_KEY_FILE_PATH, 'r') as f:
            api_key = f.read().strip()
        if not api_key:
            print(f"Error: API key file at {API_KEY_FILE_PATH} is empty.")
            return
    except FileNotFoundError:
        print(f"Error: API key file not found at {API_KEY_FILE_PATH}")
        return
    except Exception as e:
        print(f"Error reading API key file: {e}")
        return

    genai.configure(api_key=api_key)

    # 2. Check video file existence
    if not os.path.exists(args.video_file):
        print(f"Error: Video file not found at {args.video_file}")
        return

    all_summaries = []
    processed_file_resources = [] # Keep track of uploaded file resources for deletion

    try:
        # Get video duration using ffmpeg
        try:
            print(f"Probing video file: {args.video_file} for duration...")
            probe = ffmpeg.probe(args.video_file)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            if not video_stream or 'duration' not in video_stream:
                print("Error: Could not find video stream or duration in video metadata.")
                return
            video_duration = float(video_stream['duration'])
            print(f"Original video duration: {video_duration:.2f} seconds.")
        except ffmpeg.Error as e:
            print(f"Error probing video file with ffmpeg: {e.stderr.decode('utf-8') if e.stderr else str(e)}")
            return
        except Exception as e:
            print(f"An unexpected error occurred while probing video: {e}")
            return

        if args.max_chunk_duration > 0 and video_duration > args.max_chunk_duration:
            print(f"Video is longer than max_chunk_duration ({args.max_chunk_duration}s). Splitting into chunks with {args.overlap_duration}s overlap.")
            
            chunk_index = 0
            # Effective step takes overlap into account for advancing start time
            effective_step = args.max_chunk_duration - args.overlap_duration
            if effective_step <= 0: # Should be caught by the check above, but as a safeguard
                effective_step = args.max_chunk_duration 

            # Estimate number of chunks for user feedback
            if video_duration <= args.max_chunk_duration:
                 estimated_num_chunks = 1
            else:
                 estimated_num_chunks = 1 + math.ceil((video_duration - args.max_chunk_duration) / effective_step)
            
            current_start_time = 0.0
            while current_start_time < video_duration:
                chunk_index += 1
                # Actual start time for ffmpeg is current_start_time
                # Chunk end time is start_time + chunk_duration, capped by video_duration
                actual_chunk_end_time = min(current_start_time + args.max_chunk_duration, video_duration)
                # Duration for ffmpeg -t option
                current_ffmpeg_duration = actual_chunk_end_time - current_start_time

                if current_ffmpeg_duration <= 0:
                    break # No more video content to process

                base, orig_ext = os.path.splitext(args.video_file)
                chunk_filename = f"temp_chunk_{chunk_index}{orig_ext if orig_ext else '.mp4'}"
                
                print(f"Processing chunk {chunk_index}/{estimated_num_chunks} (video time {current_start_time:.2f}s - {actual_chunk_end_time:.2f}s, duration: {current_ffmpeg_duration:.2f}s)...")
                
                try:
                    (
                        ffmpeg
                        .input(args.video_file, ss=current_start_time, t=current_ffmpeg_duration)
                        .output(chunk_filename, vcodec='copy', acodec='copy', format='mp4') 
                        .overwrite_output()
                        .run(capture_stdout=True, capture_stderr=True)
                    )
                    print(f"Successfully created chunk: {chunk_filename}")
                except ffmpeg.Error as e:
                    print(f"Error splitting video chunk {chunk_filename} using ffmpeg: {e.stderr.decode('utf-8') if e.stderr else str(e)}")
                    current_start_time += effective_step # Advance to next potential start time
                    continue 

                summary_text, uploaded_resource = summarize_single_video_file(chunk_filename, args.model, args.timeout_per_chunk)
                if summary_text:
                    all_summaries.append(f"Summary for chunk {chunk_index} (video time {current_start_time:.2f}s - {actual_chunk_end_time:.2f}s):\n{summary_text}")
                if uploaded_resource:
                    processed_file_resources.append(uploaded_resource)
                
                os.remove(chunk_filename) 
                print(f"Deleted local chunk: {chunk_filename}")

                # Advance start time for the next chunk
                current_start_time += effective_step
                
                # Respect RPM limit if there are more chunks to process
                if current_start_time < video_duration:
                    delay_seconds = 4 if "flash" in args.model.lower() else 12
                    rpm_target = 15 if "flash" in args.model.lower() else 5
                    print(f"Waiting for {delay_seconds} seconds to respect API rate limits (target: {rpm_target} RPM for {args.model})...")
                    time.sleep(delay_seconds)

        else: # Process the whole video
            print("Video is within max_chunk_duration or splitting is disabled. Processing as a single file.")
            summary_text, uploaded_resource = summarize_single_video_file(args.video_file, args.model, args.timeout_per_chunk)
            if summary_text:
                all_summaries.append(summary_text)
            if uploaded_resource:
                processed_file_resources.append(uploaded_resource)

        if all_summaries:
            print("\n--- Combined Video Summary ---")
            full_summary_text = "\n\n".join(all_summaries)
            print(full_summary_text)

            # Write summary to file
            video_basename = os.path.splitext(os.path.basename(args.video_file))[0]
            summary_filename = f"{video_basename}_summary.txt"
            # Path in the same directory as the script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_file_path = os.path.join(script_dir, summary_filename)

            try:
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write(full_summary_text)
                print(f"\nSummary successfully written to: {output_file_path}")
            except IOError as e_io:
                print(f"\nError writing summary to file {output_file_path}: {e_io}")

        else:
            print("\nNo summaries were generated.")

    except Exception as e:
        print(f"An overall error occurred: {e}")
    finally:
        # No explicit video object to close like with moviepy when using ffmpeg-python this way
        # Attempt to Delete all Uploaded Files from Gemini
        if processed_file_resources:
            print("\nCleaning up uploaded files from Gemini storage...")
            for resource in processed_file_resources:
                try:
                    genai.delete_file(resource.name)
                    print(f"Deleted uploaded file {resource.name} from Gemini storage.")
                except Exception as e:
                    print(f"Warning: Could not delete uploaded file {resource.name}: {e}")
        print("Processing complete.")

if __name__ == "__main__":
    main()
