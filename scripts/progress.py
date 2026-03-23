#!/usr/bin/env python3
"""
进度报告器 - 测试期间显示实时进度
"""

import sys
import time
from typing import Optional


class ProgressReporter:
    """测试执行期间报告进度"""
    
    def __init__(self, total: int, description: str = "测试中"):
        self.total = total
        self.description = description
        self.current = 0
        self.start_time = time.time()
        self.last_update = 0
    
    def update(self, increment: int = 1, message: Optional[str] = None):
        """更新进度"""
        self.current += increment
        
        # 限制更新频率（每秒最多 10 次）
        now = time.time()
        if now - self.last_update < 0.1 and self.current < self.total:
            return
        
        self.last_update = now
        
        # 计算进度
        percent = (self.current / self.total) * 100
        elapsed = now - self.start_time
        
        # 估计剩余时间
        if self.current > 0:
            rate = elapsed / self.current
            remaining = rate * (self.total - self.current)
            eta = f"预计: {remaining:.0f}秒"
        else:
            eta = "预计: --"
        
        # 构建进度条
        bar_length = 30
        filled = int(bar_length * self.current / self.total)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        # 格式化消息
        msg = f"\r{self.description}: [{bar}] {percent:.0f}% ({self.current}/{self.total}) {eta}"
        if message:
            msg += f" - {message}"
        
        # 打印
        sys.stdout.write(msg)
        sys.stdout.flush()
    
    def finish(self, message: str = "完成"):
        """完成进度报告"""
        self.current = self.total
        elapsed = time.time() - self.start_time
        
        bar = '█' * 30
        msg = f"\r{self.description}: [{bar}] 100% ({self.total}/{self.total}) 完成，用时 {elapsed:.1f}秒"
        if message:
            msg += f" - {message}"
        msg += "\n"
        
        sys.stdout.write(msg)
        sys.stdout.flush()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.finish()
        else:
            sys.stdout.write(f"\n{self.description}: 因错误中止\n")
            sys.stdout.flush()


class PhaseReporter:
    """报告分阶段进度"""
    
    PHASES = [
        "安全预检",
        "深度分析",
        "多维度测试",
        "定性评估",
        "报告生成"
    ]
    
    def __init__(self):
        self.current_phase = 0
        self.start_time = time.time()
    
    def start_phase(self, phase_name: str):
        """开始新阶段"""
        self.current_phase += 1
        print(f"\n[{self.current_phase}/5] {phase_name}...")
    
    def phase_complete(self, message: Optional[str] = None):
        """标记当前阶段完成"""
        msg = f"   ✅ 阶段 {self.current_phase} 完成"
        if message:
            msg += f" ({message})"
        print(msg)
    
    def finish(self):
        """完成所有阶段"""
        elapsed = time.time() - self.start_time
        print(f"\n{'='*50}")
        print(f"所有阶段完成，用时 {elapsed:.1f}秒")
        print('='*50)


if __name__ == '__main__':
    # 演示
    print("进度报告器演示")
    print("=" * 50)
    
    # 阶段报告器演示
    phase = PhaseReporter()
    
    for i, phase_name in enumerate(PhaseReporter.PHASES):
        phase.start_phase(phase_name)
        
        # 模拟工作
        with ProgressReporter(10, f"   {phase_name}") as progress:
            for j in range(10):
                time.sleep(0.1)
                progress.update(1)
        
        phase.phase_complete()
    
    phase.finish()