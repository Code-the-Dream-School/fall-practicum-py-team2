import json
from datetime import datetime, timezone
from pathlib import Path

from pipeline.extract.extract import extract, BASE_URL, REGION_ID


def collect_snapshot():
    """Collecting a fresh bike-share snapshot into a local JSON file."""

    # Finding the station information and status API URLs
    feeds = extract(BASE_URL)["en"]["feeds"]
    feed_urls = {feed["name"]: feed["url"] for feed in feeds}

    # Downloading current station information and availability
    info = extract(feed_urls["station_information"])["stations"]
    status = extract(feed_urls["station_status"])["stations"]

    # Matching station information with its current availability
    status_by_id = {row["station_id"]: row for row in status}

    # Filtering stations for our San Francisco region
    stations = [
        {**station, **status_by_id.get(station["station_id"], {})}
        for station in info
        if str(station.get("region_id")) == REGION_ID
    ]

    # Creating a timestamp for this collection
    collected_at = datetime.now(timezone.utc)
    filename = f"stations_{collected_at:%Y%m%d_%H%M%S}.json"

    # Creating the local output directory
    output_dir = Path("data/kan28_snapshots")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Saving the snapshot without changing existing team files
    output_path = output_dir / filename

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "collected_at": collected_at.isoformat(),
                "stations": stations,
            },
            file,
            indent=2,
        )

    # Displaying the collection results
    print(f"Stations collected: {len(stations)}")
    print(f"Snapshot saved: {output_path}")


if __name__ == "__main__":
    collect_snapshot()