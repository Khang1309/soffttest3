# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
import unittest, time, csv, os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class T_001(unittest.TestCase):
    def setUp(self):
        # Using machine-specific path for the driver
        self.driver = webdriver.Edge(executable_path=r'D:/KR-exported-python-unitest-project1/TC002/msedgedriver.exe')
        self.driver.maximize_window() 
        self.wait = WebDriverWait(self.driver, 15)
        self.verificationErrors = []

    def safe_click(self, locator):
        """Wait, scroll, and click with a JavaScript fallback if intercepted[cite: 144]."""
        try:
            element = self.wait.until(EC.presence_of_element_located(locator))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5) 
            clickable_element = self.wait.until(EC.element_to_be_clickable(locator))
            try:
                clickable_element.click()
            except Exception:
                # Direct JS click bypasses overlay issues [cite: 289]
                self.driver.execute_script("arguments[0].click();", clickable_element)
        except Exception as e:
            print("Could not click element %s: %s" % (str(locator), str(e)))
            raise

    def test_001(self):
        driver = self.driver
        basePath = "$D:\\TC_002"
        assignment_url = "https://school.moodledemo.net/mod/assign/view.php?id=807&action=view"

        # 1. Login once (Outside the loop) 
        driver.get("https://school.moodledemo.net/login/index.php")
        driver.find_element(By.ID, "username").send_keys("student")
        driver.find_element(By.ID, "password").send_keys("moodle26")
        self.safe_click((By.ID, "loginbtn"))

        with open('test_data.csv', mode='r', encoding='utf-8-sig') as file:
            csvFile = csv.reader(file)
            next(csvFile) 
            
            for lines in csvFile:
                if not lines or not any(lines): # Stop if the row is empty
                    break
                
                # 2. Reset state if a submission exists
                driver.get(assignment_url)
                try:
                    remove_btn = driver.find_elements(By.XPATH, "//button[contains(text(), 'Remove submission')]")
                    if remove_btn:
                        self.safe_click((By.XPATH, "//button[contains(text(), 'Remove submission')]"))
                        self.safe_click((By.XPATH, "//button[contains(text(), 'Continue')]"))
                        driver.get(assignment_url)
                except Exception:
                    pass

                # 3. Add Submission
                self.safe_click((By.XPATH, "//button[contains(text(), 'Add submission')]"))

                # 4. File Upload [cite: 173, 289]
                self.safe_click((By.XPATH, "//a[@title='Add...']"))
                time.sleep(1)
                self.safe_click((By.XPATH, "//a[contains(., 'Upload a file')]"))

                full_path = os.path.join(basePath, lines[1])
                file_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
                file_input.send_keys(full_path)

                # 5. Finalize Submission
                self.safe_click((By.XPATH, "//button[contains(text(), 'Upload this file')]"))
                self.safe_click((By.ID, "id_submitbutton"))

                # 6. Verification
                expected_text = lines[4]
                status_cell = self.wait.until(EC.presence_of_element_located((By.XPATH, "//th[contains(., 'Submission status')]/following-sibling::td")))
                
                try: 
                    self.assertIn(expected_text, status_cell.text)
                except AssertionError as e: 
                    self.verificationErrors.append("Test %s Failed: %s" % (lines[0], str(e)))

                # 7. Cleanup for next loop
                self.safe_click((By.XPATH, "//button[contains(text(), 'Remove submission')]"))
                self.safe_click((By.XPATH, "//button[contains(text(), 'Continue')]"))

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()