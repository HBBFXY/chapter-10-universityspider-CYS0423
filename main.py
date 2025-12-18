import requests
from bs4 import BeautifulSoup
import csv
import time
import random
from requests.exceptions import RequestException
from tqdm import tqdm  # 进度条库
import os

def create_user_agent_pool():
    """创建User-Agent池，模拟不同浏览器访问"""
    return [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/128.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ]

def get_page_data(url, user_agents, retry=3):
    """获取单页数据，支持重试机制"""
    headers = {
        "User-Agent": random.choice(user_agents),
        "Referer": "https://www.shanghairanking.cn/rankings/bcur/202411",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",  # 禁用缓存，获取最新数据
        "Connection": "keep-alive"
    }

    for attempt in range(retry):
        try:
            # 随机延迟1-3秒，模拟真实用户浏览节奏
            time.sleep(random.uniform(1, 3))
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"
            
            soup = BeautifulSoup(response.text, "html.parser")
            rank_table = soup.find("table", class_="rk-table")
            if not rank_table:
                print(f"警告：页面{url}未找到排名表格，跳过该页")
                return []
            
            table_body = rank_table.find("tbody")
            if not table_body:
                print(f"警告：页面{url}未找到表格数据，跳过该页")
                return []
            
            # 提取当前页所有大学数据
            university_rows = table_body.find_all("tr")
            page_data = []
            for row in university_rows:
                cells = row.find_all("td")
                if len(cells) < 5:
                    continue  # 跳过不完整数据
                
                rank = cells[0].text.strip()
                name = cells[1].text.strip()
                province = cells[2].text.strip()
                category = cells[3].text.strip()
                total_score = cells[4].text.strip()
                
                # 过滤无效数据（排名为空或总分异常）
                if not rank or not total_score.replace(".", "").isdigit():
                    continue
                
                page_data.append([rank, name, province, category, total_score])
            
            return page_data
        
        except RequestException as e:
            print(f"警告：页面{url}第{attempt+1}次请求失败 - {str(e)}")
            if attempt == retry - 1:
                print(f"错误：页面{url}多次请求失败，已跳过")
                return []
        except Exception as e:
            print(f"错误：解析页面{url}时异常 - {str(e)}，已跳过")
            return []

def crawl_all_universities():
    """爬取所有页面的大学排名数据"""
    base_url = "https://www.shanghairanking.cn/rankings/bcur/202411"
    user_agents = create_user_agent_pool()
    all_data = []
    page = 1
    csv_filename = "软科中国大学排名2024完整名单.csv"
    crawled_ranks = set()  # 用于去重（避免分页重复数据）

    # 断点续爬：如果文件已存在，读取已爬取的排名，避免重复
    if os.path.exists(csv_filename):
        with open(csv_filename, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader)  # 跳过表头
            for row in reader:
                if row:
                    crawled_ranks.add(row[0])
        print(f"检测到已存在爬取文件，已爬取{len(crawled_ranks)}所高校，将继续补充剩余数据")

    try:
        print("开始爬取软科中国大学排名完整数据...")
        while True:
            # 构造分页URL（软科分页规则：page=1,2,3...）
            page_url = f"{base_url}?page={page}"
            print(f"\n正在爬取第{page}页：{page_url}")
            
            # 获取当前页数据
            page_data = get_page_data(page_url, user_agents)
            
            # 终止条件：当前页无数据（已爬完所有页面）
            if not page_data:
                print(f"第{page}页无有效数据，已爬完所有页面")
                break
            
            # 去重：过滤已爬取的排名数据
            new_data = []
            for item in page_data:
                if item[0] not in crawled_ranks:
                    new_data.append(item)
                    crawled_ranks.add(item[0])
            
            if new_data:
                all_data.extend(new_data)
                print(f"第{page}页爬取成功，新增{len(new_data)}所高校数据")
            else:
                print(f"第{page}页无新增数据（已去重）")
            
            # 批量写入CSV（每爬3页写入一次，减少I/O操作）
            if page % 3 == 0:
                write_to_csv(all_data, csv_filename, mode="a")
                all_data.clear()  # 清空临时数据，避免内存占用过大
            
            page += 1

        # 爬取结束后，写入剩余数据
        if all_data:
            write_to_csv(all_data, csv_filename, mode="a")
        
        print(f"\n爬取完成！共获取{len(crawled_ranks)}所高校的完整数据")
        print(f"数据已保存至：{csv_filename}")

    except KeyboardInterrupt:
        # 捕获Ctrl+C中断，保存已爬取数据
        if all_data:
            write_to_csv(all_data, csv_filename, mode="a")
        print(f"\n爬取被手动中断，已保存当前爬取的{len(crawled_ranks)}所高校数据")
    except Exception as e:
        # 未知异常时保存已爬取数据
        if all_data:
            write_to_csv(all_data, csv_filename, mode="a")
        print(f"\n错误：程序异常终止 - {str(e)}")
        print(f"已保存当前爬取的{len(crawled_ranks)}所高校数据")

def write_to_csv(data, filename, mode="w"):
    """写入CSV文件，支持新建和追加模式"""
    # 新建文件时写入表头，追加模式时跳过表头
    write_header = (mode == "w")
    with open(filename, mode, newline="", encoding="utf-8-sig") as csv_file:
        csv_writer = csv.writer(csv_file)
        if write_header:
            csv_writer.writerow(["排名", "大学名称", "省市", "类型", "总分"])
        csv_writer.writerows(data)

if __name__ == "__main__":
    crawl_all_universities()
