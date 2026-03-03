"""
SHL Product Catalog Scraper
Scrapes real SHL Individual Test Solutions from the live website.

Primary strategy (Option A): Selenium crawler with dynamic loading, explicit waits,
retries, and pagination discovery.
Fallback strategy: requests + BeautifulSoup over paginated URLs.
Safety net (Option C): merge real URLs from training dataset if live crawl misses some.
"""

import json
import re
import time
from typing import Dict, List, Optional, Set
from urllib.parse import parse_qs, urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class SHLCatalogScraper:
    def __init__(self):
        self.base_url = "https://www.shl.com/products/product-catalog/?start=0&type=1"
        self.site_root = "https://www.shl.com"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        self.assessments: List[Dict] = []

    def scrape_catalog(self) -> List[Dict]:
        """Scrape SHL Individual Test Solutions from live website."""
        print("Starting SHL catalog scraping (real website)...")

        selenium_data = self._scrape_with_selenium()
        print(f"Selenium crawl collected {len(selenium_data)} assessments")

        if len(selenium_data) < 377:
            print("Selenium crawl below target. Running requests fallback on paginated URLs...")
            requests_data = self._scrape_with_requests()
            selenium_data = self._merge_unique_by_url(selenium_data, requests_data)
            print(f"After requests fallback merge: {len(selenium_data)} assessments")

        if len(selenium_data) < 377:
            print("Merging real URLs from training dataset as safety net...")
            seeded = bootstrap_from_training_data("Gen_AI Dataset.xlsx")
            selenium_data = self._merge_unique_by_url(selenium_data, seeded)
            print(f"After training-data merge: {len(selenium_data)} assessments")

        self.assessments = selenium_data

        if len(self.assessments) < 377:
            print(
                "WARNING: Could not reach 377 real assessments from live sources. "
                "Please re-run on stable internet and ensure browser automation is allowed."
            )

        return self.assessments

    def _init_driver(self):
        """Initialize Selenium driver with robust options (Chrome first, then Edge)."""
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )

        try:
            return webdriver.Chrome(options=chrome_options)
        except Exception:
            edge_options = EdgeOptions()
            edge_options.add_argument("--headless=new")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--window-size=1920,1080")
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            return webdriver.Edge(options=edge_options)

    def _scrape_with_selenium(self) -> List[Dict]:
        data: List[Dict] = []
        try:
            driver = self._init_driver()
        except WebDriverException as e:
            print(f"Could not initialize Selenium driver: {e}")
            return data

        try:
            starts = self._discover_starts_selenium(driver)
            if not starts:
                starts = list(range(0, 385, 12))

            print(f"Discovered {len(starts)} catalog pages for type=1")

            for i, start in enumerate(starts, start=1):
                page_url = f"https://www.shl.com/products/product-catalog/?start={start}&type=1"
                page_items = self._crawl_page_selenium(driver, page_url)
                data = self._merge_unique_by_url(data, page_items)
                print(f"[{i}/{len(starts)}] start={start}: +{len(page_items)} items (total {len(data)})")
                time.sleep(0.8)

        finally:
            driver.quit()

        return data

    def _discover_starts_selenium(self, driver) -> List[int]:
        """Discover valid pagination starts from first page links."""
        starts: Set[int] = {0}
        try:
            driver.get(self.base_url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
            time.sleep(1.5)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            for a in soup.select("a[href]"):
                href = a.get("href", "")
                if "product-catalog/?" not in href:
                    continue
                parsed = urlparse(urljoin(self.site_root, href))
                query = parse_qs(parsed.query)
                types = query.get("type", [])
                if "1" not in types:
                    continue
                start_values = query.get("start", [])
                if start_values:
                    try:
                        starts.add(int(start_values[0]))
                    except ValueError:
                        pass

            if starts:
                max_start = max(starts)
                starts = set(range(0, max_start + 12, 12))

        except Exception as e:
            print(f"Pagination discovery (selenium) failed: {e}")

        return sorted(starts)

    def _crawl_page_selenium(self, driver, url: str, retries: int = 3) -> List[Dict]:
        """Load one page using Selenium with retries and explicit waits."""
        for attempt in range(1, retries + 1):
            try:
                driver.get(url)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
                time.sleep(1.0)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                return self._extract_individual_assessments_from_soup(soup)
            except TimeoutException:
                wait_seconds = attempt * 2
                print(f"Timeout on {url} (attempt {attempt}/{retries}), retrying in {wait_seconds}s...")
                time.sleep(wait_seconds)
            except Exception as e:
                wait_seconds = attempt * 2
                print(f"Error on {url} (attempt {attempt}/{retries}): {e}; retrying in {wait_seconds}s...")
                time.sleep(wait_seconds)

        return []

    def _scrape_with_requests(self) -> List[Dict]:
        """Requests fallback over paginated pages for robustness."""
        data: List[Dict] = []
        starts = self._discover_starts_requests()
        if not starts:
            starts = list(range(0, 385, 12))

        for i, start in enumerate(starts, start=1):
            page_url = f"https://www.shl.com/products/product-catalog/?start={start}&type=1"
            page_items = self._crawl_page_requests(page_url)
            data = self._merge_unique_by_url(data, page_items)
            print(f"[requests {i}/{len(starts)}] start={start}: +{len(page_items)} items (total {len(data)})")
            time.sleep(0.3)

        return data

    def _discover_starts_requests(self) -> List[int]:
        starts: Set[int] = {0}
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for a in soup.select("a[href]"):
                href = a.get("href", "")
                if "product-catalog/?" not in href:
                    continue
                parsed = urlparse(urljoin(self.site_root, href))
                query = parse_qs(parsed.query)
                types = query.get("type", [])
                if "1" not in types:
                    continue
                start_values = query.get("start", [])
                if start_values:
                    try:
                        starts.add(int(start_values[0]))
                    except ValueError:
                        pass

            if starts:
                max_start = max(starts)
                starts = set(range(0, max_start + 12, 12))

        except Exception as e:
            print(f"Pagination discovery (requests) failed: {e}")

        return sorted(starts)

    def _crawl_page_requests(self, url: str, retries: int = 3) -> List[Dict]:
        for attempt in range(1, retries + 1):
            try:
                response = requests.get(url, headers=self.headers, timeout=20)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                return self._extract_individual_assessments_from_soup(soup)
            except Exception as e:
                wait_seconds = attempt * 2
                print(f"Requests error on {url} (attempt {attempt}/{retries}): {e}; retrying in {wait_seconds}s...")
                time.sleep(wait_seconds)

        return []

    def _extract_individual_assessments_from_soup(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract only rows under table headed 'Individual Test Solutions'."""
        output: List[Dict] = []

        for table in soup.find_all("table"):
            headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
            if not headers:
                continue
            if "Individual Test Solutions" not in headers[0]:
                continue

            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if not cells:
                    continue

                first_cell = cells[0]
                name = first_cell.get_text(" ", strip=True)
                if not name:
                    continue

                link = first_cell.find("a", href=True)
                if not link:
                    continue

                href = link.get("href", "").strip()
                full_url = urljoin(self.site_root, href)

                if "/products/product-catalog/view/" not in full_url:
                    continue

                test_types_raw = cells[-1].get_text(" ", strip=True).upper() if cells else ""
                test_type = self._extract_primary_test_type(test_types_raw)
                category = self._category_from_test_type(test_type)

                item = {
                    "name": re.sub(r"\s+", " ", name),
                    "url": full_url,
                    "category": category,
                    "test_type": test_type,
                    "test_types": test_types_raw,
                    "description": "",
                }
                output.append(item)

        return self._merge_unique_by_url([], output)

    def _extract_primary_test_type(self, raw: str) -> str:
        if "K" in raw:
            return "K"
        if "P" in raw:
            return "P"
        if "A" in raw:
            return "A"
        if "S" in raw:
            return "S"
        return "O"

    def _category_from_test_type(self, test_type: str) -> str:
        mapping = {
            "K": "skills",
            "P": "personality",
            "A": "cognitive",
            "S": "situational",
            "O": "other",
        }
        return mapping.get(test_type, "other")

    def _merge_unique_by_url(self, left: List[Dict], right: List[Dict]) -> List[Dict]:
        seen = {item.get("url", "").rstrip("/") for item in left if item.get("url")}
        merged = left.copy()

        for item in right:
            url = item.get("url", "").rstrip("/")
            if not url:
                continue
            if url in seen:
                continue
            if not url.startswith("https://www.shl.com/products/product-catalog/view/"):
                continue
            seen.add(url)
            merged.append(item)

        return merged

    def save_to_file(self, filename: str = "shl_assessments.json"):
        """Save scraped data to JSON and CSV files."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.assessments, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(self.assessments)} assessments to {filename}")

        csv_filename = filename.replace(".json", ".csv")
        pd.DataFrame(self.assessments).to_csv(csv_filename, index=False)
        print(f"Also saved to {csv_filename}")

    def load_from_file(self, filename: str = "shl_assessments.json") -> List[Dict]:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.assessments = json.load(f)
            print(f"Loaded {len(self.assessments)} assessments from {filename}")
            return self.assessments
        except Exception as e:
            print(f"Could not load from file: {e}")
            return []


def bootstrap_from_training_data(filename: str = "Gen_AI Dataset.xlsx") -> List[Dict]:
    """Collect only real SHL URLs from training data (no synthetic expansion)."""
    print("Bootstrapping from training data (real URLs only)...")

    try:
        df = pd.read_excel(filename, sheet_name="Train-Set")
        urls = (
            df["Assessment_url"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

        assessments: List[Dict] = []
        for url in urls:
            if "/products/product-catalog/view/" not in url:
                continue
            slug = url.rstrip("/").split("/")[-1]
            name = slug.replace("-", " ").title()

            url_lower = url.lower()
            if any(x in url_lower for x in ["java", "python", "sql", "javascript", "programming", "coding"]):
                category = "skills"
                test_type = "K"
            elif any(x in url_lower for x in ["personality", "opq", "motivation", "behavior"]):
                category = "personality"
                test_type = "P"
            elif any(x in url_lower for x in ["verify", "cognitive", "numerical", "verbal", "reasoning"]):
                category = "cognitive"
                test_type = "A"
            elif any(x in url_lower for x in ["situational", "judgment", "sjt"]):
                category = "situational"
                test_type = "S"
            else:
                category = "other"
                test_type = "O"

            assessments.append(
                {
                    "name": name,
                    "url": url,
                    "category": category,
                    "test_type": test_type,
                    "test_types": test_type,
                    "description": "",
                }
            )

        # Deduplicate
        dedup: List[Dict] = []
        seen: Set[str] = set()
        for item in assessments:
            key = item["url"].rstrip("/")
            if key in seen:
                continue
            seen.add(key)
            dedup.append(item)

        print(f"Collected {len(dedup)} unique real URLs from training data")
        return dedup

    except Exception as e:
        print(f"Error bootstrapping from training data: {e}")
        return []


if __name__ == "__main__":
    scraper = SHLCatalogScraper()
    assessments = scraper.scrape_catalog()

    print(f"\nTotal assessments collected: {len(assessments)}")

    if assessments:
        scraper.save_to_file("shl_assessments.json")

        print("\nSample assessments:")
        for i, assessment in enumerate(assessments[:10]):
            print(f"{i+1}. {assessment['name']}")
            print(f"   URL: {assessment['url']}")
            print(f"   Category: {assessment['category']}, Type: {assessment['test_type']}\n")

        if len(assessments) >= 377:
            print(f"✓ Successfully created real assessment catalog with {len(assessments)} items")
        else:
            print(
                f"⚠ Collected {len(assessments)} real items (<377). "
                "Retry scraping with stable network/browser setup."
            )
    else:
        print("✗ Failed to create assessment catalog")
