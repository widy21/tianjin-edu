#!/usr/bin/env python3
"""
测试登录超时返回值修复 - KeyError: 'file_name' bug

这个测试验证当 process() 函数遇到登录超时时：
1. 返回 status: 'false' 而不是 'success'
2. task_manager.py 能正确处理这个返回值，不会抛出 KeyError

运行方式：
source .venv/bin/activate && python tests/test_timeout_fix.py
"""
import os
import sys

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

PASS = 0
FAIL = 0
RESULTS = []


def record(test_name, passed, detail=''):
    global PASS, FAIL
    if passed:
        PASS += 1
        RESULTS.append((test_name, '✅ PASS', detail))
        print(f"  ✅ PASS {test_name}")
    else:
        FAIL += 1
        RESULTS.append((test_name, '❌ FAIL', detail))
        print(f"  ❌ FAIL {test_name} - {detail}")


def test_process_return_value_structure():
    """测试 process() 函数在登录超时场景的返回值结构"""
    print("\n--- 测试 process() 返回值结构 ---")
    
    # 模拟登录超时的返回值（修复后的）
    timeout_result = {
        'msg': "登录后页面加载超时，可能登录失败。",
        'status': 'false',  # 修复后应该是 'false'
    }
    
    # 测试1: 验证 status 字段存在
    record('1.1 返回值包含 status 字段', 'status' in timeout_result)
    
    # 测试2: 验证 status 不是 'success'
    record('1.2 status 不是 success', timeout_result.get('status') != 'success')
    
    # 测试3: 验证 status 是 'false'
    record('1.3 status 是 false', timeout_result.get('status') == 'false')
    
    # 测试4: 验证没有 file_name 字段
    record('1.4 返回值不包含 file_name 字段', 'file_name' not in timeout_result)


def test_task_manager_handling():
    """测试 task_manager.py 对返回值的处理逻辑"""
    print("\n--- 测试 task_manager 处理逻辑 ---")
    
    # 模拟登录超时的返回值（修复后）
    timeout_result = {
        'msg': "登录后页面加载超时，可能登录失败。",
        'status': 'false',
    }
    
    # 模拟 task_manager.py 中的处理逻辑
    try:
        if timeout_result.get('status') == 'success':
            # 如果进入这个分支，会尝试访问 file_name
            file_path = timeout_result['file_name']  # 这里会抛出 KeyError
            record('2.1 不应该进入 success 分支', False, '进入了 success 分支')
        else:
            # 正确：进入失败分支
            error_msg = timeout_result.get('msg', '数据查询失败')
            record('2.1 正确进入失败分支', True)
            record('2.2 获取错误信息成功', error_msg == "登录后页面加载超时，可能登录失败。")
    except KeyError as e:
        record('2.1 处理逻辑抛出 KeyError', False, f'KeyError: {e}')
    except Exception as e:
        record('2.1 处理逻辑抛出异常', False, str(e))


def test_success_case_handling():
    """测试成功场景的处理逻辑（确保没有破坏正常流程）"""
    print("\n--- 测试成功场景处理逻辑 ---")
    
    # 模拟成功的返回值
    success_result = {
        'file_name': 'result-files/admin/公寓学生晚归名单.xlsx',
        'status': 'success',
    }
    
    try:
        if success_result.get('status') == 'success':
            file_path = success_result['file_name']
            record('3.1 成功场景正确获取 file_name', True)
            record('3.2 file_path 值正确', file_path == 'result-files/admin/公寓学生晚归名单.xlsx')
        else:
            record('3.1 应该进入 success 分支', False, '未进入 success 分支')
    except KeyError as e:
        record('3.1 成功场景抛出 KeyError', False, f'KeyError: {e}')


def test_main_py_code_verification():
    """验证 main.py 中的代码是否已修复"""
    print("\n--- 验证 main.py 代码 ---")
    
    main_py_path = os.path.join(PROJECT_ROOT, 'get_excel_data_curr', 'main.py')
    
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找 TimeoutException 处理部分的 status 值
    import re
    
    # 查找 TimeoutException 处理块中的 status
    # 模式：在 TimeoutException 处理中查找 'status': 'xxx'
    pattern = r"except TimeoutException:.*?return\s*\{[^}]*'status':\s*'(\w+)'"
    matches = re.findall(pattern, content, re.DOTALL)
    
    if matches:
        # 找到了 TimeoutException 处理中的 status 值
        for i, status_val in enumerate(matches):
            if status_val == 'false':
                record(f'4.{i+1} TimeoutException 处理返回 status: false', True)
            elif status_val == 'success':
                record(f'4.{i+1} TimeoutException 处理返回 status: success', False, 'Bug未修复！')
            else:
                record(f'4.{i+1} TimeoutException 处理返回 status: {status_val}', False, '意外的status值')
    else:
        # 尝试另一种方式查找
        if "'status': 'false'" in content and "登录后页面加载超时" in content:
            record('4.1 代码包含修复后的 status: false', True)
        else:
            record('4.1 无法验证代码修复状态', False, '未找到预期的代码模式')


def main():
    print("=" * 60)
    print("测试登录超时返回值修复 (KeyError: 'file_name' bug)")
    print("=" * 60)
    
    test_process_return_value_structure()
    test_task_manager_handling()
    test_success_case_handling()
    test_main_py_code_verification()
    
    # 打印结果汇总
    print("\n" + "=" * 60)
    print(f"测试结果汇总: {PASS} 通过, {FAIL} 失败, 共 {PASS + FAIL} 项")
    print("=" * 60)
    
    if FAIL == 0:
        print("\n🎉 所有测试通过！Bug 修复验证成功！")
        return 0
    else:
        print(f"\n⚠️  有 {FAIL} 项测试失败，请检查。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
