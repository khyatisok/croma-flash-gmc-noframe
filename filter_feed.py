import re
import requests
from lxml import etree

# =====================================================
# CONFIG
# =====================================================

CAMPAIGN_URL = "https://www.croma.com/campaign/24hrs-flash-sale-offers/c/7442"
GMC_FEED = "https://www.croma.com/gmcfeed.xml"

OUTPUT_FILE = "feed.xml"

# =====================================================

print("Downloading EDLP campaign page...")

session = requests.Session()

response = session.get(
    CAMPAIGN_URL,
    timeout=30
)

response.raise_for_status()

html = response.text

# Find current EDLP SKUs
skus = set(
    re.findall(
        r'"sku"\s*:\s*"(\d+)"',
        html
    )
)

print(f"Found {len(skus)} EDLP SKUs")

if not skus:
    raise Exception("No EDLP SKUs found. Feed update stopped.")

# =====================================================
# Download GMC Feed
# =====================================================

print("Downloading GMC feed...")

response = session.get(
    GMC_FEED,
    timeout=60
)

response.raise_for_status()

xml = response.content

root = etree.fromstring(xml)

ns = {
    "g": "http://base.google.com/ns/1.0"
}

channel = root.find("channel")

if channel is None:
    raise Exception("Could not find channel in GMC feed.")

items = channel.findall("item")

print(f"GMC feed contains {len(items)} products")

# =====================================================
# Update EDLP Products
# =====================================================

updated = 0

for item in items:

    sku_node = item.find("g:id", ns)

    if sku_node is None:
        continue

    sku = sku_node.text.strip()

    # -------------------------------------------------
    # Only modify current EDLP products
    # -------------------------------------------------

    if sku not in skus:
        continue

    # -------------------------------------------------
    # custom_label_3 = edlp
    # -------------------------------------------------

    custom_label_3 = item.find("g:custom_label_3", ns)

    if custom_label_3 is not None:
        custom_label_3.text = "edlp"

    # -------------------------------------------------
    # internal_label = ['edlp']
    # Place after custom_label_4
    # -------------------------------------------------

    custom_label_4 = item.find("g:custom_label_4", ns)

    if custom_label_4 is not None:

        # Remove existing internal_label if present
        # to prevent duplicates on repeated runs
        existing_internal_labels = item.findall(
            "g:internal_label",
            ns
        )

        for existing in existing_internal_labels:
            item.remove(existing)

        internal_label = etree.Element(
            "{http://base.google.com/ns/1.0}internal_label"
        )

        internal_label.text = "['edlp']"

        item.insert(
            list(item).index(custom_label_4) + 1,
            internal_label
        )

    updated += 1

    print(f"Updated EDLP SKU: {sku}")

# =====================================================
# Save Feed
# =====================================================

tree = etree.ElementTree(root)

tree.write(
    OUTPUT_FILE,
    encoding="utf-8",
    xml_declaration=True,
    pretty_print=True
)

print("----------------------------------------")
print(f"EDLP products updated: {updated}")
print(f"Output created: {OUTPUT_FILE}")
print("Done.")
