# Software Testing - Project 3: Data-Driven Automation Testing

**Feature Tested:** Student attempt quiz (Moodle System)
**Student Name:** [Tên của bạn]
**Student ID:** [MSSV]

## 1. Kiến trúc thư mục (Level 1)

Dự án áp dụng Data-Driven Testing (DDT) kết hợp với Data Preparation (Chuẩn bị dữ liệu đầu vào) để xử lý việc Moodle reset server mỗi giờ.

- `01_teacher_setup_quiz.py`: Kịch bản chuẩn bị dữ liệu (Pre-condition). Teacher sẽ tự động login, tạo mật khẩu cho quiz và xuất URL động ra file `quiz_url.txt`.
- `02_student_attempt_quiz.py`: Kịch bản kiểm thử chính (Execution). Áp dụng DDT để đọc URL từ file text, và duyệt qua các Test Cases trong file CSV.
- `level1_data.csv`: Nơi chứa dữ liệu đầu vào và Expected Results cho các kịch bản đúng/sai password.

## 2. Hướng dẫn chạy Script

**Yêu cầu hệ thống:** Python 2, thư viện Selenium (`pip install selenium`), Google Chrome.

- **Bước 1:** Mở Terminal, chạy lệnh: `python 01_teacher_setup_quiz.py`
  (Đợi trình duyệt tự động setup và đóng lại).
- **Bước 2:** Ngay sau đó, chạy lệnh: `python 02_student_attempt_quiz.py`
  (Hệ thống sẽ chạy vòng lặp 3 Test Cases và in kết quả Pass/Fail ra console).

## 3. Khó khăn mắc phải & Giải pháp kỹ thuật đã áp dụng

Trong quá trình chuyển đổi mã nguồn từ Katalon Recorder sang Python (WebDriver + unittest), tôi đã xử lý 2 rào cản kỹ thuật lớn của nền tảng Moodle:

1. **Dynamic IDs (ID động):** Katalon bắt các phần tử bằng ID sinh tự động của thư viện YUI (ví dụ: `yui_3_18_1_1_1779...` hoặc `single_button6a09...`). Code sẽ lập tức crash ở lần chạy thứ 2.
   _-> Giải pháp:_ Chuyển đổi toàn bộ bộ định vị (Locators) sang `By.XPATH` sử dụng cấu trúc tương đối và `contains(text())` để đảm bảo tính ổn định cao nhất.
2. **Lỗi Đăng xuất (Logout Flow):** Katalon không record được thao tác mở Dropdown Avatar và nhấn xác nhận Logout.
   _-> Giải pháp:_ Cập nhật Script điều hướng thẳng đến API `login/logout.php` và kết hợp thẻ `try-except` để bypass màn hình Confirm.

## Cấu trúc Level 2: Object Repository Architecture

Nhằm đáp ứng yêu cầu cao nhất của đồ án (Tách biệt hoàn toàn Element Locators ra khỏi mã nguồn), thư mục Level 2 bổ sung thêm:

- `level2_elements.csv`: Chứa danh sách các Web Elements (Button, TextBox) dưới dạng Dictionary Mapping (Name -> Type -> Locator).
- `03_student_level2_DDT.py`: Mã nguồn nâng cao. Được thiết kế một `Locator Parser` (hàm `load_elements()`) tự động convert String từ CSV sang hằng số của Selenium (`By.ID`, `By.XPATH`). Mã nguồn hiện tại hoàn toàn agnostic (mù) với cấu trúc HTML của trang Moodle, đáp ứng 100% tiêu chuẩn bảo trì của Framework Tự động hóa.
