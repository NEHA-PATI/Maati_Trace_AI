import numpy as np


def test_linear_power_to_db_formula():
    values = np.array([1.0, 0.1, 0.01])
    db = 10.0 * np.log10(values)
    assert np.allclose(db, [0.0, -10.0, -20.0])


def test_rvi_formula_range_for_positive_dual_pol():
    vv = np.array([0.2, 0.4])
    vh = np.array([0.05, 0.1])
    rvi = 4.0 * vh / (vv + vh)
    assert np.all(rvi >= 0)
    assert np.all(rvi <= 4)
