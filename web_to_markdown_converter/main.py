from crawl4ai import AsyncWebCrawler
import argparse
import asyncio
import sys

async def async_main(): # Renamed from main to async_main
    parser = argparse.ArgumentParser(description='Convert a website to Markdown.')
    parser.add_argument('url', type=str, help='The URL of the website to convert.')

    # Explicitly pass arguments to parse_args
    # When run as 'uv run convert <URL>', sys.argv should be ['<path_to_convert_script>', 'URL']
    # So, sys.argv[1:] correctly isolates the arguments for the script itself.
    if len(sys.argv) > 1:
        args = parser.parse_args(sys.argv[1:])
    else:
        # Handle case where no URL is provided, perhaps print help or raise error
        parser.print_help()
        sys.exit(1)


    try:
        crawler = AsyncWebCrawler()
        result_container = await crawler.arun(url=args.url)

        if result_container and hasattr(result_container, '_results') and result_container._results:
            actual_result = result_container._results[0] # Get the first CrawlResult

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
                print(str(markdown_content)) # Print full markdown
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

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

def main(): # New synchronous main function for the entry point
    asyncio.run(async_main())

if __name__ == '__main__':
    # This block allows direct execution like 'python main.py <URL>'
    # It will also call the synchronous main, which sets up argparse correctly.
    main()
