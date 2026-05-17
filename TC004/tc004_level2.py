# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
import unittest, time, csv, os, json, warnings
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
    by  = BY_MAP[locator_dict["by"]]
    val = locator_dict["value"]
    if fmt_kwargs:
        val = val.format(**fmt_kwargs)
    return (by, val)

class T_004_L2(unittest.TestCase):
    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)
        cfg_path = os.path.join(os.path.dirname(__file__) or '.', 'locators.json')
        with open(cfg_path, 'r', encoding='utf-8') as f:
            self.cfg = json.load(f)

        self.driver = webdriver.Edge(
            executable_path=self.cfg["config"]["driver_path"],
            service_log_path=os.devnull
        )
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, self.cfg["config"]["wait_timeout"])
        self.verificationErrors = []

    def safe_click(self, locator_tuple):
        element = self.wait.until(EC.presence_of_element_located(locator_tuple))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.5)
        element.click()

    def test_add_quiz_level2(self):
        driver = self.driver
        loc_login = self.cfg["locators"]["login"]
        loc_quiz = self.cfg["locators"]["add_quiz"]
        
        # 1. Login
        driver.get(self.cfg["urls"]["login"])
        driver.find_element(*_resolve(loc_login["username_field"])).send_keys(self.cfg["credentials"]["username"])
        driver.find_element(*_resolve(loc_login["password_field"])).send_keys(self.cfg["credentials"]["password"])
        driver.find_element(*_resolve(loc_login["login_button"])).click()
        
        # Wait for login
        self.wait.until(EC.presence_of_element_located(_resolve(self.cfg["locators"]["session_check"]["logged_in_indicator"])))

        # URL thay bằng Add Quiz link của bạn (có thể thêm vào json)
        ADD_QUIZ_URL = "https://school.moodledemo.net/course/modedit.php?add=quiz&type=&course=59&section=1&return=0&sr=0"

        # 2. Đọc Data và chạy Test
        with open('test_data_tc004_level2.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tc_id = row['TC_ID']
                q_name = row['QuizName']
                t_limit = row['TimeLimit']
                grade = row['Grade']
                expected = row['ExpectedResult']
                flow_type = row['FlowType']

                print(f"Executing {tc_id}...")
                try:
                    t_start = time.time()
                    driver.get(ADD_QUIZ_URL)
                    
                    # Tên Quiz
                    name_input = self.wait.until(EC.presence_of_element_located(_resolve(loc_quiz["quiz_name"])))
                    name_input.clear()
                    if q_name: name_input.send_keys(q_name)

                    # Timing
                    self.safe_click(_resolve(loc_quiz["section_timing"]))
                    enable_time_cb = driver.find_element(*_resolve(loc_quiz["enable_time_cb"]))
                    if not enable_time_cb.is_selected():
                        self.driver.execute_script("arguments[0].click();", enable_time_cb)
                        time.sleep(0.5)
                        
                    timelimit_input = driver.find_element(*_resolve(loc_quiz["time_limit_input"]))
                    timelimit_input.clear()
                    if t_limit: timelimit_input.send_keys(t_limit)

                    # Grade
                    self.safe_click(_resolve(loc_quiz["section_grade"]))
                    grade_input = driver.find_element(*_resolve(loc_quiz["grade_pass_input"]))
                    grade_input.clear()
                    if grade: grade_input.send_keys(grade)

                    # Lưu
                    self.safe_click(_resolve(loc_quiz["save_btn"]))

                    # Kiểm tra kết quả
                    if flow_type == "error_msg":
                        err_elem = self.wait.until(EC.presence_of_element_located(_resolve(loc_quiz["error_message"])))
                        actual_err = err_elem.text
                        try:
                            self.assertIn(expected, actual_err)
                        except AssertionError as e:
                            self.verificationErrors.append(f"Test {tc_id} Failed: {str(e)}")

                    elif flow_type == "success" or flow_type == "performance":
                        self.wait.until(lambda d: "view.php" in d.current_url or "course" in d.current_url)
                        if flow_type == "performance":
                            t_elapsed = time.time() - t_start
                            try:
                                self.assertLessEqual(t_elapsed, float(expected))
                            except AssertionError as e:
                                self.verificationErrors.append(f"Test {tc_id} NFT Failed: {str(e)}")

                    tc_errors = [e for e in self.verificationErrors if tc_id in e]
                    print(f"  [{'FAIL' if tc_errors else 'PASS'}] {tc_id}")

                except Exception as e:
                    err = f"Test {tc_id} ERROR: {type(e).__name__}: {str(e)}"
                    self.verificationErrors.append(err)
                    print(f"  [ERROR] {err}")

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