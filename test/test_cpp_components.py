from __future__ import absolute_import, division, print_function

import os

import procrunner
import pytest

@pytest.mark.parametrize('executable', [
    # Paths are under /build/
    "test/algorithms/spatial_indexing/tst_collision_detection",
    "test/algorithms/spatial_indexing/tst_octree",
    "test/algorithms/spatial_indexing/tst_quadtree",
    "test/algorithms/spot_prediction/tst_reeke_model",
])
def test_cpp_program(executable):
  full_path = os.path.join(os.environ["LIBTBX_BUILD"], 'dials', *(executable.split('/')))
  print(full_path)

  result = procrunner.run([full_path])
  assert not result['exitcode'] and not result['stderr']
