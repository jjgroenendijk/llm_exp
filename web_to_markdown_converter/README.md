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

### Important Note on Playwright (First-time Setup)

`crawl4ai`, a core dependency of this project, uses Playwright for browser automation. If you are running this project for the first time or after a Playwright update, you might need to install the necessary browser binaries.

After running `uv sync` and before the first execution of the script, run the following command from within the `web_to_markdown_converter` project directory:

```bash
uv run playwright install
```

This will download and install the default browsers (like Chromium) that Playwright needs to operate. If you encounter errors related to missing browser executables when running the `convert` script, this step is usually the solution. The script itself will also try to detect if browsers are missing when you run it. If it detects this issue, it will print a message guiding you to run the `uv run playwright install` command.

## Usage

To convert a website to Markdown, use the `convert` script with `uv run`. You need to specify the input URL using the `-i` or `--input` flag. Optionally, you can specify an output file path using the `-o` or `--output` flag.

**Arguments:**
-   `-i URL`, `--input URL`: (Required) The URL of the website to convert.
-   `-o FILE_PATH`, `--output FILE_PATH`: (Optional) The path where the Markdown file should be saved. If not provided, the script will generate a filename from the URL (e.g., `https_example_com.md`) and save it in the current directory.

**Examples:**

1.  Convert a website and save to an automatically generated filename in the current directory:
    ```bash
    uv run convert -i https://docs.checkmk.com/latest/en/
    ```
    (This might create a file like `https_docs_checkmk_com_latest_en.md`)

2.  Convert a website and specify the output file name and location:
    ```bash
    uv run convert -i https://docs.checkmk.com/latest/en/ -o checkmk_docs.md
    ```

**Note on `uvx` vs `uv run`:**

The `convert` command is a script defined within this project's `pyproject.toml`. The standard and recommended way to execute such project-specific scripts with `uv` is by using `uv run convert`.

`uvx` is typically used to execute commands from packages (e.g., linters or formatters like `uvx ruff check .`) which `uv` can download and run on-the-fly. It is not a direct replacement for `uv run` for scripts defined as part of the current project. Therefore, please use `uv run convert ...` for this tool.

## Dependencies

- `crawl4ai`: For fetching and extracting website content, including direct Markdown conversion.

(Note: Initially, `markdownify` was considered as a fallback for HTML-to-Markdown conversion, but `crawl4ai`'s built-in capabilities appear sufficient for many cases.)
