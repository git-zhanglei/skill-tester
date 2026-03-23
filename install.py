#!/usr/bin/env python3
"""
安装 Skill Certifier
安装设置脚本
"""

import os
import sys
import shutil
from pathlib import Path


def install():
    """安装 skill-certifier 到用户的 skill 目录"""
    
    # 确定安装位置
    home = Path.home()
    default_install_dir = home / '.openclaw' / 'workspace' / 'skills' / 'skill-certifier'
    
    # 检查是否已安装
    if default_install_dir.exists():
        print(f"⚠️  skill-certifier 已安装在 {default_install_dir}")
        response = input("覆盖? (y/N): ")
        if response.lower() != 'y':
            print("安装已取消。")
            return
        shutil.rmtree(default_install_dir)
    
    # 复制文件
    source_dir = Path(__file__).parent
    shutil.copytree(source_dir, default_install_dir)
    
    print(f"✅ skill-certifier 已安装到 {default_install_dir}")
    
    # 创建 CLI 符号链接（可选）
    bin_dir = home / '.local' / 'bin'
    if bin_dir.exists() or input("在 ~/.local/bin 创建 CLI 符号链接? (y/N): ").lower() == 'y':
        bin_dir.mkdir(parents=True, exist_ok=True)
        symlink_path = bin_dir / 'skill-certifier'
        
        if symlink_path.exists() or symlink_path.is_symlink():
            symlink_path.unlink()
        
        os.symlink(default_install_dir / 'skill-certifier', symlink_path)
        print(f"✅ CLI 符号链接已创建: {symlink_path}")
        print("   确保 ~/.local/bin 在你的 PATH 中")
    
    print("\n🎉 安装完成！")
    print("\n用法:")
    print("  测试skill ./my-skill/")
    print("  skill-certifier ./my-skill/ --parallel 8")


if __name__ == '__main__':
    install()