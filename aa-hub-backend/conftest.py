import os
import sys

# Thêm thư mục gốc dự án (nơi chứa folder "app/") vào sys.path
# để "from app.xxx import ..." chạy được dù pytest được gọi từ đâu.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
