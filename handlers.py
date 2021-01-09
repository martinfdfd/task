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
