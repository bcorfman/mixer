from os.path import exists
from parselib import AV, Surfaces, Output, Matrix, Kill, Detail
import numpy as np
import util


class DataModel(object):
    def __init__(self):
        self.term_vel = None
        self.burst_height = None
        self.attack_az = None
        self.aof = None
        self.blast_vol = None
        self.av_file = None
        self.srf_file = None
        self.mtx_extent_range, self.mtx_extent_defl = None, None
        self.cls_range, self.cls_defl = None, None
        self.offset_range, self.offset_defl = None, None
        self.gridlines_range, self.gridlines_defl = None, None
        self.gridlines_range_mid, self.gridlines_defl_mid = None, None
        self.cell_size_range, self.cell_size_defl = None, None
        self.pks = None
        self.surf_names = None
        self.surfaces = None
        self.srf_min_x, self.srf_max_x = None, None
        self.srf_min_y, self.srf_max_y = None, None
        self.srf_max_z = None
        self.comp_list = None
        self.x_avg_loc, self.y_avg_loc = None, None
        self.x_loc, self.y_loc, self.z_loc = None, None, None
        self.num_tables = None
        self.num_az, self.num_el, self.num_vl, self.num_ms = None, None, None, None
        self.az_idx = None
        self.el_idx = None
        self.azs = None
        self.els = None
        self.vls = None
        self.mss = None
        self.table_names = None
        self.avs = None
        self.pes = None
        self.av_averaging = None
        self.az_averaging = None
        self.num_kills = None
        self.kill_file = None
        self.kill_desc = None
        self.kill_id = None
        self.kill_lines = None
        self.last_node = None
        self.tgt_center = None
        self.volume_radius = None
        self.mtx_kill_id = None
        self.frag_comps = []
        self.blast_comps = []
        self.dh_comps = []
        self.dtl_file = None
        self.comp_num = None
        self.sample_loc = None
        self.burst_loc = None

    def read_and_transform_all_files(self, out_file):
        av_file, srf_file, mtx_file, kill_file, self.dtl_file = Output(self).read(out_file)
        if av_file is None:
            raise IOError("Case didn't complete.")
        AV(self).read(av_file)
        Surfaces(self).read(srf_file)
        Kill(self).read(kill_file)
        if exists(mtx_file):
            Matrix(self).read(mtx_file)
            self.transform_matrix()
        self.dtl_file += "zzz"
        if exists(self.dtl_file):
            detail = Detail(self)
            if detail.validate(self.dtl_file):
                detail.read(self.dtl_file)
            else:
                raise IOError(".dtl file does not have the full level of detail.")
        kill_comps = self.extract_components(self.mtx_kill_id)
        self.transform_blast_volumes(kill_comps)
        self.transform_direct_hit_components(kill_comps)
        self.transform_frag_components(kill_comps)
        self.transform_surfaces()
        self.find_closest_az_and_el_indices()

    def transform_blast_volumes(self, kill_comps):
        if kill_comps:
            self.blast_comps = set(kill_comps).intersection(self.blast_vol.keys())
        else:
            self.blast_comps = self.blast_vol.keys()

    def transform_direct_hit_components(self, kill_comps):
        if kill_comps:
            self.dh_comps = set(kill_comps).intersection(self.blast_vol.keys())
        else:
            self.dh_comps = self.blast_vol.keys()

    def transform_frag_components(self, kill_comps):
        potential_frag_comps = [c.id for c in self.comp_list if c.id != 0]
        if kill_comps:
            self.frag_comps = set(kill_comps).intersection(potential_frag_comps)
        else:
            self.frag_comps = potential_frag_comps

    def transform_surfaces(self):
        """
        Calculate a volume radius and geometric center for the target surfaces.
        """
        self.surfaces = np.array(self.surfaces)
        # surface_points = [(s[0], s[1]) for s in self.surfaces]
        # tgt_center_points = [(self.tgt_center[0], self.tgt_center[1]) for _ in self.surfaces]
        # self.volume_radius = max(util.distance_between(surface_points, tgt_center_points))
        self.volume_radius = max(self.srf_min_x, self.srf_max_x, self.srf_min_y, self.srf_max_y)
        if self.blast_comps:
            for i in self.blast_comps:
                r1, r2, r3, z1, z2 = self.blast_vol[i]
                self.volume_radius = max(self.volume_radius, z1 + z2 + max(r3, r2, r1))

    def transform_matrix(self):
        # Store the matrix extents in range & deflection for later display in the 3D scene.
        self.mtx_extent_range = (self.gridlines_range[0], self.gridlines_range[-1])
        self.mtx_extent_defl = (self.gridlines_defl[0], self.gridlines_defl[-1])
        # Rotate the matrix by 180 degrees by reversing all gridlines and PK values
        self.gridlines_range = [-i for i in self.gridlines_range]
        self.gridlines_defl = [-i for i in self.gridlines_defl]
        # Shift gridlines by applying matrix offset and target center extracted from .out file.
        # Otherwise, would have to apply the shift to the target/obstacle surfaces, AVs, blast volumes, etc.
        self.gridlines_range = util.apply_list_offset(self.gridlines_range, self.offset_range + self.tgt_center[0])
        self.gridlines_defl = util.apply_list_offset(self.gridlines_defl, self.offset_defl + self.tgt_center[1])
        # Calculate midpoint of gridlines and a list of cell sizes based on gridline measurements
        self.gridlines_range_mid = util.midpoints(self.gridlines_range)
        self.gridlines_defl_mid = util.midpoints(self.gridlines_defl)
        self.cell_size_range = util.measure_between(self.gridlines_range)
        self.cell_size_defl = util.measure_between(self.gridlines_defl)
        # Get rid of floating point noise that can cause Pk values > 1.0
        self.pks = np.clip(self.pks, 0.0, 1.0)

    def extract_components(self, kill_type, kill_node=None):
        """
        :param kill_type: string with k number (e.g., 'k1' or 'k5') matched against the same type in the kill
                          definition file.
        :param kill_node: node number in string format
        :return: list of components for that kill
        """
        if not kill_type:
            return []
        if kill_node is None:
            kill_node = self.last_node.get(kill_type, '')
        type_and_node = kill_type + ',' + kill_node
        if not self.kill_lines.get(type_and_node):
            return []
        components = []
        for item in self.kill_lines[type_and_node].items:
            if item.startswith('c'):
                components.append(int(item[1:]))
            elif item.startswith('n'):
                new_kill_type = kill_type.split(',')[0]
                components.extend(self.extract_components(new_kill_type, item[1:]))
            elif item.startswith('k'):
                new_kill_type, new_kill_node = item.split(',')
                components.extend(self.extract_components(new_kill_type, new_kill_node))
            else:
                raise ValueError("Unrecognized item %s in kill file for %s" % (item, kill_type))
        return components

    def find_closest_az_and_el_indices(self):
        """
        find and set closest azimuth index and elevation index that will be used to display appropriate AVs/PEs from
         the component AV file.
        :return: None
        """
        # TODO: Include JMAE interpolation code to get AVs to be a true match
        # Obtain deltas between all azimuths in the AV file and the chosen attack azimuth.
        # This algorithm still works for azimuth averaged data since there's only one azimuth in the list.
        az_delta_idx_pairs = util.delta(self.azs, self.attack_az)
        az_delta_idx_pairs.sort()  # order by smallest to largest delta

        # obtain deltas between all elevations in the AV file and the chosen angle of fall
        el_delta_idx_pairs = util.delta(self.els, self.aof)
        el_delta_idx_pairs.sort()  # order by smallest to largest delta

        # first item in deltas (smallest delta after sorting) and the second item in the pair (index)
        self.az_idx = az_delta_idx_pairs[0][1]
        self.el_idx = el_delta_idx_pairs[0][1]

    def get_sample_points(self):
        return self.sample_loc

    def get_burst_points(self):
        return self.burst_loc
