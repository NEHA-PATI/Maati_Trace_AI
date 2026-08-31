import numpy as np

from services.raster_processor_service.app.processors.landsat_c2_l2 import (
    SR_OFFSET,
    SR_SCALE,
    ST_OFFSET,
    ST_SCALE,
    _qa_valid,
)


def test_collection2_documented_scale_constants():
    assert SR_SCALE == 0.0000275
    assert SR_OFFSET == -0.2
    assert ST_SCALE == 0.00341802
    assert ST_OFFSET == 149.0


def test_qa_rejects_cloud_shadow_and_fill():
    # 0 means clear. Set individual bad bits for fill/cloud/shadow/snow.
    qa = np.array([[0, 1 << 0, 1 << 3, 1 << 4, 1 << 5]], dtype=float)
    valid = _qa_valid(qa, None)
    assert valid.tolist() == [[True, False, False, False, False]]
