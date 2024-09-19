from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException

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
from captcha_modules import *
from more_details_modules import *

def setup_driver():
  chrome_options = Options()
  chrome_options.add_argument('--headless')
  chrome_options.add_argument('--no-sandbox')
  chrome_options.add_argument('--disable-dev-shm-usage')
  return webdriver.Chrome(options=chrome_options)

def take_screenshot(driver):
  driver.save_screenshot("screenshot.png")

def clean_text(t):
  t=t.replace("\n","").replace("\t","").replace(":","").replace("*","").strip()
  return t

def well_formated_dict(df_dict):
  for record in df_dict:
    for key, value in record.items():
      if isinstance(value, str):
        try:
          # Try converting to integer
          record[key] = int(value)
        except ValueError:
          try:
            # If integer conversion fails, try converting to float
            record[key] = float(value)
          except ValueError:
            # If both conversions fail, leave the value as it is
            pass
  return df_dict


def date_standizer(text_with_date, failed_dates=None):
  dformat = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']
  if failed_dates is None:
      failed_dates = []  # Initialize the list if not provided

  if isinstance(text_with_date, str):
      text_with_date = text_with_date.strip()
      if len(text_with_date) == 0:
          return text_with_date
      else:
          for i, d in enumerate(dformat):
              try:
                  standard_date = pd.to_datetime(text_with_date, format=d)
                  return standard_date  # Return the standardized date
              except ValueError:
                  continue
          # If all formats fail, log the original text
          failed_dates.append(text_with_date)
          return text_with_date  # Return the original text if conversion fails
  return text_with_date

def date_standizer_for_table(df):
  for col in df.columns:
    df[col]=df[col].apply(date_standizer)
  return df

def manage_captcha_logic(driver):
    attempt = 1
    while attempt <= 3:
        try:
            captcha_canvas_img = get_captcha_canvas_image(driver)
            if captcha_canvas_img is None:
                print("captcha_canvas_img is None")
                return False

            new_image = replace_multiple_colors_rgba(captcha_canvas_img, color_map)
            optimized_image = optimize_image_for_ocr(new_image)
            recognized_text = recognize_captcha(optimized_image)
            captcha_alpha_num = get_all_recognized_alpha_num(recognized_text)

            if is_captcha_length_valid(captcha_alpha_num):
                type_captcha_to_input(driver, captcha_alpha_num)
                submit_button = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Submit']"))
                )
                submit_button.click()

                if is_invalid_captcha_dialog(driver):
                    print(f"Invalid CAPTCHA. Attempt: {attempt}")  # Moved here
                    ok_button = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[text()='Ok']"))
                    )
                    ok_button.click()
                    # No return False here, allowing the loop to continue
                else:
                    print(f"CAPTCHA solved in attempt: {attempt}")
                    return True

        except Exception as e:
            print(f"Error in attempt {attempt}: {str(e)}")

        attempt += 1
        # Uncomment the following line if you want a delay between attempts
        # time.sleep(2)

    return False

def switch_tab(driver, visit_details_url):
    try:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        load_captcha_website(driver, visit_details_url)

        if manage_captcha_logic(driver):
            WebDriverWait(driver, 20).until(
                EC.all_of(
                    EC.visibility_of_element_located((By.TAG_NAME, "select")),
                    EC.visibility_of_element_located((By.TAG_NAME, "input")),
                    EC.visibility_of_element_located((By.TAG_NAME, "table")),
                    EC.visibility_of_element_located((By.TAG_NAME, "td")),
                )
            )
            try:
              df1 = data1_extraction_df(driver)
              df2 = data2_extraction_df(driver)
              combined_df = pd.concat([df1, df2], ignore_index=True)
              combined_df_after_date_standardization = date_standizer_for_table(combined_df)
              df_dict = combined_df_after_date_standardization.to_dict(orient="records")
              property_details_dict = well_formated_dict(df_dict)
            except Exception as e:
              property_details_dict = None

            try:
              building_title_element = driver.find_element(By.XPATH, "//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'summary of building details')]")
              table_element = building_title_element.find_element(By.XPATH, "./following::table[1]")
              building_details = get_building_details(table_element)
            except NoSuchElementException:
              building_details = None

            return property_details_dict, building_details
        else:
            print("Captcha not solved")
            return None, None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None, None
    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])