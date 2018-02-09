import bpy, os
from bpy.props import *
from bpy.app.handlers import persistent
from .common import *
from . import paint_slots

class YPSaveAsImage(bpy.types.Operator):
    bl_idname = "image.yp_save_as_texture_paint"
    bl_label = "Save As texture paint image"
    bl_description = "Save As texture paint Image"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.object and get_active_material()

    def execute(self, context):
        scene = context.scene
        obj = context.object
        mat = get_active_material()
        screen = context.screen
        area = context.area

        img = mat.texture_paint_images[mat.paint_active_slot]

        screen.ps_props.old_type = area.type
        scene.ps_props.screen_name = screen.name

        for i, a in enumerate(context.screen.areas):
            if a == area:
                screen.ps_props.temp_image_area_index = i
        
        old_type = area.type
        area.type = 'IMAGE_EDITOR'
        area.spaces[0].image = img
        scene.ps_props.last_image_name = img.name

        # HACK! remember filepath if image is packed
        if img.packed_file:
            # Get absolute and normalized path
            scene.ps_props.last_image_path = img.filepath_raw

            # Mark filepath to flag if the image is saved or not
            img.filepath_raw = '__TEMP__'

        bpy.ops.image.save_as('INVOKE_DEFAULT', relative_path=True)

        return{'FINISHED'}

class YPSaveImage(bpy.types.Operator):
    bl_idname = "image.yp_save_texture_paint"
    bl_label = "Save texture paint image"
    bl_description = "Save texture paint image"

    @classmethod
    def poll(cls, context):
        return paint_slots.get_active_image()

    def execute(self, context):
        obj = context.object
        mat = get_active_material()

        img = mat.texture_paint_images[mat.paint_active_slot]

        area = context.area
        old_type = area.type
        area.type = 'IMAGE_EDITOR'
        area.spaces[0].image = img
        bpy.ops.image.save()
        area.type = old_type

        return{'FINISHED'}

class YPSaveAllImage(bpy.types.Operator):
    bl_idname = "image.yp_save_dirty"
    bl_label = "Save All Images"
    bl_description = "Save all texture paint images (will pack instead if image is packed)"

    @classmethod
    def poll(cls, context):
        return paint_slots.get_active_image()

    def execute(self, context):
        bpy.ops.image.save_dirty()
        return {'FINISHED'}

class YPReloadImage(bpy.types.Operator):
    bl_idname = "image.yp_reload_texture_paint"
    bl_label = "Reload texture paint image"
    bl_description = "Reload texture paint image"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return paint_slots.get_active_image()

    def execute(self, context):
        obj = context.object
        mat = get_active_material()

        img = mat.texture_paint_images[mat.paint_active_slot]

        area = context.area
        old_type = area.type
        area.type = 'IMAGE_EDITOR'
        area.spaces[0].image = img
        bpy.ops.image.reload()
        area.type = old_type

        return {'FINISHED'}

class YPPackImage(bpy.types.Operator):
    bl_idname = "image.yp_pack_image"
    bl_label = "Pack image into blend file"
    bl_description = "Pack image to blend file"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return paint_slots.get_active_image()

    def execute(self, context):
        obj = context.object
        mat = get_active_material()
        img = mat.texture_paint_images[mat.paint_active_slot]

        img.pack(as_png=True)

        return{'FINISHED'}

# UPDATE HANDLERS
@persistent
def set_recover_area_enable(scene):
    screen = bpy.context.screen
    ops = bpy.context.window_manager.operators

    #print(ops[-1].bl_idname)

    if (ops and 'IMAGE_OT_yp_save_as_texture_paint' in ops[-1].bl_idname and
            screen.areas[0].type == 'FILE_BROWSER' and
            not screen.ps_props.recover_area):

        normal_screen = bpy.data.screens[scene.ps_props.screen_name]
        normal_screen.ps_props.recover_area = True

        #print(normal_screen)

@persistent
def do_recover_area(scene):
    screen = bpy.context.screen
    ops = bpy.context.window_manager.operators

    if (ops and 'IMAGE_OT_yp_save_as_texture_paint' in ops[-1].bl_idname and
        screen.areas[0].type != 'FILE_BROWSER' and
        screen.ps_props.recover_area):
        
        for i, area in enumerate(screen.areas):
            if i == screen.ps_props.temp_image_area_index and area.type == 'IMAGE_EDITOR':

                area.type = screen.ps_props.old_type
                screen.ps_props.recover_area = False
                img = bpy.data.images.get(scene.ps_props.last_image_name)

                if img and img.packed_file:

                    # This means image is not saved
                    if img.filepath_raw == '__TEMP__':
                        img.filepath_raw = scene.ps_props.last_image_path

                    # This means image is saved
                    else:

                        # Get absolute and normalized last image path
                        last_path = os.path.normpath(bpy.path.abspath(scene.ps_props.last_image_path))

                        # Check if last image file path is already there
                        file_exist = os.path.isfile(last_path)

                        #print(file_exist, scene.ps_props.last_image_path)

                        # Get already saved filepath
                        true_filepath = img.filepath
                        true_name = img.name

                        # Get absolute and normalized path
                        abs_path = bpy.path.abspath(true_filepath)
                        abs_path = os.path.normpath(abs_path)

                        # JUST ANOTHER HACK! Blender sometimes unpack at wrong filepath
                        # Just make sure it can be tracked and then delete it
                        img.name = '__TEMP__'
                        img.unpack(method='USE_ORIGINAL')
                        unpack_path = img.filepath_from_user()

                        #print(abs_path, unpack_path)

                        if '__TEMP__' in unpack_path or not file_exist:
                            os.remove(unpack_path)

                        # Recover image
                        img.filepath = true_filepath
                        img.name = true_name

                return
# PROPS
class ScenePaintSlotsProps(bpy.types.PropertyGroup):
    screen_name = StringProperty(default='')
    last_image_name = StringProperty(default='')
    last_image_path = StringProperty(default='')

class ScreenPaintSlotsProps(bpy.types.PropertyGroup):
    temp_image_area_index = IntProperty(default=-1)
    old_type = StringProperty(default='')
    recover_area = BoolProperty(default=False)

def register():
    bpy.types.Screen.ps_props = PointerProperty(type=ScreenPaintSlotsProps)
    bpy.types.Scene.ps_props = PointerProperty(type=ScenePaintSlotsProps)

    bpy.app.handlers.scene_update_pre.append(set_recover_area_enable)
    bpy.app.handlers.scene_update_pre.append(do_recover_area)

def unregister():
    bpy.app.handlers.scene_update_pre.remove(do_recover_area)
    bpy.app.handlers.scene_update_pre.remove(set_recover_area_enable)
