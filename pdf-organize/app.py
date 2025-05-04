import os
import time
import json
import re
import fitz  # PyMuPDF
import google.generativeai as genai
from google.generativeai import types # Added for inline data
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
import logging
import shutil

# --- Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
INPUT_DIR = os.getenv('INPUT_DIR', '/input')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/output')
PAGES_TO_ANALYZE = int(os.getenv('PAGES_TO_ANALYZE', 3))
KEEP_ORIGINAL_FILE = os.getenv('KEEP_ORIGINAL_FILE', 'false').lower() == 'true'

if not GEMINI_API_KEY:
    logging.error("GEMINI_API_KEY environment variable not set.")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY) # Configure the Gemini client
generation_config = {
    "temperature": 0.7, # Controls randomness (higher = more creative)
    "top_p": 1,         # Nucleus sampling parameter
    "top_k": 1,         # Top-k sampling parameter
    "max_output_tokens": 2048, # Maximum length of the response
    "response_mime_type": "application/json", # Expect JSON output from the model
}
model = genai.GenerativeModel(model_name="gemini-2.0-flash", # Specify the Gemini model
                              generation_config=generation_config)

# --- Helper Functions ---

def sanitize_filename(filename):
    """Removes invalid characters for filenames and replaces spaces with underscores."""
    # Remove invalid characters
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(" ", "_")
    # Limit length (optional)
    return sanitized[:200] # Limit length to avoid issues

def get_dir_structure(rootdir):
    """Creates a string representation of the directory structure."""
    structure = []
    for dirpath, dirnames, filenames in os.walk(rootdir):
        # Calculate relative path from rootdir
        relative_path = os.path.relpath(dirpath, rootdir)
        if relative_path == ".":
            relative_path = "" # Root level

        indent = relative_path.count(os.sep) * '  '
        if relative_path:
             structure.append(f"{indent}[{os.path.basename(dirpath)}/]")
        # Optional: List files too
        # for f in filenames:
        #     structure.append(f"{indent}  - {f}")
    return "\n".join(structure) if structure else "Output directory is empty."


def organize_pdf(pdf_path):
    """Extracts info, calls LLM, and moves the PDF."""
    logging.info(f"Processing new file: {pdf_path}")
    pdf_bytes = None # Initialize pdf_bytes
    try:
        original_doc = fitz.open(pdf_path)
        metadata = original_doc.metadata
        pages_to_read = min(PAGES_TO_ANALYZE, len(original_doc))

        # Create a new in-memory PDF with the first pages
        temp_doc = fitz.open() # Create a new empty PDF
        temp_doc.insert_pdf(original_doc, from_page=0, to_page=pages_to_read - 1)
        pdf_bytes = temp_doc.tobytes() # Get bytes of the new PDF
        temp_doc.close()
        original_doc.close() # Close the original PDF document

        title = metadata.get('title', '') # Extract title from metadata
        author = metadata.get('author', '') # Extract author from metadata

        dir_structure = get_dir_structure(OUTPUT_DIR) # Get current directory structure

        prompt = f"""
Analyze the provided PDF data (representing the first {pages_to_read} pages of the original document) and its metadata to determine the appropriate category and subcategory for organization.

Existing Directory Structure in Output Folder:
{dir_structure}

PDF Metadata:
Title: {title if title else "Not specified"}
Author: {author if author else "Not specified"}
(Other metadata: { {k: v for k, v in metadata.items() if k not in ['title', 'author']} })

Task:
Suggest a new file path relative to the output directory based on the content of the provided PDF data and the existing structure. The format MUST be exactly JSON: {{ "path": "category/subcategory/filename.pdf" }}

Instructions for filename.pdf:
1.  Determine the best 'category' and 'subcategory' based on the PDF content and existing structure ({dir_structure}).
2.  Determine the filename components:
    *   **Title Component:** If the metadata Title ('{title if title else "Not specified"}') is available and meaningful, use it. Otherwise, **generate a concise, descriptive title** based on the PDF content (maximum 64 characters).
    *   **Author Component:** If the metadata Author ('{author if author else "Not specified"}') is available and meaningful, use it. Otherwise, **generate a brief description of the likely author or source** based on the content (maximum 32 characters).
3.  Construct the filename as: `TitleComponent_AuthorComponent.pdf`.
4.  **Sanitize the entire suggested path**: Replace spaces with underscores ('_') and remove any characters invalid for file paths (like / \\ * ? : " < > |). Ensure the final path string is valid.
5.  Combine everything into the JSON format: {{ "path": "sanitized_category/sanitized_subcategory/sanitized_filename.pdf" }}

Example Output: {{ "path": "Computer_Science/Machine_Learning/Intro_To_Neural_Networks_University_Report.pdf" }}

Ensure the final output is valid JSON.
"""
        if not pdf_bytes:
             logging.error("Failed to extract bytes from the first pages.")
             return

        logging.info("Sending request to Gemini with inline PDF data...")
        # Send PDF bytes inline along with the prompt
        response = model.generate_content([
            types.Part.from_bytes(data=pdf_bytes, mime_type='application/pdf'),
            prompt
        ])

        # --- Response Parsing ---
        try:
            # Accessing the JSON content correctly based on google-generativeai SDK
            if response.parts:
                 # Assuming the first part contains the JSON text if mime_type is application/json
                 json_text = response.parts[0].text
                 logging.info(f"Received Gemini response text: {json_text}")
                 result = json.loads(json_text)
                 suggested_rel_path = result.get("path")
            else:
                 # Fallback or error if no parts or text found
                 logging.error(f"Gemini response format unexpected or empty: {response}")
                 suggested_rel_path = None


            if not suggested_rel_path:
                logging.error("Gemini response did not contain a valid 'path'.")
                # Decide error handling: move to error folder or just log and skip?
                return # Skip for now

            # Basic sanitization (more robust might be needed)
            # Prevent path traversal, remove leading slashes
            suggested_rel_path = suggested_rel_path.lstrip('/')
            # Further sanitization might be needed depending on LLM output variance

            full_dest_path = os.path.join(OUTPUT_DIR, suggested_rel_path)
            dest_dir = os.path.dirname(full_dest_path)

            logging.info(f"Suggested path: {suggested_rel_path}")

            # --- File Operations ---
            os.makedirs(dest_dir, exist_ok=True)

            # Check if destination file already exists and append counter if needed
            counter = 1
            original_full_dest_path = full_dest_path
            base, ext = os.path.splitext(full_dest_path)
            while os.path.exists(full_dest_path):
                logging.warning(f"Destination file already exists: {full_dest_path}. Appending counter.")
                full_dest_path = f"{base}_{counter}{ext}"
                counter += 1

            if full_dest_path != original_full_dest_path:
                 logging.info(f"Adjusted destination path to: {full_dest_path}")

            shutil.move(pdf_path, full_dest_path)
            logging.info(f"Moved '{os.path.basename(pdf_path)}' to '{full_dest_path}'")

            if not KEEP_ORIGINAL_FILE:
                # Deletion is handled by watchdog after move completes if needed,
                # but explicit delete might be desired if move fails or for clarity.
                # Let's keep it simple: move implies removal from source.
                logging.info(f"Original file '{pdf_path}' implicitly removed by move.")
                # If KEEP_ORIGINAL_FILE was true, we would copy instead of move.
                # However, the current logic uses move, so KEEP_ORIGINAL_FILE=true
                # doesn't make sense without changing shutil.move to shutil.copy.
                # Let's assume move is the primary action, and KEEP_ORIGINAL_FILE=false is default.
                # If KEEP_ORIGINAL_FILE is true, we should copy then potentially delete source based on another flag?
                # Revisit this logic if KEEP_ORIGINAL_FILE=true is a hard requirement with the current move strategy.
                # For now, move implies removal.
                pass


        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON response from Gemini: {json_text}")
        except Exception as e:
            logging.error(f"Error processing Gemini response or moving file: {e}")

    except Exception as e:
        logging.error(f"Error opening or reading PDF {pdf_path}: {e}")


# --- Watchdog Event Handler ---
class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.pdf'):
            # Wait a moment to ensure file writing is complete
            time.sleep(2)
            organize_pdf(event.src_path)

# --- Main Execution ---
if __name__ == "__main__":
    if not os.path.exists(INPUT_DIR):
        logging.error(f"Input directory does not exist: {INPUT_DIR}")
        exit(1)
    if not os.path.exists(OUTPUT_DIR):
        logging.info(f"Output directory does not exist, creating: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR)

    logging.info(f"Starting PDF Organizer...")
    logging.info(f"Monitoring directory: {INPUT_DIR}")
    logging.info(f"Output directory: {OUTPUT_DIR}")
    logging.info(f"Pages to analyze: {PAGES_TO_ANALYZE}")
    logging.info(f"Keep original file: {KEEP_ORIGINAL_FILE}")

    event_handler = PDFHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=False) # Monitor only top-level
    observer.start()
    logging.info("Observer started.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Observer stopped.")
    observer.join()
    logging.info("Exiting.")
