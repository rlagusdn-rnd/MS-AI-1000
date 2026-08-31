import sys
import os
from pathlib import Path

from typing import Dict, Union, List
import numpy as np
import torch
import torchvision
from torch.utils import data
from torch.utils.data import TensorDataset, DataLoader

from .transforms import (CenterCrop, Normalize, Resize,
                               ToFloatTensorInZeroOne, ToFloatTensorInZeroOne_Only_one)
                        
from ._base.base_framewise_extractor import BaseFrameWiseExtractor
import omegaconf
from .clip_src import clip
import cv2
import math
import os

from PIL import Image

class Img_Feature_Extraction_r21d(torch.nn.Module):
    def __init__(self):
        super().__init__()

        self.feature_type = 'r21d'
        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'

        r21d_model_cfgs = {
        'r2plus1d_18_16_kinetics': {
            'repo': None,
            'stack_size': 16, 'step_size': 16, 'num_classes': 400, 'dataset': 'kinetics'
        },
        'r2plus1d_34_32_ig65m_ft_kinetics': {
            'repo': 'moabitcoin/ig65m-pytorch', 'model_name_in_repo': 'r2plus1d_34_32_kinetics',
            'stack_size': 32, 'step_size': 32, 'num_classes': 400, 'dataset': 'kinetics'
        },
        'r2plus1d_34_8_ig65m_ft_kinetics': {
            'repo': 'moabitcoin/ig65m-pytorch', 'model_name_in_repo': 'r2plus1d_34_8_kinetics',
            'stack_size': 8, 'step_size': 8, 'num_classes': 400, 'dataset': 'kinetics'
        },
    }

        self.model_name = "r2plus1d_34_32_ig65m_ft_kinetics" #r2plus1d_34_32_ig65m_ft_kinetics
        self.model_def = r21d_model_cfgs[self.model_name]
        self.extraction_fps = None
        self.step_size = None # 24
        self.stack_size = None # 24

        if self.step_size is None:
            self.step_size = self.model_def['step_size']
        if self.stack_size is None:
            self.stack_size = self.model_def['stack_size']

        self.show_pred = False
        self.output_feat_keys = [self.feature_type]
        self.name2module = self.load_model()

        self.resize_transforms = torchvision.transforms.Compose([
                                ToFloatTensorInZeroOne(),
                                # ToFloatTensorInZeroOne_Only_one(),
                                Resize((128, 171)),
                                Normalize(mean=[0.43216, 0.394666, 0.37645], std=[0.22803, 0.22145, 0.216989]),
                                CenterCrop((112, 112))
                                ])  

    def preprocess(self, img):
        return self.resize_transforms(img)

    def forward(self, x):
        out = self.name2module['model'](x[:, :, :, :, :].to(self.device))

        # return out.cpu().numpy()
        return out


    def load_model(self) -> Dict[str, torch.nn.Module]:
            """Defines the models, loads checkpoints, sends them to the device.

            Raises:
                NotImplementedError: if a model is not implemented.

            Returns:
                Dict[str, torch.nn.Module]: model-agnostic dict holding modules for extraction and show_pred
            """
            if self.model_name == 'r2plus1d_18_16_kinetics':
                model = torchvision.models.video.r2plus1d_18(pretrained=True)
            else:
                model = torch.hub.load(
                    self.model_def['repo'],
                    model=self.model_def['model_name_in_repo'],
                    num_classes=self.model_def['num_classes'],
                    pretrained=True,
                )
            model = model.to(self.device)
            model.eval()
            # save the pre-trained classifier for show_preds and replace it in the net with identity
            class_head = model.fc
            model.fc = torch.nn.Identity()

            return {
                'model': model,
                'class_head': class_head,
            }

class Img_Feature_Extraction_Clip(BaseFrameWiseExtractor):
    def __init__(self, args: omegaconf.DictConfig, model_path, clip_classifiction_mode = False) -> None:
        super().__init__(
            feature_type=args.feature_type,
            on_extraction=args.on_extraction,
            tmp_path=args.tmp_path,
            output_path=args.output_path,
            keep_tmp_files=args.keep_tmp_files,
            device=args.device,
            model_name=args.model_name,
            batch_size=args.batch_size,
            extraction_fps=args.extraction_fps,
            extraction_total=args.extraction_total,
            show_pred=args.show_pred,
        )
        self.transforms = 'For CLIP, it is easier to define in .load_model method because we need input size'
        self.model_path = model_path

        self.name2module = self.load_model()

        if self.show_pred:
            pred_texts = args.get('pred_texts', None)
            # if the user didn't specify custom text descriptions, do zero-shot on Kinetics 400
            self.pred_texts = list(pred_texts)
            # .long() is required because torch.nn.Embedding allows only Longs for pytorch 1.7.1
            self.pred_texts_tok = clip.tokenize(self.pred_texts).long()
            self.text_feats = self.name2module['model.encode_text'](self.pred_texts_tok.to(self.device))


        self.clip_classifiction_mode = clip_classifiction_mode

    def load_model(self) -> Dict[str, torch.nn.Module]:
        """Defines the models, loads checkpoints, sends them to the device.
        For CLIP, it also sets the appropriate transforms

        Raises:
            NotImplementedError: if a model is not implemented.

        Returns:
            Dict[str, torch.nn.Module]: model-agnostic dict holding modules for extraction and show_pred
        """
        from torchvision.transforms import (CenterCrop, Compose, Normalize, Resize,
                                            ToTensor)
        from PIL import Image

        # if self.model_name in clip.available_models():
        #     model_path = self.model_name
        # elif self.model_name == 'custom':
        #     # Reserved methods for using custom weights
        #     # *There is a bug in original repo when loading not-jit weights,
        #     # *and ignore it for now.
        #     model_path = pathlib.Path(__file__).parent / 'checkpoints' / 'CLIP-custom.pth'
        #     if not model_path.exists():
        #         raise FileNotFoundError(f'{model_path}')
        # else:
        #     raise NotImplementedError(f'Model {self.model_name} not found')

        model, _ = clip.load(str(self.model_path), device=self.device)
        model.eval()

        # defining transforms
        # doing it here instead of __init__ because it is cleaner to access model input size from here
        input_size = model.visual.input_resolution

        self.transforms = Compose([
            lambda np_array: Image.fromarray(np_array),
            Resize(input_size, interpolation=Image.BICUBIC),
            CenterCrop(input_size),
            lambda image: image.convert('RGB'),
            ToTensor(),
            Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711)),
        ])

        return {
            'model': model.encode_image,
            'model.encode_text': model.encode_text,
            'model.logit_scale': model.logit_scale,
        }

    def forward(self, x):
        input_img = cv2.cvtColor(x, cv2.COLOR_BGR2RGB)
        batch = self.transforms(input_img).unsqueeze(0)

        model = self.name2module['model']
        batch = torch.cat([batch]).to(self.device)
        batch_feats = model(batch)
        if self.show_pred:
            logits = self.maybe_show_pred(batch_feats, self.text_feats)

            if self.clip_classifiction_mode == True:
                logits_norm = logits.softmax(dim=-1)
                return batch_feats, logits_norm

            return batch_feats, logits
        return batch_feats

    def maybe_show_pred(self, visual_feats: torch.Tensor, text_feats: torch.Tensor):
        # for each batch we will compute text representation: it is a bit redundant but it only
        # creates a problem during `show_pred`, i.e. debugging. It is not a big deal
            # to(device) is called here (instead of __init__) because device is defined in .extract()

            # visual_feats:T, 512  text_feats:N, 512
            visual_feats = visual_feats.to(device=self.device, dtype=torch.double)
            text_feats = text_feats.to(dtype=torch.double)

            # normalized features
            visual_feats = visual_feats / visual_feats.norm(dim=1, keepdim=True)
            text_feats = text_feats / text_feats.norm(dim=1, keepdim=True)

            # cosine similarity as logits
            logit_scale = self.name2module['model.logit_scale'].exp().to(dtype=visual_feats.dtype)
            logits = logit_scale * visual_feats @ text_feats.t()
            logits = logits.cpu()

            return logits

class Img_Feature_Extraction_cilp4clip(torch.nn.Module):
    def __init__(self, weight_path : str, device : str) -> None:
        from torchvision.transforms import Compose, Resize, CenterCrop, ToTensor, Normalize, InterpolationMode

        super().__init__()

        self.device = device
        self.model = self.load_model(weight_path)

        self.size = (224,224)
        self.resize_transforms = Compose([
                                lambda np_array: Image.fromarray(np_array),
                                Resize(self.size, interpolation=InterpolationMode.BICUBIC),            
                                CenterCrop(self.size),
                                lambda image: image.convert("RGB"),
                                ToTensor(),
                                Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711)),
                            ])

    def load_model(self, weight_path : str) : 
        from transformers import CLIPVisionModelWithProjection

        model = CLIPVisionModelWithProjection.from_pretrained(weight_path)
        model.eval()
        model.to(self.device)

        return model
    
    def preprocess(self, n_px, ):
        return self.resize_transforms(n_px).unsqueeze(0)

    def forward(self, x : List):
        """x : List of image (32, 3, 224, 224)
        """

        input_data = torch.cat(x, dim = 0)
        visual_output = self.model(input_data.to(self.device))
        visual_output = visual_output["image_embeds"]
        visual_output = visual_output / visual_output.norm(dim=-1, keepdim=True)
        visual_output = torch.mean(visual_output, dim=0)
        visual_output = visual_output / visual_output.norm(dim=-1, keepdim=True)

        return visual_output

class Swish(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.sigmoid = torch.nn.Sigmoid()

    def forward(self, x):
        return x * self.sigmoid(x)

class Action_Classification_Model_r21d_b0(torch.nn.Module):
    def __init__(self):
        super().__init__()

        self.block_cls = torch.nn.Sequential(
                        torch.nn.Linear(512, 128),
                        torch.nn.BatchNorm1d(128, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(128, 64),
                        torch.nn.BatchNorm1d(64, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(64, 3),
                        torch.nn.Softmax(),
        )

        self.init_weights()

    def init_weights(self):
        for m in self.modules():
            if isinstance(m, torch.nn.Linear):
                init_range = 1.0 / math.sqrt(m.weight.shape[1])
                # torch.nn.init.uniform_(m.weight, -init_range, init_range)
                torch.nn.init.xavier_uniform_(m.weight)



    def forward(self, x):
        output = self.block_cls(x)

        # output = self.block_2(x)

        return output
    
class Action_Classification_Model_r21d_b1(torch.nn.Module):
    def __init__(self):
        super().__init__()

        self.block = torch.nn.Sequential(
                        torch.nn.Flatten(),

                        torch.nn.Linear(512, 1024),
                        torch.nn.BatchNorm1d(1024, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(1024, 512),
                        torch.nn.BatchNorm1d(512, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(512, 128),
                        torch.nn.BatchNorm1d(128, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(128, 64),
                        torch.nn.BatchNorm1d(64, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(64, 3),
                        torch.nn.Softmax(),
        )

        self.init_weights()

    def init_weights(self):
        for m in self.modules():
            if isinstance(m, torch.nn.Linear):
                init_range = 1.0 / math.sqrt(m.weight.shape[1])
                # torch.nn.init.uniform_(m.weight, -init_range, init_range)
                torch.nn.init.xavier_uniform_(m.weight)

    def forward(self, x):
        output = self.block(x)

        return output

class Action_Classification_Model_Vit_b0(torch.nn.Module):
    def __init__(self):
        super().__init__()

        self.block = torch.nn.Sequential(
                        torch.nn.Flatten(),

                        torch.nn.Linear(16384, 1024),
                        torch.nn.BatchNorm1d(1024, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(1024, 64),
                        torch.nn.BatchNorm1d(64, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(64, 3),
                        torch.nn.Softmax(),
                        # torch.nn.Sigmoid(),
        )

        self.init_weights()

    def init_weights(self):
        for m in self.modules():
            if isinstance(m, torch.nn.Linear):
                init_range = 1.0 / math.sqrt(m.weight.shape[1])
                # torch.nn.init.uniform_(m.weight, -init_range, init_range)
                torch.nn.init.xavier_uniform_(m.weight)

    def forward(self, x):
        output = self.block(x)

        return output

class Action_Classification_Vit_b1(torch.nn.Module):
    def __init__(self):
        super().__init__()

        self.block = torch.nn.Sequential(
                        torch.nn.Flatten(),

                        torch.nn.Linear(16384, 2048),
                        torch.nn.BatchNorm1d(2048, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(2048, 512),
                        torch.nn.BatchNorm1d(512, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(512, 128),
                        torch.nn.BatchNorm1d(128, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(128, 64),
                        torch.nn.BatchNorm1d(64, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(64, 3),
                        torch.nn.Softmax(),
        )

        self.init_weights()

    def init_weights(self):
        for m in self.modules():
            if isinstance(m, torch.nn.Linear):
                init_range = 1.0 / math.sqrt(m.weight.shape[1])
                # torch.nn.init.uniform_(m.weight, -init_range, init_range)
                torch.nn.init.xavier_uniform_(m.weight)



    def forward(self, x):
        output = self.block(x)

        return output
    
class Action_Classification_Model_Vit_b2(torch.nn.Module):
    def __init__(self):
        super().__init__()

        self.block_0 = torch.nn.Sequential(
                        torch.nn.Flatten(),

                        torch.nn.Linear(16384, 2048),
                        torch.nn.BatchNorm1d(2048, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(2048, 1024),
                        torch.nn.BatchNorm1d(1024, momentum=0.99, eps=1e-3),
                        Swish(),


        )

        self.block_1 = torch.nn.Sequential(
                        torch.nn.Linear(1024, 512),
                        torch.nn.BatchNorm1d(512, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(512, 1024),
                        torch.nn.BatchNorm1d(1024, momentum=0.99, eps=1e-3),
                        Swish(),

        )


        self.block_2 = torch.nn.Sequential(

                        torch.nn.Linear(2048, 512),
                        torch.nn.BatchNorm1d(512, momentum=0.99, eps=1e-3),
                        Swish(),
                        
                        torch.nn.Linear(512, 64),
                        torch.nn.BatchNorm1d(64, momentum=0.99, eps=1e-3),
                        Swish(),
                        
                        torch.nn.Linear(64, 32),
                        torch.nn.BatchNorm1d(32, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(32, 3),
                        torch.nn.Softmax(),

        )

        self.init_weights()

    def init_weights(self):
        for m in self.modules():
            if isinstance(m, torch.nn.Linear):
                init_range = 1.0 / math.sqrt(m.weight.shape[1])
                # torch.nn.init.uniform_(m.weight, -init_range, init_range)
                torch.nn.init.xavier_uniform_(m.weight)



    def forward(self, x):
        x1 = self.block_0(x)
        x2 = self.block_1(x1)
        x12 = torch.cat([x1, x2], dim = 1)
        output = self.block_2(x12)

        return output

class Action_Classification_Model_Clip_c1(torch.nn.Module):
    def __init__(self):
        super().__init__()

        self.img_block = torch.nn.Sequential(
                        torch.nn.Flatten(),

                        torch.nn.Linear(16384, 2048),
                        torch.nn.BatchNorm1d(2048, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(2048, 512),
                        torch.nn.BatchNorm1d(512, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(512, 128),
                        torch.nn.BatchNorm1d(128, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(128, 64),
                        torch.nn.BatchNorm1d(64, momentum=0.99, eps=1e-3),
                        Swish(),

        )

        self.score_block = torch.nn.Sequential(
                        torch.nn.Flatten(),
                        
                        torch.nn.Linear(192, 128),
                        torch.nn.BatchNorm1d(128, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(128, 64),
                        torch.nn.BatchNorm1d(64, momentum=0.99, eps=1e-3),
                        Swish(),
        )

        self.end_block = torch.nn.Sequential(
                        torch.nn.Linear(128, 64),
                        torch.nn.BatchNorm1d(64, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(64, 3),
                        torch.nn.Softmax(),
        )

        self.init_weights()

    def init_weights(self):
        for m in self.modules():
            if isinstance(m, torch.nn.Linear):
                init_range = 1.0 / math.sqrt(m.weight.shape[1])
                # torch.nn.init.uniform_(m.weight, -init_range, init_range)
                torch.nn.init.xavier_uniform_(m.weight)

    def forward(self, x_img, x_score):
        img_output = self.img_block(x_img)
        score_output = self.score_block(x_score)
        x = torch.cat([img_output, score_output], dim = 1)
        output = self.end_block(x)

        return output

class Action_Classification_Model_Clip_c1_2(torch.nn.Module):
    def __init__(self):
        super().__init__()

        self.img_block = torch.nn.Sequential(
                        torch.nn.Flatten(),

                        torch.nn.Linear(16384, 2048),
                        torch.nn.BatchNorm1d(2048, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(2048, 512),
                        torch.nn.BatchNorm1d(512, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(512, 128),
                        torch.nn.BatchNorm1d(128, momentum=0.99, eps=1e-3),
                        Swish(),

                        torch.nn.Linear(128, 64),
                        torch.nn.BatchNorm1d(64, momentum=0.99, eps=1e-3),
                        Swish(),

        )

        self.end_block = torch.nn.Sequential(
                        torch.nn.Linear(256, 3),
                        torch.nn.Softmax(),
        )

        self.init_weights()

    def init_weights(self):
        for m in self.modules():
            if isinstance(m, torch.nn.Linear):
                init_range = 1.0 / math.sqrt(m.weight.shape[1])
                # torch.nn.init.uniform_(m.weight, -init_range, init_range)
                torch.nn.init.xavier_uniform_(m.weight)

    def forward(self, x_img, x_score):
        img_output = self.img_block(x_img)
        x = torch.cat([img_output, x_score], dim = 1)
        output = self.end_block(x)

        return output

# if __name__ == "__main__":
    # device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    # video_path = "./videos/C001101_003.mp4"

    # cap = cv2.VideoCapture(video_path)

    # resize_transforms = torchvision.transforms.Compose([
    #                     ToFloatTensorInZeroOne(),
    #                     # ToFloatTensorInZeroOne_Only_one(),
    #                     Resize((128, 171)),
    #                     Normalize(mean=[0.43216, 0.394666, 0.37645], std=[0.22803, 0.22145, 0.216989]),
    #                     CenterCrop((112, 112))
    #                 ])  
    
    # model = Img_Feature_Extraction_r21d()
    # cls_model = Action_Classification_Model().to(device)
    # cls_model.eval()

    # frame_num = 0
    # stack_size = 24
    # rgb_stack = []

    # while cap.isOpened():
    #     t0 = time.time()
    #     frame_exists, rgb_ori = cap.read()
        
    #     if frame_exists:
    #         frame_num += 1

    #         rgb = torch.tensor(cv2.cvtColor(rgb_ori, cv2.COLOR_BGR2RGB)).unsqueeze(0)
    #         rgb = resize_transforms(rgb)
    #         print(rgb.size())
    #         # rgb = rgb.squeeze(0)

    #         rgb_stack.append(rgb)

    #         with torch.no_grad():
    #             if len(rgb_stack) - 1 == stack_size:

    #                 rgb_stack_input = torch.cat(rgb_stack, dim = 1).to(device).unsqueeze(0)
    #                 img_feature = model(rgb_stack_input)
    #                 result = cls_model(img_feature)

    #                 print(result.shape)
    #                 print(result)

    #                 rgb_stack = rgb_stack[1:]

    #         print("FPS: ", 1/(time.time() - t0))

    #         cv2.imshow("img", rgb_ori)
    #         cv2.waitKey(1)

    #     else:
    #         print("End of video")
    #         break

    # device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    # video_path = "./videos/00000000.mp4"

    # cap = cv2.VideoCapture(video_path)

    # model = Img_Feature_Extraction_cilp()
    # # cls_model = Action_Classification_Model().to(device)
    # # cls_model.eval()

    # frame_num = 0
    # rgb_stack = []

    # while cap.isOpened():
    #     t0 = time.time()
    #     frame_exists, rgb_ori = cap.read()
        

    #     with torch.no_grad():

    #         img_feature = model(rgb_ori)
    #         print(img_feature.keys())
    #         print(img_feature["clip"].shape)


    #     print("FPS: ", 1/(time.time() - t0))

    #     cv2.imshow("img", rgb_ori)
    #     key = cv2.waitKey(1)

    #     if key == ord('q'):
    #         cv2.destroyAllWindows()
    #         break
