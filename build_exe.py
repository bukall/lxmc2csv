import os
import sys
import subprocess

def build_exe():
    # 源文件路径
    source_file = "main.py"

    # 检查源文件是否存在
    if not os.path.exists(source_file):
        print(f"错误: 找不到源文件 {source_file}")
        return False

    # 构建命令
    # --onefile: 打包成单个可执行文件
    # --console: 使用控制台窗口（适合命令行程序）
    # --name: 指定输出文件名
    # --clean: 清理临时文件
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--name", "lxmc2csv",
        "--clean",
        source_file
    ]

    print("开始编译...")
    print(f"执行命令: {' '.join(cmd)}")

    try:
        # 执行编译
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("\n✅ 编译成功!")
            return True
        else:
            print("\n❌ 编译失败!")
            print("\n错误输出:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"\n❌ 编译过程中发生错误: {e}")
        return False

def main():
    print("Python 编译为 exe 脚本")
    print("=" * 50)

    # 检查是否安装了 PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
    except ImportError:
        print("✗ PyInstaller 未安装")
        print("请先运行: pip install pyinstaller")
        return

    # 开始编译
    build_exe()

if __name__ == "__main__":
    main()
