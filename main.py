from typing import Optional, Iterator

import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class UrlData:
    url: str
    emails: list[str]
    links: list['UrlData']
    occurrence: int = 1

    def __init__(self, url):
        self.url = url


url_worked_on: dict[str, str] = {}

email_regex = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
found_urls: dict[str, UrlData] = {}
domains: dict[str, set[UrlData]] = {}


def extract_emails_from_html(html: str) -> list[str]:
    return email_regex.findall(html)


def extract_urls_from_html(base_url: str, html: str) -> Iterator[str]:
    soup = BeautifulSoup(html, "html.parser")
    return (urljoin(base_url, link.get("href")) for link in soup.find_all("a"))


async def scrap_emails_and_urls_from_url(url: str) -> UrlData:
    if url in found_urls:
        found_urls[url].occurrence += 1
        return found_urls[url]
    this_page = UrlData(url)
    found_urls[url] = this_page
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            html = await response.text()
    this_page.emails = extract_emails_from_html(html)
    this_page.links = await asyncio.gather(*(
        scrap_emails_and_urls_from_url(url) for url in extract_urls_from_html(url, html)
    ))
    found_urls[url] = this_page
    domain = urlparse(url).netloc
    if domain not in domains:
        domains[domain] = set()
    domains[domain].add(this_page)
    return this_page


async def scrapper(urls: list[str]):
    await asyncio.gather(*(scrap_emails_and_urls_from_url(url) for url in urls))
    for domain, urls in domains.items():
        most_significant_url_strength = 0
        most_significant_url: Optional[UrlData] = None
        for url in urls:
            url_strength = len(url.emails) + len(url.links) + url.occurrence
            if url_strength > most_significant_url_strength:
                most_significant_url_strength = url_strength
                most_significant_url = url

        print(f"most significant url {most_significant_url.url} with strength {most_significant_url_strength}")


if __name__ == '__main__':
    asyncio.run(scrapper(['http://127.0.0.1:8080/index.html']))
