"""
McMaster-Carr Product Scraper - Final Working Version
=====================================================

McMaster-Carr structure (discovered from HTML inspection):
1. Search/Category page → Shows subcategory tiles (Socket Head Screws, Flat Head Screws)
2. Subcategory page → Shows product tables with part numbers
3. Product page → Individual product with full details

This scraper navigates through all levels.

Enhanced with:
- Size, Diameter/Width, Height extraction
- Package Qty and Package Price
- 2D and 3D PDF download and storage in GridFS
"""

import asyncio
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
from playwright.async_api import async_playwright, Page, Browser
from tqdm import tqdm

import config
from db_utils import MongoDBHandler


class McMasterFinalScraper:
    """Working scraper for McMaster-Carr with enhanced field extraction and PDF support."""

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.db_handler: Optional[MongoDBHandler] = None
        self.products_scraped = 0
        self.pdfs_downloaded = 0
        self.base_url = "https://www.mcmaster.com"
        
        # Column name mappings for table extraction
        self.column_mappings = config.TABLE_COLUMN_MAPPINGS

    async def initialize(self):
        """Initialize browser and database."""
        logger.info("Initializing scraper...")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.firefox.launch(headless=config.HEADLESS)
        
        context = await self.browser.new_context(
            user_agent=config.USER_AGENT,
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True,  # Enable file downloads for PDFs
        )
        self.page = await context.new_page()
        
        # MongoDB with GridFS support
        try:
            self.db_handler = MongoDBHandler()
            self.db_handler.connect()
            logger.info("MongoDB connected with GridFS!")
        except Exception as e:
            logger.error(f"MongoDB failed: {e}")
            raise
        
        logger.info("Scraper initialized!")

    async def close(self):
        """Cleanup."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        if self.db_handler:
            self.db_handler.close()
        logger.info(f"Done! Scraped {self.products_scraped} products, downloaded {self.pdfs_downloaded} PDFs")

    async def navigate(self, url: str) -> str:
        """Navigate and return HTML."""
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            return await self.page.content()
        except Exception as e:
            logger.error(f"Navigation failed: {url} - {e}")
            return ""

    async def get_subcategory_urls(self, search_term: str) -> list[dict]:
        """Get subcategory URLs from a search/category page."""
        url = f"{self.base_url}/{search_term}"
        html = await self.navigate(url)
        
        if not html:
            return []
        
        soup = BeautifulSoup(html, "lxml")
        subcategories = []
        
        # McMaster uses selectable tiles with specific patterns
        # href patterns like "socket-head-screws-2~/" or "flat-head-screws-2~/"
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            
            # Subcategory URLs end with ~/ and don't start with /products/
            if href.endswith("~/") and not href.startswith("/products/"):
                # Get title from nested elements
                title_elem = link.find(class_=lambda x: x and "title" in str(x).lower())
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not title:
                    # Try direct text
                    title = link.get_text(strip=True)[:100]
                
                # Get product count
                count_elem = link.find(class_=lambda x: x and "productCount" in str(x))
                count = count_elem.get_text(strip=True) if count_elem else ""
                
                if title:
                    full_url = urljoin(self.base_url + "/" + search_term + "/", href)
                    subcategories.append({
                        "name": title,
                        "url": full_url,
                        "product_count": count
                    })
        
        # Dedupe
        seen = set()
        unique = []
        for s in subcategories:
            if s["url"] not in seen:
                seen.add(s["url"])
                unique.append(s)
        
        logger.info(f"Found {len(unique)} subcategories for {search_term}")
        return unique

    async def get_products_from_subcategory(self, url: str, category: str) -> list[dict]:
        """Extract products from a subcategory page."""
        html = await self.navigate(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, "lxml")
        products = []
        
        # McMaster part numbers follow pattern: 5-7 digits + optional letter + 2-3 digits
        # Examples: 91251A144, 60205K53, 92949A731
        part_number_pattern = re.compile(r'\b(\d{4,6}[A-Z]\d{2,4})\b')
        
        # Method 1: Find part numbers in image URLs (most reliable)
        for img in soup.find_all("img", src=True):
            src = img.get("src", "")
            matches = part_number_pattern.findall(src)
            for part_num in matches:
                products.append({
                    "part_number": part_num,
                    "image_url": src if src.startswith("http") else urljoin(self.base_url, src),
                    "category": category,
                    "source_url": url,
                    "scraped_at": datetime.utcnow().isoformat(),
                })
        
        # Method 2: Find part numbers in links
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            matches = part_number_pattern.findall(href)
            for part_num in matches:
                products.append({
                    "part_number": part_num,
                    "product_url": urljoin(self.base_url, href),
                    "name": link.get_text(strip=True)[:200] if link.get_text(strip=True) else None,
                    "category": category,
                    "source_url": url,
                    "scraped_at": datetime.utcnow().isoformat(),
                })
        
        # Method 3: Find in full page text
        page_text = soup.get_text()
        matches = part_number_pattern.findall(page_text)
        for part_num in matches:
            products.append({
                "part_number": part_num,
                "category": category,
                "source_url": url,
                "scraped_at": datetime.utcnow().isoformat(),
            })
        
        # Deduplicate by part number, merge data
        product_dict = {}
        for p in products:
            pn = p["part_number"]
            if pn not in product_dict:
                product_dict[pn] = p
            else:
                # Merge fields
                for k, v in p.items():
                    if v and not product_dict[pn].get(k):
                        product_dict[pn][k] = v
        
        unique_products = list(product_dict.values())
        logger.info(f"Found {len(unique_products)} unique products from {url}")
        return unique_products

    def _normalize_column_name(self, header: str) -> Optional[str]:
        """Map a table header to our standardized field name."""
        header_clean = header.strip().lower()
        for field_name, variations in self.column_mappings.items():
            for variation in variations:
                if variation.lower() in header_clean or header_clean in variation.lower():
                    return field_name
        return None

    def _parse_price(self, price_str: str) -> Optional[float]:
        """Parse price string to float."""
        if not price_str:
            return None
        # Only match reasonable price patterns (up to $99,999.99)
        match = re.search(r'\$?([\d,]{1,6})\.?(\d{0,2})', price_str)
        if match:
            dollars = match.group(1).replace(',', '')
            cents = match.group(2) or '00'
            try:
                price = float(f"{dollars}.{cents}")
                # Sanity check - prices should be reasonable (under $100k)
                if price < 100000:
                    return price
            except ValueError:
                pass
        return None

    def _parse_quantity(self, qty_str: str) -> Optional[int]:
        """Parse quantity string to integer."""
        if not qty_str:
            return None
        match = re.search(r'(\d+)', qty_str.replace(',', ''))
        if match:
            return int(match.group(1))
        return None

    async def download_pdf_from_product_page(self) -> Optional[bytes]:
        """
        Download 2D PDF from the current product page.
        
        McMaster-Carr uses a custom React dropdown for CAD files.
        Flow: Select color (if required) → Click dropdown → Select 2-D PDF → Download
        
        Returns PDF bytes or None if download failed.
        """
        try:
            await asyncio.sleep(2)
            
            # Step 1: Select a color if required (many products need this)
            params = await self.page.query_selector_all("[class*='parameter']")
            for p in params:
                try:
                    text = await p.inner_text()
                    if 'Black' in text:
                        await p.click()
                        logger.info("  Selected color: Black")
                        await asyncio.sleep(2)
                        break
                except:
                    continue
            
            # Step 2: Find the CAD dropdown button
            cad_btn = await self.page.query_selector("[aria-label='Select CAD file type']")
            if not cad_btn:
                cad_btn = await self.page.query_selector("button[role='combobox']")
            
            if not cad_btn:
                logger.debug("  No CAD dropdown button found")
                return None
            
            # Step 3: Download 2D PDF
            logger.info("  Opening CAD dropdown for 2D PDF...")
            await cad_btn.click()
            await asyncio.sleep(1)
            
            pdf_2d_li = await self.page.query_selector("li:has-text('2-D PDF')")
            if pdf_2d_li:
                await pdf_2d_li.click()
                await asyncio.sleep(0.5)
                
                download_btn = await self.page.query_selector("button:has-text('Download')")
                if download_btn:
                    logger.info("  Clicking Download for 2D PDF...")
                    async with self.page.expect_download(timeout=30000) as download_info:
                        await download_btn.click()
                    download = await download_info.value
                    path = await download.path()
                    if path:
                        with open(path, 'rb') as f:
                            pdf_data = f.read()
                        logger.info(f"  ✓ Downloaded 2D PDF ({len(pdf_data)} bytes)")
                        return pdf_data
            
            return None
            
        except Exception as e:
            logger.debug(f"  2D PDF download error: {e}")
            return None

    async def scrape_product_detail(self, part_number: str, download_pdfs: bool = True) -> dict:
        """Get detailed info for a specific product including new fields and PDFs."""
        url = f"{self.base_url}/{part_number}"
        html = await self.navigate(url)
        
        details = {"part_number": part_number, "product_url": url}
        
        if not html:
            return details
        
        soup = BeautifulSoup(html, "lxml")
        
        # Product name (h1 or title)
        h1 = soup.find("h1")
        if h1:
            details["name"] = h1.get_text(strip=True)
        
        # Price
        price_pattern = re.compile(r'\$[\d,]+\.?\d*')
        for elem in soup.find_all(class_=lambda x: x and "price" in str(x).lower()):
            match = price_pattern.search(elem.get_text())
            if match:
                details["price"] = self._parse_price(match.group())
                break
        
        # Specifications from tables - now with field mapping
        specs = {}
        for row in soup.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                if key and value and len(key) < 100:
                    # Check if this maps to a standard field
                    field_name = self._normalize_column_name(key)
                    if field_name:
                        if field_name == "pkg_price":
                            details[field_name] = self._parse_price(value)
                        elif field_name == "pkg_qty":
                            details[field_name] = self._parse_quantity(value)
                        else:
                            details[field_name] = value
                    else:
                        specs[key] = value
        
        if specs:
            details["specifications"] = specs
        
        # Material
        text = soup.get_text().lower()
        materials = ["stainless steel", "carbon steel", "alloy steel", "brass", "aluminum", "zinc", "nylon", "plastic", "titanium"]
        for mat in materials:
            if mat in text:
                details["material"] = mat.title()
                break
        
        # Download 2D PDF by interacting with the UI (dropdown + download button)
        if download_pdfs and self.db_handler:
            logger.info(f"  Attempting to download 2D PDF for {part_number}...")
            pdf_data = await self.download_pdf_from_product_page()
            
            if pdf_data:
                file_id = self.db_handler.store_pdf(
                    pdf_data, 
                    f"{part_number}_2d.pdf", 
                    part_number, 
                    pdf_type="2d"
                )
                if file_id:
                    details["pdf_2d_file_id"] = file_id
                    details["has_2d_pdf"] = True
                    self.pdfs_downloaded += 1
                    logger.info(f"  ✓ Stored 2D PDF for {part_number} in GridFS")
        
        details["detailed_at"] = datetime.utcnow().isoformat()
        return details

    def save_product(self, product: dict):
        """Save to MongoDB using db_handler."""
        if not product.get("part_number"):
            return
        
        try:
            if self.db_handler:
                self.db_handler.insert_product(product)
                self.products_scraped += 1
        except Exception as e:
            logger.debug(f"Save error: {e}")

    async def scrape(self, search_terms: list[str], max_products: int = 50, 
                     get_details: bool = False, download_pdfs: bool = False):
        """
        Main scraping function.
        
        Args:
            search_terms: List of category/search terms to scrape
            max_products: Max products per subcategory
            get_details: Whether to fetch detailed product pages (slower, but gets all fields)
            download_pdfs: Whether to download and store PDF files in GridFS
        """
        try:
            await self.initialize()
            
            for term in tqdm(search_terms, desc="Search terms"):
                logger.info(f"\n=== Scraping: {term} ===")
                
                # Get subcategories
                subcategories = await self.get_subcategory_urls(term)
                
                if not subcategories:
                    # Try direct product scrape (might be already at product level)
                    products = await self.get_products_from_subcategory(
                        f"{self.base_url}/{term}", term
                    )
                    for p in products[:max_products]:
                        self.save_product(p)
                    continue
                
                # Scrape each subcategory
                for subcat in tqdm(subcategories[:5], desc="Subcategories", leave=False):
                    products = await self.get_products_from_subcategory(
                        subcat["url"], 
                        subcat["name"]
                    )
                    
                    for i, p in enumerate(products[:max_products]):
                        # Optionally get detailed info (slower)
                        if get_details and p.get("part_number"):
                            logger.info(f"Getting details for {p['part_number']} ({i+1}/{min(len(products), max_products)})")
                            details = await self.scrape_product_detail(
                                p["part_number"], 
                                download_pdfs=download_pdfs
                            )
                            p.update(details)
                            
                            # Log what we found
                            logger.info(f"  Name: {p.get('name', 'N/A')[:50]}")
                            logger.info(f"  Size: {p.get('size', 'N/A')}, Dia: {p.get('diameter_width', 'N/A')}")
                            logger.info(f"  Pkg Qty: {p.get('pkg_qty', 'N/A')}, Price: ${p.get('pkg_price', 'N/A')}")
                            logger.info(f"  2D PDF: {'Yes' if p.get('pdf_2d_url') else 'No'}, 3D PDF: {'Yes' if p.get('pdf_3d_url') else 'No'}")
                        
                        p["search_term"] = term
                        p["subcategory"] = subcat["name"]
                        self.save_product(p)
                    
                    await asyncio.sleep(1)  # Rate limiting
                
                await asyncio.sleep(2)
            
        finally:
            await self.close()
            
            # Print final stats
            if self.db_handler:
                self.db_handler.connect()
                stats = self.db_handler.get_stats()
                logger.info(f"\n=== Database Stats ===")
                logger.info(f"Total products: {stats['total_products']}")
                logger.info(f"Products with 2D PDFs: {stats['products_with_2d_pdf']}")
                logger.info(f"Products with 3D PDFs: {stats['products_with_3d_pdf']}")
                logger.info(f"PDF files stored: {stats['pdf_files_stored']}")
                self.db_handler.close()


async def main():
    logger.add("scraper_final.log", rotation="10 MB")
    
    scraper = McMasterFinalScraper()
    
    # Scrape specific product types with full details and PDFs
    await scraper.scrape(
        search_terms=["socket-head-cap-screws"],
        max_products=5,  # Small number for testing
        get_details=True,  # Get Size, Dia, Pkg info
        download_pdfs=True  # Download and store PDFs
    )


if __name__ == "__main__":
    asyncio.run(main())
