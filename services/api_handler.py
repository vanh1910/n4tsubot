import random
import aiohttp
import asyncio
import json
import pandas as pd
import logging
import math
from typing import Optional, Dict, Any
import time
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()


class StockAPIHandler:
    BASE_URL = "https://api.vietstock.vn/tvnew/history"
    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Origin": "https://stockchart.vietstock.vn",
        "Referer": "https://stockchart.vietstock.vn/"
    }

    def __init__(self, timeout: int = 5):
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def __fetch_history(
        self,
        session: aiohttp.ClientSession,
        from_date: pd.Timestamp,
        to_date: pd.Timestamp,
        ticker: str,
        resolution: str
    ) -> Optional[Dict[str, Any]]:
        """Lấy dữ liệu lịch sử của cổ phiếu từ Vietstock API."""
        from_ts = int(from_date.timestamp())
        to_ts = int(to_date.timestamp())

        params = {
            "symbol": ticker,
            "resolution": resolution,
            "from": from_ts,
            "to": to_ts,
            "countback": 2
        }

        try:
            async with session.get(
                self.BASE_URL,
                headers=self.HEADERS,
                params=params
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                data["params"] = params
                return data

        except aiohttp.ClientError as e:
            logger.error(f"API request failed for {ticker}: {e}")
            return None

    async def __fetch_realtime_data(
        self,
        session: aiohttp.ClientSession,
        resolution: str,
        range_: pd.Timedelta,
        ticker: str
    ) -> Optional[Dict[str, Any]]:
        """Lấy dữ liệu thời gian thực."""
        to_date = pd.Timestamp.now()
        from_date = to_date - range_
        return await self.__fetch_history(session, from_date, to_date, ticker, resolution)

    async def get_latest_tickers_data(self,tickers: list, from_date: pd.Timestamp, resolution: str):
        """
            Get price from a list of tickers from 'from_date' to now
            Args:
                tickers (list[str]): A list of ticker symbols
                from_date (pd.Timestam) Start time
                resolution (str): Time resolution, only accept "1", "60", "1D"
        """
        to_date = pd.Timestamp.now()
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = [
                self.__fetch_history(session, from_date, to_date, ticker, resolution)
                for ticker in tickers
            ]
            results = await asyncio.gather(*tasks)
        
        with open("data/json/realtime_cache.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        return results

    async def get_historical_tickers_data(
        self,
        tickers: list,
        from_date: pd.Timestamp,
        to_date: pd.Timestamp,
        resolution: str
    ):
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = [
                self.__fetch_history(session, from_date, to_date, ticker, resolution)
                for ticker in tickers
            ]
            results = await asyncio.gather(*tasks)
        with open("data/json/realtime_cache.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        return results

class CFHandler:
    BASE_URL = " https://codeforces.com/api/"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Connection': 'keep-alive'
    }
    def __init__(self, timeout: int = 20):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        

    async def fetch_problem(self):
        tags = ['*special', '2-sat', 'binary search', 'bitmasks', 'brute force', 'chinese remainder theorem', 'combinatorics', 'constructive algorithms', 'data structures', 'dfs and similar', 'divide and conquer', 'dp', 'dsu', 'expression parsing', 'fft', 'flows', 'games', 'geometry', 'graph matchings', 'graphs', 'greedy', 'hashing', 'implementation', 'interactive', 'math', 'matrices', 'meet-in-the-middle', 'number theory', 'probabilities', 'schedules', 'shortest paths', 'sortings', 'string suffix structures', 'strings', 'ternary search', 'trees', 'two pointers']
        tag = random.choice(tags)
        
        url = self.BASE_URL + "problemset.problems"
        params = {
            "tags": tag
        }
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    url,
                    headers=self.HEADERS,
                    params=params
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    return data

        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {e}")
            return None
    
    async def fetch_all_problems(self):
        url = self.BASE_URL + "problemset.problems"
        problems = []
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    url,
                    headers=self.HEADERS,
                ) as resp:
                    resp.raise_for_status()
                    problems = await resp.json()

        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {e}")
            return None

        data = {}
        for problem in problems["result"]["problems"]:
            try: 
                problem["rating"]
            except:
                continue
            id = f"{problem["contestId"]}_{problem["index"].lower()}"
            problem.pop("type")
            problem.pop("tags")
            if "points" in problem:
                problem["rating"] = problem["points"]
                problem.pop("points")
            problem["platform"] = "cf"
            data[f"cf_{id}"] = problem

        return data
        

        
    async def random_problem(self):
        data = await self.fetch_problem()
        problems = data["result"]["problems"]
        weights = []
        for problem in problems:
            rating = problem.get('rating', 0)
            if rating == 0 or rating > 2500:
                weights.append(20)
            elif rating > 1600: 
                weights.append(2*1600 - rating * 1.1 - (rating-1700)//1.5)
            else:
                weights.append(rating)
        
        return random.choices(problems, weights=weights, k=1)[0]
    

    async def true_random_problem(self):
        data = await self.fetch_problem()
        return random.choice(data["result"]["problems"])



    async def fetch_user_submission(self, handle, from_sub = 1, count_sub = 10):
        url = self.BASE_URL + "user.status"
        params = {
            "handle": handle,
            "from" : from_sub,
            "count": count_sub,
        }
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
               async with session.get(
                    url,
                    headers=self.HEADERS,
                    params=params
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    return data
               
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {e}")
            return None

    async def fetch_user_info(self, handle):
        url = self.BASE_URL + "user.info"
        params = {
            "handles": handle,
            "checkHistoricHandles": "false",
        }
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    url,
                    headers = self.HEADERS,
                    params = params
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    return data
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {e}")
            return None
 

class ATCODERAPIHANDLER:
    BASE_URL = "https://kenkoooo.com/atcoder/"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Connection': 'keep-alive'
    }
    def __init__(self, timeout: int = 40):
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def fetch_all_problems(self):
        problems = {}
        models = {}
        url = self.BASE_URL + "resources/merged-problems.json"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    url
                ) as resp:
                    resp.raise_for_status()
                    problems = await resp.json()

        except aiohttp.ClientError as e:
            logger.error(f"API request failed for merged-problems: {e}")
        
        url = self.BASE_URL + "resources/problem-models.json"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    url
                ) as resp:
                    resp.raise_for_status()
                    models = await resp.json()
                    
        except aiohttp.ClientError as e:
            logger.error(f"API request failed for problems-model: {e}")
            return None 
        data = {}
        for problem in problems:
            if problem["point"] is None:
                continue
            id = f"{problem["contest_id"]}_{"h" if problem["problem_index"] == "Ex" else problem["problem_index"].lower()}"
            try:
                data[f"at_{id}"] = {
                    "contestId": problem["contest_id"],
                    "index": problem["problem_index"],
                    "rating": models[id]["difficulty"] if models[id]["difficulty"] is not None else -1000,
                    "platform": "at",
                    "name": problem["name"]
                }
            except:
                continue
        
        return data


    async def true_random(self):
        with open("data/json/atcoder/merged-problems.json", "r") as f:
            data = json.load(f)
            return random.choice(data)
        
    async def fetch_user_submissions(self, handle, from_time: int=int(time.time()) - 10000):
        url = self.BASE_URL + "atcoder-api/v3/user/submissions"
        params = {
            "user": handle,
            "from_second": from_time
        }
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    url,
                    params = params
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    return data
        except aiohttp.ClientError as e:
            logger.error(f"API request failed for problems-model: {e}")



    def __parse_atcoder_submissions(self, html_content):
        """
        Parses AtCoder submission HTML and returns a list of submission dictionaries.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        submissions = []

        # Find the main submissions table
        table = soup.find('table', class_='table-bordered')
        
        if not table:
            return []

        # Iterate through the table body rows
        rows = table.find('tbody').find_all('tr')

        for row in rows:
            cols = row.find_all('td')
            if not cols:
                continue

            try:
                # 1. Submission Time
                time_str = cols[0].get_text(strip=True)

                # 2. Task (e.g., "A - Swapping Game")
                task = cols[1].get_text(strip=True)

                # 3. User
                user = cols[2].get_text(strip=True)

                # 4. Language
                language = cols[3].get_text(strip=True)

                # 5. Score
                score = cols[4].get_text(strip=True)

                # 6. Code Size
                code_size = cols[5].get_text(strip=True)

                # 7. Status (AC, WA, CE, etc.)
                # The status is usually inside a span with class 'label'
                status_span = cols[6].find('span', class_='label')
                status = status_span.get_text(strip=True) if status_span else cols[6].get_text(strip=True)

                # 8. & 9. Execution Time and Memory
                # Note: If Status is "CE" (Compilation Error), AtCoder uses colspan='3',
                # meaning Exec Time and Memory columns do not exist for that row.
                if cols[6].has_attr('colspan'):
                    exec_time = None
                    memory = None
                    detail_col_index = 7 # Detail link shifts left
                else:
                    exec_time = cols[7].get_text(strip=True)
                    memory = cols[8].get_text(strip=True)
                    detail_col_index = 9

                # 10. Submission ID (Extract from the "Detail" link)
                # The link is usually /contests/arcXXX/submissions/12345678
                detail_link = row.find_all('td')[-1].find('a')
                submission_id = None
                if detail_link and 'href' in detail_link.attrs:
                    href = detail_link['href']
                    submission_id = href.split('/')[-1]

                index = "H" if task[0:2] == "Ex" else task[0]

                submissions.append({
                    'id': submission_id,
                    'time': time_str,
                    'task': task,
                    'user': user,
                    'language': language,
                    'score': score,
                    'code_size': code_size,
                    'status': status,
                    'exec_time': exec_time,
                    'memory': memory,
                    'index' : index
                })

            except IndexError:
                # Skip malformed rows
                continue

        return submissions

    async def fetch_contest_submissions(self, contestid, problemid):
        referrer = f"https://atcoder.jp/contests/{contestid}/submissions?.Task={contestid}_{problemid.lower()}"
        url = referrer
        user_agent = os.getenv('USER_AGENT', 'Mozilla/5.0')
        cookie_value = os.getenv('ATCODER_COOKIE', '')

        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': referrer,  # Assumes 'referrer' variable is defined earlier in your code
            'Connection': 'keep-alive',
            'Cookie': cookie_value,
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=0, i',
            'TE': 'trailers',
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                # print(f"Status: {response.status}")
                
                # Read the response body
                html = await response.text()
                # print(f"Body length: {len(html)}")
                # print(html)
                return (self.__parse_atcoder_submissions(html))
                # print(html) # Uncomment to see the full content



class CPAPIHANDLER:
    def __init__(self):
        self.cf_api = CFHandler()
        self.atcoder_api = ATCODERAPIHANDLER()
    
    @staticmethod
    def build_dynamic_weight_map(target_mid_prob: float=0.36, mu: int = 1600):
        bin_counts = {}
        with open("data/json/problems.json", "r", encoding="utf-8") as f:
            problems_data = json.loads(f.read())
        for p in problems_data.values():
            r = p.get('rating')
            if r is not None and r > 0:
                b = int((r // 100) * 100)
                bin_counts[b] = bin_counts.get(b, 0) + 1
        
        if not bin_counts: return {}
        all_bins = sorted(bin_counts.keys())
        best_sigma = 300 # Giá trị khởi tạo
        
        for s in range(100, 1000):
            target_weights = {b: math.exp(-((b + 50 - mu)**2) / (2 * s**2)) for b in all_bins}
            total_target = sum(target_weights.values())
            mid_target = sum(target_weights[b] for b in all_bins if 1500 <= b < 1700)
            if total_target > 0 and (mid_target / total_target) <= target_mid_prob:
                best_sigma = s
                break

        weight_map = {}
        for b, count in bin_counts.items():
            target_val = math.exp(-((b + 50 - mu)**2) / (2 * best_sigma**2))
            weight_map[b] = target_val / count
            
        max_w = max(weight_map.values())
        for b in weight_map:
            weight_map[b] = round((weight_map[b] / max_w) * 100, 8)
            if weight_map[b] == 0:
                weight_map[b] = 0.0001
            
        with open("data/json/weights.json", "w", encoding="utf-8") as f:
            json.dump(weight_map, f, indent = 4)


    def true_random_problem(self):
        return self.cf_api.true_random_problem()

    async def random_problem(self, hard = 0):
        data = {}
        weights = []
        with open("data/json/weights.json", "r", encoding="utf-8") as f:
            weights_map = json.loads(f.read())
        with open("data/json/problems.json", "r", encoding="utf-8") as f:
            data = json.loads(f.read())
        items = list(data.values())
        for problem in items:
            rating = int(problem["rating"] // 100) * 100
            if rating <= 0:
                rating = 0
            w = weights_map[str(rating)]
            if problem["platform"] == "atcoder":
                w *= 2
            weights.append(w)
        return random.choices(items,weights = weights, k=1)[0]
    

    async def update_data(self):
        data = await self.cf_api.fetch_all_problems() | await self.atcoder_api.fetch_all_problems()
        with open("data/json/problems.json", "w", encoding="utf-8") as f:
            json.dump(data,f, indent=4)


    async def fetch_user_submission(self, handle, platform):
        if platform == "cf":
            return await self.cf_api.fetch_user_submission(handle)
        elif platform == "at": 
            return await self.atcoder_api.fetch_user_submissions(handle)

    async def at_fetch_contest(self, contestid, problemid):
        return await self.atcoder_api.fetch_contest_submissions(contestid, problemid)

    async def fetch_user_info(self, handle, platform):
        if platform == "cf":
            return await self.cf_api.fetch_user_info(handle)

async def main():
    pass

if __name__ == "__main__":
    asyncio.run(main())
