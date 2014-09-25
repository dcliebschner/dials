from __future__ import division
from libtbx import test_utils
import libtbx.load_env

tst_list = (
    ["$D/test/command_line/tst_dials_process.py", "1"],
    ["$D/test/command_line/tst_dials_process.py", "2"],
    "$D/test/tst_phil.py",
    "$D/test/command_line/tst_reindex.py",
    "$D/test/framework/tst_interface.py",
    "$D/test/command_line/tst_import.py",
    "$D/test/command_line/tst_dials_show_isig_rmsd.py",
    "$D/test/command_line/tst_integrate.py",
    "$D/test/command_line/tst_detector_max_resolution.py",
    "$D/test/command_line/tst_predict.py",
    "$D/test/command_line/tst_import_xds.py",
    "$D/test/command_line/tst_merge_reflection_lists.py",
    "$D/test/command_line/tst_spotfinder.py",
    "$D/test/command_line/tst_export.py",
    "$D/test/command_line/tst_export_xds.py",
    "$D/test/command_line/tst_refine.py",
    "$D/test/command_line/tst_create_profile_model.py",
    "$D/test/command_line/tst_sort_reflections.py",
    "$D/test/command_line/tst_plot_scan_varying_crystal.py",
    "$D/test/command_line/tst_generate_mask.py",
    "$D/test/command_line/tst_show_extensions.py",
    "$D/test/util/tst_command_line.py",
    "$D/test/array_family/tst_flex_shoebox.py",
    "$D/test/array_family/tst_reflection_table.py",
    "$D/test/model/data/tst_reflection_pickle.py",
    "$D/test/model/data/tst_prediction.py",
    "$D/test/model/data/tst_observation.py",
    "$D/test/model/data/tst_shoebox.py",
    "$D/test/model/data/tst_reflection_list.py",
    "$D/test/model/serialize/tst_shoebox_file.py",
    "$D/test/algorithms/spot_prediction/tst_index_generator.py",
    "$D/test/algorithms/spot_prediction/tst_ray_predictor.py",
    "$D/test/algorithms/spot_prediction/tst_rotation_angles.py",
    "$D/test/algorithms/spot_prediction/tst_spot_prediction.py",
    "$D/test/algorithms/spot_prediction/tst_scan_varying_predictor.py",
    "$D/test/algorithms/spot_prediction/tst_reeke.py",
    "$D/test/algorithms/spot_prediction/tst_reeke_index_generator.py",
    "$B/test/algorithms/spot_prediction/tst_reeke_model",
    "$D/test/algorithms/spot_prediction/tst_scan_static_reflection_predictor.py",
    "$D/test/algorithms/spot_prediction/tst_scan_varying_reflection_predictor.py",
    "$D/test/algorithms/spot_prediction/tst_stills_reflection_predictor.py",
    "$D/test/algorithms/spot_prediction/tst_scan_varying_ray_predictor.py",
    "$D/test/algorithms/profile_model/tst_profile_model.py",
    "$D/test/algorithms/background/tst_modeller.py",
    "$D/test/algorithms/background/tst_outlier_rejector.py",
    "$D/test/algorithms/background/tst_mosflm_outlier_rejector.py",
    "$D/test/algorithms/background/tst_creator.py",
    "$D/test/algorithms/integration/profile/tst_grid_sampler.py",
    "$D/test/algorithms/integration/profile/tst_grid_sampler_2d.py",
    "$D/test/algorithms/integration/profile/tst_xds_circle_sampler.py",
    "$D/test/algorithms/integration/profile/tst_reference_locator.py",
    "$D/test/algorithms/integration/profile/tst_reference_learner.py",
    "$D/test/algorithms/integration/profile/tst_reference_learner2d.py",
    "$D/test/algorithms/integration/profile/tst_profile_fitting.py",
    "$D/test/algorithms/integration/tst_interface.py",
    "$D/test/algorithms/integration/tst_summation.py",
    "$D/test/algorithms/integration/tst_profile_fitting_rs.py",
    "$D/test/algorithms/integration/tst_corrections.py",
    "$B/test/algorithms/spatial_indexing/tst_quadtree",
    "$B/test/algorithms/spatial_indexing/tst_octree",
    "$B/test/algorithms/spatial_indexing/tst_collision_detection",
    "$D/test/algorithms/spatial_indexing/tst_spatial_index.py",
    "$D/test/algorithms/refinement/tst_refinement_regression.py",
    "$D/test/algorithms/refinement/tst_ref_passage_categorisation.py",
    "$D/test/algorithms/refinement/tst_prediction_parameters.py",
    "$D/test/algorithms/refinement/tst_finite_diffs.py",
    "$D/test/algorithms/refinement/tst_scan_varying_prediction_parameters.py",
    "$D/test/algorithms/refinement/tst_beam_parameters.py",
    "$D/test/algorithms/refinement/tst_crystal_parameters.py",
    "$D/test/algorithms/refinement/tst_detector_parameters.py",
    "$D/test/algorithms/refinement/tst_hierarchical_detector_refinement.py",
    "$D/test/algorithms/refinement/tst_multi_experiment_refinement.py",
    "$D/test/algorithms/refinement/tst_multi_panel_detector_parameterisation.py",
    "$D/test/algorithms/refinement/tst_refine_multi_wedges.py",
    "$D/test/algorithms/refinement/tst_stills_refinement.py",
    "$D/test/algorithms/image/tst_centroid.py",
    "$D/test/algorithms/image/filter/tst_summed_area.py",
    "$D/test/algorithms/image/filter/tst_mean_and_variance.py",
    "$D/test/algorithms/image/filter/tst_median.py",
    "$D/test/algorithms/image/filter/tst_fano.py",
    "$D/test/algorithms/image/threshold/tst_local.py",
    "$D/test/algorithms/image/connected_components/tst_connected_components.py",
    "$D/test/algorithms/polygon/clip/tst_clipping.py",
    "$D/test/algorithms/polygon/tst_spatial_interpolation.py",
    "$D/test/algorithms/reflection_basis/tst_coordinate_system.py",
    "$D/test/algorithms/reflection_basis/tst_map_frames.py",
    "$D/test/algorithms/reflection_basis/tst_beam_vector_map.py",
    "$D/test/algorithms/reflection_basis/tst_grid_index_generator.py",
    "$D/test/algorithms/reflection_basis/tst_transform.py",
    "$D/test/algorithms/shoebox/tst_bbox_calculator.py",
    "$D/test/algorithms/shoebox/tst_partiality_calculator.py",
    "$D/test/algorithms/shoebox/tst_mask_foreground.py",
    "$D/test/algorithms/shoebox/tst_mask_overlapping.py",
    "$D/test/algorithms/shoebox/tst_find_overlapping.py",
    "$D/test/algorithms/generate_test_reflections/tst_generate_test_refl.py",
    "$D/test/tst_plot_reflections.py",
    ["$D/test/algorithms/indexing/tst_index.py", "1"],
    ["$D/test/algorithms/indexing/tst_index.py", "2"],
    ["$D/test/algorithms/indexing/tst_index.py", "3"],
    ["$D/test/algorithms/indexing/tst_index.py", "4"],
    ["$D/test/algorithms/indexing/tst_index.py", "7"],
    ["$D/test/algorithms/indexing/tst_index.py", "8"],
    ["$D/test/algorithms/indexing/tst_index.py", "9"],
    ["$D/test/algorithms/indexing/tst_index.py", "10"],
    ["$D/test/algorithms/indexing/tst_index.py", "11"],
    ["$D/test/algorithms/indexing/tst_index.py", "12"],
    ["$D/test/algorithms/indexing/tst_index.py", "13"],
    ["$D/test/algorithms/indexing/tst_index.py", "14"],
    "$D/test/algorithms/indexing/tst_assign_indices.py",
    "$D/test/command_line/tst_refine_bravais_settings.py",
    "$D/test/command_line/tst_discover_better_experimental_model.py",
    "$D/test/algorithms/indexing/tst_compare_orientation_matrices.py",
    "$D/test/algorithms/indexing/tst_symmetry.py",
    "$D/scratch/rjg/unit_cell_refinement.py",
    )

def run () :
  build_dir = libtbx.env.under_build("dials")
  dist_dir = libtbx.env.dist_path("dials")
  test_utils.run_tests(build_dir, dist_dir, tst_list)

if (__name__ == "__main__"):
  run()
