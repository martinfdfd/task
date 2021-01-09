import time

from api import (
    Authentication,
    Api,
    Kraken,
    Kraken_GEO,
    SceneryAllocation,
    Scenery,
    Tiles,
)
import json
from handlers import SimpleAsyncHandler
from settings import Credentials
from utils import count_cars, open_geojson

Api.CLIENT = Authentication(
    Credentials.USERNAME, Credentials.PASSWORD, Credentials.PUBLIC_CLIENT
)


scenery = Scenery()
kraken = Kraken()
kraken_geo = Kraken_GEO()


geoconfig = {"provider": "gbdx",
    "dataset": "idaho-pansharpened",
    "startDatetime": "2018-01-01 00:00:00",
    "endDatetime": "2018-01-31 00:00:00",
    "minIntersection": 0.4,
    "onlyIngested": False,}


payload = open_geojson('geotest.geojson',geoconfig)


resp_scenery, _ = scenery.initiate(payload)
retrieved_scenery, status = scenery.retrieve(resp_scenery["pipelineId"])

while status != 200:
    time.sleep(1)
    retrieved_scenery, status = scenery.retrieve(resp_scenery["pipelineId"])
    print(
        "Retrieving sceneries",
        status,
    )


alloc_req = kraken.kraken_formatter(retrieved_scenery["results"])
scenealloc = SceneryAllocation()
allocate, status = scenealloc.initiate(alloc_req)
print("Analysis will cost", allocate["cost"])


handler = []


for scene in retrieved_scenery["results"]:

    kraken_req = kraken.kraken_formatter_single(scene)
    res, status = kraken.initiate(kraken_req)
    pipelineId_k = res["pipelineId"]
    res, status = kraken_geo.initiate(kraken_req)
    pipelineId_kg = res["pipelineId"]

    task = {
        "kraken": {
            "finish": False,
            "obj": Kraken_GEO(),
            "pipelineId": pipelineId_k,
            "apply": Tiles().get_images,
            "status": None,
            "result": None,
            "id": scene["sceneId"],
        },
        "kraken_geo": {
            "finish": False,
            "obj": Kraken(),
            "pipelineId": pipelineId_kg,
            "apply": Tiles().get_detections,
            "status": None,
            "result": None,
            "id": scene["sceneId"],
        },
    }

    handler.append(SimpleAsyncHandler(task))

print("Retrieving detections and images from tiles")

while not all([i.tasks["kraken"]["finish"] for i in handler]) and not all(
    [i.tasks["kraken_geo"]["finish"] for i in handler]
):
    [i.eval() for i in handler]

    time.sleep(3)
    print("Waiting for retrieval...")

print("Number of cars")
for detection_task in handler:
    if detection_task.tasks["kraken_geo"]["status"] == 200:
        num_cars = count_cars(detection_task.tasks["kraken_geo"]["result"])
        print(f"sceneId: {detection_task.tasks['kraken_geo']['id']}", num_cars)
    else:
        print(
            f"sceneId: {detection_task.tasks['kraken_geo']['id']}",
            'Could not calculate because of "Something went wrong in the pipeline"',
        )


print("saving images")
for img_num, detection_task in enumerate(handler):
    if detection_task.tasks["kraken"]["status"] == 200:
        imgs = detection_task.tasks["kraken"]["result"]
        print(f"sceneId: {detection_task.tasks['kraken']['id']}", f"{img_num}.png")
        for n, img in enumerate(imgs):
            try:
                img.save(f"./images/{n}-{img_num}.png")
            except Exception as e:
                print("Could not save image", e)
    else:
        print(
            f"sceneId: {detection_task.tasks['kraken']['id']}",
            'Could not get image because of "Something went wrong in the pipeline"',
        )
