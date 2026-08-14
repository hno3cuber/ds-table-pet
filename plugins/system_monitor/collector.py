import threading
import time

import psutil
import pynvml


class CpuGpuCollector:
    def __init__(self, interval_s: float = 1.0):
        self.interval_s = interval_s
        self._snapshot = {"cpu": 0.0, "gpu": 0.0, "gpu_ok": False}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._nvml_handle = None

    def read_cpu(self) -> float:
        return psutil.cpu_percent(interval=None)

    def read_gpu(self) -> tuple[float, bool]:
        try:
            if self._nvml_handle is None:
                pynvml.nvmlInit()
                self._nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = pynvml.nvmlDeviceGetUtilizationRates(self._nvml_handle)
            return float(util.gpu), True
        except Exception:
            return 0.0, False

    def _update(self):
        cpu = self.read_cpu()
        try:
            gpu, gpu_ok = self.read_gpu()
        except Exception:
            # read_gpu 自身已吞异常；此处兜底意外异常，避免采集线程死亡
            gpu, gpu_ok = 0.0, False
        with self._lock:
            self._snapshot = {"cpu": cpu, "gpu": gpu, "gpu_ok": gpu_ok}

    def _loop(self):
        self.read_cpu()  # 预热：psutil 首次调用返回 0
        while not self._stop.is_set():
            time.sleep(self.interval_s)
            self._update()

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="cpu-gpu-collector")
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            # 保留 _thread 引用（test_start_stop_lifecycle 断言 stop 后仍可访问）

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._snapshot)
