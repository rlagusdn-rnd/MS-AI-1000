import os
from os import PathLike

from typing import Dict, Union, List
from typing import Union, Optional, Callable, List, Tuple

import cv2
import numpy as np
import torch
from .base_extractor import BaseExtractor
import subprocess
import platform
from torch import Tensor


def which_ffmpeg() -> str:
    '''Determines the path to ffmpeg library

    Returns:
        str -- path to the library
    '''
    # Determine the platform on which the program is running
    if platform.system().lower() == 'windows':
        result = subprocess.run(['where', 'ffmpeg'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ffmpeg_path = result.stdout.decode('utf-8').replace('\r\n', '')
    else:
        result = subprocess.run(['which', 'ffmpeg'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ffmpeg_path = result.stdout.decode('utf-8').replace('\n', '')
    return ffmpeg_path

def reencode_video_with_diff_fps(video_path: str, tmp_path: str, extraction_fps: float) -> str:
    '''Reencodes the video given the path and saves it to the tmp_path folder.

    Args:
        video_path (str): original video
        tmp_path (str): the folder where tmp files are stored (will be appended with a proper filename).
        extraction_fps (float): target fps value

    Returns:
        str: The path where the tmp file is stored. To be used to load the video from
    '''
    assert which_ffmpeg() != '', 'Is ffmpeg installed? Check if the conda environment is activated.'
    assert video_path.endswith('.mp4'), 'The file does not end with .mp4. Comment this if expected'
    # create tmp dir if doesn't exist
    os.makedirs(tmp_path, exist_ok=True)

    # form the path to tmp directory
    new_path = os.path.join(tmp_path, f'{Path(video_path).stem}_new_fps.mp4')
    cmd = f'{which_ffmpeg()} -hide_banner -loglevel panic '
    cmd += f'-y -i {video_path} -filter:v fps=fps={extraction_fps} {new_path}'
    subprocess.call(cmd.split())

    return new_path


class VideoLoader:
    def __init__(self,
                 path: Union[str, PathLike],
                 batch_size: int = 1,
                 fps: Optional[int] = None,
                 total: Optional[int] = None,
                 tmp_path: Optional[Union[str, PathLike]] = 'tmp',
                 keep_tmp: Optional[bool] = False,
                 transform: Optional[Callable] = None,
                 overlap: Optional[int] = 0
                 ):
        '''
        Args:
            path: The path of the video
            batch_size: len(result) = batch_size
            fps: Extract frames by fps. The parameter 'fps' and 'total' is mutually exclusive
            total: Extract frames by a fix number. The parameter 'fps' and 'total' is mutually exclusive
            tmp_path: Path of temporary file(s).
            keep_tmp: whether keep the temporary file.
            transform: A Callable object that applies transformation on each [3, H, W] images.
            overlap: Overlap of two adjacent batches.
        Returns:
            Tuple of (batch, times, indices)
            batch: a list of collected features
            times: the corresponding timestamp of the above features in milliseconds.
            indices: the corresponding indices of the above features. start from zero.
        '''
        # sanity check & save properties
        assert type(batch_size) is int and batch_size > 0
        assert type(overlap) is int and 0 <= overlap < batch_size
        self.batch_size = batch_size
        self.transform = transform
        self.overlap = overlap
        self.keep_tmp = keep_tmp
        self.have_generated_tmp_file = False

        if fps is not None and total is not None:
            raise ValueError(f"You can only choose one frame extracting method."
                             f" The parameter 'fps' and 'total' is mutually exclusive")
        elif fps is not None:  # new fps
            self.path = reencode_video_with_diff_fps(path, tmp_path=tmp_path, extraction_fps=fps)
            self.have_generated_tmp_file = True
            for k, v in self._get_video_prop(self.path).items():
                self.__setattr__(k, v)
        elif total is not None:  # fix number of frames
            video_prop = self._get_video_prop(path)
            self.height, self.width = video_prop['height'], video_prop['width']
            self.num_frames = total
            self.fps = total * video_prop['fps'] / video_prop['num_frames']
            self.path = reencode_video_with_diff_fps(path, tmp_path=tmp_path, extraction_fps=self.fps)
            self.have_generated_tmp_file = True
        else:  # old fps
            for k, v in self._get_video_prop(path).items():
                self.__setattr__(k, v)
            self.path = path

    def __iter__(self):
        self.cap = cv2.VideoCapture(self.path)
        self.current_idx = 0  # maintain the index of current frame instead of getting property in CV2 to avoid bugs
        self._last_batch, self._last_times, self._last_indices = [], [], []  # cache the overlap
        # BUG of cv2:
        # Sometimes frame#0 is missing, which needs to skip.
        frame_exists, _ = self.cap.read()
        if frame_exists:  # if not missing, go back to the start
            self.cap.release()
            self.cap = cv2.VideoCapture(self.path)
        else:
            print('Detect missing frame')  # For debug
        return self

    def __next__(self) -> Tuple[List[Union[np.ndarray, Tensor]], List[float], List[int]]:
        """
        Normally, a call will read `batch_size-overlap` frames from the video and `overlap` frames from the cache.
        As exceptions, the first batch reads `batch_size` frames and the last batch may contain fewer frames.
        """
        if not self.cap.isOpened():
            raise StopIteration
        # If all frames have been read at the beginning, raise StopIteration
        if self.current_idx == len(self):
            raise StopIteration

        # load overlap
        batch, times, indices = [], [], []
        if self.overlap != 0 and self.current_idx != 0:
            batch += self._last_batch
            times += self._last_times
            indices += self._last_indices

        while len(batch) < self.batch_size:
            frame_exists, rgb = self.cap.read()
            self.current_idx += 1
            if frame_exists:
                rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
                timestamps_ms = (self.current_idx - 1) / self.fps * 1000
                indices.append(self.current_idx - 1)
                times.append(timestamps_ms)
                if self.transform is not None:
                    batch.append(self.transform(rgb))
                else:
                    batch.append(rgb)
            else:
                # If read a non-exist frame, which indicates all frames of the video have been read,
                # release the VideoCapture and return the smaller batch. The StopIteration will be
                # raised in the next start.
                self.cap.release()
                break
        if len(batch) == 0:
            raise StopIteration

        # save overlap
        if self.overlap != 0:
            self._last_batch = batch[-self.overlap:]
            self._last_times = times[-self.overlap:]
            self._last_indices = indices[-self.overlap:]

        return batch, times, indices

    def __len__(self):
        return self.num_frames

    def __del__(self):
        # use `hasattr` in case the attribution has not been defined
        if hasattr(self, 'cap'):
            self.cap.release()
        if hasattr(self, 'have_generated_tmp_file') and hasattr(self, 'keep_tmp'):
            if self.have_generated_tmp_file and not self.keep_tmp:
                os.remove(self.path)

    @staticmethod
    def _get_video_prop(path):
        """Get properties of a video"""
        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        cap.release()
        return dict(fps=fps, num_frames=num_frames, height=height, width=width)


class BaseFrameWiseExtractor(BaseExtractor):
    '''Common things for all frame-wise extractors (such as ResNet or CLIP).
    However, optical flow has another parent class: OpticalFlowExtractor'''

    def __init__(self,
                 # BaseExtractor arguments
                 feature_type: str,
                 on_extraction: str,
                 tmp_path: str,
                 output_path: str,
                 keep_tmp_files: bool,
                 device: str,
                 # This class
                 model_name: str,
                 batch_size: int,
                 extraction_fps: Union[None, int],
                 extraction_total: Union[None, int],
                 show_pred: bool,
                 ) -> None:
        # init the BaseExtractor
        super().__init__(
            feature_type=feature_type,
            on_extraction=on_extraction,
            tmp_path=tmp_path,
            output_path=output_path,
            keep_tmp_files=keep_tmp_files,
            device=device,
        )
        # (Re-)Define arguments for this class
        self.model_name = model_name
        self.batch_size = batch_size
        self.extraction_fps = extraction_fps  # use `None` to skip reencoding and keep the original video fps
        self.extraction_total = extraction_total
        self.output_feat_keys = [self.feature_type, 'fps', 'timestamps_ms']
        self.show_pred = show_pred

    @torch.no_grad()
    def extract(self, video_path: str) -> Dict[str, np.ndarray]:
        '''Extracts features for a given video path.

        Arguments:
            video_path (str): a video path from which to extract features

        Returns:
            Dict[str, np.ndarray]: 'features_name', 'fps', 'timestamps_ms'
        '''

        video = VideoLoader(
            video_path,
            batch_size=self.batch_size,
            fps=self.extraction_fps,
            total=self.extraction_total,
            tmp_path=self.tmp_path,
            keep_tmp=self.keep_tmp_files,
            transform=lambda x: self.transforms(x).unsqueeze(0)
        )
        vid_feats = []
        timestamps_ms = []
        for batch, timestamp_ms, idx in video:
            # batch = torch.stack(batch, dim=0)
            batch_feats = self.run_on_a_batch(batch)
            vid_feats.extend(batch_feats.tolist())
            timestamps_ms.extend(timestamp_ms)

        features_with_meta = {
            self.feature_type: np.array(vid_feats),
            'fps': np.array(video.fps),
            'timestamps_ms': np.array(timestamps_ms)
        }

        return features_with_meta

    def run_on_a_batch(self, batch: List[torch.Tensor]) -> torch.Tensor:
        model = self.name2module['model']
        batch = torch.cat(batch).to(self.device)
        batch_feats = model(batch)
        self.maybe_show_pred(batch_feats)
        return batch_feats
