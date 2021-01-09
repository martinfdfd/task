from collections import defaultdict


def count_cars(obj):
    vehicle = defaultdict(int)
    for doc in obj:
        features = doc.get("features", [])
        if features:
            for feature in features:
                prop = feature.get("properties")
                vehicle[prop["class"]] += prop["count"]
    return dict(vehicle)
