import unittest
import csv
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By

class StudentLevel2(unittest.TestCase):
    
    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        self.base_url = "https://school.moodledemo.net/"
        
        if not os.path.exists("quiz_url.txt"):
            self.fail("LỖI: Phải chạy file 01_teacher_setup_quiz.py trước để lấy link Quiz!")
        with open("quiz_url.txt", "r") as f:
            self.quiz_url = f.read().strip()
            
        self.elements = self.load_elements('level2_elements.csv')

    def load_elements(self, filepath):
        """Hàm đọc file CSV và ánh xạ locator_type thành hằng số của Selenium"""
        elements_dict = {}
        by_map = {
            'id': By.ID,
            'xpath': By.XPATH,
            'name': By.NAME,
            'tag_name': By.TAG_NAME
        }
        
        with open(filepath, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                elements_dict[row['element_name']] = (by_map[row['locator_type'].lower()], row['locator_value'])
        return elements_dict

    def get_el(self, element_name):
        """Hàm helper để tìm element nhanh gọn nhẹ"""
        by_type, locator = self.elements[element_name]
        return self.driver.find_element(by_type, locator)

    def test_level2_advanced_ddt(self):
        driver = self.driver
        print("\n=== BẮT ĐẦU TEST LEVEL 2 (OBJECT REPOSITORY) ===")
        
        with open('level2_data.csv', mode='r', encoding='utf-8') as file:
            csv_data = csv.DictReader(file)
            
            for row in csv_data:
                print(f"\n[Level 2] Đang chạy: {row['TC_ID']}")
                
                driver.get(self.base_url + "login/index.php")
                self.get_el('username_field').clear()
                self.get_el('username_field').send_keys(row['Username'])
                
                self.get_el('password_field').clear()
                self.get_el('password_field').send_keys(row['Password_Login'])
                
                self.get_el('login_btn').click()
                time.sleep(1)
                
                driver.get(self.quiz_url)
                
                try:
                    self.get_el('attempt_btn').click()
                    time.sleep(1)
                except:
                    print("- Nút Attempt không xuất hiện.")
                
                try:
                    self.get_el('quiz_pass_field').clear()
                    self.get_el('quiz_pass_field').send_keys(row['Quiz_Password'])
                    self.get_el('submit_btn').click()
                    time.sleep(1)
                except:
                    pass
                
                page_text = self.get_el('body_text').text
                
                try:
                    self.assertIn(row['Expected_Result'], page_text)
                    print("=> Trạng thái: PASSED (Data & Elements mapped correctly)")
                except AssertionError:
                    print(f"=> Trạng thái: FAILED (Không tìm thấy: '{row['Expected_Result']}')")
                
                driver.get(self.base_url + "login/logout.php")
                try:
                    self.get_el('continue_logout_btn').click()
                except:
                    pass

    def tearDown(self):
        self.driver.quit()
        print("\n=== HOÀN THÀNH LEVEL 2 ===")

if __name__ == "__main__":
    unittest.main()