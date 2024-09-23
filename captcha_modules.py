import numpy as np
import base64
from PIL import Image
from io import BytesIO
from io import StringIO
import cv2

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

import pandas as pd
import re
from doctr.io import DocumentFile
from doctr.models import ocr_predictor

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

predictor = ocr_predictor(
    det_arch='fast_small',  # Text detection model
    reco_arch='crnn_vgg16_bn',
    # resolve_blocks=True,
    pretrained=True
    )

color_map = {
    (147, 194, 172,255): (242, 239, 210, 255),
    (151, 191, 163,255): (242, 239, 210, 255),
    (150, 196, 175,255): (242, 239, 210, 255),
    (145, 192, 170,255): (242, 239, 210, 255),
    (147, 195, 174,255): (242, 239, 210, 255),
    (149, 193, 170,255): (242, 239, 210, 255),
    (146, 194, 173,255): (242, 239, 210, 255),
    # Add more color mappings as needed
}
def optimize_image_for_ocr(pil_image):
    # Convert PIL Image to numpy array
    image_np = np.array(pil_image)

    # Check if the image is RGBA
    if image_np.shape[-1] == 4:
        # Separate the alpha channel
        rgb = image_np[:,:,:3]
        alpha = image_np[:,:,3]

        # Convert RGB to grayscale
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    elif len(image_np.shape) == 3:
        # RGB image
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    else:
        # Already grayscale
        gray = image_np

    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # If original image was RGBA, merge the thresholded image with the alpha channel
    if image_np.shape[-1] == 4:
        thresh = cv2.merge([thresh, thresh, thresh, alpha])

    # Convert back to PIL Image
    optimized_image = Image.fromarray(thresh)
    return optimized_image

def replace_multiple_colors_rgba(image, color_map, threshold=98):
    img_array = np.array(image.convert('RGBA'))
    for original_color, replacement_color in color_map.items():
        # Convert colors to numpy arrays for easier comparison
        orig_color = np.array(original_color[:3])
        repl_color = np.array(replacement_color)

        # Create mask for RGB channels
        mask = np.all(np.abs(img_array[:, :, :3] - orig_color) <= threshold, axis=2)

        # Replace colors and alpha
        img_array[mask] = repl_color
    return Image.fromarray(img_array)

# prompt: type a text to input field with name=captcha
def type_captcha_to_input(driver,captcha_text):
  captcha_input = WebDriverWait(driver, 10).until(
          EC.presence_of_element_located((By.NAME, "captcha"))
  )
  captcha_input.send_keys(captcha_text)

# def get_captcha_canvas_image(driver,timeout=20):
#     try:
#         canvas_element = WebDriverWait(driver, timeout).until(
#             EC.presence_of_element_located((By.ID, "captcahCanvas"))
#         )
#         canvas_base64 = driver.execute_script(
#             "return arguments[0].toDataURL('image/png').substring(21);",
#             canvas_element
#         )
#         canvas_png = base64.b64decode(canvas_base64)
#         image = Image.open(BytesIO(canvas_png))
#         return image
#     except TimeoutException:
#         print(f"Canvas element did not load within {timeout} seconds")
#         return None



def get_captcha_canvas_image(driver, timeout=20, max_retries=3, retry_delay=1):
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempting to locate captcha canvas (Attempt {attempt + 1}/{max_retries})")
            canvas_element = WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((By.ID, "captcahCanvas"))
            )
            
            # Wait for the canvas to be visible and have a non-zero size
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return arguments[0].width > 0 && arguments[0].height > 0", canvas_element)
            )
            
            # Additional check to ensure the captcha is fully rendered
            time.sleep(0.5)  # Short delay to allow for any final rendering
            
            logging.info("Extracting canvas image data")
            canvas_base64 = driver.execute_script(
                "return arguments[0].toDataURL('image/png').substring(21);",
                canvas_element
            )
            
            # Verify that we actually got image data
            if not canvas_base64:
                logging.warning("Canvas data is empty, retrying...")
                time.sleep(retry_delay)
                continue
            
            canvas_png = base64.b64decode(canvas_base64)
            image = Image.open(BytesIO(canvas_png))
            
            # Final check: ensure the image has actual content
            if image.size[0] > 1 and image.size[1] > 1:
                print("Successfully extracted captcha image")
                return image
            else:
                logging.warning("Extracted image is too small, likely not fully loaded. Retrying...")
        except TimeoutException:
            logging.warning(f"Canvas element did not load within {timeout} seconds")
        except StaleElementReferenceException:
            logging.warning("Canvas element became stale, retrying...")
        except Exception as e:
            logging.error(f"Unexpected error occurred: {str(e)}")
        
        time.sleep(retry_delay)
    
    logging.error(f"Failed to extract captcha image after {max_retries} attempts")
    return None

def is_captcha_length_valid(predicted_captcha):
  if len(predicted_captcha) != 6:
    return False
  return True

def refresh_captcha(driver,timeout=10):
    try:
        # Click the refresh button
        captcha_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "cpt-btn"))
        )
        captcha_button.click()

        # Wait for the new captcha to appear
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "captcahCanvas"))
        )

        # Verify that the captcha has actually changed
        def captcha_changed(driver):
            try:
                new_captcha = driver.find_element(By.ID, "captcahCanvas")
                return new_captcha.is_displayed() and new_captcha.size['width'] > 0
            except StaleElementReferenceException:
                return False

        WebDriverWait(driver, timeout).until(captcha_changed)

        print("Captcha refreshed successfully")
        return True
    except TimeoutException:
        print(f"Failed to refresh captcha within {timeout} seconds")
        return False

# prompt: detect if a string has something else than alphnumeric

def recognize_captcha(optimized_image):
  optimized_image.save('optimized_captcha.png')
  doc = DocumentFile.from_images('optimized_captcha.png')
  result = predictor(doc)
  return result

# def get_all_recognized_alpha_num(result):
#   for t1 in result.pages[0].blocks:
#       line_content=""
#       for t2 in t1.lines:
#           for t3 in t2.words:
#             if t3.confidence>0.45:
#               line_content+=t3.value+""

#   only_alphanum = re.sub(r'[^a-zA-Z0-9]', '', line_content).upper()
#   return only_alphanum

def get_all_recognized_alpha_num(result):
    line_content = []
    for block in result.pages[0].blocks:
        for line in block.lines:
            for word in line.words:
                if word.confidence > 0.45:
                    line_content.append(word.value)

    full_content = ''.join(line_content)
    only_alphanum = re.sub(r'[^a-zA-Z0-9]', '', full_content).upper()
    return only_alphanum

def take_screenshot(driver):
  driver.save_screenshot("screenshot.png")

def is_invalid_captcha_dialog(driver):
  try:
      element = WebDriverWait(driver,1).until(
          EC.visibility_of_element_located((By.XPATH, "//button[text()='Ok']"))
      )
      is_visible = True
  except TimeoutException:
      is_visible = False
  return is_visible

def load_captcha_website(driver,url, timeout=30):
    driver.get(url)
    try:
        WebDriverWait(driver, timeout).until(
            EC.all_of(
                EC.visibility_of_element_located((By.CLASS_NAME, "cpt-btn")),
                EC.visibility_of_element_located((By.ID, "captcahCanvas"))
            )
        )
        print(f"Page loaded successfully {url}")
        return True
    except TimeoutException:
        print(f"FAILED loading {url}")
        return False