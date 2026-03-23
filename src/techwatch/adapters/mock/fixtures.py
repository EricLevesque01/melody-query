"""Realistic mock fixture data for demo mode.

These fixtures produce the same shape as real API responses from Best Buy and
eBay, so the normalization and scoring engines work identically. No network
calls are made.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

# ── Best Buy mock products ──────────────────────────────────────────────


BESTBUY_PRODUCTS: list[dict] = [
    {
        "sku": 6565042,
        "name": "Lenovo ThinkPad X1 Carbon Gen 11 14\" Laptop - Intel Core i7-1365U - 16GB Memory - 512GB SSD - Black",
        "brandName": "Lenovo",
        "modelNumber": "21HM004HUS",
        "upc": "196802350334",
        "categoryPath": [
            {"name": "Computers & Tablets", "id": "abcat0500000"},
            {"name": "Laptops", "id": "abcat0502000"},
            {"name": "All Laptops", "id": "abcat0502001"},
        ],
        "salePrice": 1099.99,
        "regularPrice": 1449.99,
        "onSale": True,
        "savings": "350.00",
        "savingsAsPercentageOfRegularPrice": "24",
        "priceUpdateDate": "2026-05-04T10:00:00",
        "freeShipping": True,
        "shippingCost": 0.0,
        "details": [
            {"name": "Processor Model", "value": "Intel Core i7-1365U"},
            {"name": "System Memory RAM", "value": "16 GB"},
            {"name": "Total Storage Capacity", "value": "512 GB"},
            {"name": "Screen Size", "value": "14"},
            {"name": "GPU Brand", "value": "Intel Iris Xe"},
        ],
        "condition": "New",
        "image": "https://pisces.bbystatic.com/image2/BestBuy_US/images/products/6565/6565042_sd.jpg",
        "url": "https://www.bestbuy.com/site/lenovo-thinkpad-x1-carbon-gen11/6565042.p",
        "customerReviewAverage": 4.6,
        "customerReviewCount": 127,
        "inStoreAvailability": True,
        "onlineAvailability": True,
        "shortDescription": "14\" WUXGA (1920 x 1200) IPS, Intel Core i7-1365U, 16GB RAM, 512GB SSD",
    },
    {
        "sku": 6564289,
        "name": "Lenovo ThinkPad X1 Carbon Gen 11 14\" Laptop - Intel Core i5-1345U - 16GB Memory - 256GB SSD - Black",
        "brandName": "Lenovo",
        "modelNumber": "21HM004GUS",
        "upc": "196802350327",
        "categoryPath": [
            {"name": "Computers & Tablets", "id": "abcat0500000"},
            {"name": "Laptops", "id": "abcat0502000"},
        ],
        "salePrice": 849.99,
        "regularPrice": 1149.99,
        "onSale": True,
        "savings": "300.00",
        "savingsAsPercentageOfRegularPrice": "26",
        "priceUpdateDate": "2026-05-03T14:00:00",
        "freeShipping": True,
        "shippingCost": 0.0,
        "details": [
            {"name": "Processor Model", "value": "Intel Core i5-1345U"},
            {"name": "System Memory RAM", "value": "16 GB"},
            {"name": "Total Storage Capacity", "value": "256 GB"},
            {"name": "Screen Size", "value": "14"},
            {"name": "GPU Brand", "value": "Intel Iris Xe"},
        ],
        "condition": "New",
        "image": "https://pisces.bbystatic.com/image2/BestBuy_US/images/products/6564/6564289_sd.jpg",
        "url": "https://www.bestbuy.com/site/lenovo-thinkpad-x1-carbon-gen11/6564289.p",
        "customerReviewAverage": 4.4,
        "customerReviewCount": 89,
        "inStoreAvailability": True,
        "onlineAvailability": True,
        "shortDescription": "14\" WUXGA (1920 x 1200) IPS, Intel Core i5-1345U, 16GB RAM, 256GB SSD",
    },
    {
        "sku": 6565199,
        "name": "Lenovo ThinkPad X1 Carbon Gen 10 14\" Laptop - Intel Core i7-1260P - 16GB Memory - 512GB SSD - Deep Black",
        "brandName": "Lenovo",
        "modelNumber": "21CB00B1US",
        "upc": "196378753867",
        "categoryPath": [
            {"name": "Computers & Tablets", "id": "abcat0500000"},
            {"name": "Laptops", "id": "abcat0502000"},
        ],
        "salePrice": 879.99,
        "regularPrice": 1379.99,
        "onSale": True,
        "savings": "500.00",
        "savingsAsPercentageOfRegularPrice": "36",
        "priceUpdateDate": "2026-05-02T09:00:00",
        "freeShipping": True,
        "shippingCost": 0.0,
        "details": [
            {"name": "Processor Model", "value": "Intel Core i7-1260P"},
            {"name": "System Memory RAM", "value": "16 GB"},
            {"name": "Total Storage Capacity", "value": "512 GB"},
            {"name": "Screen Size", "value": "14"},
            {"name": "GPU Brand", "value": "Intel Iris Xe"},
        ],
        "condition": "New",
        "image": "https://pisces.bbystatic.com/image2/BestBuy_US/images/products/6565/6565199_sd.jpg",
        "url": "https://www.bestbuy.com/site/lenovo-thinkpad-x1-carbon-gen10/6565199.p",
        "customerReviewAverage": 4.7,
        "customerReviewCount": 214,
        "inStoreAvailability": False,
        "onlineAvailability": True,
        "shortDescription": "14\" WUXGA, 12th Gen Intel Core i7, 16GB RAM, 512GB SSD",
    },
]

BESTBUY_OPENBOX: list[dict] = [
    {
        "sku": 6565042,
        "name": "Lenovo ThinkPad X1 Carbon Gen 11 14\" Laptop - Open Box Excellent",
        "brandName": "Lenovo",
        "modelNumber": "21HM004HUS",
        "upc": "196802350334",
        "categoryPath": [
            {"name": "Computers & Tablets", "id": "abcat0500000"},
            {"name": "Laptops", "id": "abcat0502000"},
        ],
        "salePrice": 879.99,
        "regularPrice": 1449.99,
        "onSale": True,
        "savings": "570.00",
        "savingsAsPercentageOfRegularPrice": "39",
        "priceUpdateDate": "2026-05-04T18:00:00",
        "freeShipping": True,
        "shippingCost": 0.0,
        "details": [
            {"name": "Processor Model", "value": "Intel Core i7-1365U"},
            {"name": "System Memory RAM", "value": "16 GB"},
            {"name": "Total Storage Capacity", "value": "512 GB"},
            {"name": "Screen Size", "value": "14"},
        ],
        "condition": "Open-Box Excellent - Certified",
        "image": "https://pisces.bbystatic.com/image2/BestBuy_US/images/products/6565/6565042_sd.jpg",
        "url": "https://www.bestbuy.com/site/lenovo-thinkpad-x1-carbon-gen11/6565042.p?openbox=true",
        "customerReviewAverage": 4.6,
        "customerReviewCount": 127,
        "inStoreAvailability": True,
        "onlineAvailability": True,
        "shortDescription": "Open Box Excellent - Certified. Full warranty. 14\" WUXGA, i7, 16GB, 512GB SSD",
    },
    {
        "sku": 6564289,
        "name": "Lenovo ThinkPad X1 Carbon Gen 11 14\" Laptop - Open Box Satisfactory",
        "brandName": "Lenovo",
        "modelNumber": "21HM004GUS",
        "upc": "196802350327",
        "categoryPath": [
            {"name": "Computers & Tablets", "id": "abcat0500000"},
            {"name": "Laptops", "id": "abcat0502000"},
        ],
        "salePrice": 649.99,
        "regularPrice": 1149.99,
        "onSale": True,
        "savings": "500.00",
        "savingsAsPercentageOfRegularPrice": "43",
        "priceUpdateDate": "2026-05-04T12:00:00",
        "freeShipping": True,
        "shippingCost": 0.0,
        "details": [
            {"name": "Processor Model", "value": "Intel Core i5-1345U"},
            {"name": "System Memory RAM", "value": "16 GB"},
            {"name": "Total Storage Capacity", "value": "256 GB"},
            {"name": "Screen Size", "value": "14"},
        ],
        "condition": "Open-Box Satisfactory",
        "image": "https://pisces.bbystatic.com/image2/BestBuy_US/images/products/6564/6564289_sd.jpg",
        "url": "https://www.bestbuy.com/site/lenovo-thinkpad-x1-carbon-gen11/6564289.p?openbox=true",
        "customerReviewAverage": 4.4,
        "customerReviewCount": 89,
        "inStoreAvailability": True,
        "onlineAvailability": False,
        "shortDescription": "Open Box Satisfactory. Minor cosmetic wear. 14\" WUXGA, i5, 16GB, 256GB SSD",
    },
]

# ── eBay mock items ─────────────────────────────────────────────────


EBAY_ITEMS: list[dict] = [
    {
        "itemId": "v1|295178631485|0",
        "title": "Lenovo ThinkPad X1 Carbon Gen 10 14\" (512GB SSD, i7-1260P, 16GB) Laptop - USED",
        "price": {"value": "629.99", "currency": "USD"},
        "conditionId": "3000",
        "condition": "Used",
        "categories": [
            {"categoryId": "177", "categoryName": "Laptops & Netbooks"},
        ],
        "shippingOptions": [
            {
                "shippingCost": {"value": "0.00", "currency": "USD"},
                "type": "FIXED",
                "shippingServiceCode": "ShippingMethodStandard",
            }
        ],
        "seller": {
            "username": "tech_deals_2024",
            "feedbackPercentage": "99.2",
            "feedbackScore": "4521",
        },
        "itemWebUrl": "https://www.ebay.com/itm/295178631485",
        "brand": "Lenovo",
    },
    {
        "itemId": "v1|295189442876|0",
        "title": "Lenovo ThinkPad X1 Carbon Gen 9 14\" (1TB SSD, i7-1185G7, 32GB) Laptop - Excellent",
        "price": {"value": "549.00", "currency": "USD"},
        "conditionId": "3000",
        "condition": "Used",
        "categories": [
            {"categoryId": "177", "categoryName": "Laptops & Netbooks"},
        ],
        "shippingOptions": [
            {
                "shippingCost": {"value": "12.99", "currency": "USD"},
                "type": "FIXED",
            }
        ],
        "seller": {
            "username": "refurb_nation",
            "feedbackPercentage": "98.7",
            "feedbackScore": "12890",
        },
        "itemWebUrl": "https://www.ebay.com/itm/295189442876",
        "brand": "Lenovo",
    },
    {
        "itemId": "v1|296201557392|0",
        "title": "Lenovo ThinkPad X1 Carbon Gen 11 14\" i7-1365U 16GB 512GB SSD - Certified Refurbished",
        "price": {"value": "749.99", "currency": "USD"},
        "conditionId": "2000",
        "condition": "Certified - Refurbished",
        "categories": [
            {"categoryId": "177", "categoryName": "Laptops & Netbooks"},
        ],
        "shippingOptions": [
            {
                "shippingCost": {"value": "0.00", "currency": "USD"},
                "type": "FIXED",
            }
        ],
        "seller": {
            "username": "lenovo_outlet_official",
            "feedbackPercentage": "99.8",
            "feedbackScore": "45230",
        },
        "itemWebUrl": "https://www.ebay.com/itm/296201557392",
        "brand": "Lenovo",
    },
    {
        "itemId": "v1|296333289104|0",
        "title": "ThinkPad X1 Carbon 5th Gen 14\" i7-7600U 16GB 256GB SSD Win 11 - Good",
        "price": {"value": "219.99", "currency": "USD"},
        "conditionId": "3000",
        "condition": "Used",
        "categories": [
            {"categoryId": "177", "categoryName": "Laptops & Netbooks"},
        ],
        "shippingOptions": [
            {
                "shippingCost": {"value": "8.50", "currency": "USD"},
                "type": "FIXED",
            }
        ],
        "seller": {
            "username": "surplus_center_tech",
            "feedbackPercentage": "97.1",
            "feedbackScore": "832",
        },
        "itemWebUrl": "https://www.ebay.com/itm/296333289104",
        "brand": "Lenovo",
    },
    {
        "itemId": "v1|296445872013|0",
        "title": "Lenovo ThinkPad X1 Carbon Gen 10 14\" WUXGA i5-1240P 8GB 256GB SSD - Like New",
        "price": {"value": "489.00", "currency": "USD"},
        "conditionId": "3000",
        "condition": "Used",
        "categories": [
            {"categoryId": "177", "categoryName": "Laptops & Netbooks"},
        ],
        "shippingOptions": [
            {
                "shippingCost": {"value": "0.00", "currency": "USD"},
                "type": "FIXED",
            }
        ],
        "seller": {
            "username": "corporate_liquidation",
            "feedbackPercentage": "99.5",
            "feedbackScore": "22145",
        },
        "itemWebUrl": "https://www.ebay.com/itm/296445872013",
        "brand": "Lenovo",
    },
]


def get_mock_bestbuy_products(keyword: str, **kwargs) -> list[dict]:
    """Return mock Best Buy product data filtered by keyword relevance."""
    kw = keyword.lower()
    results = [
        p for p in BESTBUY_PRODUCTS
        if any(w in p["name"].lower() for w in kw.split())
    ]
    if not results:
        results = BESTBUY_PRODUCTS[:2]
    max_price = kwargs.get("max_price")
    if max_price:
        results = [p for p in results if p["salePrice"] <= max_price]
    return results


def get_mock_bestbuy_openbox(keyword: str, **kwargs) -> list[dict]:
    """Return mock Best Buy open box data."""
    return BESTBUY_OPENBOX


def get_mock_ebay_items(keyword: str, **kwargs) -> list[dict]:
    """Return mock eBay item data filtered by keyword relevance."""
    kw = keyword.lower()
    results = [
        item for item in EBAY_ITEMS
        if any(w in item["title"].lower() for w in kw.split())
    ]
    if not results:
        results = EBAY_ITEMS[:3]
    price_max = kwargs.get("price_max")
    if price_max:
        results = [
            item for item in results
            if float(item["price"]["value"]) <= price_max
        ]
    return results
