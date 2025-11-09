from dataclasses import dataclass
import cv2
import numpy as np

@dataclass
class Stream:
    frame: np.ndarray
    mode: int
    exec_time: float
    progress_capt: float
    progress_proc: float
    resource: np.ndarray

    def __str__(self):
        """ Return a string representation of the stream object """
        _mode = {1: "view mode", 2: "reference mode", 3: "scan mode"}
        _capt = self.progress_capt*100 if self.mode != 1 else 0.0
        _proc = self.progress_proc*100 if self.mode != 1 else 0.0
        return (
            f"[Stream]\n"
            f"MODE: {_mode.get(self.mode)} -- "
            f"Exec Time: {self.exec_time:.2f}s\n"
            f"Progresso de captura: {_capt:.2f} -- "
            f"Progresso de processamento: {_proc:.2f}\n"
            f"Resource: {self.resource}\n"
        )

    def __post_init__(self):
        """ Ensure the frame is in BGR format """
        if len(self.frame.shape) == 2:
            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_GRAY2BGR)