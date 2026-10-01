"""
录制文件加载派发器。

唯一入口: load(path) -> Recording
读文件头 VERSION: 决定用 3.0 还是 legacy。
"""
import os

from shared import record_format, record_format_legacy


def peek_version(path) -> int:
    with open(path, "r") as f:
        for line in f:
            if line.startswith("VERSION:"):
                try:
                    return int(line.split(":", 1)[1].strip())
                except ValueError:
                    return 0
            if not line.startswith("#") and line.strip():
                # 遇到第一个非注释非空行还不是 VERSION，说明文件格式异常
                return 0
    return 0


def load(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    version = peek_version(path)
    if version >= 3:
        return record_format.load(path)
    elif version in (1, 2):
        return record_format_legacy.load(path)
    else:
        raise ValueError(f"无法识别的录制文件版本: {version}")