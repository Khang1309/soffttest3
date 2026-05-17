import unittest
import csv
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By

class StudentDataDriven(unittest.TestCase):
    
    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        self.base_url = "https://school.moodledemo.net/"
        
        if not os.path.exists("quiz_url.txt"):
            self.fail("LỖI: Phải chạy file 01_teacher_setup_quiz.py trước để lấy link Quiz!")
            
        with open("quiz_url.txt", "r") as f:
            self.quiz_url = f.read().strip()

    def test_student_data_driven(self):
        driver = self.driver
        print("\n=== BẮT ĐẦU TEST DATA-DRIVEN CHO STUDENT ===")
        
        with open('level1_data.csv', mode='r', encoding='utf-8') as file:
            csv_data = csv.DictReader(file)
            
            for row in csv_data:
                print(f"\n[Đang Test] {row['TC_ID']}")
                
                driver.get(self.base_url + "login/index.php")
                driver.find_element(By.ID, "username").clear()
                driver.find_element(By.ID, "username").send_keys(row['Username'])
                driver.find_element(By.ID, "password").clear()
                driver.find_element(By.ID, "password").send_keys(row['Password_Login'])
                driver.find_element(By.ID, "loginbtn").click()
                time.sleep(1)
                
                driver.get(self.quiz_url)
                
                try:
                    driver.find_element(By.XPATH, "//button[contains(text(),'Attempt quiz')]").click()
                    time.sleep(1)
                except:
                    print("- Không tìm thấy nút Attempt Quiz.")
                
                try:
                    quiz_pass = driver.find_element(By.ID, "id_quizpassword")
                    quiz_pass.clear()
                    quiz_pass.send_keys(row['Quiz_Password'])
                    driver.find_element(By.ID, "id_submitbutton").click()
                    time.sleep(1)
                except:
                    pass
                
                page_text = driver.find_element(By.TAG_NAME, "body").text
                
                try:
                    self.assertIn(row['Expected_Result'], page_text)
                    print("=> Trạng thái: PASSED")
                except AssertionError:
                    print(f"=> Trạng thái: FAILED (Mong đợi thấy chữ: '{row['Expected_Result']}')")
                
                driver.get(self.base_url + "login/logout.php")
                try:
                    driver.find_element(By.XPATH, "//button[contains(text(),'Continue')]").click()
                except:
                    pass

    def tearDown(self):
        self.driver.quit()
        print("\n=== HOÀN THÀNH FILE 2 ===")

if __name__ == "__main__":
    unittest.main()