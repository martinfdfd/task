from collections import defaultdict
import json
import math
import time

from PIL import Image
from io import BytesIO
import requests
from tqdm import tqdm


def resp2image(response):
    img = Image.open(BytesIO(response.content))
    return img


class Authentication:
    AUTH_ENDPOINT = "https://spaceknow.auth0.com/oauth/ro"

    def __init__(self, username, password, public_client):
        self.__password = password
        self.__username = username
        self.__public_client = public_client
        self._bearer_token = None

    @property
    def bearer(self):
        if not self._bearer_token:
            self._bearer_token = self._issue_JWT()

        return self._bearer_token

    def _issue_JWT(self):
        payload = {
            "client_id": self.__public_client,
            "username": self.__username,
            "password": self.__password,
            "connection": "Username-Password-Authentication",
            "grant_type": "password",
            "scope": "openid",
        }

        r = requests.post(
            self.AUTH_ENDPOINT, data=json.dumps(payload), headers=self.basic_header
        )
        return r.json()["id_token"]

    @property
    def authorization_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.bearer}",
        }

    @property
    def basic_header(self):
        return {
            "Content-Type": "application/json",
        }


class Api:
    CLIENT = None


class Base(Api):
    PROTOCOL = "https"
    DOMAIN = "api.spaceknow.com"
    STATUS_CHECK = "/tasking/get-status"

    def get_status(self, pipelineId):

        url = self.url_formatter(self.PROTOCOL, self.DOMAIN, self.STATUS_CHECK)

        payload = {"pipelineId": pipelineId}

        r = requests.post(
            url, data=json.dumps(payload), headers=self.CLIENT.authorization_headers
        )
        return r.json(), r.status_code

    def url_formatter(self, protocol, domain, uri):
        return f"{protocol}://{domain}{uri}"

    def request(self, url, payload, headers):
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        return (r.json(), r.status_code)

    def initiate(self, payload):
        url = self.url_formatter(self.PROTOCOL, self.DOMAIN, self.INITIATE_URL)

        return self.request(url, payload, self.CLIENT.authorization_headers)

    def retrieve(self, pipelineId) -> list:  # tiles
        url = self.url_formatter(self.PROTOCOL, self.DOMAIN, self.RETRIEVE_URL)

        payload = {"pipelineId": pipelineId}
        return self.request(url, payload, self.CLIENT.authorization_headers)


class Kraken(Base):
    INITIATE_URL = "/kraken/release/imagery/geojson/initiate"
    RETRIEVE_URL = "/kraken/release/imagery/geojson/retrieve"
    SCENE_ID = None
    STATUS = None

    def kraken_formatter(self, scenery_object):
        print("Total found sceneries", len(scenery_object))

        scene = scenery_object[1]
        sceneId = scene["sceneId"]
        geometry = scene["footprint"]
        return {
            "sceneIds": [i["sceneId"] for i in scenery_object],
            "geojson": {
                "geometry": geometry,
                "properties": {"name": "over Brisbane Airport"},
                "type": "Feature",
            },
        }

    def kraken_formatter_single(self, scene):
        sceneId = scene["sceneId"]
        geometry = scene["footprint"]
        return {
            "sceneId": sceneId,
            "extent": {
                "geometry": geometry,
                "properties": {"name": "over Brisbane Airport"},
                "type": "Feature",
            },
        }


class Kraken_GEO(Base):
    INITIATE_URL = "/kraken/release/cars/geojson/initiate"
    RETRIEVE_URL = "/kraken/release/cars/geojson/retrieve"


class SceneryAllocation(Base):  # 1
    INITIATE_URL = "/credits/area/allocate-geojson"


class Scenery(Base):  # 1
    INITIATE_URL = "/imagery/search/initiate"
    RETRIEVE_URL = "/imagery/search/retrieve"


class Tiles(Base):
    def get_detections(self, obj, maxzoom=None):
        mapId = obj["mapId"]
        images = []
        detections = []
        for tile in tqdm(obj["tiles"]):
            args = tile
            if maxzoom is not None:
                args[0] = maxzoom
            url = f"https://api.spaceknow.com/kraken/grid/{mapId}/-/{args[0]}/{args[1]}/{args[2]}/detections.geojson"
            r = requests.get(url, headers=self.CLIENT.authorization_headers)

            detections.append(r.json())

        return detections

    def get_images(self, obj):
        mapId = obj["mapId"]
        images = []
        for tile in tqdm(obj["tiles"]):
            args = tile
            try:
                url = f"https://api.spaceknow.com/kraken/grid/{mapId}/-/{args[0]}/{args[1]}/{args[2]}/truecolor.png"

                r = requests.get(url, headers=self.CLIENT.authorization_headers)
                images.append(resp2image(r))
            except Exception as e:
                print(e)
                images.append(None)

        return images


if __name__ == "__main__":

    auth_client = Authentication(Config.USERNAME, Config.PASSWORD, Config.PUBLIC_CLIENT)
    Api.CLIENT = auth_client

    scenery = Scenery()

    payload = {
        "extent": {
            "type": "Feature",
            "properties": {"name": "over Brisbane Airport"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [153.1140525504701, -27.384232208334343],
                        [153.11560217582382, -27.384232208334343],
                        [153.11715180117756, -27.384232208334343],
                        [153.1171518041458, -27.385608168490847],
                        [153.11715180711485, -27.38698412864734],
                        [153.11560218176123, -27.38698412864734],
                        [153.11405255640761, -27.38698412864734],
                        [153.11405255343834, -27.385608168490847],
                        [153.1140525504701, -27.384232208334343],
                    ]
                ],
            },
        },
        "provider": "gbdx",
        "dataset": "idaho-pansharpened",
        "startDatetime": "2018-01-01 00:00:00",
        "endDatetime": "2018-01-31 00:00:00",
        "minIntersection": 0.4,
        "onlyIngested": False,
    }

    resp_scenery, _ = scenery.initiate(payload)
    retrieved_scenery, status = scenery.retrieve(resp_scenery["pipelineId"])
    while status != 200:
        time.sleep(1)
        retrieved_scenery, status = scenery.retrieve(resp_scenery["pipelineId"])
        print("waiting", status, retrieved_scenery)

    kraken = Kraken()
    kraken_geo = Kraken_GEO()

    alloc_req = kraken.kraken_formatter(retrieved_scenery["results"])
    scenealloc = SceneryAllocation()
    allocate, status = scenealloc.initiate(alloc_req)
    print("Analyses will cost", allocate["cost"])

    def count_cars(obj):
        vehicle = defaultdict(int)
        for doc in obj:
            features = doc.get("features", [])
            if features:
                for feature in features:
                    prop = feature.get("properties")
                    vehicle[prop["class"]] += prop["count"]
        print(dict(vehicle))

    class SimpleAsyncHandler:
        def __init__(self, tasks):
            self.tasks = tasks

        def eval(self):
            for key, value in self.tasks.items():
                if not value["finish"]:
                    res, status = value["obj"].retrieve(value["pipelineId"])
                    value["status"] = status
                    if status == 200:
                        value["result"] = value["apply"](res)
                        value["finish"] = True

                    if status == 424:
                        value["finish"] = True

    handler = []

    for sc in retrieved_scenery["results"]:

        kraken_req = kraken.kraken_formatter_single(sc)
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
                "id": sc["sceneId"],
            },
            "kraken_geo": {
                "finish": False,
                "obj": Kraken(),
                "pipelineId": pipelineId_kg,
                "apply": Tiles().get_detections,
                "status": None,
                "result": None,
                "id": sc["sceneId"],
            },
        }

        handler.append(SimpleAsyncHandler(task))
