from collections import defaultdict

import json


def count_cars(obj):
    vehicle = defaultdict(int)
    for doc in obj:
        features = doc.get("features", [])
        if features:
            for feature in features:
                prop = feature.get("properties")
                vehicle[prop["class"]] += prop["count"]
    return dict(vehicle)


def open_geojson(filename, extras):
    with open(filename) as json_file:
        data = json.load(json_file)
        geojson = {"extent": data}
        for key, value in extras.items():
            geojson[key] = value
    return geojson
