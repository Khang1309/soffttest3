# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
import unittest, time, re

class Teacher(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome(executable_path=r'')
        self.driver.implicitly_wait(30)
        self.base_url = "https://www.google.com/"
        self.verificationErrors = []
        self.accept_next_alert = True
    
    def test_teacher(self):
        driver = self.driver
        driver.get(self.base_url + "chrome://newtab/")
        driver.get("https://school.moodledemo.net/")
        driver.find_element_by_link_text(u"Đăng nhập").click()
        driver.find_element_by_id("username").click()
        driver.find_element_by_id("username").click()
        driver.find_element_by_id("username").clear()
        driver.find_element_by_id("username").send_keys("")
        driver.find_element_by_id("region-main").click()
        driver.find_element_by_id("username").click()
        driver.find_element_by_id("username").clear()
        driver.find_element_by_id("username").send_keys("teacher")
        driver.find_element_by_id("password").click()
        driver.find_element_by_id("password").clear()
        driver.find_element_by_id("password").send_keys("moodle26")
        driver.find_element_by_id("loginbtn").click()
        driver.find_element_by_xpath("//div[@id='usernavigation']/form/div/div/input").click()
        driver.find_element_by_xpath("(.//*[normalize-space(text()) and normalize-space(.)='Digital Literacy'])[4]/following::span[1]").click()
        driver.find_element_by_xpath("//li[@id='module-789']/div[2]/div[2]/div[2]/div/div/span/a").click()
        driver.find_element_by_link_text("Settings").click()
        driver.find_element_by_id("collapseElement-8").click()
        driver.find_element_by_xpath("(.//*[normalize-space(text()) and normalize-space(.)='Require password'])[1]/following::em[1]").click()
        driver.find_element_by_id("id_quizpassword").clear()
        driver.find_element_by_id("id_quizpassword").send_keys("123")
        driver.find_element_by_id("id_submitbutton").click()
        #ERROR: Caught exception [ERROR: Unsupported command [removeSelection | id=id_tags | label=Advanced]]
        #ERROR: Caught exception [ERROR: Unsupported command [removeSelection | id=id_tags | label=Basic]]
        #ERROR: Caught exception [ERROR: Unsupported command [removeSelection | id=id_tags | label=Intermediate]]
    
    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException as e: return False
        return True
    
    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException as e: return False
        return True
    
    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True
    
    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
