# 华为云上传文件到OBS
HUAWEI_OBS_AUTH = {
    "access_key_id": "",
    "secret_access_key": "",
    "server": ""
}

DINGDING_ALERT_AUTH = {
    'dingding_token': '',
    'dingding_secret': ''
}

UPLOAD_DIR = "/nfs/data/apk"
FINISH_DIR = "finish"
ERROR_DIR = "error"

LOG_DIR = "/tmp"
LOG_FILE = "obs.log"
LOG_LEVEL = "INFO"

__all__ = [
    HUAWEI_OBS_AUTH,
    UPLOAD_DIR,
    ERROR_DIR,
    FINISH_DIR,
    DINGDING_ALERT_AUTH
]
