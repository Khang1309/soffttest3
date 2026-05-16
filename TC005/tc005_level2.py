# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
import unittest, time, csv, os, re, json, warnings
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BY_MAP = {
    "ID":    By.ID,
    "XPATH": By.XPATH,
    "CSS":   By.CSS_SELECTOR,
    "NAME":  By.NAME,
    "CLASS": By.CLASS_NAME,
    "TAG":   By.TAG_NAME,
    "LINK":  By.LINK_TEXT,
}

def _resolve(locator_dict, **fmt_kwargs):
    """Turn a {"by": "XPATH", "value": "..."} dict into a Selenium (By.*, value) tuple."""
    by  = BY_MAP[locator_dict["by"]]
    val = locator_dict["value"]
    if fmt_kwargs:
        val = val.format(**fmt_kwargs)
    return (by, val)

class T_005_L2(unittest.TestCase):
    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)

        cfg_path = os.path.join(os.path.dirname(__file__) or '.', 'locators.json')
        with open(cfg_path, 'r', encoding='utf-8') as f:
            self.cfg = json.load(f)

        config = self.cfg["config"]
        self.driver = webdriver.Edge(
            executable_path=config["driver_path"],
            service_log_path=os.devnull
        )
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, config["wait_timeout"])
        self.verificationErrors = []
        self.current_tc = "(not started)"

        self.urls      = self.cfg["urls"]
        self.creds     = self.cfg["credentials"]
        self.loc       = self.cfg["locators"]
        self.csv_file  = os.path.join(os.path.dirname(__file__) or '.', config["test_data_csv"])

    def safe_click(self, locator_tuple):
        element = self.wait.until(EC.presence_of_element_located(locator_tuple))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.4)
        clickable = self.wait.until(EC.element_to_be_clickable(locator_tuple))
        try:
            clickable.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", clickable)

    def is_element_present(self, locator_tuple):
        try:
            self.driver.find_element(*locator_tuple)
            return True
        except Exception:
            return False

    def _safe_navigate(self, url):
        try:
            self.driver.execute_script("window.onbeforeunload = null;")
        except Exception:
            pass
        self.driver.get(url)
        time.sleep(1)
        try:
            self.driver.switch_to.alert().accept()
        except Exception:
            pass

    def _ensure_logged_in(self):
        indicator = _resolve(self.loc["session_check"]["logged_in_indicator"])
        for attempt in range(1, 4):
            if self.is_element_present(indicator):
                return
            
            try:
                self.driver.delete_all_cookies()
            except Exception:
                pass

            self._safe_navigate(self.urls["login"])
            time.sleep(2)
            try:
                un = self.wait.until(EC.element_to_be_clickable(_resolve(self.loc["login"]["username_field"])))
                un.clear()
                un.send_keys(self.creds["username"])
                time.sleep(1.5)

                pw = self.wait.until(EC.element_to_be_clickable(_resolve(self.loc["login"]["password_field"])))
                pw.clear()
                pw.send_keys(self.creds["password"])
                time.sleep(1.5)

                self.safe_click(_resolve(self.loc["login"]["login_button"]))
                time.sleep(3)
            except Exception:
                pass
        if not self.is_element_present(indicator):
            raise RuntimeError("Could not log in after 3 attempts")

    def test_005(self):
        driver = self.driver
        quiz = self.loc["quiz"]
        
        quiz_url = self.urls["quiz_edit"].format(cmid="1160")

        # Initial login
        driver.get(self.urls["login"])
        time.sleep(2)

        un = self.wait.until(EC.element_to_be_clickable(_resolve(self.loc["login"]["username_field"])))
        un.clear()
        un.send_keys(self.creds["username"])
        
        pw = self.wait.until(EC.element_to_be_clickable(_resolve(self.loc["login"]["password_field"])))
        pw.clear()
        pw.send_keys(self.creds["password"])
        
        self.safe_click(_resolve(self.loc["login"]["login_button"]))
        time.sleep(3)

        with open(self.csv_file, mode='r', encoding='utf-8-sig') as f:
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
                        self._safe_navigate(self.urls["login"])
                        un = self.wait.until(EC.presence_of_element_located(_resolve(self.loc["login"]["username_field"])))
                        un.clear()
                        un.send_keys(self.creds["username"])
                        
                        pw = driver.find_element(*_resolve(self.loc["login"]["password_field"]))
                        pw.clear()
                        pw.send_keys(self.creds["password"])
                        
                        t_start = time.time()
                        self.safe_click(_resolve(self.loc["login"]["login_button"]))
                        
                        indicator = _resolve(self.loc["session_check"]["logged_in_indicator"])
                        self.wait.until(EC.presence_of_element_located(indicator))
                        
                        t_elapsed = time.time() - t_start
                        threshold = float(expected)
                        try:
                            self.assertLessEqual(t_elapsed, threshold, "Login took %.2fs, threshold is %.0fs" % (t_elapsed, threshold))
                        except AssertionError as e:
                            self.verificationErrors.append("Test %s Failed: %s" % (tc_id, str(e)))
                    except Exception as e:
                        err = "Test %s ERROR: %s: %s" % (tc_id, type(e).__name__, str(e))
                        self.verificationErrors.append(err)
                        print("  [ERROR] %s" % err)
                        
                    tc_errors = [e for e in self.verificationErrors if tc_id in e]
                    print("  [%s] %s" % ("FAIL" if tc_errors else "PASS", tc_id))
                    continue

                self._safe_navigate(quiz_url)

                try:
                    self._ensure_logged_in()
                    self._safe_navigate(quiz_url)
                except Exception as e:
                    err = "Test %s ERROR: %s: %s" % (tc_id, type(e).__name__, str(e))
                    self.verificationErrors.append(err)
                    print("  [ERROR] %s" % err)
                    continue

                try:
                    if flow_type in ['normal', 'error_msg', 'performance']:
                        t_start = time.time()
                        
                        self.safe_click(_resolve(quiz["add_menu"]))
                        self.safe_click(_resolve(quiz["add_new_question"]))
                        self.safe_click(_resolve(quiz["true_false_radio"]))
                        self.safe_click(_resolve(quiz["add_question_btn"]))
                        
                        self.wait.until(EC.presence_of_element_located(_resolve(quiz["question_name"])))
                        
                        if question_name:
                            driver.find_element(*_resolve(quiz["question_name"])).send_keys(question_name)
                            
                        if question_text:
                            iframe = self.wait.until(EC.presence_of_element_located(_resolve(quiz["question_text_iframe"])))
                            driver.switch_to.frame(iframe)
                            driver.find_element(*_resolve(quiz["question_text_body"])).send_keys(question_text)
                            driver.switch_to.default_content()
                            
                        if default_mark:
                            mark_field = driver.find_element(*_resolve(quiz["default_mark"]))
                            mark_field.clear()
                            mark_field.send_keys(default_mark)
                            
                        if id_number:
                            driver.find_element(*_resolve(quiz["id_number"])).send_keys(id_number)
                            
                        self.safe_click(_resolve(quiz["save_btn"]))
                        
                        if flow_type in ['normal', 'error_msg']:
                            try:
                                body = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                                self.assertIn(expected, body.text)
                            except Exception as e:
                                self.verificationErrors.append("Test %s Failed: Expected text '%s' not found. %s" % (tc_id, expected, str(e)))
                                
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
                                        print("  [WARNING] Could not clean up question: %s" % str(ex))
                                
                        elif flow_type == 'performance':
                            question_list = self.wait.until(EC.presence_of_element_located(_resolve(quiz["question_list"])))
                            t_elapsed = time.time() - t_start
                            threshold = float(expected)
                            try:
                                self.assertLessEqual(t_elapsed, threshold, "Execution took %.2fs, threshold is %.0fs" % (t_elapsed, threshold))
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
