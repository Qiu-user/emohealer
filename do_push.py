import subprocess
import os

os.chdir(r'c:\Users\18746\Desktop\biyeshixi')

print("推送到 GitHub...")
result = subprocess.run(
    ['git', 'push', '-u', 'origin', 'master'],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.stderr:
    print(result.stderr)
if result.returncode == 0:
    print("\n推送成功!")
    print("仓库地址: https://github.com/Qiu-user/emohealer")
else:
    print("\n推送失败，请检查认证信息")
