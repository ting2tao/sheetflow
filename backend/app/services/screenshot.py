"""Screenshot service using Playwright.

Takes HTML content and captures it as an image (PNG/JPG).
Uses Chromium for consistent rendering with proper font support.
"""

import asyncio
import os
from typing import Optional, Literal
from playwright.async_api import async_playwright, Browser, Page as PlaywrightPage


# Global browser instance for reuse
_browser: Optional[Browser] = None
_playwright = None


async def _get_browser() -> Browser:
    """Get or create a shared browser instance."""
    global _browser, _playwright

    if _browser is None or not _browser.is_connected():
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--font-render-hinting=none',
            ]
        )

    return _browser


async def close_browser():
    """Close the browser instance."""
    global _browser, _playwright

    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None


async def capture_html_to_image(
    html_content: str,
    output_path: str,
    format: Literal['png', 'jpg'] = 'png',
    quality: Optional[int] = None,
    scale_factor: float = 2.0,
) -> str:
    """Capture HTML content as an image.

    Args:
        html_content: HTML string to render
        output_path: Path to save the image
        format: Output format ('png' or 'jpg')
        quality: JPEG quality (1-100, only for JPG)
        scale_factor: Device scale factor for higher resolution

    Returns:
        Path to the saved image
    """
    browser = await _get_browser()

    # Create a new page with higher DPI
    context = await browser.new_context(
        viewport={'width': 1200, 'height': 800},
        device_scale_factor=scale_factor,
    )
    page = await context.new_page()

    try:
        # Set content and wait for rendering
        await page.set_content(html_content, wait_until='networkidle')

        # Wait a bit for fonts to load
        await asyncio.sleep(0.1)

        # Get the table container dimensions
        table_box = await page.evaluate('''() => {
            const table = document.querySelector('table');
            if (table) {
                const rect = table.getBoundingClientRect();
                return {
                    width: Math.ceil(rect.width) + 2,
                    height: Math.ceil(rect.height) + 2,
                    x: Math.floor(rect.x),
                    y: Math.floor(rect.y)
                };
            }
            return null;
        }''')

        if table_box:
            # Clip to just the table
            clip = {
                'x': max(0, table_box['x'] - 1),
                'y': max(0, table_box['y'] - 1),
                'width': table_box['width'] + 2,
                'height': table_box['height'] + 2,
            }

            # Take screenshot
            screenshot_options = {
                'path': output_path,
                'type': format,
                'clip': clip,
            }

            if format == 'jpg' and quality:
                screenshot_options['quality'] = quality

            await page.screenshot(**screenshot_options)
        else:
            # Fallback: full page screenshot
            screenshot_options = {
                'path': output_path,
                'type': format,
                'full_page': True,
            }
            if format == 'jpg' and quality:
                screenshot_options['quality'] = quality

            await page.screenshot(**screenshot_options)

    finally:
        await context.close()

    return output_path


def capture_html_to_image_sync(
    html_content: str,
    output_path: str,
    format: Literal['png', 'jpg'] = 'png',
    quality: Optional[int] = None,
    scale_factor: float = 2.0,
) -> str:
    """Synchronous wrapper for capture_html_to_image."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(
            capture_html_to_image(html_content, output_path, format, quality, scale_factor)
        )
    finally:
        loop.close()


async def batch_capture(
    html_pages: list[str],
    output_dir: str,
    format: Literal['png', 'jpg'] = 'png',
    quality: Optional[int] = None,
    scale_factor: float = 2.0,
    filename_prefix: str = '',
) -> list[str]:
    """Capture multiple HTML pages as images.

    Args:
        html_pages: List of HTML strings
        output_dir: Directory to save images
        format: Output format
        quality: JPEG quality
        scale_factor: DPI scale factor
        filename_prefix: Prefix for filenames

    Returns:
        List of saved image paths
    """
    os.makedirs(output_dir, exist_ok=True)

    output_paths = []
    for i, html in enumerate(html_pages):
        filename = f"{filename_prefix}{i+1:03d}.{format}"
        output_path = os.path.join(output_dir, filename)

        await capture_html_to_image(
            html, output_path, format, quality, scale_factor
        )
        output_paths.append(output_path)

    return output_paths
