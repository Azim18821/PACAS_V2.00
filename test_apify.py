from apify_client import ApifyClient

client = ApifyClient("apify_api_1a4jEwUXsMNvw5IK8lDrJM2GUFTOBQ2RQpmd")

run_input = {
    "listUrls": [
        { "url": "https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=OUTCODE%5E2445" }
    ],
    "propertyUrls": [],
    "fullScrape": True,
    "monitoringMode": False,
    "deduplicateAtTaskLevel": False,
    "fullPropertyDetails": True,
    "includePriceHistory": False,
    "includeNearestSchools": False,
    "enableDelistingTracker": False,
    "addEmptyTrackerRecord": False,
    "maxProperties": 1000,
    "proxy": { "useApifyProxy": True }
}

# Run the actor
run = client.actor("jKpgGfgRfzrGgEMa8").call(run_input=run_input)

# Fetch results
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["title"], "-", item["price"], "-", item["url"])
