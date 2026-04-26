#!/usr/bin/env python3
"""
验证楼栋取数失败时不会发送空报表。
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

PASS = 0
FAIL = 0


def record(test_name, passed, detail=''):
    global PASS, FAIL
    if passed:
        PASS += 1
        print(f"  ✅ PASS {test_name}")
    else:
        FAIL += 1
        print(f"  ❌ FAIL {test_name} - {detail}")


class FakeConfigTool:
    def get_username(self):
        return 'fake-user'

    def get_password(self):
        return 'fake-pass'

    def get_flag(self):
        return 'whosyourdady'

    def get_binary_location(self):
        return ''

    def get_driver_location(self):
        return ''

    def get_bid_dict(self):
        return {'1': 'bid-1', '2': 'bid-2'}

    def get_pagesize(self):
        return 30

    def get_data_cfg(self):
        return {}


class FakeDriver:
    def quit(self):
        pass


def patch_process_runtime(main_module):
    main_module._get_config_tool = lambda: FakeConfigTool()
    main_module.webdriver.Chrome = lambda *args, **kwargs: FakeDriver()
    main_module._login_with_retry = lambda *args, **kwargs: (
        True,
        '登录成功',
        [{'value': 'fake-sid'}],
    )


def test_all_buildings_failed():
    print("\n--- 全部楼栋取数失败 ---")
    import get_excel_data_curr.main as main_module
    import get_excel_data_curr.t3 as t3_module

    patch_process_runtime(main_module)
    called = {'excel': False}
    original_deal = main_module.t3.deal
    original_gen_excel = main_module.gen_excel_data_v1

    def fail_deal(*args, **kwargs):
        raise t3_module.DataFetchError('接口返回登录页')

    def fake_gen_excel(*args, **kwargs):
        called['excel'] = True
        return './result-files/admin/should-not-exist.xlsx'

    main_module.t3.deal = fail_deal
    main_module.gen_excel_data_v1 = fake_gen_excel

    try:
        result = main_module.process({
            'buildings': ['1', '2'],
            'username': 'admin',
            'startTime': '23:20:00',
            'endTime': '05:30:00',
        })
    finally:
        main_module.t3.deal = original_deal
        main_module.gen_excel_data_v1 = original_gen_excel

    record('1.1 返回失败状态', result.get('status') == 'false', str(result))
    record('1.2 不返回 file_name', 'file_name' not in result, str(result))
    record('1.3 不生成 Excel', called['excel'] is False)
    record('1.4 错误信息说明全部失败', '所有楼栋取数失败' in result.get('msg', ''), result.get('msg', ''))


def test_partial_building_failure_still_succeeds():
    print("\n--- 部分楼栋失败仍生成成功楼栋报表 ---")
    import get_excel_data_curr.main as main_module
    import get_excel_data_curr.t3 as t3_module

    patch_process_runtime(main_module)
    captured = {}
    original_deal = main_module.t3.deal
    original_gen_excel = main_module.gen_excel_data_v1

    def mixed_deal(cookie, building_id, b_num, request_data, page_size=20):
        if b_num == '1':
            raise t3_module.DataFetchError('接口返回登录页')
        return [{
            'userId': '001',
            'passTimeText': '2026-04-25 23:30:00',
            'schoolInstituteName': '人工智能学院',
            'userName': '测试',
            'roomName': '101',
            'grade': '2026',
            'studentType': '研究生',
        }]

    def fake_gen_excel(ret_dict, username, data_cfg=None, request_data=None):
        captured['ret_dict'] = ret_dict
        return './result-files/admin/fake.xlsx'

    main_module.t3.deal = mixed_deal
    main_module.gen_excel_data_v1 = fake_gen_excel

    try:
        result = main_module.process({
            'buildings': ['1', '2'],
            'username': 'admin',
            'startTime': '23:20:00',
            'endTime': '05:30:00',
        })
    finally:
        main_module.t3.deal = original_deal
        main_module.gen_excel_data_v1 = original_gen_excel

    record('2.1 返回成功状态', result.get('status') == 'success', str(result))
    record('2.2 返回 file_name', result.get('file_name') == './result-files/admin/fake.xlsx', str(result))
    record('2.3 只包含成功楼栋', set(captured.get('ret_dict', {}).keys()) == {'2'}, str(captured))


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text='', url='http://gygl.tust.edu.cn/api', history=None):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.url = url
        self.history = history or []

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def test_zero_total_is_not_failure():
    print("\n--- total=0 不算取数失败 ---")
    import get_excel_data_curr.t3 as t3_module

    original_get = t3_module.requests.get
    t3_module.requests.get = lambda *args, **kwargs: FakeResponse(payload={'total': 0, 'rows': []})
    try:
        rows = t3_module.deal('sid', 'bid-1', '1', {'startTime': '23:20:00', 'endTime': '05:30:00'})
        record('3.1 返回空列表', rows == [], str(rows))
    except Exception as e:
        record('3.1 total=0 不应抛异常', False, str(e))
    finally:
        t3_module.requests.get = original_get


def test_login_redirect_is_failure():
    print("\n--- 接口跳转登录页算取数失败 ---")
    import get_excel_data_curr.t3 as t3_module

    original_get = t3_module.requests.get
    t3_module.requests.get = lambda *args, **kwargs: FakeResponse(
        status_code=200,
        payload=ValueError('not json'),
        text='<html>login</html>',
        url='http://gygl.tust.edu.cn:8080/cas/login',
    )
    try:
        t3_module.deal('sid', 'bid-1', '1', {'startTime': '23:20:00', 'endTime': '05:30:00'})
        record('4.1 跳转登录页应抛 DataFetchError', False, '未抛异常')
    except t3_module.DataFetchError:
        record('4.1 跳转登录页抛 DataFetchError', True)
    except Exception as e:
        record('4.1 异常类型错误', False, type(e).__name__)
    finally:
        t3_module.requests.get = original_get


def test_task_manager_failed_result_does_not_send_email():
    print("\n--- TaskManager 失败结果不发送邮件 ---")
    import scheduler.task_manager as task_manager_module
    from scheduler.task_manager import TaskManager

    class FakeDb:
        def __init__(self):
            self.updates = []

        def create_task_log(self, email_task_id, username, status='pending'):
            return 123

        def update_task_log(self, log_id, status, file_path=None, error_message=None):
            self.updates.append((log_id, status, file_path, error_message))

    class FailIfEmailSender:
        @classmethod
        def from_db(cls, db):
            raise AssertionError('失败结果不应发送邮件')

    original_process = task_manager_module.process
    original_email_sender = task_manager_module.EmailSender
    fake_db = FakeDb()
    task_manager_module.process = lambda request_data: {
        'status': 'false',
        'msg': '所有楼栋取数失败：楼栋1: 登录态失效',
    }
    task_manager_module.EmailSender = FailIfEmailSender
    try:
        TaskManager(fake_db).execute_single_task({
            'id': 1,
            'task_name': '失败测试',
            'username': 'admin',
            'buildings': ['1'],
            'recipients': ['test@example.com'],
            'start_time': '23:20:00',
            'end_time': '05:30:00',
        })
        record('5.1 任务日志标记 failed', fake_db.updates and fake_db.updates[-1][1] == 'failed', str(fake_db.updates))
        record('5.2 失败日志不含 file_path', fake_db.updates and fake_db.updates[-1][2] is None, str(fake_db.updates))
    finally:
        task_manager_module.process = original_process
        task_manager_module.EmailSender = original_email_sender


def main():
    print("=" * 60)
    print("测试全楼栋取数失败时不发送空报表")
    print("=" * 60)
    test_all_buildings_failed()
    test_partial_building_failure_still_succeeds()
    test_zero_total_is_not_failure()
    test_login_redirect_is_failure()
    test_task_manager_failed_result_does_not_send_email()
    print("\n" + "=" * 60)
    print(f"测试结果汇总: {PASS} 通过, {FAIL} 失败, 共 {PASS + FAIL} 项")
    print("=" * 60)
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
