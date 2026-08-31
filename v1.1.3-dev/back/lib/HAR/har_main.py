import numpy as np
import torch
import time
import cv2

from back.lib.HAR.models.HAR_model import Img_Feature_Extraction_Clip, Action_Classification_Vit_b1
from omegaconf import OmegaConf

class Har_System():
    def __init__(self, model_weight_path, device, model_path, feature_extract = 'clip', model_yml_path = "./", stack_size = 32):
        self.id_dict = {}
        self.stack_size = stack_size


        model_weight = torch.load(model_weight_path)

        self.har_model = Action_Classification_Vit_b1()
        self.har_model.load_state_dict(model_weight["model_state_dict"])
        self.har_model.to(device).eval()

        self.device = device
        self.feature_extract = feature_extract

        # Load and patch the config
        cfg_path = model_yml_path + f'/{feature_extract}.yml'
        args = OmegaConf.load(cfg_path)
        args.feature_type = feature_extract
        args.batch_size = 1
        args.show_pred = True

        args.pred_texts = [ #'There is no person', 
                            #normal
                           'There is a moving person',                      #0
                           'There is a standing person',                    #1
                           'There is a sitting person',                     #2
                           #falldown
                           'There is a lying down person',                  #3
                            #fire
                            # "There is a smoke rising",                      #4
                            # "There is something that shines brightly",      #5
                            # "There is a campfire",                          #6
                            # "There is flame and fire soaring",              #7
                            # arsonist
                            # "A photo of a standing person",                 #8 normal
                            # "A photo of a walking person",                  #9
                            # "A photo of a bending person",                  #10
                            # "A photo of a squats person",                   #11
                            # "A photo of a man fighting a fire",             #12 fire
                            # "A photo of flames an fires soaring",           #13
                            # "A photo of a campfire",                        #14
                            # "A photo of a burning cooking pan",           
                            # "A photo of a man doing a barbecue",            #14
                            ]

        self.pred_texts = args.pred_texts
        self.img_extraction_model = Img_Feature_Extraction_Clip(args, 
                                                                model_path = model_path, 
                                                                clip_classifiction_mode = True)


    def update(self, id, camera_name, person_img):
        if camera_name not in self.id_dict.keys():
            self.id_dict[camera_name] = {}

        if person_img.shape[0] > 0 and person_img.shape[1] > 0:
            img_resize = self.har_img_processing(person_img)
        
            feature_data, clip_output = self.img_extraction_model.forward(img_resize)


            clip_falldown_top1 = int(np.argmax(clip_output[0][:4].detach().cpu().numpy()))
            clip_falldown_top1 = self.get_status_class(clip_falldown_top1)

            # clip_fire_top1 = int(np.argmax(clip_output[0][:8].cpu().numpy()))
            # clip_arsonist_top1 = int(np.argmax(clip_output[0][8:].cpu().numpy()))

            if id not in self.id_dict[camera_name].keys():
                self.id_dict[camera_name][id] = {"feature_buffer" : [feature_data.detach().cpu()],
                                    "last_time" : time.time(),
                                    "status" : [0],
                                    "clip_falldown" :[clip_falldown_top1],
                                    # "clip_fire" :[clip_fire_top1],
                                    # "clip_arsonist" :[clip_arsonist_top1],
                                    }
            else:
                self.id_dict[camera_name][id]["feature_buffer"].append(feature_data.detach().cpu())
                self.id_dict[camera_name][id]["last_time"] = time.time()
                self.id_dict[camera_name][id]["clip_falldown"].append(clip_falldown_top1)
                # self.id_dict[id]["clip_fire"].append(logits_fire_top1)
                # self.id_dict[id]["clip_arsonist"].append(logits_arsonist_top1)


            if len(self.id_dict[camera_name][id]["feature_buffer"]) == self.stack_size:
                self.id_status_update(camera_name, id)

        # else:
        #     print(f"fail update HAR {camera_name}:{id} ({person_img.shape[0]}, {person_img.shape[1]})")

    def id_status_update(self, camera_name, id):
        status = self.har_model(torch.cat(self.id_dict[camera_name][id]["feature_buffer"]).type(torch.FloatTensor).to(self.device).unsqueeze(0))
        cls = np.argmax(status.detach().cpu().numpy())
        self.id_dict[camera_name][id]["status"].append(int(cls))
        del self.id_dict[camera_name][id]["feature_buffer"][0]
        
        if id in self.id_dict[camera_name].keys() and len(self.id_dict[camera_name][id]["status"]) > 50:
            self.id_dict[camera_name][id]["status"].pop(0)

    def refresh_id_dict(self):
        for camera_name in self.id_dict.keys():
            expired_id_list = [id for id, data in self.id_dict[camera_name].items() if time.time() - data["last_time"] > 10]

            for id in expired_id_list:
                del self.id_dict[camera_name][id]

    def get_status_class(self, index):
        if index <= 2:
            return 0

        elif index == 3:
            return 1

        elif index >= 3:
            return 2 

    @staticmethod
    def har_img_processing(image, target_img_size=(224,224), padding_color=(0, 0, 0)):
        """
        Resizes an image to target dimensions while maintaining aspect ratio and adding padding.
        
        Parameters:
            image (numpy.ndarray): Input image to resize.
            target_img_size (tuple): Target dimensions (width, height) in pixels.
            padding_color (tuple): RGB values for padding color (default is black).
            
        Returns:
            numpy.ndarray: The resized and padded image.
        """
        if image is None:
            raise ValueError("Input image is None")

        height, width, _ = image.shape
        aspect_ratio = width / height
        target_aspect_ratio = target_img_size[0] / target_img_size[1]

        if aspect_ratio > target_aspect_ratio:
            new_width = target_img_size[0]
            new_height = int(target_img_size[0] / aspect_ratio)
        else:
            new_height = target_img_size[1]
            new_width = int(target_img_size[1] * aspect_ratio)

        resized_image = cv2.resize(image, (new_width, new_height))
        pad_height = max(0, target_img_size[1] - new_height)
        pad_width = max(0, target_img_size[0] - new_width)

        top_pad = pad_height // 2
        bottom_pad = pad_height - top_pad
        left_pad = pad_width // 2
        right_pad = pad_width - left_pad

        padded_image = cv2.copyMakeBorder(
            resized_image, top_pad, bottom_pad, left_pad, right_pad,
            cv2.BORDER_CONSTANT, value=padding_color
        )

        return padded_image