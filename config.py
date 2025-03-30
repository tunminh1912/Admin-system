import os
SECRET_KEY = os.urandom(24)  # Tạo khóa ngẫu nhiên
GANACHE_RPC_URL = "http://127.0.0.1:7545"
SESSION_TYPE = "filesystem"
