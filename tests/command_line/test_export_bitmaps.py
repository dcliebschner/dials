from __future__ import annotations

import os
from pathlib import Path

import pytest

from dials.command_line import export_bitmaps


@pytest.mark.parametrize(
    "show_resolution_rings,show_ice_rings",
    [
        (False, False),
        (True, False),
        (False, True),
        (True, True),
    ],
)
def test_export_single_bitmap(
    dials_data,
    tmp_path,
    show_resolution_rings,
    show_ice_rings,
):
    export_bitmaps.run(
        [
            str(dials_data("centroid_test_data", pathlib=True) / "centroid_0001.cbf"),
            f"resolution_rings.show={show_resolution_rings}",
            f"ice_rings.show={show_ice_rings}",
            f"output.directory={tmp_path}",
        ],
    )
    assert tmp_path.joinpath("image0001.png").is_file()


def test_export_multiple_bitmaps(dials_data, tmp_path):
    export_bitmaps.run(
        [
            str(dials_data("centroid_test_data", pathlib=True) / "experiments.json"),
            "prefix=variance_",
            "binning=2",
            "display=variance",
            "colour_scheme=inverse_greyscale",
            "brightness=25",
            "kernel_size=5,5",
            f"output.directory={tmp_path}",
        ],
    )

    for i in range(1, 8):
        assert tmp_path.joinpath(f"variance_000{i}.png").is_file()


def test_export_bitmap_with_prefix_and_no_padding(dials_data, tmp_path):
    export_bitmaps.run(
        [
            str(dials_data("centroid_test_data", pathlib=True) / "centroid_0001.cbf"),
            "prefix=img_",
            "padding=0",
            f"output.directory={tmp_path}",
        ],
    )
    assert tmp_path.joinpath("img_1.png").is_file()


def test_export_bitmap_with_prefix_and_extra_padding(dials_data, tmp_path):
    export_bitmaps.run(
        [
            str(dials_data("centroid_test_data", pathlib=True) / "centroid_0001.cbf"),
            "prefix=img_",
            "padding=5",
            f"output.directory={tmp_path}",
        ],
    )
    assert tmp_path.joinpath("img_00001.png").is_file()


def test_export_bitmap_with_specified_output_filename(dials_data, tmp_path):
    export_bitmaps.run(
        [
            str(dials_data("centroid_test_data", pathlib=True) / "centroid_0001.cbf"),
            "output.file=kittens.png",
            f"output.directory={tmp_path}",
        ],
    )
    assert tmp_path.joinpath("kittens.png").is_file()


def test_export_multiple_bitmaps_with_specified_output_filename_fails(
    dials_data, tmp_path
):
    with pytest.raises(SystemExit):
        # setting output filename not allowed with >1 image
        export_bitmaps.run(
            [
                str(
                    dials_data("centroid_test_data", pathlib=True) / "experiments.json"
                ),
                "output.file=kittens.png",
                f"output.directory={tmp_path}",
            ],
        )


def test_export_still_image(dials_regression: Path, tmp_path):
    image = os.path.join(
        dials_regression,
        "image_examples",
        "DLS_I24_stills",
        "still_0001.cbf",
    )

    export_bitmaps.run(
        [
            image,
            f"output.directory={tmp_path}",
        ],
    )
    assert tmp_path.joinpath("image0001.png").is_file()


@pytest.mark.parametrize(
    "show_resolution_rings",
    [
        False,
        True,
    ],
)
def test_export_multi_panel(dials_regression: Path, tmp_path, show_resolution_rings):
    image = os.path.join(
        dials_regression, "image_examples", "DLS_I23", "germ_13KeV_0001.cbf"
    )

    for binning in (1, 4):
        export_bitmaps.run(
            [
                image,
                "binning=%i" % binning,
                "prefix=binning_%i_" % binning,
                f"resolution_rings.show={show_resolution_rings}",
                f"output.directory={tmp_path}",
            ],
        )
        assert tmp_path.joinpath(f"binning_{binning}_0001.png").is_file()


def test_export_restricted_multiimage(dials_data, tmp_path):
    "Test exporting a subset of an imageset"
    export_bitmaps.run(
        [
            str(dials_data("centroid_test_data", pathlib=True) / "experiments.json"),
            "imageset_index=2",
            f"output.directory={tmp_path}",
        ],
    )
    assert [f.name for f in tmp_path.glob("*.png")] == [
        "image0002.png"
    ], "Only one image expected"
