import argparse
import asyncio
import sys
from playwright._impl import _errors as PlaywrightErrors
from crawl4ai import AsyncWebCrawler
import os
import re

# Helper function to sanitize URL into a filename
def sanitize_url_to_filename(url: str, extension: str) -> str:
    name = url.replace("://", "_")
    # Explicitly replace known problematic characters for file paths
    name = name.replace("/", "_")
    name = name.replace("?", "_")
    name = name.replace("&", "_")
    name = name.replace("=", "_")
    # Then, replace any other remaining non-alphanumeric (excluding ., _, -)
    name = re.sub(r'[^\w.-_]', '_', name)
    name = re.sub(r'_+', '_', name) # Collapse multiple underscores
    name = name.strip('_') # Remove leading/trailing underscores
    # Ensure it doesn't start with a dot or hyphen if that's problematic
    if name.startswith('.') or name.startswith('-'):
        name = '_' + name
    # Add extension if not already present (e.g. if url somehow ended with .md)
    if not name.endswith(f'.{extension}'):
        name += f'.{extension}'
    return name

async def async_main():
    parser = argparse.ArgumentParser(description='Convert a website to Markdown.')
    parser.add_argument('-i', '--input', type=str, required=True, help='The URL of the website to convert.')
    parser.add_argument('-o', '--output', type=str, help='The file path to save the content. If not provided, a filename is derived from the URL and saved in the current directory.')

    if len(sys.argv) == 1: # No arguments provided, print help and exit.
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()

    try:
        crawler = AsyncWebCrawler()
        # print(f"Attempting to crawl URL: {args.input}") # Debugging line
        result_container = await crawler.arun(url=args.input)

        output_content = None
        source_format_header = "" # This will be like "--- Source: markdown_v2 ---"
        file_extension = "txt" # Default extension if nothing specific found
        action_message = "" # Message to print like "Markdown content saved to..."

        if result_container and hasattr(result_container, '_results') and result_container._results:
            actual_result = result_container._results[0]

            if hasattr(actual_result, 'markdown_v2') and actual_result.markdown_v2:
                output_content = actual_result.markdown_v2
                source_format_header = "--- Source: markdown_v2 ---\n"
                file_extension = "md"
            elif hasattr(actual_result, 'markdown') and actual_result.markdown:
                output_content = actual_result.markdown
                source_format_header = "--- Source: markdown ---\n"
                file_extension = "md"
            elif hasattr(actual_result, 'fit_markdown') and actual_result.fit_markdown:
                output_content = actual_result.fit_markdown
                source_format_header = "--- Source: fit_markdown ---\n"
                file_extension = "md"
            elif hasattr(actual_result, 'html') and actual_result.html:
                output_content = actual_result.html
                source_format_header = "--- Source: HTML (fallback) ---\n"
                file_extension = "html"
            else:
                print("Could not extract any content (Markdown or HTML).")
                if not args.output and hasattr(actual_result, '__dict__'): # Print details if not writing to file
                    print("\nAttributes of CrawlResult object:")
                    for attr_name in dir(actual_result):
                        if not attr_name.startswith('_'):
                             print(f"  {attr_name}: {getattr(actual_result, attr_name)[:200] if isinstance(getattr(actual_result, attr_name), str) else type(getattr(actual_result, attr_name))}")
                return # Exit if no content found

            if output_content:
                final_output_path = args.output # Use the user-specified path directly if provided

                if not final_output_path:
                    # Derive filename if -o is not provided
                    derived_filename = sanitize_url_to_filename(args.input, file_extension)
                    final_output_path = os.path.join(os.getcwd(), derived_filename)

                # Ensure directory exists if output path includes directories
                # For now, assume if -o is given, path is valid or OS handles error.
                # If derived, it's in CWD, which exists.

                with open(final_output_path, 'w', encoding='utf-8') as f:
                    f.write(source_format_header)
                    f.write(str(output_content))

                if file_extension == "html":
                    action_message = f"No direct Markdown content found. HTML fallback content saved to {final_output_path}"
                else:
                    action_message = f"Markdown content saved to {final_output_path}"
                print(action_message)

        else: # No result_container or it's empty
            print("No result returned from crawler or result format is unexpected.")
            if not args.output and result_container: # Print details if not writing to file
                print(f"Result container type: {type(result_container)}")
                if hasattr(result_container, '__dict__'):
                     print(f"Result container attributes: {vars(result_container)}")

    except PlaywrightErrors.Error as pe:
        error_message = str(pe)
        # Keep the detailed Playwright error message for missing browsers
        if "Executable doesn't exist" in error_message or "Looks like Playwright was just installed or updated." in error_message:
            print("\n---------------------------------------------------------------------", file=sys.stderr)
            print("ERROR: Playwright browser executables not found!", file=sys.stderr)
            print("It seems the necessary browser binaries for Playwright are missing.", file=sys.stderr)
            print("Please run the following command in your terminal from the project", file=sys.stderr)
            print("directory to install them:", file=sys.stderr)
            print("\n    uv run playwright install\n", file=sys.stderr) # Escaped newline
            print("After the installation is complete, please try running this script again.", file=sys.stderr)
            print("---------------------------------------------------------------------\n", file=sys.stderr) # Escaped newline
            sys.exit(1) # Ensure exit after this specific error
        else:
            # Generic Playwright error
            print(f"A Playwright error occurred: {pe}", file=sys.stderr)
            # import traceback # Already imported sys
            # traceback.print_exc() # This can be noisy, pe often has enough info
            sys.exit(1) # Exit for other playwright errors too

    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

# The main guard and function call should remain
def main():
    asyncio.run(async_main())

if __name__ == '__main__':
    main()
