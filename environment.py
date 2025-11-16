import pyautogui
import time
import math

'''
const el = document.getElementById('map');
const r = el.getBoundingClientRect();
console.log(r)

{
    "x": 658,
    "y": 372.40625,
    "width": 1000,
    "height": 545.59375,
    "top": 372.40625,
    "right": 1658,
    "bottom": 918,
    "left": 658
}
'''

MAP_LEFT   = 2457.609375
MAP_TOP    = 419.40625
MAP_WIDTH  = 950.390625
MAP_HEIGHT = 545.59375

def latlon_to_mercator(lat, lon, world_size):
    lat = math.radians(lat)
    x = (lon + 180.0) / 360.0 * world_size
    y = (1 - math.log(math.tan(lat) + 1 / math.cos(lat)) / math.pi) / 2 * world_size
    return x, y

def expand_mouse():
    pyautogui.moveTo(1500, 1000)
    time.sleep(3)

def click_map_latlon_pyauto(lat, lon):
    Z = 2
    TILE = 256
    WORLD_SIZE = TILE * (2**Z)

    px, py = latlon_to_mercator(lat, lon, WORLD_SIZE)

    norm_x = px / WORLD_SIZE
    norm_y = py / WORLD_SIZE

    screen_x = MAP_LEFT + MAP_WIDTH * norm_x
    screen_y = MAP_TOP  + MAP_HEIGHT * norm_y

    print("Click at:", screen_x, screen_y)
    pyautogui.moveTo(screen_x, screen_y, duration=0.15)
    pyautogui.click()

if __name__ == "__main__":
    time.sleep(3)  # safe delay
    expand_mouse()
    click_map_latlon_pyauto(0,0) # Null Island
    click_map_latlon_pyauto(48.8575, 2.3514)  # Paris
