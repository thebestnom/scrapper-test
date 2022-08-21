from typing import Optional, Iterator

import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class PageData:
    emails: list[str]
    links: list['PageData']


url_worked_on: dict[str, str] = {}

email_regex = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
found_urls: dict[str, PageData] = {}


def extract_emails_from_html(html: str) -> list[str]:
    return email_regex.findall(html)


def extract_urls_from_html(base_url: str, html: str) -> Iterator[str]:
    soup = BeautifulSoup(html, "html.parser")
    return (urljoin(base_url, link.get("href")) for link in soup.find_all("a"))


async def scrap_emails_and_urls_from_url(url: str) -> Optional[PageData]:
    if url in found_urls:
        return found_urls[url]
    this_page = PageData()
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
    return this_page


async def scrapper(urls: list[str]):
    print(await asyncio.gather(*(scrap_emails_and_urls_from_url(url) for url in urls)))


if __name__ == '__main__':
    asyncio.run(scrapper(['http://127.0.0.1:8080/index.html']))
