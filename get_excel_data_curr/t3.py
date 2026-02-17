import requests
from datetime import datetime, timedelta


def deal(cookie, buildingId, b_num, requst_data, page_size=20):
    """
    查询指定楼栋的晚归数据。
    :param cookie: 登录后的 session cookie
    :param buildingId: 楼栋在公寓系统中的内部 ID
    :param b_num: 楼栋编号
    :param requst_data: 请求数据（包含 startTime, endTime 等）
    :param page_size: 每页数据条数，从调用方传入
    """
    # 获取当前日期
    current_date = datetime.now().strftime("%Y-%m-%d")
    # 获取前一天日期
    previous_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # 根据楼栋号判断使用哪个楼群ID
    # 中院: 1-14 (1栋到12B栋)
    # 西院: 15-20 (13栋到17B栋)
    if int(b_num) >= 15:
        building_group_id = "5760ba66b341e2bb968ea7b990fa873d"  # 西院
    else:
        building_group_id = "851c0092fe8a5c4969fd9e8e2b5200e9"  # 中院

    url = "http://gygl.tust.edu.cn:8080/da-roadgate-resident/inout/inout_record/get_inout_list_paged_json"
    params = {
        "offset": 0,
        "limit": page_size,
        "studentTypeSearch": "",
        "schoolInstituteNameSearch": "",
        "schoolMajorNameSearch": "",
        "schoolClassNameSearch": "",
        "gradeSearch": "",
        "studentType": "",
        "schoolInstituteName": "",
        "grade": "",
        "schoolClassName": "",
        "keyWords": "",
        "campusId": "2852cbacb09b6b110f4bb162b636e204",
        "buildingGroupId": building_group_id,
        "buildingId": buildingId,
        # "beginTime": f"{previous_date} {config_tool.get_beginTime()}",
        # "endTime": f"{current_date} {config_tool.get_endTime()}",
        "beginTime": f"{previous_date} {requst_data['startTime']}",
        "endTime": f"{current_date} {requst_data['endTime']}",
        "passDirection": ""
    }

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Content-Type": "application/json",
        "Proxy-Connection": "keep-alive",
        "Referer": "http://gygl.tust.edu.cn:8080/da-roadgate-resident/index",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    cookies = {
        "sid": cookie
    }

    all_rows = []
    response = requests.get(url, headers=headers, params=params, cookies=cookies, verify=False)
    if response.status_code == 200:
        # print(json.dumps(response.json(), indent=4, ensure_ascii=False))
        # print(response.status_code)

        total_rows = response.json()['total']
        page_num = int(total_rows / page_size) if total_rows % page_size == 0 else int(total_rows / page_size) + 1
        print(f'处理公寓{b_num}数据，page_num={page_num}')
        for i in range(page_num):
            print(f'查询第{i}页')
            params["offset"] = i * page_size
            response = requests.get(url, headers=headers, params=params, cookies=cookies, verify=False)
            all_rows += response.json()['rows']

    print(f'共{len(all_rows)}条记录')
    return all_rows

# deal('a87653ef-07b6-4ae5-8682-8378cb052e67')

