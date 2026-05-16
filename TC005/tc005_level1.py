# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
import unittest, time, csv, os, re, warnings
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

LOGIN_URL      = "https://school.moodledemo.net/login/index.php"
USERNAME       = "teacher"
PASSWORD       = "moodle26"
BASE_QUIZ_URL  = "https://school.moodledemo.net/mod/quiz/edit.php"

class T_005(unittest.TestCase):
    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)
        self.driver = webdriver.Edge(
            executable_path=r'd:\STUDY\HK252\Testing\proj3\softtest3\TC002\msedgedriver.exe',
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

    def test_005(self):
        driver = self.driver
        # cmid=1160 as per the image
        quiz_url = f"{BASE_QUIZ_URL}?cmid=1160"

        # --- 1. Initial login ---
        driver.get(LOGIN_URL)
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys(USERNAME)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        self.safe_click((By.ID, "loginbtn"))
        time.sleep(3)

        csv_file_path = os.path.join(os.path.dirname(__file__), 'test_data_level1.csv')
        with open(csv_file_path, mode='r', encoding='utf-8-sig') as f:
            for row in csv.reader(f):
                if row and row[0] == 'TC_ID':
                    continue
                if not row or not any(row):
                    break

                tc_id         = row[0]
                question_name = row[1]
                question_text = row[2]
                default_mark  = row[3]
                id_number     = row[4]
                expected      = row[5]
                flow_type     = row[6]
                self.current_tc = tc_id

                if flow_type == 'performance_login':
                    try:
                        self.driver.delete_all_cookies()
                        self._safe_navigate(LOGIN_URL)
                        self.wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(USERNAME)
                        driver.find_element(By.ID, "password").send_keys(PASSWORD)
                        
                        t_start = time.time()
                        self.safe_click((By.ID, "loginbtn"))
                        
                        self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'usermenu')] | //a[contains(@href,'logout')]")))
                        t_elapsed = time.time() - t_start
                        threshold = float(expected)
                        try:
                            self.assertLessEqual(t_elapsed, threshold, f"Login took {t_elapsed:.2f}s, threshold is {threshold:.0f}s")
                        except AssertionError as e:
                            self.verificationErrors.append(f"Test {tc_id} Failed: {str(e)}")
                    except Exception as e:
                        err = f"Test {tc_id} ERROR: {type(e).__name__}: {str(e)}"
                        self.verificationErrors.append(err)
                        print(f"  [ERROR] {err}")
                        
                    tc_errors = [e for e in self.verificationErrors if tc_id in e]
                    print(f"  [{'FAIL' if tc_errors else 'PASS'}] {tc_id}")
                    continue

                self._safe_navigate(quiz_url)

                try:
                    self._ensure_logged_in()
                    self._safe_navigate(quiz_url)
                except Exception as e:
                    err = f"Test {tc_id} ERROR: {type(e).__name__}: {str(e)}"
                    self.verificationErrors.append(err)
                    print(f"  [ERROR] {err}")
                    continue

                try:
                    if flow_type in ['normal', 'error_msg', 'performance']:
                        t_start = time.time()
                        
                        # Click Add -> a new question
                        self.safe_click((By.XPATH, "//span[contains(text(), 'Add')]"))
                        self.safe_click((By.XPATH, "//span[contains(text(), 'a new question')]"))
                        
                        # Select True/False and submit
                        self.safe_click((By.XPATH, "//label[contains(normalize-space(), 'True/False')]//input[@type='radio']"))
                        self.safe_click((By.XPATH, "//input[@value='Add' and @type='submit']"))
                        
                        # Fill in the form
                        self.wait.until(EC.presence_of_element_located((By.ID, "id_name")))
                        if question_name:
                            driver.find_element(By.ID, "id_name").send_keys(question_name)
                        
                        if question_text:
                            # Switch to TinyMCE iframe
                            iframe = self.wait.until(EC.presence_of_element_located((By.XPATH, "//iframe[contains(@class, 'tox-edit-area__iframe')]")))
                            driver.switch_to.frame(iframe)
                            driver.find_element(By.ID, "tinymce").send_keys(question_text)
                            driver.switch_to.default_content()
                        
                        if default_mark:
                            mark_field = driver.find_element(By.ID, "id_defaultmark")
                            mark_field.clear()
                            mark_field.send_keys(default_mark)
                            
                        if id_number:
                            driver.find_element(By.ID, "id_idnumber").send_keys(id_number)
                            
                        self.safe_click((By.ID, "id_submitbutton"))
                        
                        if flow_type in ['normal', 'error_msg']:
                            # Verify expected text appears anywhere on the page
                            try:
                                body = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                                self.assertIn(expected, body.text)
                            except Exception as e:
                                self.verificationErrors.append(f"Test {tc_id} Failed: Expected text '{expected}' not found. {str(e)}")
                                
                            # Clean up question if created successfully
                            if "mod/quiz/edit.php" in driver.current_url:
                                remove_buttons = driver.find_elements(By.XPATH, "//a[@data-action='remove' or @title='Remove' or @title='Delete' or contains(@class, 'editing_remove')] | //i[contains(@class, 'fa-trash')]/parent::a")
                                if remove_buttons:
                                    try:
                                        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", remove_buttons[-1])
                                        time.sleep(0.5)
                                        self.driver.execute_script("arguments[0].click();", remove_buttons[-1])
                                        time.sleep(1)
                                        try:
                                            driver.switch_to.alert.accept()
                                        except:
                                            pass
                                        yes_btns = driver.find_elements(By.XPATH, "//button[contains(translate(normalize-space(), 'YES', 'yes'), 'yes')]")
                                        for btn in yes_btns:
                                            if btn.is_displayed():
                                                self.driver.execute_script("arguments[0].click();", btn)
                                                time.sleep(1)
                                                break
                                        time.sleep(2)
                                    except Exception as ex:
                                        print(f"  [WARNING] Could not clean up question: {str(ex)}")
                                
                        elif flow_type == 'performance':
                            question_list = self.wait.until(EC.presence_of_element_located((By.XPATH, "//ul[contains(@class, 'slots')]")))
                            t_elapsed = time.time() - t_start
                            threshold = float(expected)
                            try:
                                self.assertLessEqual(t_elapsed, threshold, f"Execution took {t_elapsed:.2f}s, threshold is {threshold:.0f}s")
                            except AssertionError as e:
                                self.verificationErrors.append(f"Test {tc_id} Failed: {str(e)}")
                                
                    else:
                        print(f"  [SKIP] Unknown flow_type '{flow_type}'")

                    tc_errors = [e for e in self.verificationErrors if tc_id in e]
                    print(f"  [{'FAIL' if tc_errors else 'PASS'}] {tc_id}")

                except Exception as e:
                    err = f"Test {tc_id} ERROR: {type(e).__name__}: {str(e)}"
                    self.verificationErrors.append(err)
                    print(f"  [ERROR] {err}")
                    self._safe_navigate(quiz_url)

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
