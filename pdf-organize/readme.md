# LLM PDF Organizer

This application monitors a directory for new PDF files, uses the Google Gemini LLM to determine an appropriate organizational structure based on the PDF's content and existing folders, and then renames and moves the file accordingly. It is designed to run exclusively within a Docker container.

## Prerequisites

*   Docker installed and running.
*   A Google Gemini API Key.

## Setup

1.  **Clone the repository (or create the files):**
    Ensure you have `app.py`, `requirements.txt`, and `dockerfile` in a directory (e.g., `pdf-organize`).

2.  **Build the Docker Image:**
    Navigate to the directory containing the `dockerfile` and run:
    ```bash
    docker build -t pdf-organizer .
    ```

## Running the Container

You need to provide the necessary environment variables and map local directories for input and output PDFs to the container's `/input` and `/output` volumes.

**Example `docker run` command:**

```bash
docker run -d --name pdf-organizer-instance \
  -v /path/to/your/local/input/folder:/input \
  -v /path/to/your/local/output/folder:/output \
  -e GEMINI_API_KEY="YOUR_GEMINI_API_KEY" \
  -e PAGES_TO_ANALYZE="3" \
  -e KEEP_ORIGINAL_FILE="false" \
  pdf-organizer
```

**Explanation:**

*   `-d`: Run the container in detached mode (in the background).
*   `--name pdf-organizer-instance`: Assign a name to the running container.
*   `-v /path/to/your/local/input/folder:/input`: Mount your local folder where new PDFs will appear into the container's `/input` directory. **Replace `/path/to/your/local/input/folder` with the actual path on your host machine.**
*   `-v /path/to/your/local/output/folder:/output`: Mount your local folder where organized PDFs should be saved into the container's `/output` directory. **Replace `/path/to/your/local/output/folder` with the actual path on your host machine.**
*   `-e GEMINI_API_KEY="YOUR_GEMINI_API_KEY"`: **Replace `YOUR_GEMINI_API_KEY` with your actual Gemini API key.**
*   `-e PAGES_TO_ANALYZE="3"`: (Optional) Set the number of pages to analyze. Defaults to 3 if not provided.
*   `-e KEEP_ORIGINAL_FILE="false"`: (Optional) Set to `true` if you want to keep the original file in the input directory after processing. Defaults to `false` (original is removed after successful move).
*   `pdf-organizer`: The name of the Docker image built earlier.

## How it Works

1.  The application starts and monitors the `/input` directory inside the container.
2.  When a new `.pdf` file is detected, it waits briefly to ensure the file is fully written.
3.  It extracts metadata and text from the first `PAGES_TO_ANALYZE` pages using PyMuPDF.
4.  It scans the `/output` directory to understand the existing folder structure.
5.  It sends the extracted text, metadata, and directory structure to the Gemini API (gemini-2.0-flash model).
6.  It specifically asks the LLM to return a JSON object containing a suggested relative path in the format `{"path": "category/subcategory/title_author.pdf"}`.
7.  It parses the JSON response.
8.  It creates the necessary `category/subcategory` directories within `/output` if they don't exist.
9.  It moves the PDF file from `/input` to the suggested path within `/output`.
10. If `KEEP_ORIGINAL_FILE` is `false`, the original file in `/input` is effectively removed by the move operation.

## Stopping the Container

```bash
docker stop pdf-organizer-instance
docker rm pdf-organizer-instance
```

## Viewing Logs

```bash
docker logs pdf-organizer-instance -f
