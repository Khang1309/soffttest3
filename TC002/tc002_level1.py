# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
import unittest, time, csv, os, re, warnings
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

LOGIN_URL      = "https://school.moodledemo.net/login/index.php"
USERNAME       = "student"
PASSWORD       = "moodle26"
BASE_ASSIGN_URL = "https://school.moodledemo.net/mod/assign/view.php"
BASE_PATH = "D:\\TC_002"

class T_002(unittest.TestCase):
    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)
        self.driver = webdriver.Edge(
            executable_path=r'D:/KR-exported-python-unitest-project1/TC002/msedgedriver.exe',
            service_log_path=os.devnull
        )
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 15)
        self.verificationErrors = []
        self.current_tc = "(not started)"


    def safe_click(self, locator):
        """Scroll into view and click; JS fallback for overlay-blocked clicks."""
        element = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.4)
        clickable = self.wait.until(EC.element_to_be_clickable(locator))
        try:
            clickable.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", clickable)

    def is_element_present(self, how, what):
        try:
            self.driver.find_element(by=how, value=what)
            return True
        except Exception:
            return False

    def _safe_navigate(self, url):
        """Navigate away, disabling Moodle's beforeunload handler first so it
        never blocks. Accepts any stray browser alert that might still appear."""
        try:
            self.driver.execute_script("window.onbeforeunload = null;")
        except Exception:
            pass
        self.driver.get(url)
        try:
            self.driver.switch_to.alert().accept()
        except Exception:
            pass

    def _ensure_logged_in(self):
        """Verify we are still logged in; if not, re-authenticate (up to 3 tries).
        Clears cookies before each attempt to avoid Moodle rejecting correct
        credentials due to stale/expired session cookies."""
        for attempt in range(1, 4):
            if self.is_element_present(By.XPATH,
                    "//div[contains(@class,'usermenu')] | "
                    "//a[contains(@href,'logout')] | "
                    "//span[contains(@class,'userbutton')]"):
                return  

            try:
                self.driver.delete_all_cookies()
            except Exception:
                pass

            self._safe_navigate(LOGIN_URL)
            time.sleep(2)
            try:
                un = self.driver.find_element(By.ID, "username")
                un.clear(); un.send_keys(USERNAME)
                pw = self.driver.find_element(By.ID, "password")
                pw.clear(); pw.send_keys(PASSWORD)
                self.safe_click((By.ID, "loginbtn"))
                time.sleep(3)
            except Exception as ex:
                pass  
        if not self.is_element_present(By.XPATH,
                "//div[contains(@class,'usermenu')] | //a[contains(@href,'logout')]"):
            raise RuntimeError("Could not log in after 3 attempts")

    def _open_file_picker_and_upload(self, basePath, file_name):
        """Add… → Upload a file → send file path → Upload this file."""
        self.safe_click((By.XPATH, "//a[@title='Add...']"))
        time.sleep(1)
        self.safe_click((By.XPATH, "//a[contains(., 'Upload a file')]"))
        full_path = os.path.join(basePath, file_name)
        file_input = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        file_input.send_keys(full_path)
        time.sleep(3)
        self.safe_click((By.XPATH, "//button[contains(text(), 'Upload this file')]"))

    def _reset_submission(self, assignment_url):
        """Remove any existing submission so every TC starts from a clean state."""
        self._safe_navigate(assignment_url)
        try:
            if self.driver.find_elements(By.XPATH,
                    "//button[contains(text(), 'Remove submission')]"):
                self.safe_click((By.XPATH, "//button[contains(text(), 'Remove submission')]"))
                self.safe_click((By.XPATH, "//button[contains(text(), 'Continue')]"))
                self._safe_navigate(assignment_url)
        except Exception:
            pass

    def _create_temp_submission(self, assignment_url, basePath, file_name):
        """Create a submission (needed as pre-condition for edit/remove flows)."""
        self.safe_click((By.XPATH, "//button[contains(text(), 'Add submission')]"))
        self._open_file_picker_and_upload(basePath, file_name)
        self.safe_click((By.ID, "id_submitbutton"))
        self._safe_navigate(assignment_url)
   

    def test_002(self):
        driver = self.driver
        basePath = BASE_PATH
        driver.get(LOGIN_URL)
        driver.find_element(By.ID, "username").send_keys(USERNAME)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        self.safe_click((By.ID, "loginbtn"))
        time.sleep(2)

        with open('test_data.csv', mode='r', encoding='utf-8-sig') as f:
            for row in csv.reader(f):
                if row and row[0] == 'TC_ID':
                    continue            
                if not row or not any(row):
                    break

                tc_id         = row[0]
                file_name     = row[1]
                expected      = row[4]
                assignment_id = row[5]
                flow_type     = row[6]
                self.current_tc = tc_id

                assignment_url = "%s?id=%s&action=view" % (BASE_ASSIGN_URL, assignment_id)
                edit_url       = "%s?id=%s&action=editsubmission" % (BASE_ASSIGN_URL, assignment_id)

                self._safe_navigate(assignment_url)
                self._reset_submission(assignment_url)

                try:
                    self._ensure_logged_in()
                    self._safe_navigate(assignment_url)
                    self._reset_submission(assignment_url)
                except Exception as e:
                    err = "Test %s ERROR: %s: %s" % (tc_id, type(e).__name__, str(e))
                    self.verificationErrors.append(err)
                    print("  [ERROR] %s" % err)
                    continue

                try:
                    if flow_type == 'normal':
                        self.safe_click((By.XPATH, "//button[contains(text(), 'Add submission')]"))
                        self._open_file_picker_and_upload(basePath, file_name)
                        self.safe_click((By.ID, "id_submitbutton"))

                        status_cell = self.wait.until(EC.presence_of_element_located(
                            (By.XPATH, "//th[contains(., 'Submission status')]/following-sibling::td")))
                        try:
                            self.assertIn(expected, status_cell.text)
                        except AssertionError as e:
                            self.verificationErrors.append("Test %s Failed: %s" % (tc_id, str(e)))

                        self.safe_click((By.XPATH, "//button[contains(text(), 'Remove submission')]"))
                        self.safe_click((By.XPATH, "//button[contains(text(), 'Continue')]"))

                    elif flow_type == 'error_dialog':
                        self.safe_click((By.XPATH, "//button[contains(text(), 'Add submission')]"))
                        self._open_file_picker_and_upload(basePath, file_name)
                        time.sleep(2)   # let the error dialog render

                        dialog_xpath = ("//div[contains(@class,'moodle-dialogue')]"
                                        "[contains(.,'%s')]" % expected)
                        try:
                            self.assertTrue(self.is_element_present(By.XPATH, dialog_xpath))
                        except AssertionError as e:
                            self.verificationErrors.append("Test %s Failed: %s" % (tc_id, str(e)))

                        self._safe_navigate(assignment_url)

                    elif flow_type == 'empty_submit':
                        self.safe_click((By.XPATH, "//button[contains(text(), 'Add submission')]"))
                        self.safe_click((By.ID, "id_submitbutton"))
                        time.sleep(1)

                        try:
                            alert_div = self.wait.until(EC.presence_of_element_located(
                                (By.XPATH, "//div[contains(@class,'alert')]")))
                            self.assertRegex(alert_div.text,
                                             r"^[\s\S]*%s[\s\S]*$" % re.escape(expected))
                        except AssertionError as e:
                            self.verificationErrors.append("Test %s Failed: %s" % (tc_id, str(e)))
                    elif flow_type == 'late':
                        self.safe_click((By.XPATH, "//button[contains(text(), 'Add submission')]"))
                        self._open_file_picker_and_upload(basePath, file_name)
                        self.safe_click((By.ID, "id_submitbutton"))
                        self._safe_navigate(assignment_url)

                        try:
                            time_cell = self.wait.until(EC.presence_of_element_located(
                                (By.XPATH, "//th[contains(.,'Time remaining')]/following-sibling::td")))
                            self.assertRegex(time_cell.text,
                                             r"^[\s\S]*%s[\s\S]*$" % re.escape(expected))
                        except AssertionError as e:
                            self.verificationErrors.append("Test %s Failed: %s" % (tc_id, str(e)))

                        try:
                            self.safe_click((By.XPATH, "//button[contains(text(), 'Remove submission')]"))
                            self.safe_click((By.XPATH, "//button[contains(text(), 'Continue')]"))
                        except Exception:
                            pass

                    elif flow_type == 'edit':
                        if driver.find_elements(By.XPATH,
                                "//button[contains(text(), 'Add submission')]"):
                            self._create_temp_submission(assignment_url, basePath, file_name)

                        self.safe_click((By.XPATH, "//button[contains(.,'Edit submission')]"))
                        self._safe_navigate(edit_url)

                        self.wait.until(EC.presence_of_element_located(
                            (By.XPATH, "//div[contains(@class,'fp-filename-field')]")))
                        self.safe_click((By.XPATH, "//div[contains(@class,'fp-filename')]"))

                        self.wait.until(EC.presence_of_element_located(
                            (By.XPATH, "//button[contains(@class,'fp-file-delete')]")))
                        self.safe_click((By.XPATH, "//button[contains(@class,'fp-file-delete')]"))
                        time.sleep(1)

                        self.wait.until(EC.presence_of_element_located(
                            (By.XPATH, "//button[normalize-space()='Yes']")))
                        self.safe_click((By.XPATH, "//button[normalize-space()='Yes']"))
                        time.sleep(1)

                        self._open_file_picker_and_upload(basePath, file_name)
                        self.safe_click((By.ID, "id_submitbutton"))
                        self._safe_navigate(assignment_url)

                        status_cell = self.wait.until(EC.presence_of_element_located(
                            (By.XPATH, "//th[contains(.,'Submission status')]/following-sibling::td")))
                        try:
                            self.assertIn(expected, status_cell.text)
                        except AssertionError as e:
                            self.verificationErrors.append("Test %s Failed: %s" % (tc_id, str(e)))

                        self.safe_click((By.XPATH, "//button[contains(text(), 'Remove submission')]"))
                        self.safe_click((By.XPATH, "//button[contains(text(), 'Continue')]"))


                    elif flow_type == 'remove':
                        if driver.find_elements(By.XPATH,
                                "//button[contains(text(), 'Add submission')]"):
                            self._create_temp_submission(assignment_url, basePath, "500KB.pdf")

                        self.safe_click((By.XPATH, "//button[contains(text(), 'Remove submission')]"))
                        self.wait.until(EC.presence_of_element_located(
                            (By.XPATH, "//button[contains(.,'Continue')]")))
                        self.safe_click((By.XPATH, "//button[contains(.,'Continue')]"))
                        self._safe_navigate(assignment_url)

                        status_cell = self.wait.until(EC.presence_of_element_located(
                            (By.XPATH, "//th[contains(.,'Submission status')]/following-sibling::td")))
                        try:
                            self.assertIn(expected, status_cell.text)
                        except AssertionError as e:
                            self.verificationErrors.append("Test %s Failed: %s" % (tc_id, str(e)))

                    else:
                        print("  [SKIP] Unknown flow_type '%s'" % flow_type)

       
                    tc_errors = [e for e in self.verificationErrors if tc_id in e]
                    print("  [%s] %s" % ("FAIL" if tc_errors else "PASS", tc_id))

                except Exception as e:
                    err = "Test %s ERROR: %s: %s" % (tc_id, type(e).__name__, str(e))
                    self.verificationErrors.append(err)
                    print("  [ERROR] %s" % err)
                    self._safe_navigate(assignment_url)  


    def tearDown(self):
        self.driver.quit()
        if self.verificationErrors:
            print("\n========== SUMMARY OF FAILURES ==========")
            for err in self.verificationErrors:
                print("  " + err)
            print("=========================================")
        self.assertEqual([], self.verificationErrors)


if __name__ == "__main__":
    unittest.main()
