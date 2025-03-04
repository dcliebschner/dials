from __future__ import annotations

from os.path import basename, splitext

from dxtbx.model.experiment_list import ExperimentList

import dials.util
from dials.algorithms.refinement.refinement_helpers import calculate_frame_numbers
from dials.array_family import flex
from dials.util import Sorry
from dials.util.multi_dataset_handling import generate_experiment_identifiers
from dials.util.slice import slice_experiments, slice_reflections

help_message = """

Slice a sequence to produce a smaller sequence within the bounds of the
original. If experiments are provided, modify the scan objects within this. If
reflections are provided, remove reflections outside the provided image ranges.
Each image_range parameter refers to a single experiment ID, counting up from
zero. Any reflections with experiment ID not matched by a image_range parameter
are removed.

Examples::

  dials.slice_sequence models.expt observations.refl "image_range=1 20"

  dials.slice_sequence models.expt "image_range=1 20"

  # Two experiments and reflections with IDs '0' and '1'
  dials.slice_sequence models.expt observations.refl \
    "image_range=1 20" "image_range=5 30"
"""

from libtbx.phil import parse

phil_scope = parse(
    """

  output {

    reflections_filename = None
      .type = str
      .help = "The filename for output reflections sliced to remove those"
              "outside the reduced image range. By default generated"
              "automatically from the input name"

    experiments_filename = None
      .type = str
      .help = "The filename for the output experiments with sliced scans.
               By default generated automatically from the input name"

  }

  image_range = None
    .help = "Range in images to slice a sequence. The number of arguments"
            "must be a factor of two. Each pair of arguments gives a range"
            "that follows C conventions (e.g. j0 <= j < j1) when slicing the"
            "reflections by observed centroid."
    .type = ints(size=2)
    .multiple = True

  block_size = None
    .type = float
    .help = "Overrides image_range if present. This option splits each sequence"
            "into the nearest integer number of equal size blocks close to"
            "block_size degrees in width"

  exclude_images_multiple = None
    .type = int
    .help = "Overrides image_range and block_size if present. This option"
            "splits each scan at the specified image and at each multiple of"
            "this image number in each experiment. The specified images are"
            "also excluded from the resulting scans. This is provided as an"
            "alternative method for specifying image exclusions for cRED data,"
            "where the scan of diffraction images is interrupted at regular"
            "intervals by a crystal positioning image (typically every 20th"
            "image). The alternative is using the same-named parameter in"
            "dials.integrate, where it acts as a mask for images while keeping"
            "a single scan. Splitting the scan may be more appropriate if the"
            "experimental geometry changes after collecting calibration images."
    .expert_level = 2
"""
)


def calculate_block_ranges(scan, block_size):
    """

    :param scans
    :type a scan object
    :param block_size:
    :type block_size: target block size in degrees"""

    image_ranges = []
    nimages = scan.get_num_images()
    osc_range = scan.get_oscillation_range(deg=True)
    osc_width = abs(osc_range[1] - osc_range[0])
    nblocks = max(int(round(osc_width / block_size)), 1)
    nblocks = min(nblocks, nimages)
    # equal sized blocks except the last one that may contain extra images
    # to make up the remainder
    nimages_per_block = [nimages // nblocks] * (nblocks - 1) + [
        nimages // nblocks + nimages % nblocks
    ]
    start = scan.get_image_range()[0]
    for nim in nimages_per_block:
        image_ranges.append((start, start + nim - 1))
        start += nim

    return image_ranges


def concatenate_reflections(sliced_reflections, identifiers):
    """Join a list of reflection tables into a single table, taking care to set
    the id column and experimental identifiers"""

    if len(sliced_reflections) != len(identifiers):
        raise Sorry(
            "Sliced reflections and identifiers lists are not of the same length"
        )

    reflections = flex.reflection_table()
    for i, rt in enumerate(sliced_reflections):
        for k in rt.experiment_identifiers().keys():
            del rt.experiment_identifiers()[k]
        rt["id"] = flex.int(rt.size(), i)  # set id
        rt.experiment_identifiers()[i] = identifiers[i]
        reflections.extend(rt)
    return reflections


def exclude_images_multiple(experiments, reflections, image_number):

    sliced_experiments = []
    sliced_reflections = []

    for iexp, experiment in enumerate(experiments):

        # Calculate the image range for each slice
        first_image, last_image = experiment.scan.get_image_range()
        first_exclude = ((first_image - 1) // image_number + 1) * image_number
        excludes = list(range(first_exclude, last_image + 1, image_number))
        image_ranges = []
        start = first_image
        for i in excludes:
            image_ranges.append((start, i - 1))
            start = i + 1
        if last_image > start:
            image_ranges.append((start, last_image))

        # Slice the experiments
        sliced_experiments.extend(
            [slice_experiments(experiments, [sr])[0] for sr in image_ranges]
        )

        # Slice the reflections
        refs = reflections.select(reflections["id"] == iexp)
        if len(refs) == 0:
            raise Sorry(f"No reflections found for experiment with id={iexp}")
        sliced_reflections.extend(
            [slice_reflections(refs, [sr]) for sr in image_ranges]
        )

    # Recombine experiments and reflections
    generate_experiment_identifiers(sliced_experiments)
    experiments = ExperimentList(sliced_experiments)
    identifiers = experiments.identifiers()
    reflections = concatenate_reflections(sliced_reflections, identifiers)

    return experiments, reflections


class Script:
    """A class for running the script."""

    def __init__(self):
        """Initialise the script."""
        from dials.util.options import ArgumentParser

        usage = (
            "usage: dials.slice_sequence [options] [param.phil] "
            "models.expt observations.refl"
        )

        # Create the parser
        self.parser = ArgumentParser(
            usage=usage,
            phil=phil_scope,
            read_reflections=True,
            read_experiments=True,
            check_format=False,
            epilog=help_message,
        )

    def run(self, args=None):
        """Execute the script."""

        from dials.util.options import reflections_and_experiments_from_files

        # Parse the command line
        params, options = self.parser.parse_args(args, show_diff_phil=True)
        reflections, experiments = reflections_and_experiments_from_files(
            params.input.reflections, params.input.experiments
        )

        # Try to load the models and data
        slice_exps = len(experiments) > 0
        slice_refs = len(reflections) > 0

        # Catch case of nothing to do
        if not slice_exps and not slice_refs:
            print("No suitable input provided")
            self.parser.print_help()
            return

        if reflections:
            if len(reflections) > 1:
                raise Sorry("Only one reflections list can be imported at present")
            reflections = reflections[0]

            # calculate frame numbers if needed
            if experiments:
                reflections = calculate_frame_numbers(reflections, experiments)

            # if we still don't have the right column give up
            if "xyzobs.px.value" not in reflections:
                raise Sorry(
                    "These reflections do not have frame numbers set, and "
                    "there are no experiments provided to calculate these."
                )

        # set trivial case where no scan range is provided at all
        if not params.image_range:
            params.image_range = [None]

        # Check if excluding multiples of an image number
        if params.exclude_images_multiple:
            if not (slice_exps and slice_refs):
                raise Sorry(
                    "For slicing by exclude_images_multiple, both experiments and reflections files must be provided"
                )
            sliced_experiments, sliced_reflections = exclude_images_multiple(
                experiments, reflections, params.exclude_images_multiple
            )

        # check if slicing into blocks
        elif params.block_size is not None:
            if not slice_exps:
                raise Sorry(
                    "For slicing into blocks, an experiment file must be provided"
                )

            if len(experiments) > 1:
                raise Sorry("For slicing into blocks please provide a single scan only")
            scan = experiments[0].scan

            # Having extracted the scan, calculate the blocks
            params.image_range = calculate_block_ranges(scan, params.block_size)

            # Do the slicing then recombine
            sliced = [
                slice_experiments(experiments, [sr])[0] for sr in params.image_range
            ]
            generate_experiment_identifiers(sliced)
            sliced_experiments = ExperimentList(sliced)

            # slice reflections if present
            if slice_refs:
                sliced = [
                    slice_reflections(reflections, [sr]) for sr in params.image_range
                ]
                identifiers = sliced_experiments.identifiers()
                sliced_reflections = concatenate_reflections(sliced, identifiers)

        else:
            # slice each dataset into the requested subset
            if slice_exps:
                sliced_experiments = slice_experiments(experiments, params.image_range)
            if slice_refs:
                sliced_reflections = slice_reflections(reflections, params.image_range)

        # Save sliced experiments
        if slice_exps:
            output_experiments_filename = params.output.experiments_filename
            if output_experiments_filename is None:
                # take first filename as template
                bname = basename(params.input.experiments[0].filename)
                bname = splitext(bname)[0]
                if not bname:
                    bname = "experiments"
                if len(params.image_range) == 1 and params.image_range[0] is not None:
                    ext = "_{}_{}.expt".format(*params.image_range[0])
                else:
                    ext = "_sliced.expt"
                output_experiments_filename = bname + ext
            print(f"Saving sliced experiments to {output_experiments_filename}")

            sliced_experiments.as_file(output_experiments_filename)

        # Save sliced reflections
        if slice_refs:
            output_reflections_filename = params.output.reflections_filename
            if output_reflections_filename is None:
                # take first filename as template
                bname = basename(params.input.reflections[0].filename)
                bname = splitext(bname)[0]
                if not bname:
                    bname = "reflections"
                if len(params.image_range) == 1 and params.image_range[0] is not None:
                    ext = "_{}_{}.refl".format(*params.image_range[0])
                else:
                    ext = "_sliced.refl"
                output_reflections_filename = bname + ext

            print(f"Saving sliced reflections to {output_reflections_filename}")
            sliced_reflections.as_file(output_reflections_filename)

        return


@dials.util.show_mail_handle_errors()
def run(args=None):
    script = Script()
    script.run(args)


if __name__ == "__main__":
    run()
