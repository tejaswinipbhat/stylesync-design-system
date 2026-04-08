import re
import httpx
from playwright.async_api import async_playwright
from services.color_extractor import extract_colors_from_image_url
from services.token_normalizer import normalize_tokens


async def scrape_website(url: str) -> dict:
    """
    Main scraping entry point.
    Tries headless browser first, falls back to static HTTP scraping.
    """
    # Normalize URL
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        result = await _scrape_with_playwright(url)
        if "error" not in result:
            return result
    except Exception as e:
        print(f"Playwright scrape failed: {e}")

    # Fallback: static HTTP scraping
    try:
        result = await _scrape_static(url)
        return result
    except Exception as e:
        return {"error": f"Unable to analyze this website: {str(e)}"}


async def _scrape_with_playwright(url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1440, "height": 900}
        )
        page = await context.new_page()

        try:
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)  # Let JS render

            # --- Extract page metadata ---
            title = await page.title()
            favicon_url = await page.evaluate("""
                () => {
                    const link = document.querySelector("link[rel*='icon']");
                    return link ? link.href : null;
                }
            """)

            # --- Extract all CSS colors ---
            raw_colors = await page.evaluate("""
                () => {
                    const props = ['color', 'backgroundColor', 'borderColor',
                                   'borderTopColor', 'outlineColor'];
                    const colorSet = new Set();
                    document.querySelectorAll('*').forEach(el => {
                        const style = window.getComputedStyle(el);
                        props.forEach(prop => {
                            const val = style[prop];
                            if (val && val !== 'transparent' && val !== 'rgba(0, 0, 0, 0)') {
                                colorSet.add(val);
                            }
                        });
                    });
                    return Array.from(colorSet);
                }
            """)

            # --- Extract fonts ---
            fonts_data = await page.evaluate("""
                () => {
                    const fontSet = new Set();
                    const sizeMap = {};
                    const headings = ['h1','h2','h3','h4','h5','h6'];
                    headings.forEach((tag, i) => {
                        const el = document.querySelector(tag);
                        if (el) {
                            const s = window.getComputedStyle(el);
                            fontSet.add(s.fontFamily);
                            sizeMap['h' + (i+1)] = s.fontSize;
                        }
                    });
                    const body = document.querySelector('p, article, main, .content');
                    if (body) {
                        const s = window.getComputedStyle(body);
                        fontSet.add(s.fontFamily);
                        sizeMap['body'] = s.fontSize;
                    }
                    // Also grab body element font
                    const bodyEl = document.querySelector('body');
                    if (bodyEl) {
                        fontSet.add(window.getComputedStyle(bodyEl).fontFamily);
                    }
                    return { fonts: Array.from(fontSet), sizes: sizeMap };
                }
            """)

            # --- Extract spacing values ---
            spacing_values = await page.evaluate("""
                () => {
                    const vals = new Set();
                    const props = ['marginTop','marginBottom','marginLeft','marginRight',
                                   'paddingTop','paddingBottom','paddingLeft','paddingRight'];
                    document.querySelectorAll('section, div, article, header, nav, footer').forEach(el => {
                        const s = window.getComputedStyle(el);
                        props.forEach(p => {
                            const v = s[p];
                            if (v && v !== '0px' && /^\\d+px$/.test(v)) {
                                vals.add(v);
                            }
                        });
                    });
                    return Array.from(vals).slice(0, 50);
                }
            """)

            # --- Extract border radii ---
            border_radii = await page.evaluate("""
                () => {
                    const vals = new Set();
                    document.querySelectorAll('button, input, img, .card, [class*="card"],
                        [class*="btn"], [class*="button"], a').forEach(el => {
                        const v = window.getComputedStyle(el).borderRadius;
                        if (v && v !== '0px') vals.add(v);
                    });
                    return Array.from(vals).slice(0, 20);
                }
            """)

            # --- Extract image URLs for color extraction ---
            image_urls = await page.evaluate("""
                () => {
                    const imgs = Array.from(document.querySelectorAll('img[src]'))
                        .map(img => img.src)
                        .filter(src => src && !src.startsWith('data:') && src.startsWith('http'));
                    const bg = Array.from(document.querySelectorAll('[style*="background-image"]'))
                        .map(el => {
                            const m = el.style.backgroundImage.match(/url\\(["']?(.+?)["']?\\)/);
                            return m ? m[1] : null;
                        }).filter(Boolean);
                    return [...imgs.slice(0, 3), ...bg.slice(0, 2)];
                }
            """)

            # Extract colors from images
            image_colors = []
            for img_url in image_urls[:3]:
                colors = extract_colors_from_image_url(img_url)
                image_colors.extend(colors)

            # Build raw data
            raw = {
                "raw_colors": raw_colors,
                "fonts": fonts_data.get("fonts", []),
                "font_sizes": fonts_data.get("sizes", {}),
                "spacing_values": spacing_values,
                "border_radii": border_radii,
                "image_colors": image_colors,
            }

            tokens = normalize_tokens(raw)

            return {
                "url": url,
                "title": title,
                "favicon_url": favicon_url,
                "tokens": tokens,
                "status": "completed",
            }

        except Exception as e:
            return {"error": str(e)}

        finally:
            await browser.close()


async def _scrape_static(url: str) -> dict:
    """Fallback: parse CSS from <style> tags and linked stylesheets using httpx"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        html = resp.text

    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = title_m.group(1).strip() if title_m else url

    # Extract hex colors from CSS
    hex_colors = re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", html)
    hex_colors = list(set(f"#{c}" for c in hex_colors))

    # Extract font-family
    font_families = re.findall(r"font-family\s*:\s*([^;\"'{}]+)", html)
    fonts = [f.strip().strip("'\"").split(",")[0].strip() for f in font_families]
    fonts = list(dict.fromkeys(fonts))[:5]

    # Extract font sizes
    font_sizes = re.findall(r"font-size\s*:\s*([^;\"'{}]+)", html)

    raw = {
        "raw_colors": [],
        "fonts": fonts,
        "font_sizes": {"body": font_sizes[0].strip()} if font_sizes else {},
        "spacing_values": [],
        "border_radii": [],
        "image_colors": hex_colors[:15],
    }

    tokens = normalize_tokens(raw)

    return {
        "url": url,
        "title": title,
        "favicon_url": None,
        "tokens": tokens,
        "status": "completed_static",
    }
