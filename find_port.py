import subprocess

result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
print("占用8092端口的进程:")
for line in result.stdout.split('\n'):
    if ':8092' in line and 'LISTENING' in line:
        print(line)

print("\n占用8088端口的进程:")
for line in result.stdout.split('\n'):
    if ':8088' in line and 'LISTENING' in line:
        print(line)
