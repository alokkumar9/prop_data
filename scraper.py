import pandas as pd
from mongo import *
from basic_details_modules import *
from selenium_helper import *
from more_details_modules import *
from captcha_modules import *
driver=setup_driver()

client=connect_to_atlas()
mg_db=client["property"]
mg_collection=mg_db["maharashtra"]

pages = [11, 12, 13]  # Define the pages to scrape
all_projects_list = []
driver=setup_driver()
for page in pages:
    print(f"Current Page: ",page)

    try:
        website = f"https://maharera.maharashtra.gov.in/projects-search-result?page={page}"
        driver.get(website)
        elements = driver.find_elements(By.CSS_SELECTOR, ".row.shadow.p-3.mb-5.bg-body.rounded")
        projects_in_page_list = get_element_info(elements)

        for project in projects_in_page_list:
            complete_project_info = add_most_basic_info(project)
            visit_details_url = project['visit_details_url']

            try:
                # complete_project_info['project_details'], complete_project_info['building_details'] = None, None
                complete_project_info['project_details'], complete_project_info['building_details'] = switch_tab(driver, visit_details_url)
                if complete_project_info['project_details'] is not None:
                  complete_project_info['project_details_extracted'] = True
                if complete_project_info['building_details'] is not None:
                  complete_project_info['building_details_extracted'] = True

            except Exception as e:
                print(f"Error fetching details for project: {e}")
                continue

            all_projects_list.append(complete_project_info)
            print(complete_project_info)
            print("\n")
        insert_many(mg_db, "maharashtra", all_projects_list)
        print(f"Page {page} done\n")
        all_projects_list.clear()
    except Exception as e:
        print(f"There was an error for page {page}: {e}")
        driver = setup_driver()
        continue