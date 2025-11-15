import asyncio
from playwright.async_api import async_playwright
import math
import time

def latlon_to_mercator(lat, lon, world_size):
    x = (lon + 180.0) / 360.0
    lat_rad = math.radians(lat)
    y = (1 - math.log(math.tan(lat_rad) + 1/math.cos(lat_rad)) / math.pi) / 2 * world_size
    return x, y

async def click_map_latlon(page, lat, lon):
    # 1. Get bounding box of the map
    # hover to expand map first

    print("ATTEMPTING LOCATE")
    elem = page.locator("#map")
    await elem.hover()
    time.sleep(3)
    
    info = await page.evaluate("""
    () => {
        const container = document.querySelector('.leaflet-tile-container');
        const tile = container.querySelector('img');
        const rect = container.getBoundingClientRect();

        const url = tile.src;

        // --- extract x,y,z using regex since URLSearchParams won't work ---
        const zMatch = url.match(/\\bz=(\\d+)/);
        const xMatch = url.match(/\\bx=(\\d+)/);
        const yMatch = url.match(/\\by=(\\d+)/);

        const z = zMatch ? parseInt(zMatch[1]) : null;
        const tx = xMatch ? parseInt(xMatch[1]) : null;
        const ty = yMatch ? parseInt(yMatch[1]) : null;

        // --- get CSS transform from tile ---
        let tileOffsetX = 0, tileOffsetY = 0;

        const transform = tile.style.transform;
        if (transform && transform.includes("translate3d")) {
            const nums = transform.match(/-?\\d+\\.?\\d*/g);
            if (nums && nums.length >= 2) {
                tileOffsetX = parseFloat(nums[0]);
                tileOffsetY = parseFloat(nums[1]);
            }
        }

        const tileSize = 256;

        // guard: if tile coords missing, return everything as null
        if (z === null || tx === null || ty === null) {
            return {
                x0: rect.x,
                y0: rect.y,
                z: null,
                pixelOriginX: null,
                pixelOriginY: null,
                tileSize
            };
        }

        // compute pixel origin
        const pixelOriginX = -tileOffsetX - tx * tileSize;
        const pixelOriginY = -tileOffsetY - ty * tileSize;

        return {
            x0: rect.x,
            y0: rect.y,
            z,
            pixelOriginX,
            pixelOriginY,
            tileSize
        };
    }
    """)

    z = info["z"]
    world_size = info["tileSize"] * (2 ** z)

    # convert lat/lon → global mercator pixel coords
    px, py = latlon_to_mercator(lat, lon, world_size)

    # convert into screen pixel coords
    screen_x = info["x0"] + (px + info["pixelOriginX"])
    screen_y = info["y0"] + (py + info["pixelOriginY"])

    print(screen_x, screen_y, info, px, py, "SCREEN")

    await page.mouse.click(screen_x, screen_y)
    print("CLICKED")
    if True:
        f = lambda x,y : f"""
                const dot = document.createElement('div');
                dot.style.position = 'absolute';
                dot.style.left = `${screen_x - 5}px`; // Adjust for half the dot's size to center it
                dot.style.top = `${screen_y - 5}px`;  // Adjust for half the dot's size to center it
                dot.style.width = '10px';
                dot.style.height = '10px';
                dot.style.backgroundColor = 'red';
                dot.style.borderRadius = '50%';
                dot.style.zIndex = '10000'; // Ensure it's on top
                document.body.appendChild(dot);
                
                // Optional: Remove the dot after a few seconds
                //setTimeout(() => {{
                //    document.body.removeChild(dot);
                //}}, 3000); 
        """
        # await page.evaluate(f(screen_x, screen_y))
        await page.evaluate(f(500, 500))
        print("EVAL")
        time.sleep(100)



async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://openguessr.com")
        await asyncio.sleep(2)

        print("PAGE LOADED")

        # TODO: make this a coroutine (consumer, await click map)
        await click_map_latlon(page, 48.8575, 2.3514)
        print("OK")
        await page.screenshot(path="./example.png")
        await asyncio.sleep(3)

        # TODO: fetch score and return score
        # await browser.close()

# asyncio.get_event_loop().run_until_complete(main())

if __name__ == "__main__":
    # test to see if it works
    print("PASS")
    asyncio.run(main())
