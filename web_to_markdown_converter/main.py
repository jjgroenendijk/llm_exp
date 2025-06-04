from crawl4ai import AsyncWebCrawler
import argparse
import asyncio
import sys
from playwright._impl import _errors as PlaywrightErrors # Import Playwright error

async def async_main():
    parser = argparse.ArgumentParser(description='Convert a website to Markdown.')
    parser.add_argument('url', type=str, help='The URL of the website to convert.')

    if len(sys.argv) > 1:
        args = parser.parse_args(sys.argv[1:])
    else:
        parser.print_help()
        sys.exit(1)

    try:
        crawler = AsyncWebCrawler()
        result_container = await crawler.arun(url=args.url)

        if result_container and hasattr(result_container, '_results') and result_container._results:
            actual_result = result_container._results[0]

            markdown_content = None
            source_format = None

            if hasattr(actual_result, 'markdown_v2') and actual_result.markdown_v2:
                markdown_content = actual_result.markdown_v2
                source_format = "markdown_v2"
            elif hasattr(actual_result, 'markdown') and actual_result.markdown:
                markdown_content = actual_result.markdown
                source_format = "markdown"
            elif hasattr(actual_result, 'fit_markdown') and actual_result.fit_markdown:
                markdown_content = actual_result.fit_markdown
                source_format = "fit_markdown"

            if markdown_content:
                print(f"--- Source: {source_format} ---")
                print(str(markdown_content))
            elif hasattr(actual_result, 'html') and actual_result.html:
                print("--- Source: HTML (fallback) ---")
                print("No direct Markdown content found. Printing first 1000 characters of HTML instead.")
                content_to_print = str(actual_result.html)
                print(content_to_print[:1000])
            else:
                print("Could not extract any content (Markdown or HTML).")
                print("\nAttributes of CrawlResult object:")
                print(dir(actual_result))
        else:
            print("No result returned or result format is unexpected.")
            if result_container:
                print(f"Result container type: {type(result_container)}")
                if hasattr(result_container, '__dict__'):
                    print(f"Result container attributes: {vars(result_container)}")

    except PlaywrightErrors.Error as pe: # Catch specific Playwright error
        error_message = str(pe)
        if "Executable doesn't exist" in error_message or "Looks like Playwright was just installed or updated." in error_message:
            print("\n---------------------------------------------------------------------", file=sys.stderr)
            print("ERROR: Playwright browser executables not found!", file=sys.stderr)
            print("It seems the necessary browser binaries for Playwright are missing.", file=sys.stderr)
            print("Please run the following command in your terminal from the project", file=sys.stderr)
            print("directory to install them:", file=sys.stderr)
            print("\n    uv run playwright install\n", file=sys.stderr)
            print("After the installation is complete, please try running this script again.", file=sys.stderr)
            print("---------------------------------------------------------------------\n", file=sys.stderr)
            sys.exit(1)
        else:
            raise # Re-raise if it's a different Playwright error
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    asyncio.run(async_main())

if __name__ == '__main__':
    main()
