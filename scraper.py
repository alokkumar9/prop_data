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

pages = [i for i in range(1001,1002)]  # Define the pages to scrape
# pages=[50]
# all_projects_list = []
driver=setup_driver()


for page in pages:
    print("Current Page: ",page)
    try:
        website = f"https://maharera.maharashtra.gov.in/projects-search-result?page={page}"
        driver.get(website)
        elements = driver.find_elements(By.CSS_SELECTOR, ".row.shadow.p-3.mb-5.bg-body.rounded")
        projects_in_page_list = get_element_info(elements)

        for project in projects_in_page_list:
            complete_project_info = add_most_basic_info(project)
            visit_details_url = project['visit_details_url']
            reg_num=complete_project_info['reg_number']

            try:
                # complete_project_info['project_details'], complete_project_info['building_details'] = None, None
                project_details, building_details, parking_details= switch_tab(driver, reg_num, visit_details_url)
                complete_project_info['project_details']=project_details
                complete_project_info['building_details']=building_details
                complete_project_info["parking_details"]=parking_details
                
                if project_details is not None:
                  complete_project_info['project_details_extracted'] = True
                if building_details is not None:
                  complete_project_info['building_details_extracted'] = True

            except Exception as e:
                print(f"Page {page},  Error fetching details for project: {e}")
                # property_not_added_file([reg_num+"  "+visit_details_url])
                continue

            print(complete_project_info)
            # insert_many(mg_db, "maharashtra", [complete_project_info])
            print(f"added {reg_num} to database from Page: {page}")
            print("\n")

        print(f"Page {page} done\n")
    except Exception as e:
        print(f"There was an error for page {page}: {e}")
        driver = setup_driver()
        continue