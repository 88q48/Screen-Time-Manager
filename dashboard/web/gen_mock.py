# web/gen_mock.py
"""从 mock_data.py 生成网页用的 mock 数据。

改动 mock_data.py 后重新执行一次即可：
    python web/gen_mock.py
"""

import json
import os
import sys

# 让脚本能找到上一级目录里的 mock_data.py
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import mock_data  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock-data.js")


def main():
    data = mock_data.get_mock_response_from_events()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("// 本文件由 web/gen_mock.py 自动生成，请勿手改。\n")
        f.write("// 重新生成：python web/gen_mock.py\n")
        f.write("window.MOCK_DATA = ")
        f.write(json.dumps(data, ensure_ascii=False, indent=2))
        f.write(";\n")
    print(f"已生成 {OUT}")
    print(f"设备: {data['device_id']}  趋势天数: {len(data['trend'])}  应用数: {len(data['app_ranking'])}")


if __name__ == "__main__":
    main()
