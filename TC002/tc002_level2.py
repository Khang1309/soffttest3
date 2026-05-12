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
    """Turn a {"by": "XPATH", "value": "..."} dict into a Selenium (By.*, value) tuple.
    Supports {placeholder} substitution via fmt_kwargs."""
    by  = BY_MAP[locator_dict["by"]]
    val = locator_dict["value"]
    if fmt_kwargs:
        val = val.format(**fmt_kwargs)
    return (by, val)


class T_003(unittest.TestCase):
    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)

        # Load external config
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

        # Shortcut references
        self.urls      = self.cfg["urls"]
        self.creds     = self.cfg["credentials"]
        self.loc       = self.cfg["locators"]
        self.basePath  = config["base_path"]
        self.csv_file  = config["test_data_csv"]
        self.perf_threshold = config["performance_threshold_seconds"]

    def safe_click(self, locator_tuple):
        """Scroll into view and click; JS fallback for overlay-blocked clicks."""
        element = self.wait.until(EC.presence_of_element_located(locator_tuple))
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", element)
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

    def _is_session_alive(self):
        """Return True if the browser window is still open and responsive."""
        try:
            _ = self.driver.window_handles
            _ = self.driver.current_url
            return True
        except Exception:
            return False

    def _safe_navigate(self, url):
        # Guard: if the window is gone, re-open it before navigating
        if not self._is_session_alive():
            try:
                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
            except Exception:
                pass
        try:
            self.driver.execute_script("window.onbeforeunload = null;")
        except Exception:
            pass
        self.driver.get(url)
        time.sleep(1)          # brief pause so the page starts loading cleanly
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

            # Re-authenticate silently
            self._safe_navigate(self.urls["login"])
            time.sleep(2)
            try:
                un = self.wait.until(EC.element_to_be_clickable(
                    _resolve(self.loc["login"]["username_field"])))
                un.clear()
                un.send_keys(self.creds["username"])
                time.sleep(1.5)          # let Moodle JS register the username

                pw = self.wait.until(EC.element_to_be_clickable(
                    _resolve(self.loc["login"]["password_field"])))
                pw.clear()
                pw.send_keys(self.creds["password"])
                time.sleep(1.5)          # let Moodle JS register the password

                self.safe_click(_resolve(self.loc["login"]["login_button"]))
                time.sleep(5)            # wait longer for Moodle to complete login
            except Exception:
                pass
        if not self.is_element_present(indicator):
            raise RuntimeError("Could not log in after 3 attempts")

    def _open_file_picker_and_upload(self, file_name):
        fp = self.loc["file_picker"]
        self.safe_click(_resolve(fp["add_file_link"]))
        time.sleep(1)
        self.safe_click(_resolve(fp["upload_a_file_link"]))
        full_path = os.path.join(self.basePath, file_name)
        file_input = self.wait.until(
            EC.presence_of_element_located(_resolve(fp["file_input"])))
        file_input.send_keys(full_path)
        time.sleep(3)
        self.safe_click(_resolve(fp["upload_this_file_btn"]))

    def _reset_submission(self, assignment_url):
        self._safe_navigate(assignment_url)
        sub = self.loc["submission"]
        try:
            if self.driver.find_elements(*_resolve(sub["remove_submission_btn"])):
                self.safe_click(_resolve(sub["remove_submission_btn"]))
                self.safe_click(_resolve(sub["continue_btn"]))
                self._safe_navigate(assignment_url)
        except Exception:
            pass

    def _create_temp_submission(self, assignment_url, file_name):
        sub = self.loc["submission"]
        self.safe_click(_resolve(sub["add_submission_btn"]))
        self._open_file_picker_and_upload(file_name)
        self.safe_click(_resolve(sub["save_btn"]))
        self._safe_navigate(assignment_url)

    # ------------------------------------------------------------------ #
    #  Main test                                                           #
    # ------------------------------------------------------------------ #

    def test_003(self):
        driver = self.driver
        sub = self.loc["submission"]
        fp  = self.loc["file_picker"]

        # --- 1. Initial login ---
        driver.get(self.urls["login"])
        time.sleep(2)           # wait for login page to fully render

        un = self.wait.until(EC.element_to_be_clickable(
            _resolve(self.loc["login"]["username_field"])))
        un.clear()
        un.send_keys(self.creds["username"])
        time.sleep(1.5)         # let Moodle JS register the username

        pw = self.wait.until(EC.element_to_be_clickable(
            _resolve(self.loc["login"]["password_field"])))
        pw.clear()
        pw.send_keys(self.creds["password"])
        time.sleep(1.5)         # let Moodle JS register the password

        self.safe_click(_resolve(self.loc["login"]["login_button"]))
        time.sleep(5)           # wait longer for Moodle post-login redirect

        with open(self.csv_file, mode='r', encoding='utf-8-sig') as f:
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

                assignment_url = self.urls["assignment_view"].format(
                    assignment_id=assignment_id)
                edit_url = self.urls["assignment_edit"].format(
                    assignment_id=assignment_id)

                # --- 2. Clean state ---
                if self._is_session_alive():
                    self._safe_navigate(assignment_url)
                    self._reset_submission(assignment_url)

                # --- 3. Re-authenticate if needed ---
                try:
                    self._ensure_logged_in()
                    self._safe_navigate(assignment_url)
                    if self._is_session_alive():
                        self._reset_submission(assignment_url)
                except Exception as e:
                    err = "Test %s ERROR: %s: %s" % (tc_id, type(e).__name__, str(e))
                    self.verificationErrors.append(err)
                    print("  [ERROR] %s" % err)
                    continue

                # --- 4. Execute flow ---
                try:

                    # ---- normal ----
                    if flow_type == 'normal':
                        self.safe_click(_resolve(sub["add_submission_btn"]))
                        self._open_file_picker_and_upload(file_name)
                        self.safe_click(_resolve(sub["save_btn"]))

                        status = self.wait.until(EC.presence_of_element_located(
                            _resolve(sub["submission_status_cell"])))
                        try:
                            self.assertIn(expected, status.text)
                        except AssertionError as e:
                            self.verificationErrors.append(
                                "Test %s Failed: %s" % (tc_id, str(e)))

                        self.safe_click(_resolve(sub["remove_submission_btn"]))
                        self.safe_click(_resolve(sub["continue_btn"]))

                    # ---- error_dialog ----
                    elif flow_type == 'error_dialog':
                        self.safe_click(_resolve(sub["add_submission_btn"]))
                        self._open_file_picker_and_upload(file_name)

                        dialog_loc = _resolve(
                            fp["error_dialog"], expected=expected)
                        try:
                            self.wait.until(EC.presence_of_element_located(dialog_loc))
                        except Exception as e:
                            self.verificationErrors.append(
                                "Test %s Failed: Dialog with text '%s' not found. %s" % (tc_id, expected, str(e)))

                        self._safe_navigate(assignment_url)

                    # ---- empty_submit ----
                    elif flow_type == 'empty_submit':
                        self.safe_click(_resolve(sub["add_submission_btn"]))
                        self.safe_click(_resolve(sub["save_btn"]))
                        time.sleep(1)

                        try:
                            alert = self.wait.until(EC.presence_of_element_located(
                                _resolve(sub["alert_div"])))
                            self.assertRegex(
                                alert.text,
                                r"^[\s\S]*%s[\s\S]*$" % re.escape(expected))
                        except AssertionError as e:
                            self.verificationErrors.append(
                                "Test %s Failed: %s" % (tc_id, str(e)))

                    # ---- late ----
                    elif flow_type == 'late':
                        self.safe_click(_resolve(sub["add_submission_btn"]))
                        self._open_file_picker_and_upload(file_name)
                        self.safe_click(_resolve(sub["save_btn"]))
                        self._safe_navigate(assignment_url)

                        try:
                            time_cell = self.wait.until(
                                EC.presence_of_element_located(
                                    _resolve(sub["time_remaining_cell"])))
                            self.assertRegex(
                                time_cell.text,
                                r"^[\s\S]*%s[\s\S]*$" % re.escape(expected))
                        except AssertionError as e:
                            self.verificationErrors.append(
                                "Test %s Failed: %s" % (tc_id, str(e)))

                        try:
                            self.safe_click(_resolve(sub["remove_submission_btn"]))
                            self.safe_click(_resolve(sub["continue_btn"]))
                        except Exception:
                            pass

                    # ---- edit ----
                    elif flow_type == 'edit':
                        if driver.find_elements(
                                *_resolve(sub["add_submission_btn"])):
                            self._create_temp_submission(
                                assignment_url, file_name)

                        self.safe_click(_resolve(sub["edit_submission_btn"]))
                        self._safe_navigate(edit_url)
                        time.sleep(2)           # Wait for file picker to load files

                        self.wait.until(EC.presence_of_element_located(
                            _resolve(fp["fp_filename"])))
                        self.safe_click(_resolve(fp["fp_filename"]))

                        self.wait.until(EC.presence_of_element_located(
                            _resolve(fp["fp_file_delete_btn"])))
                        self.safe_click(_resolve(fp["fp_file_delete_btn"]))
                        time.sleep(1)

                        self.wait.until(EC.presence_of_element_located(
                            _resolve(fp["confirm_yes_btn"])))
                        self.safe_click(_resolve(fp["confirm_yes_btn"]))
                        time.sleep(1)

                        self._open_file_picker_and_upload(file_name)
                        self.safe_click(_resolve(sub["save_btn"]))
                        self._safe_navigate(assignment_url)

                        status = self.wait.until(EC.presence_of_element_located(
                            _resolve(sub["submission_status_cell"])))
                        try:
                            self.assertIn(expected, status.text)
                        except AssertionError as e:
                            self.verificationErrors.append(
                                "Test %s Failed: %s" % (tc_id, str(e)))

                        self.safe_click(_resolve(sub["remove_submission_btn"]))
                        self.safe_click(_resolve(sub["continue_btn"]))

                    # ---- remove ----
                    elif flow_type == 'remove':
                        if driver.find_elements(
                                *_resolve(sub["add_submission_btn"])):
                            self._create_temp_submission(
                                assignment_url, "500KB.pdf")

                        self.safe_click(_resolve(sub["remove_submission_btn"]))
                        self.wait.until(EC.presence_of_element_located(
                            _resolve(sub["continue_btn"])))
                        self.safe_click(_resolve(sub["continue_btn"]))
                        self._safe_navigate(assignment_url)

                        status = self.wait.until(EC.presence_of_element_located(
                            _resolve(sub["submission_status_cell"])))
                        try:
                            self.assertIn(expected, status.text)
                        except AssertionError as e:
                            self.verificationErrors.append(
                                "Test %s Failed: %s" % (tc_id, str(e)))

                    # non functional test
                    elif flow_type == 'performance':
                        threshold = float(expected)

                        t_start = time.time()
                        self.safe_click(_resolve(sub["add_submission_btn"]))
                        self._open_file_picker_and_upload(file_name)
                        self.safe_click(_resolve(sub["save_btn"]))
                        # Wait for the submission status to confirm page loaded
                        self.wait.until(EC.presence_of_element_located(
                            _resolve(sub["submission_status_cell"])))
                        t_elapsed = time.time() - t_start

                        try:
                            self.assertLessEqual(
                                t_elapsed, threshold,
                                "Upload cycle took %.2fs, threshold is %.0fs"
                                % (t_elapsed, threshold))
                        except AssertionError as e:
                            self.verificationErrors.append(
                                "Test %s Failed: %s" % (tc_id, str(e)))

                        # Cleanup
                        self.safe_click(_resolve(sub["remove_submission_btn"]))
                        self.safe_click(_resolve(sub["continue_btn"]))

                    else:
                        print("  [SKIP] Unknown flow_type '%s'" % flow_type)

                    # per-TC result
                    tc_errors = [e for e in self.verificationErrors if tc_id in e]
                    print("  [%s] %s" % ("FAIL" if tc_errors else "PASS", tc_id))

                except Exception as e:
                    err = "Test %s ERROR: %s: %s" % (
                        tc_id, type(e).__name__, str(e))
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
