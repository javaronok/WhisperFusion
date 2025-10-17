import numpy as np
import ctranslate2

model_path = "/Users/dmitriy/.cache/huggingface/hub/models--Systran--faster-whisper-small/snapshots/536b0662742c02347bc0e980a01041f333bce120"

def get_ctranslate2_storage(segment: np.ndarray) -> ctranslate2.StorageView:
    segment = np.ascontiguousarray(segment)
    segment = ctranslate2.StorageView.from_array(segment)
    return segment

m = ctranslate2.models.Whisper(model_path,
                               device="cpu",
                               device_index=0,
                               compute_type="int8",
                               intra_threads=0,
                               inter_threads=1,
                               files=None)
f = np.random.randn(80, 3000).astype(np.float32)

if f.ndim == 2:
    f = np.expand_dims(f, 0)
f = get_ctranslate2_storage(f)

out = m.encode(f, to_cpu=True)
print("ok", out.shape)