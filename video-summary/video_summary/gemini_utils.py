import google.genai as genai
from google.genai import types
import time
import os
from typing import Optional

# This is the instruction we give to the Gemini AI.
# It tells the AI to describe the video's content in a detailed way,
# focusing on important ideas, explanations, and examples.
# It also tells the AI to speak directly about the topic,
# rather than saying things like "the video shows..."
PROMPT_TEXT = (
    "You are an expert academic writer. Your task is to synthesize the core educational material from this "
    "video segment (chunk) into a single, coherent, and self-contained explanatory text. This text should "
    "directly teach the concepts, procedures, and information presented, as if it were a detailed excerpt "
    "from a well-written textbook or a comprehensive explanatory script of the lesson's content, **using clear, "
    "simple, and very easy to understand English.**\n\n"
    "**CRITICAL OUTPUT REQUIREMENTS - ADHERE STRICTLY:**\n\n"
    "1.  **ABSOLUTELY NO TITLES, HEADINGS, OR SECTION BREAKERS:**\n"
    "    * Your entire response MUST be a single, continuous block of Markdown text. Do NOT use any lines "
    "starting with '#', '##', '###', etc. Do NOT generate any form of title, sub-title, or section "
    "heading for the summary itself.\n"
    "    * Do NOT use horizontal rules (e.g., '---', '***') or any other visual section separators.\n\n"
    "2.  **IMMEDIATE AND DIRECT START - NO PREFATORY CONTENT:**\n"
    "    * Your response MUST begin *immediately* with the first piece of substantive educational content "
    "(e.g., a definition, an explanation of a concept, the start of a procedure). Do not leave any blank lines "
    "before the content begins.\n"
    "    * NO introductory sentences or framing (e.g., 'This chunk discusses...', 'The topic explained here is...').\n"
    "    * NO conversational filler, greetings, or concluding remarks.\n\n"
    "3.  **EXPLAIN THE SUBJECT MATTER CLEARLY, SIMPLY, AND COHERENTLY - NO META-COMMENTARY:**\n"
    "    * **Language Style:** Write EXCLUSIVELY in **English**, using vocabulary and sentence structures that are **very easy to understand** for a broad audience. Explain any necessary technical terms simply if they must be used. The primary goal is clarity and accessibility.\n"
    "    * Focus EXCLUSIVELY on explaining *what* information, concepts, theories, and procedures are being taught. Your goal is to make the subject matter understandable on its own.\n"
    "    * Provide necessary context *within the explanation of the subject matter itself* to ensure the "
    "information flows logically and connections between different pieces of information are clear. The text "
    "should be an integrated explanation, not a list of disconnected points or raw calculations.\n"
    "    * Crucially, DO NOT refer to 'the video,' 'the speaker,' 'the presenter,' 'this segment,' 'the lecture,' "
    "or any aspect of the presentation medium or its structure. Write only about the *information and "
    "concepts being taught*, as if you are the authoritative source of this information.\n"
    "    * For example, instead of 'The presenter then moves on to binary subtraction,' directly explain the "
    "method in simple terms: 'Subtracting binary numbers can be done using a method called two's complement "
    "addition. To subtract one number from another, you first change the number you are subtracting into its "
    "two's complement form...'\n\n"
    "4.  **CONTENT DEPTH AND INTEGRATION:**\n"
    "    * Extract and thoroughly explain all core concepts, definitions, mathematical derivations and their "
    "steps, examples with their workings, procedures, and key takeaways using simple language.\n"
    "    * Synthesize these elements into a flowing, explanatory narrative. For instance, if there are "
    "calculations, explain their purpose and walk through the steps in an easy-to-follow manner, rather "
    "than just listing them.\n\n"
    "5.  **MARKDOWN AND LATEX FORMATTING:**\n"
    "    * The entire response MUST be valid Markdown.\n"
    "    * All mathematical notation, formulas, symbols, variables, and equations MUST be rendered as LaTeX. "
    "Use '$inline\_math$' for mathematical expressions within text (e.g., the value is `$29_{10}$) and "
    "'$$block\_math$$' for standalone mathematical expressions or equations on their own lines "
    "(e.g., for a calculation like $$\\frac{29}{2} = 14 \\text{ remainder } 1$$). Crucially, do NOT enclose these LaTeX expressions in backticks (`).\n\n"
    "Your output must be a seamless piece of educational text in **very easy to understand English**, directly "
    "explaining the content of this video chunk comprehensively, clearly, and cohesively, without any "
    "structural elements like titles or separators generated by you, and without any reference to the video "
    "itself."
)

REFINE_PROMPT_TEXT = (
    "You are an expert technical editor. The following text is a machine-generated summary of a video, "
    "compiled from summaries of individual video chunks. Your task is to:\n"
    "1.  **Generate a Title and Subtitle**: Based on the overall content, create a concise and informative "
    "main title (H1, e.g., '# Main Title') and a subtitle (H2, e.g., '## Subtitle') for the document. "
    "Place these at the very beginning of your output.\n"
    "2.  **Review and Correct Formatting**: Ensure consistent use of Markdown for the rest of the summary body. "
    "Correct any awkward or inconsistent formatting. Pay attention to lists, code blocks, and mathematical "
    "notation (LaTeX).\n"
    "3.  **Improve Readability**: Make minor adjustments to the summary body to improve flow and readability "
    "without altering the core meaning or substantive content.\n"
    "4.  **Maintain LaTeX**: All mathematical notation, formulas, variables, and equations in the summary body "
    "must remain as LaTeX within the Markdown. Ensure it is correctly rendered ($inline$ or $$block$$). Crucially, do NOT enclose these LaTeX expressions in backticks (`).\n"
    "5.  **No Content Changes to Summary Body**: Do NOT add new information, remove existing information, or "
    "change the meaning of the summary body text. The focus for the body is solely on presentation and "
    "formatting improvements.\n"
    "6.  **Direct Output**: Provide only the refined Markdown text, starting with your generated title and "
    "subtitle, followed by the improved summary body. Do not include any other introductory or "
    "concluding remarks.\n\n"
    "Original Summary Body Text to Refine:\n"
    "--- BEGIN ORIGINAL TEXT ---\n"
    "{original_summary_text}\n"
    "--- END ORIGINAL TEXT ---"
)

# This function checks if a video file we uploaded to Google Gemini is ready to be used.
# Sometimes, after uploading, Gemini needs some time to process the file.
# This function will keep checking the file's status every 5 seconds.
def _wait_for_file_to_be_active(gemini_client: "genai.Client", video_file_resource: types.File) -> Optional[types.File]:
    """
    Keeps checking the status of an uploaded file on Google Gemini using the client.
    It waits until the file is either "ACTIVE" (ready) or "FAILED" (something went wrong).
    If the file becomes ACTIVE, it returns the file information.
    If it FAILED or an error happens, it returns None (nothing).
    """
    print(f"Waiting for file {video_file_resource.name} to become ACTIVE...")
    try:
        # Keep looping as long as the file is not yet ACTIVE.
        while video_file_resource.state.name != "ACTIVE":
            time.sleep(5)  # Wait for 5 seconds before checking again.
            
            # We need to ask Gemini for the latest status of the file.
            refreshed_file_resource = gemini_client.files.get(name=video_file_resource.name)
            print(f"Current state of {refreshed_file_resource.name}: {refreshed_file_resource.state.name}")
            
            # If Gemini says the file processing FAILED:
            if refreshed_file_resource.state.name == "FAILED":
                print(f"Error: File processing failed for {refreshed_file_resource.name}.")
                try:
                    # Try to delete the failed file from Gemini's storage to clean up.
                    gemini_client.files.delete(name=refreshed_file_resource.name)
                    print(f"Deleted failed file resource {refreshed_file_resource.name} from Gemini storage.")
                except Exception as del_e:
                    # If deleting fails, just print a warning.
                    print(f"Warning: Could not delete failed file resource {refreshed_file_resource.name}: {del_e}")
                return None # Indicate that waiting failed.
            
            # Update our 'video_file_resource' with the latest information we got.
            video_file_resource = refreshed_file_resource 
            
            # If it's ACTIVE now, we can stop waiting.
            if video_file_resource.state.name == "ACTIVE": 
                 break
        
        # After the loop, double-check if it's really ACTIVE.
        if video_file_resource.state.name == "ACTIVE":
            print(f"File {video_file_resource.name} is now ACTIVE.")
            return video_file_resource # Return the file info because it's ready.
        else:
            # This should not happen if FAILED is handled above, but it's a safety check.
            print(f"File {video_file_resource.name} ended in unexpected state: {video_file_resource.state.name}")
            return None # Indicate an unexpected issue.

    except Exception as e:
        # If any other error occurs while waiting (e.g., network problem):
        print(f"An error occurred while waiting for file {video_file_resource.name} to become active: {e}")
        try:
            # Try to delete the file from Gemini as a cleanup measure,
            # because we don't know its true state.
            gemini_client.files.delete(name=video_file_resource.name)
            print(f"Deleted file resource {video_file_resource.name} due to polling error.")
        except Exception as del_e:
            print(f"Warning: Could not delete file resource {video_file_resource.name} after polling error: {del_e}")
        return None # Indicate that waiting failed.

# This function uploads a single video chunk (a small piece of a larger video)
# to Google Gemini and then waits for it to be ready (ACTIVE).
def upload_video_chunk_and_wait(gemini_client: "genai.Client", local_chunk_path: str) -> Optional[types.File]:
    """
    Uploads a video file (chunk) from your computer to Google Gemini using the client.
    'local_chunk_path' is where the file is on your computer (e.g., "temp_videos/chunk1.mp4").
    It then uses the '_wait_for_file_to_be_active' function to ensure the file is processed by Gemini.
    Returns the file information if successful, or None if it fails.
    """
    video_file_resource = None # This will hold the information about the uploaded file.
    try:
        print(f"Uploading video file: {local_chunk_path}...")
        # This is the command to upload the file to Gemini using the client.
        video_file_resource = gemini_client.files.upload(file=local_chunk_path)
        
        print(f"File upload initiated for {local_chunk_path}. URI: {video_file_resource.uri}, Name: {video_file_resource.name}")

        # Now, wait for the uploaded file to become ACTIVE.
        return _wait_for_file_to_be_active(gemini_client, video_file_resource)

    except Exception as e:
        # If an error happens during the upload itself:
        print(f"An error occurred during upload for {local_chunk_path}: {e}")
        # If we have some information about the file (even if the upload was partial or failed),
        # try to delete it from Gemini to clean up.
        if video_file_resource and video_file_resource.name: 
            try:
                gemini_client.files.delete(name=video_file_resource.name)
                print(f"Cleaned up partially uploaded/failed resource {video_file_resource.name}.")
            except Exception:
                pass # If deletion fails, just ignore it (best effort).
        return None # Indicate that the upload failed.

# This function asks the Gemini AI to create a summary for a video file
# that has already been uploaded and is "ACTIVE" (ready).
def generate_summary_for_resource(
    video_file_resource: types.File, 
    gemini_client: "genai.Client",
    model_name_str: str,
    prompt: str, 
    timeout: int # timeout is not directly used by generate_content for non-streaming text
) -> Optional[str]:
    """
    Asks the Gemini AI model to generate a text summary for the given video file.
    Retries once after a 10-second delay if the first attempt fails.
    """
    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Generating summary for {video_file_resource.name} using model: {model_name_str} (Attempt {attempt}/{max_attempts})...")
            response = gemini_client.models.generate_content(
                model=model_name_str,
                contents=[prompt, video_file_resource]
            )
            
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].text
            elif hasattr(response, 'text'):
                 return response.text
            else:
                print(f"Warning: Unexpected response structure from generate_content for {video_file_resource.name} on attempt {attempt}. Full response: {response}")
                # If structure is unexpected but not an exception, treat as failure for this attempt
                if attempt < max_attempts:
                    print(f"Waiting 10 seconds before retrying summary generation for {video_file_resource.name}...")
                    time.sleep(10)
                    continue # Go to next attempt
                else:
                    return None # Failed on last attempt

        except Exception as e:
            print(f"An error occurred during summary generation for {video_file_resource.name} on attempt {attempt}: {e}")
            if attempt < max_attempts:
                print(f"Waiting 10 seconds before retrying summary generation for {video_file_resource.name}...")
                time.sleep(10)
            else:
                print(f"Failed to generate summary for {video_file_resource.name} after {max_attempts} attempts.")
                return None # Failed on last attempt
    return None # Should be unreachable if loop logic is correct, but as a fallback.


def refine_summary_text(
    original_summary_text: str,
    gemini_client: "genai.Client",
    model_name_str: str,
    timeout: int # Added timeout, though not directly used by current SDK's generate_content for text
) -> Optional[str]:
    """
    Asks the Gemini AI model to refine a given text summary.
    'original_summary_text' is the summary text to be refined.
    'gemini_client' is the initialized Gemini Client instance.
    'model_name_str' is the string name of the model to use.
    'timeout' is how long (in seconds) we're willing to wait (conceptually, as SDK might not use it for this call).
    Returns the refined summary text if successful, or None if it fails.
    """
    try:
        prompt_with_text = REFINE_PROMPT_TEXT.format(original_summary_text=original_summary_text)
        print(f"Refining summary text using model: {model_name_str}...")
        
        response = gemini_client.models.generate_content(
            model=model_name_str,
            contents=[prompt_with_text] 
            # request_options={"timeout": timeout} # Not supported by this SDK version's method
        )

        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        elif hasattr(response, 'text'):
             return response.text
        else:
            print(f"Warning: Unexpected response structure from generate_content for text refinement. Full response: {response}")
            return None

    except Exception as e:
        print(f"An error occurred during summary text refinement: {e}")
        return None
