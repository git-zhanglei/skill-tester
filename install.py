#!/usr/bin/env python3
"""
安装 skill-tester 到 OpenClaw skills 目录
"""

import os
import sys
import shutil
from pathlib import Path


def install():
    home = Path.home()
    default_install_dir = home / '.openclaw' / 'workspace' / 'skills' / 'skill-tester'

    if default_install_dir.exists():
        print(f"⚠️  skill-tester 已安装在 {default_install_dir}")
        response = input("覆盖? (y/N): ").strip().lower()
        if response != 'y':
            print("安装已取消。")
            return
        shutil.rmtree(default_install_dir)

    source_dir = Path(__file__).parent
    shutil.copytree(source_dir, default_install_dir, ignore=shutil.ignore_patterns('.git'))

    print(f"✅ skill-tester 已安装到 {default_install_dir}")
    print("\n验证安装：")
    print(f"  python3 {default_install_dir}/verify.py")
    print("\n使用方式：")
    print("  测试skill ./my-skill/")
    print("  测试skill ./my-skill/ --yes --output-json")
    print("  测试skill ./my-skill/ --multi-model")


if __name__ == '__main__':
    install()
