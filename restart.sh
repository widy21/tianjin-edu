#!/bin/bash

# 查找并杀掉包含 app.py 的进程
echo "Killing processes containing app.py..."
pids=$(ps -ef | grep 'app.py' | grep -v grep | awk '{print $2}')
for pid in $pids; do
    echo "Killing process $pid"
    kill $pid
done

# 启动 app.py 并将输出重定向到 out.log
echo "Starting app.py in the background..."
nohup python3 app.py >> out.log 2>&1 &

# 输出脚本完成信息
echo "Script completed. Check out.log for output."
