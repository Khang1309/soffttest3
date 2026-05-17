# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
import unittest, time, csv, os, warnings
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

LOGIN_URL      = "https://school.moodledemo.net/login/index.php"
USERNAME       = "teacher"
PASSWORD       = "moodle26"
# URL để vào thẳng trang Add Quiz (Thay course=59 bằng ID course thực tế)
ADD_QUIZ_URL   = "https://school.moodledemo.net/course/modedit.php?add=quiz&type=&course=59&section=1&return=0&sr=0"

class T_004(unittest.TestCase):
    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)
        # Sử dụng đúng path EdgeDriver như TC005 của nhóm bạn
        self.driver = webdriver.Edge(
            executable_path=r'd:\STUDY\HK252\Testing\proj3\softtest3\TC002\msedgedriver.exe',
            service_log_path=os.devnull
        )
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 15)
        self.verificationErrors = []

    def safe_click(self, locator):
        """Scroll into view and click; JS fallback for overlay-blocked clicks."""
        element = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.5)
        element.click()

    def test_add_quiz_level1(self):
        driver = self.driver
        
        # 1. Login
        driver.get(LOGIN_URL)
        driver.find_element(By.ID, "username").send_keys(USERNAME)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.ID, "loginbtn").click()
        
        # Đợi login xong
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'usermenu')] | //span[contains(@class,'userbutton')]")))

        # 2. Đọc Data và chạy Test
        with open('test_data_tc004_level1.csv', 'r', encoding='utf-8') as f:
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
                    # Bắt đầu tính giờ cho NFT
                    t_start = time.time()
                    
                    # Vào thẳng trang Add Quiz
                    driver.get(ADD_QUIZ_URL)
                    
                    # Điền Name
                    name_input = self.wait.until(EC.presence_of_element_located((By.ID, "id_name")))
                    name_input.clear()
                    if q_name:
                        name_input.send_keys(q_name)

                    # Mở Timing và điền Time limit
                    self.safe_click((By.XPATH, "//a[contains(text(), 'Timing')]"))
                    enable_time_cb = driver.find_element(By.ID, "id_timelimit_enabled")
                    if not enable_time_cb.is_selected():
                        self.driver.execute_script("arguments[0].click();", enable_time_cb)
                        time.sleep(0.5)
                        
                    timelimit_input = driver.find_element(By.ID, "id_timelimit_number")
                    timelimit_input.clear()
                    if t_limit:
                        timelimit_input.send_keys(t_limit)

                    # Mở Grade và điền Grade to pass
                    self.safe_click((By.XPATH, "//a[contains(text(), 'Grade')]"))
                    grade_input = driver.find_element(By.ID, "id_gradepass")
                    grade_input.clear()
                    if grade:
                        grade_input.send_keys(grade)

                    # Bấm Save
                    self.safe_click((By.ID, "id_submitbutton"))

                    # Xử lý kết quả theo Flow Type
                    if flow_type == "error_msg":
                        # Chờ thông báo lỗi xuất hiện
                        error_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.invalid-feedback, span.error")))
                        actual_error = error_element.text
                        try:
                            self.assertIn(expected, actual_error, f"Expected '{expected}' but got '{actual_error}'")
                        except AssertionError as e:
                            self.verificationErrors.append(f"Test {tc_id} Failed: {str(e)}")

                    elif flow_type == "success":
                        # Đợi URL chuyển về trang course hoặc view
                        try:
                            self.wait.until(lambda d: "view.php" in d.current_url or "course" in d.current_url)
                        except Exception as e:
                            self.verificationErrors.append(f"Test {tc_id} Failed: Did not redirect to success page")

                    elif flow_type == "performance":
                        # Đợi chuyển trang thành công và tính giờ
                        self.wait.until(lambda d: "view.php" in d.current_url or "course" in d.current_url)
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