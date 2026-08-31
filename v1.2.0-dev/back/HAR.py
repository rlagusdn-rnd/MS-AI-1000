import time
import numpy as np

class Person_Info():
    def __init__(self):
        self.info = dict()

    def add_id(self, track_info):
        x1, y1, x2, y2, id_, conf, label, _ = track_info
        id_ = int(id_)
        
        self.info[id_] = {"trejectory" : [[int((x2 + x1)/2), int(y2)]],
                         "status" : [0],
                        #  "bbox" : [x1, y1, x2, y2],
                        #  "stop" : False,
                         "last_time" : time.time()}

    def update_id(self, track_info):
        if len(track_info):
            for x1, y1, x2, y2, id_, conf, label, _ in track_info:
                id_ = int(id_)
                if id_ in self.info.keys():
                    self.info[id_]["trejectory"].append([int((x2 + x1)/2), int(y2)]) 
                    # self.info[id_]["status"].append(status) 
                    # self.info[id_]["bbox"].append([x1, y1, x2, y2])
                    self.info[id_]["last_time"] = time.time()


                    if len(self.info[id_]["trejectory"]) > 60:
                        self.info[id_]["trejectory"].pop(0)

                else:
                    self.add_id([x1, y1, x2, y2, id_, conf, label, _])


        self.refresh_info()

    def update_status(self, id_, status):
        self.info[id_]["status"].append(status) 

        if len(self.info[id_]["status"]) > 11:
            self.info[id_]["status"].pop(0)

    def get_status(self, id_):
        if len(self.info[id_]["status"]) > 5:
            status_list, counts =  np.unique(np.array(self.info[id_]["status"][-5:]), return_counts=True)
            status = status_list[np.argmax(counts)]
        
        else:
            status_list, counts =  np.unique(np.array(self.info[id_]["status"]), return_counts=True)
            status = status_list[np.argmax(counts)]

        return status

    def refresh_info(self):
        delete_id = []
        for id_ in self.info.keys():
            if time.time() - self.info[id_]["last_time"] > 60:
                delete_id.append(id_)

        for id_ in delete_id:
            del self.info[id_]