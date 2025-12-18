import requests
from bs4 import BeautifulSoup
import csv
from requests.exceptions import RequestException

def crawl_soft_science_ranking():
    # 目标URL
    url = "https://www.shanghairanking.cn/rankings/bcur/202411"
    
    # 请求头：模拟浏览器访问，避免被反爬
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Referer": "https://www.shanghairanking.cn/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }

    try:
        # 发送HTTP请求（超时30秒）
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # 抛出HTTP错误（4xx/5xx状态码）
        
        # 自动识别编码，避免中文乱码
        response.encoding = response.apparent_encoding or "utf-8"

        # 解析HTML页面
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 定位排名表格（根据页面结构，class为"rk-table"）
        rank_table = soup.find("table", class_="rk-table")
        if not rank_table:
            print("错误：未找到排名表格，可能页面结构已更新")
            return

        # 定位表格主体（tbody），提取所有行（跳过表头）
        table_body = rank_table.find("tbody")
        if not table_body:
            print("错误：未找到表格数据主体")
            return
        
        # 获取所有大学行数据（取前30条）
        university_rows = table_body.find_all("tr")[:30]
        if len(university_rows) < 30:
            print(f"警告：仅获取到{len(university_rows)}条数据，不足30条")

        # 提取目标数据（排名、名称、省市、类型、总分）
        result_data = []
        for idx, row in enumerate(university_rows, 1):
            # 获取当前行的所有单元格
            cells = row.find_all("td")
            if len(cells) < 5:  # 确保数据完整（至少5个单元格）
                print(f"警告：第{idx}条数据不完整，已跳过")
                continue
            
            # 提取各字段（根据页面结构，索引对应关系如下）
            # 0: 排名, 1: 学校名称, 2: 省市, 3: 类型, 4: 总分
            rank = cells[0].text.strip()
            name = cells[1].text.strip()
            province = cells[2].text.strip()
            category = cells[3].text.strip()
            total_score = cells[4].text.strip()

            # 添加到结果列表
            result_data.append([rank, name, province, category, total_score])

        # 保存数据到CSV文件
        csv_filename = "软科中国大学排名2024前30名.csv"
        with open(csv_filename, "w", newline="", encoding="utf-8-sig") as csv_file:
            # 创建CSV写入器
            csv_writer = csv.writer(csv_file)
            # 写入表头
            csv_writer.writerow(["排名", "大学名称", "省市", "类型", "总分"])
            # 写入数据
            csv_writer.writerows(result_data)

        print(f"爬取成功！共获取{len(result_data)}条有效数据")
        print(f"数据已保存至：{csv_filename}")

    except RequestException as e:
        print(f"错误：网络请求失败 - {str(e)}")
    except Exception as e:
        print(f"错误：程序执行异常 - {str(e)}")

if __name__ == "__main__":
    crawl_soft_science_ranking()
