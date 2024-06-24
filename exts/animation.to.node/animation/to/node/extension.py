import omni.ext
import omni.kit

import omni.ui as ui
import omni.usd
from omni.usd import Selection
from pxr import Usd, UsdGeom, Gf, Sdf

import omni.graph.core as og
import omni.graph.nodes as og_nodes




class AnimationExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        print("[animation] animation startup")

        self._window = ui.Window("Animation Creater", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                ui.Label("Create KeyFrame")
                with ui.HStack(height=20):
                    ui.Label("Frame:", width=50)
                    self.frame_input = ui.IntField(width=100, default=0)
                with ui.HStack(height=20):
                    ui.Label("X:", width=50)
                    self.x_input = ui.FloatField(width=100, default=0.0)
                with ui.HStack(height=20):
                    ui.Label("Y:", width=50)
                    self.y_input = ui.FloatField(width=100, default=0.0)
                with ui.HStack(height=20):
                    ui.Label("Z:", width=50)
                    self.z_input = ui.FloatField(width=100, default=0.0)
                with ui.HStack(height=20):
                    ui.Label("Rx:", width=50)
                    self.rx_input = ui.FloatField(width=100, default=0.0)
                with ui.HStack(height=20):
                    ui.Label("Ry:", width=50)
                    self.ry_input = ui.FloatField(width=100, default=0.0)
                with ui.HStack(height=20):
                    ui.Label("Rz:", width=50)
                    self.rz_input = ui.FloatField(width=100, default=0.0)
                ui.Button("Get Current Values", clicked_fn=self.get_current_values)
                ui.Button("Add Frame", clicked_fn=self.add_frame)
                self.frames = []
                self.coordinates = []
                self.rotations = []
                with ui.HStack(height=20):
                    ui.Label("Frames:", width=50)
                    self.frame_list = ui.StringField( default="")
                with ui.HStack(height=20):
                    ui.Label("Coordinates:", width=50)
                    self.coordinate_list = ui.StringField( default="")
                with ui.HStack(height=20):
                    ui.Label("Rotations:", width=50)
                    self.rotation_list = ui.StringField( default="")
                ui.Button("Create Animation", clicked_fn=self.create_animation)
                ui.Button("Delete KeyFrame", clicked_fn=self.delete_keyframe)
            
    def get_selected_object(self):
        stage = omni.usd.get_context().get_stage()
        selection = omni.usd.get_context().get_selection()
        selected_paths = selection.get_selected_prim_paths()

        if selected_paths:
            path = selected_paths[0]
            prim = stage.GetPrimAtPath(path)
            if prim.IsValid():
                print(f"Selected object: {path}")
                return prim
        return None
    
    def get_current_values(self):
        prim = self.get_selected_object()
        if prim is not None:
            xform = UsdGeom.Xformable(prim)
            translate_op = None
            rotate_op = None

            for op in xform.GetOrderedXformOps():
                if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                    translate_op = op
                elif op.GetOpType() == UsdGeom.XformOp.TypeRotateXYZ:
                    rotate_op = op

            if translate_op:
                current_translate = translate_op.Get()
                
                self.x_input.model.set_value(current_translate[0])
                self.y_input.model.set_value(current_translate[1])
                self.z_input.model.set_value(current_translate[2])

            if rotate_op:
                current_rotate = rotate_op.Get()
                self.rx_input.model.set_value(current_rotate[0])
                self.ry_input.model.set_value(current_rotate[1])
                self.rz_input.model.set_value(current_rotate[2])

    def delete_keyframe(self):
        if not self.frames:
            return
        self.frames.pop()
        self.coordinates.pop()
        self.rotations.pop()
        self.update_lists()

    def add_frame(self):
        frame = self.frame_input.model.get_value_as_int()
        x = self.x_input.model.get_value_as_float()
        y = self.y_input.model.get_value_as_float()
        z = self.z_input.model.get_value_as_float()
        rx = self.rx_input.model.get_value_as_float()
        ry = self.ry_input.model.get_value_as_float()
        rz = self.rz_input.model.get_value_as_float()
        self.frames.append(frame)
        self.coordinates.append((x, y, z))
        self.rotations.append((rx, ry, rz))
        self.update_lists()

    def update_lists(self):
        self.frame_list.model.set_value(", ".join(map(str, self.frames)))
        self.coordinate_list.model.set_value(", ".join(map(str, self.coordinates)))
        self.rotation_list.model.set_value(", ".join(map(str, self.rotations)))

    def create_animation(self):
        prim = self.get_selected_object()
        if prim is not None:
            frame_positions = {frame: coord for frame, coord in zip(self.frames, self.coordinates)}
            frame_rotations = {frame: rot for frame, rot in zip(self.frames, self.rotations)}
            create_animation(prim, frame_positions, frame_rotations)
            self.reset_fields()

    def reset_fields(self):
        self.frames.clear()
        self.coordinates.clear()
        self.rotations.clear()
        self.frame_input.model.set_value(0)
        self.x_input.model.set_value(0.0)
        self.y_input.model.set_value(0.0)
        self.z_input.model.set_value(0.0)
        self.rx_input.model.set_value(0.0)
        self.ry_input.model.set_value(0.0)
        self.rz_input.model.set_value(0.0)
        self.update_lists()

    def on_shutdown(self):
        print("[animation] animation shutdown")

def create_animation(prim, frame_positions, frame_rotations):
    xform = UsdGeom.Xformable(prim)

    translate_op = None
    rotate_op = None
    for op in xform.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            translate_op = op
        elif op.GetOpType() == UsdGeom.XformOp.TypeRotateXYZ:
            rotate_op = op

    if translate_op is None:
        translate_op = xform.AddTranslateOp()
    if rotate_op is None:
        rotate_op = xform.AddRotateXYZOp()

    for frame, position in frame_positions.items():
        translate_op.Set(Gf.Vec3f(*position), frame)
    for frame, rotation in frame_rotations.items():
        rotate_op.Set(Gf.Vec3f(*rotation), frame)

    prim.GetStage().GetRootLayer().Save()
