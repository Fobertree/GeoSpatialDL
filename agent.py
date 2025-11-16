import asyncio
import math
import pyautogui
from playwright.async_api import async_playwright, Page
import time


class GeoUtils:
    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2, mode="km"):
        """Distance between two lat/lon points."""
        # Radius of Earth in km/miles
        R = 6371 if mode == "km" else 3959 if mode == "mi" else -1

        if R == -1:
            raise Exception(f"Invalid mode: {mode}")

        lat1, lon1 = math.radians(lat1), math.radians(lon1)
        lat2, lon2 = math.radians(lat2), math.radians(lon2)
        dlat, dlon = lat2 - lat1, lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

class CursorController:
    @staticmethod
    async def hover_map(page: Page, click=True):
        """Hover the OpenGuessr map using pyautogui."""
        win = await page.evaluate("() => ({x: window.screenX, y: window.screenY})")
        cx, cy = win["x"] + 1500, win["y"] + 900

        pyautogui.moveTo(cx, cy, duration=0.5)
        if click:
            pyautogui.click(cx, cy)

class OpenGuessrAgent:
    def __init__(self, viewport=(1728, 992)):
        self.viewport = viewport
        self.browser = None
        self.context = None
        self.page: Page = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False, ignore_default_args=["--mute-audio"]
        )
        self.context = await self.browser.new_context(
            viewport={"width": self.viewport[0], "height": self.viewport[1]}
        )
        self.page = await self.context.new_page()

    async def load_game(self):
        await self.page.goto("https://openguessr.com/")

        
    async def screenshot(page: Page, path="ex.png"):
        '''
        Very inelegant

        Override element visibility hidden
        Restore visibility afterwards
        
        inserting random time sleeps for now
        TODO: improve this impl bc its expensive and poorly done
        '''

        time.sleep(5)
        # hide elements
        HIDE_SELECTORS = [
            ".barMenu",                         # top bar
            ".gm-compass",                      # compass
            ".gmnoprint",                       # Google navigation UI
            "path",                             # SVG paths for buttons
            ".image.svelte-1s6d94d",            # logo
            "#adunit",                          # ads
            "button",                           # generic buttons
            "#map",                             # guessing map
            ".bottomFooterAds"                  # ads
        ]

        for sel in HIDE_SELECTORS:
            await page.evaluate(
                """(sel) => {
                    document.querySelectorAll(sel).forEach(el => {
                        el.setAttribute("__hidden__", "1");
                        el.style.visibility = "hidden";
                        el.style.opacity = "0";
                        el.style.pointerEvents = "none";
                    });
                }""",
                sel,
            )
        
        time.sleep(5)
        await page.screenshot(path=path) # TODO: return image via buffer -> pil/numpy instead of only to path
        time.sleep(3) 

        # ----------- RESTORE ELEMENTS -----------
        for sel in HIDE_SELECTORS:
            await page.evaluate(
                """(sel) => {
                    document.querySelectorAll(sel).forEach(el => {
                        if (el.getAttribute("__hidden__") === "1") {
                            el.style.visibility = "";
                            el.style.opacity = "";
                            el.style.pointerEvents = "";
                            el.removeAttribute("__hidden__");
                        }
                    });
                }""",
                sel,
            )

    async def get_answer(self, lat_pred, lon_pred):
        """
        Makes a dummy guess, opens the Google Maps popup to extract coordinates,
        then computes the haversine distance.
        """
        # Click random place on map to activate "Guess"
        await CursorController.hover_map(self.page)
        await self.page.get_by_text("? Guess", exact=True).click()

        # Open Streetview popup
        async with self.page.expect_popup() as popup_info:
            await self.page.get_by_role("button", name="Streetview symbol").click()

        popup = await popup_info.value
        raw_url = popup.url
        # print(raw_url)

        lat_label, lon_label = map(
            lambda x: round(float(x), 4),
            raw_url.split("&viewpoint=")[1].split(","),
        )
        print("Actual:", lat_label, lon_label)

        await popup.close()

        await self.page.get_by_role(
            "button", name="Continue Expand or close arrow"
        ).click()

        distance_km = GeoUtils.haversine_distance(
            lat_pred, lon_pred, lat_label, lon_label
        )

        return distance_km

    async def close(self):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

async def main():
    agent = OpenGuessrAgent()

    await agent.start()
    await agent.load_game()

    screenshot = ...
    diff = await agent.get_answer(lat_pred=0, lon_pred=0)

    print(f"\nDistance error: {diff:.2f} km\n")
    print("DONE")

    await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
