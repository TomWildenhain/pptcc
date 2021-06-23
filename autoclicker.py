import pyautogui
import win32gui
import time
import random

# While background middle pixel is active color:
    # Find click colors
    
ACTIVE_COLOR = (0, 94, 172)
WALL_COLOR = (255, 28, 228)
CLICK_COLORS = [(209, 69, 38), (232, 122, 0)]
WAIT_COLOR = (255, 255, 255)
pyautogui.PAUSE = 0.025
(width, height) = pyautogui.size()
screenshot = None
last_screenshot_time = None

def get_pixel_at(x, y, refresh=False):
    if not (0 <= x < width and 0 <= y < height):
        return None
    global last_screenshot_time
    global screenshot
    if refresh or screenshot is None or time.time() - last_screenshot_time > 0.2:
        screenshot = pyautogui.screenshot()
        last_screenshot_time = time.time()
    return screenshot.getpixel((x, y))

def pixel_matches_color(x, y, color):
    return get_pixel_at(x, y) == color

def main():
    while True:
        if is_active() and not mouse_is_spinner():
            mx, my = pyautogui.position()
            if not (can_click_new(mx, my) or can_click(mx, my)):
                x = random.randint(0, width-1)
                y = random.randint(0, height-1)
            if can_click_new(x, y) or can_click(x, y):
                pyautogui.moveTo(x, y)
                if mouse_is_hand():
                    color = get_pixel_at(x, y)
                    pyautogui.click()
                    if 0.3 <= x/width <= 0.7 and 0.44 <= y/height <= 0.91:
                        timeout = time.time() + 0.2
                        while pixel_matches_color(x, y, color) and time.time() < timeout:
                            pass
                    else:
                        timeout = time.time() + 0.2
                        while not mouse_is_spinner() and time.time() < timeout:
                            pass
                        while mouse_is_spinner():
                            pass


def is_active():
    return pixel_matches_color(0, height//2, ACTIVE_COLOR)

def can_click_new(x, y):
    if not get_pixel_at(x, y) in CLICK_COLORS:
        return False
    mx, my = pyautogui.position()
    while my > 0:
        if pixel_matches_color(mx, my, WALL_COLOR):
            return False
        my -= 1

    dx = 1 if x > mx else -1

    while mx != x:
        if pixel_matches_color(mx, my, WALL_COLOR):
            return False
        mx += dx

    while my < y:
        if pixel_matches_color(mx, my, WALL_COLOR):
            return False
        my += 1

    return True

def can_click(x, y):
    if not get_pixel_at(x, y) in CLICK_COLORS:
        return False
    mx, my = pyautogui.position()
    dx = x - mx
    dy = y - my
    scale = max(abs(dx), abs(dy))
    if scale == 0:
        return True
    if dx == 0:
        dx = 1
    if dy == 0:
        dy = 1
    dx *= 2 / scale
    dy *= 2 / scale
    xpositive = dx > 0
    ypositive = dy > 0
    while (mx < x) == xpositive or (my < y) == ypositive:
        mx += dx
        my += dy
        if pixel_matches_color(mx, my, WALL_COLOR):
            return False
    return True

def mouse_is_hand():
    return win32gui.GetCursorInfo()[1] == 65567

def mouse_is_spinner():
    return win32gui.GetCursorInfo()[1] == 65543

main()
