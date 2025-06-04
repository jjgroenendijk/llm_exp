# Web to Markdown Converter

This script converts a given website URL into Markdown format using `crawl4ai`.

## Prerequisites

- Python 3.10+
- [uv](https://astral.sh/uv) (Python package and project manager)

If you don't have `uv`, you can install it by following the instructions on the official `uv` website (e.g., `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`).

## Setup

1. Clone this repository (or otherwise obtain the project files).
2. Navigate to the project directory:
   ```bash
   cd web_to_markdown_converter
   ```
3. Install dependencies and set up the environment using `uv`:
   ```bash
   uv sync
   ```
   This command will create a virtual environment (if one doesn't exist) and install the dependencies specified in `pyproject.toml`.

## Usage

To convert a website to Markdown, run the following command from within the `web_to_markdown_converter` project directory:

```bash
uv run convert <URL>
```

Replace `<URL>` with the actual URL of the website you want to convert.

Example:
```bash
uv run convert https://docs.checkmk.com/latest/en/
```

The script will print the Markdown content to the console.

## Dependencies

- `crawl4ai`: For fetching and extracting website content, including direct Markdown conversion.

(Note: Initially, `markdownify` was considered as a fallback for HTML-to-Markdown conversion, but `crawl4ai`'s built-in capabilities appear sufficient for many cases.)
