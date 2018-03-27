import bpy, time, os, math 
from . import material_override
from mathutils import Euler
from bpy.props import *
from .common import *

# Todo:
# BUG: AO not working for basic suzanne mesh V
# BUG: DVC not working if using highpoly meshes V
# Automatic bake normal on multires V
# Report if no bake happen, especially on failed normal bake V
# Bake at shadeless

blend_type_items = (("MIX", "Mix", ""),
	             ("ADD", "Add", ""),
	             ("SUBTRACT", "Subtract", ""),
	             ("MULTIPLY", "Multiply", ""),
	             ("SCREEN", "Screen", ""),
	             ("OVERLAY", "Overlay", ""),
	             ("DIFFERENCE", "Difference", ""),
	             ("DIVIDE", "Divide", ""),
	             ("DARKEN", "Darken", ""),
	             ("LIGHTEN", "Lighten", ""),
	             ("HUE", "Hue", ""),
	             ("SATURATION", "Saturation", ""),
	             ("VALUE", "Value", ""),
	             ("COLOR", "Color", ""),
	             ("SOFT_LIGHT", "Soft Light", ""),
	             ("LINEAR_LIGHT", "Linear Light", ""))

vcol_mat_name = '__VCOL_MAT_TEMP'
temp_lamp_name = '__temp_lamp__'

def downsample_image(ss_img, target_img):

    # Create temp scene
    temp_scene = bpy.data.scenes.new('_temp_scene')
    bpy.context.screen.scene = temp_scene

    # Set Plane
    bpy.ops.mesh.primitive_plane_add(radius=1, view_align=False, enter_editmode=True, location=(0, 0, 0))
    #bpy.ops.uv.unwrap(method='CONFORMAL', margin=0.0)
    bpy.ops.uv.reset()
    bpy.ops.object.mode_set(mode='OBJECT') 
    plane = bpy.context.object.data
    plane.uv_textures.active.data[0].image = target_img

    # New material for plane
    ss_mat = bpy.data.materials.new('_supersample_mat')
    ss_mat.use_shadeless = True
    ss_tex = bpy.data.textures.new('_supersample_tex', 'IMAGE')
    ss_tex.image = ss_img
    ss_ts = ss_mat.texture_slots.add()
    ss_ts.texture = ss_tex
    plane.materials.append(ss_mat)

    bpy.ops.object.bake_image()

    # Delete temp scene!
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.scene.delete()

    # delete mesh, material, & camera
    ss_ts.texture = None
    ss_tex.image = None
    bpy.data.textures.remove(ss_tex, do_unlink=True)
    bpy.data.materials.remove(ss_mat, do_unlink=True)

class YPBakeStuffs(bpy.types.Operator):
    bl_idname = "view3d.yp_bake_stuffs"
    bl_label = "Bake Stuffs"
    bl_description = "Bake stuffs like you never bake before"
    bl_options = {'REGISTER', 'UNDO'}

    type = EnumProperty(
        name = "Type",
        description="Type of bake", 
        items=(
            ('NORMALS', "Normal", ""),
            ('AO', "Ambient Occlusion", ""),
            ('DIRTY', "Dirty Vertex Color", ""),
            ('LIGHTS', "Lights", ""),
            ('DIFFUSE_COLOR', "Diffuse Color", ""),
            ('SPECULAR_COLOR', "Specular Color", ""),
            ('FULL_RENDER', "Full Render", ""),
            #('POINTINESS', "Pointiness", ""),
            ), 
        default='AO',
        )

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == 'MESH' and in_active_layer(obj) and context.area.type == 'VIEW_3D'

    def set_supersample_image(self, m):
        sce = bpy.context.scene
        opt = sce.bt_props

        # Supersample image
        self.ss_img = bpy.data.images.get(m.name + '_supersample')
        if not self.ss_img:
            self.ss_img = bpy.data.images.new(m.name + '_supersample', 
                    self.target_img.size[0] * int(opt.sample), 
                    self.target_img.size[1] * int(opt.sample), True, False)
            if self.type == 'AO':
                self.ss_img.generated_color = (1, 1, 1, 1)
            elif self.type == 'NORMALS':
                self.ss_img.generated_color = (0.5, 0.5, 1.0, 1)

    def set_target_image(self, m):
        sce = bpy.context.scene
        opt = sce.bt_props

        # Search or create new image
        self.target_img = None
        self.temp_img = None
        self.target_tex = None
        self.target_uv = None

        # New image suffix
        suffix = getattr(opt, self.type.lower() + '_suffix')

        # Overwrite already available target image
        if opt.overwrite:

            #if self.original_engine in {'BLENDER_RENDER', 'BLENDER_GAME'}:

            for ts in m.texture_slots:
                if not ts or not ts.texture or ts.texture.type != 'IMAGE' or not ts.texture.image: continue

                # Search for already available target image
                if (ts.texture.image.name.endswith(suffix) or 
                        os.path.splitext(ts.texture.image.name)[0].endswith(suffix)):
                    self.target_img = ts.texture.image
                    self.target_uv = ts.uv_layer

                    # Use temp image to texture
                    #if not opt.antialias and sce.render.engine != 'CYCLES':
                    if not opt.antialias:
                        self.target_tex = ts.texture
                        self.temp_img = self.target_img.copy()
                        self.target_tex.image = self.temp_img

                    break

            #elif self.original_engine == 'CYCLES':
            #    pass

        # Target image
        if not self.target_img:
            img_name = m.name + suffix
            self.target_img = bpy.data.images.new(img_name, int(opt.res_x), int(opt.res_y), True, False)
            if self.type == 'AO':
                self.target_img.generated_color = (1, 1, 1, 1)
            elif self.type == 'NORMALS':
                self.target_img.generated_color = (0.5, 0.5, 1.0, 1)
            elif self.type == 'DIRTY':
                self.target_img.generated_color = (0.0, 0.0, 0.0, 1)
            #elif self.type == 'POINTINESS':
            #    self.target_img.generated_color = (0.0, 0.0, 0.0, 1)
        
        #print(self.target_img)

    def delete_temp_image(self):
        # RECOVER texture that using temp image
        if self.temp_img:
            self.target_tex.image = self.target_img
            bpy.data.images.remove(self.temp_img, do_unlink=True)

    def set_polygon_image(self, o, m_idx):
        sce = bpy.context.scene
        opt = sce.bt_props

        # List for recovering polygon data
        self.temp_poly_imgs = []
        #self.temp_poly_m_idxs = []

        for i, p in enumerate(o.data.polygons):
            # REMEMBER polygon material index
            #self.temp_poly_m_idxs.append(p.material_index)

            # Set target image to polygon
            if m_idx == p.material_index:
                if opt.antialias:
                    o.data.uv_textures.active.data[i].image = self.ss_img
                    if self.ss_img.name not in self.ss_dict:
                        self.ss_dict[self.ss_img.name] = self.target_img.name
                else:
                    o.data.uv_textures.active.data[i].image = self.target_img
                self.temp_poly_imgs.append(self.target_img)

            # Set None image to polygon 
            else: 
                self.temp_poly_imgs.append(o.data.uv_textures.active.data[i].image)
                o.data.uv_textures.active.data[i].image = None

    def recover_polygon_image(self, o):
        # RECOVER UV Image
        for i, p in enumerate(o.data.polygons):
            o.data.uv_textures.active.data[i].image = self.temp_poly_imgs[i]

    def add_image_to_material(self, m):
        sce = bpy.context.scene
        opt = sce.bt_props

        # Search or add new texture using the image
        tex = [ts.texture for ts in m.texture_slots if
                ts and ts.texture and ts.texture.type == 'IMAGE' and ts.texture.image == self.target_img]
        if tex: tex = tex[0]
        else:
            tex = bpy.data.textures.new(self.target_img.name, 'IMAGE')
            tex.image = self.target_img
            if self.type == 'NORMALS':
                tex.use_normal_map = True

        # Add new texture slot for material
        ts = [(i, ts) for i, ts in enumerate(m.texture_slots) if ts and ts.texture == tex]
        if ts: 
            idx = ts[0][0]
            ts = ts[0][1]

            # force activate texture slots
            m.bt_props.original_active_slots += str(idx) + ';'
        else:
            ts = m.texture_slots.add()
            ts.texture = tex
            ts.texture_coords = 'UV'
            if self.type == 'AO':
                ts.blend_type = opt.ao_blend
            elif self.type == 'DIRTY':
                ts.blend_type = opt.dirty_blend
            elif self.type == 'LIGHTS':
                ts.blend_type = opt.lights_blend
            elif self.type == 'DIFFUSE_COLOR':
                ts.blend_type = opt.color_blend
            elif self.type == 'SPECULAR_COLOR':
                ts.use_map_color_diffuse = False
                ts.use_map_color_spec = True
                ts.blend_type = opt.specular_blend
            elif self.type == 'NORMALS':
                ts.use_map_color_diffuse = False
                ts.use_map_normal = True

        if self.type == 'NORMALS':
            ts.normal_map_space = sce.render.bake_normal_space

    def get_create_clone_object(self, obj):
        sce = bpy.context.scene
        opt = sce.bt_props

        if obj.type not in {'MESH', 'CURVE'}:
            return

        # Remember selection
        original_active = sce.objects.active
        original_selected_objs = [o for o in sce.objects if o.select]
        bpy.ops.object.select_all(action='DESELECT')

        # Trying to get clone object
        clone_name = 'CLONE-' + obj.name
        clone_obj = sce.objects.get(clone_name)

        if not clone_obj:

            # Make multires modifier active and in full level first
            if self.type == 'NORMALS':
                for mod in obj.modifiers:
                    if mod.type == 'MULTIRES':
                        mod.show_viewport = True
                        mod.show_render = True
                        mod.levels = mod.total_levels
                        mod.render_levels = mod.total_levels

                        # If multires found, disable other subsurf modifier
                        for mod in obj.modifiers:
                            if mod.type == 'SUBSURF':
                                mod.show_viewport = False
                                mod.show_render = False

            # Clone if dirty object not found
            clone_mesh = obj.data.copy()
            clone_obj = obj.copy()
            clone_obj.data = clone_mesh
            clone_obj.name = clone_name
            sce.objects.link(clone_obj)

            # Select dirty object
            sce.objects.active = clone_obj
            clone_obj.select = True

            # Convert if object is a curve
            if clone_obj.type == 'CURVE':
                bpy.ops.object.convert(target='MESH')

            # Apply shape keys
            if clone_obj.data.shape_keys:

                # Add mix shapes
                bpy.ops.object.shape_key_add(from_mix=True)

                # Get Number of keys
                keylen = len(clone_obj.data.shape_keys.key_blocks) #+ 1
                
                # Delete all shapes
                for i in range(keylen):
                    clone_obj.active_shape_key_index = 0
                    bpy.ops.object.shape_key_remove(all=False)

            # Do something on modifiers
            for mod in clone_obj.modifiers:
                # Remove potentially harmful modiefiers
                if (mod.type in {'SOLIDIFY', 'MIRROR'}
                    or (mod.type == 'ARMATURE' and opt.use_rest_pose)
                    # or (not sce.render.use_bake_multires and mod.type == 'MULTIRES'):
                    ):
                    bpy.ops.object.modifier_remove(modifier = mod.name)
                else:
                    # Apply all other ones
                    try:
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier = mod.name)
                    except: pass

            # Delete materials on clone objects for safety purpose
            if self.type != 'NORMALS':
                clone_obj.data.materials.clear()

            if self.type == 'DIRTY':
                # Paint dirty color
                bpy.ops.object.mode_set(mode='VERTEX_PAINT')
                bpy.ops.paint.vertex_color_dirt(
                        blur_strength = opt.dirt_blur_strength,
                        blur_iterations = opt.dirt_blur_iterations,
                        clean_angle = opt.dirt_clean_angle,
                        dirt_angle = opt.dirt_angle,
                        dirt_only = opt.dirt_only
                        )
                bpy.ops.object.mode_set(mode='OBJECT')

        if self.type == 'NORMALS':
            #subsurf_found = False
            for mod in obj.modifiers:
                #print(mod.name)
                if mod.type == 'MULTIRES':
                    #print('bbbb')
                    #mod.show_render = False
                    #mod.show_viewport = False
                    mod.levels = opt.subdiv_base
                    mod.render_levels = opt.subdiv_base
                #if mod.type == 'SUBSURF':
                #    subsurf_found = True
                #    mod.show_render = True
                #    mod.show_viewport = True
                #    mod.levels = opt.subdiv_base
                #    mod.render_levels = opt.subdiv_base
                #    break

            #if not subsurf_found:
            #    sce.objects.active = obj
            #    bpy.ops.object.modifier_add(type='SUBSURF')
            #    obj.name += '-EXTRASUBSURF'
            #    mod = obj.modifiers[-1]
            #    mod.levels = opt.subdiv_base
            #    mod.render_levels = opt.subdiv_base

        # Recover selection
        bpy.ops.object.select_all(action='DESELECT')
        sce.objects.active = original_active
        for o in original_selected_objs:
            o.select = True

        return clone_obj

    def get_create_temp_mat(self):
        temp_mat = bpy.data.materials.get('__temp_hi_mat')
        if not temp_mat:
            temp_mat = bpy.data.materials.new('__temp_hi_mat')

        return temp_mat

    def populate_highpoly_objects_and_materials(self, o):
        sce = bpy.context.scene
        opt = sce.bt_props
        active_layer = [i for i, layer in enumerate(sce.layers) if layer == True][0]
        self.hi_objs = [ob for ob in sce.objects if opt.highpoly_prefix + o.name in ob.name]

        # Report object that has no highpoly version
        if not self.hi_objs:
            self.report({'ERROR'}, "Highpoly objects of " + o.name + 
                    " not found! They should have '" + opt.highpoly_prefix + o.name + "' in their name")
            return False

        for i, ho in enumerate(self.hi_objs):

            if self.type == 'DIRTY':
                ho = self.get_create_clone_object(ho)
                self.hi_objs[i] = ho

            # Use active layer
            if not ho.layers[active_layer]:
                ho.layers[active_layer] = True

            # Create new mat if object hasn't one
            if not ho.data.materials:
                temp_mat = self.get_create_temp_mat()
                ho.data.materials.append(temp_mat)

            ho.select = True

        return True

    def prepare_bake_setting(self):
        sce = bpy.context.scene
        opt = sce.bt_props

        # Set some bake properties
        if self.type == 'DIRTY':
            sce.render.bake_type = 'VERTEX_COLORS'
            #sce.render.bake_type = 'FULL'
        elif self.type in {'LIGHTS', 'FULL_RENDER'}:
            sce.render.bake_type = 'FULL'
        #elif self.type == 'DIFFUSE_COLOR':
        elif self.type in {'DIFFUSE_COLOR', 'SPECULAR_COLOR'}:
            sce.render.bake_type = 'TEXTURE'
        #elif self.type == 'SPECULAR_COLOR':
        #    sce.render.bake_type = 'SPEC_COLOR'
        else: sce.render.bake_type = self.type

        #if sce.render.engine == 'BLENDER_RENDER':
        sce.render.use_bake_clear = False

        if self.type in {'LIGHTS'} or (sce.render.bake_type == 'AO' and not opt.use_highpoly):
            sce.render.use_bake_selected_to_active = False
        else:
            sce.render.use_bake_selected_to_active = True

        sce.render.use_bake_multires = False
        #elif sce.render.engine == 'CYCLES':
        #    sce.render.bake.use_clear = False
        #    sce.render.bake.use_selected_to_active = True

        sce.render.use_simplify = False

        if opt.antialias:
            # Supersample image dictionary, for lazy downsampling
            self.ss_dict = {}

            # REMEMBER margin setting
            #if sce.render.engine == 'BLENDER_RENDER':
            sce.render.bake_margin *= int(opt.sample)
            #elif sce.render.engine == 'CYCLES':
            #    sce.render.bake.margin = sce.render.bake_margin * int(opt.sample)

    def downsample_images(self):
        sce = bpy.context.scene

        # Downsample image for antialias
        for key, value in self.ss_dict.items():
            ss_img = bpy.data.images.get(key)
            target_img = bpy.data.images.get(value)
            print('Downsampling ' + self.target_img.name + '...')
            downsample_image(ss_img, target_img)

        # Delete supersample image
        for img in bpy.data.images:
            if img.name.endswith('_supersample'):
                img.user_clear()
                bpy.data.images.remove(img, do_unlink=True)

    def select_object(self, o):
        o.hide = False
        sce = bpy.context.scene
        bpy.ops.object.select_all(action='DESELECT')
        o.select = True
        sce.objects.active = o
        bpy.ops.object.mode_set(mode='OBJECT') 

    def delete_stuffs(self):
        sce = bpy.context.scene
        opt = sce.bt_props
        
        # Delete temporary highpoly mat
        temp_mat = bpy.data.materials.get('__temp_hi_mat')
        if temp_mat:
            for o in bpy.data.objects:
                if o.type != 'MESH': continue
                mats = o.data.materials
                if mats and mats[0] == temp_mat:
                    o.data.materials.clear()
            temp_mat.user_clear()
            bpy.data.materials.remove(temp_mat, do_unlink=True)

        bpy.ops.object.select_all(action='DESELECT')
        for o in bpy.data.objects:
            # Delete clone objects
            if o.name.startswith('CLONE-'):
                mesh = o.data
                o.select = True
                sce.objects.active = o

                bpy.ops.object.delete(use_global=False)
                bpy.data.meshes.remove(mesh, do_unlink=True)

            # Delete extra modifiers
            if o.name.endswith('-EXTRASUBSURF'):
                
                # Select object
                o.select = True
                sce.objects.active = o

                # Delete modifier
                mod = o.modifiers[-1]
                bpy.ops.object.modifier_remove(modifier=mod.name)

                # Recover name
                o.name = o.name.replace('-EXTRASUBSURF', '')

                # Deselect object
                o.select = False

        # Recover lights
        if self.type in {'LIGHTS'} and opt.bake_light_type != 'AVAILABLE':
            bpy.ops.object.select_all(action='DESELECT')
            for o in sce.objects:
                if o.type == 'LAMP':
                    if o.name == temp_lamp_name:
                        lamp = o.data
                        o.select = True
                        sce.objects.active = o
                        bpy.ops.object.delete(use_global=False)
                        bpy.data.lamps.remove(lamp, do_unlink=True)
                    else:
                        o.hide_render = self.original_active_lamp[o.name]

    def setup_lights(self):
        sce = bpy.context.scene
        opt = sce.bt_props

        self.affected_lights = []

        # Disable world lighting
        world = sce.world
        world.light_settings.use_ambient_occlusion = False
        world.light_settings.use_environment_light = False
        world.light_settings.use_indirect_light = False

        if opt.bake_light_type == 'AVAILABLE':
            for obj in sce.objects:
                if obj.type == 'LAMP' and in_active_layer(obj):
                    self.affected_lights.append(obj)
        else:
            self.original_active_lamp = {}

            for o in sce.objects:
                if o.type == 'LAMP':
                    self.original_active_lamp[o.name] = o.hide_render
                    o.hide_render = True
            bpy.ops.object.mode_set(mode='OBJECT') 

            if opt.bake_light_type == 'SUN':
                bpy.ops.object.lamp_add(type='SUN', location=(0.0, 0.0, 0.0))
            elif opt.bake_light_type == 'HEMI':
                bpy.ops.object.lamp_add(type='HEMI', location=(0.0, 0.0, 0.0))

            if opt.bake_light_linear:
                sce.display_settings.display_device = 'None'
        
            new_lamp = bpy.context.object
            new_lamp.name = temp_lamp_name
            new_lamp.data.use_specular = False
            new_lamp.data.color = opt.light_color

            if opt.bake_light_direction == 'UP':
                new_lamp.rotation_euler = Euler((0.0, 0.0, 0.0))
            elif opt.bake_light_direction == 'DOWN':
                new_lamp.rotation_euler = Euler((0.0, math.radians(180), 0.0))
            elif opt.bake_light_direction == 'FRONT':
                new_lamp.rotation_euler = Euler((math.radians(90), 0.0, 0.0))
            elif opt.bake_light_direction == 'BACK':
                new_lamp.rotation_euler = Euler((math.radians(270), 0.0, 0.0))
            elif opt.bake_light_direction == 'LEFT':
                new_lamp.rotation_euler = Euler((0.0, math.radians(90), 0.0))
            elif opt.bake_light_direction == 'RIGHT':
                new_lamp.rotation_euler = Euler((0.0, math.radians(270), 0.0))

            self.affected_lights.append(new_lamp)

    def prepare_affected_objs_and_mats(self, o):
        sce = bpy.context.scene
        opt = sce.bt_props

        # Disable modifiers that potentially cause problem on low poly object
        for mod in o.modifiers:
            if mod.type in {'MIRROR', 'SOLIDIFY'}:
                mod.show_render = False
                mod.show_viewport = False

        # Iterate through low and highpoly objects
        objs = [o] + self.hi_objs
        #print(objs)

        # Use rest pose for all armatures if use rest pose is true
        if opt.use_rest_pose:
            for ob in sce.objects:
                if ob.type == 'ARMATURE':
                    ob.data.pose_position = 'REST'

        # Dealing with isolated bake
        if (self.type == 'AO' and opt.isolated_ao) or (self.type == 'LIGHTS' and opt.isolated_light):
            #print('aaaaaaa')

            active_layer = [i for i, layer in enumerate(sce.layers) if layer == True][0]
            inactive_layer = [i for i in range(20) if i != active_layer][0]
            #print(active_layer, inactive_layer)
            #print(objs)

            if self.type == 'LIGHTS':
                affected_objs = objs + self.affected_lights
            else: affected_objs = objs

            # Disable other layer than active layer
            for i, layer in enumerate(sce.layers):
                if i != active_layer:
                    sce.layers[i] = False

            # Move affected objects to active layer
            for obj in affected_objs:
                obj.layers[active_layer] = True

            # Move over other objects to inactive layer
            for obj in sce.objects:
                if obj not in affected_objs:
                    obj.layers[inactive_layer] = True
                    for i, layer in enumerate(obj.layers):
                        if i != inactive_layer:
                            obj.layers[i] = False

        for ob in objs:

            # Modify materials
            for m in ob.data.materials:

                # Make material not using nodes
                #m.use_nodes = False

                # Disable shadeless
                m.use_shadeless = False

                # Make material color pure white for AO and light baking
                if self.type in {'AO', 'LIGHTS'}:
                    m.diffuse_intensity = 1.0
                    m.diffuse_color = (1.0, 1.0, 1.0)
                    m.use_diffuse_ramp = False
                    m.use_nodes = False
                # Copy specular color to diffuse color
                elif self.type == 'SPECULAR_COLOR':
                    m.diffuse_intensity = 1.0
                    m.diffuse_color = m.specular_color.copy()

                for i, ts in enumerate(m.texture_slots):
                    if not ts or not ts.texture or not m.use_textures[i]: continue

                    # Normal and light bake will still use normal map
                    if self.type in {'NORMALS', 'LIGHTS'}:
                        if ts.use_map_normal: continue

                    # Disable textures on other than diffuse bake
                    if self.type not in {'DIFFUSE_COLOR', 'SPECULAR_COLOR', 'FULL_RENDER'}:
                        m.use_textures[i] = False

                    # Make diffuse active on specular color
                    #if self.type == 'SPECULAR_COLOR':
                    #    ts.specular_color_factor = srgb_to_linear(ts.specular_color_factor)

                    if self.type == 'SPECULAR_COLOR':
                        if ts.use_map_color_spec:
                            ts.use_map_color_diffuse = True
                            ts.diffuse_color_factor = ts.specular_color_factor
                        else:
                            m.use_textures[i] = False

                    # HACK! Fix gamma on bake if using rgb to intensity
                    #if self.type == 'DIFFUSE_COLOR' and ts.use_rgb_to_intensity:
                    if ts.use_rgb_to_intensity:
                        ts.color = srgb_to_linear(ts.color)

                # Modify modifiers
                for mod in ob.modifiers:
                    #if self.type in {'AO', 'LIGHTS'} and mod.type in {'MULTIRES', 'SUBSURF'}:
                    if self.type in {'AO'} and mod.type in {'MULTIRES'}:
                        mod.levels = mod.total_levels
                        mod.render_levels = mod.total_levels

            # Modify modifiers
            #if sce.render.use_bake_multires and not opt.use_highpoly:

            #    multires_found = False

            #    for mod in ob.modifiers:

            #        if mod.type == 'MULTIRES':

            #            if not mod.show_viewport:
            #                mod.show_viewport = True
            #            if not mod.show_render:
            #                mod.show_render = True

            #            multires_found = True

            #            if opt.multires_base > mod.total_levels:
            #                mod.levels = mod.total_levels
            #            else: mod.levels = opt.multires_base
            #            mod.render_levels = mod.total_levels

            #        # If multires already found, disable all modifier after that
            #        if multires_found and mod.type != 'MULTIRES':
            #            mod.show_render = False
            #            mod.show_viewport = False

    def bake_internal(self, objs):
        sce = bpy.context.scene
        opt = sce.bt_props

        self.original_engine = sce.render.engine
        if sce.render.engine != 'BLENDER_RENDER':
            sce.render.engine = 'BLENDER_RENDER'

        self.prepare_bake_setting()

        if self.type in {'LIGHTS'}:
            self.setup_lights()

        # Cycle though objects
        for o in objs:

            # Select object
            self.select_object(o)

            # Check if multires is present
            multires_found = any([mod for mod in o.modifiers if mod.type == 'MULTIRES'])

            # Populate high poly objects & materials
            self.hi_objs = []
            #if opt.use_highpoly and not o.name.startswith(opt.highpoly_prefix):
            if opt.use_highpoly:
                if not self.populate_highpoly_objects_and_materials(o):
                    continue
            elif self.type == 'DIRTY' or (self.type == 'NORMALS' and multires_found):
                clone_obj = self.get_create_clone_object(o)
                clone_obj.select = True
                self.hi_objs = [clone_obj]

            # Populate affected objects
            self.prepare_affected_objs_and_mats(o)

            # Populate target materials
            if opt.all_selected:
                target_mats = [m for m in o.data.materials]
            else: target_mats = [o.active_material]
            #else: target_mats = [paint_slots.get_active_material()]

            # Cycle though materials
            for m in target_mats:
                if not m: continue

                # Select material and faces that using it
                m_idx = [i for i, mat in enumerate(o.data.materials) if m == mat][0]
                #o.active_material_index = m_idx
                
                # Use node material if using nodes
                actual_mat = None
                if m.use_nodes:
                    #m.use_nodes = False
                    actual_mat = m.active_node_material
                else: 
                    actual_mat = m

                if not actual_mat:
                    continue

                # Preparing target and higher res image for antialiasing
                self.set_target_image(actual_mat)
                if opt.antialias:
                    self.set_supersample_image(actual_mat)

                # Set active uv if it's already set
                if self.target_uv:
                    uv = o.data.uv_textures.get(self.target_uv)
                    uv.active = True

                # Set target image to polygon
                self.set_polygon_image(o, m_idx)

                #return {'FINISHED'}

                # Bake!
                print('Baking ' + self.target_img.name + '...')
                bpy.ops.object.bake_image()

                # Add baked count
                self.baked_count += 1

                #return {'FINISHED'}

                # If set shadeless if forced
                if ((self.type == 'LIGHTS' and opt.set_shadeless_after_baking_lights) or
                    (self.type == 'FULL_RENDER' and opt.set_shadeless_after_baking_full_render)
                    ):
                    m.use_shadeless = True

                # Activate  paint slot if disabled

                # Recover some stuffs
                self.delete_temp_image()
                self.recover_polygon_image(o)
                self.add_image_to_material(actual_mat)
        
        if opt.antialias:
            self.downsample_images()

        sce.render.engine = self.original_engine

    # REMEMBER many stuffs
    def remember_stuffs(self, context):
        sce = context.scene
        opt = sce.bt_props
        world = sce.world

        # Remember active object and object selection
        self.original_active_object = context.object
        self.original_selected_objects = [o for o in sce.objects if o.select]
        self.original_object_hide = [o for o in sce.objects if o.hide]
        #self.old_mode = context.object.mode
        self.old_active_layers = [i for i, layer in enumerate(sce.layers) if layer == True]

        # Remember bake setting
        self.original_margin = sce.render.bake_margin
        self.original_use_bake_clear = sce.render.use_bake_clear
        self.original_use_bake_multires = sce.render.use_bake_multires
        #self.original_bake_use_clear = sce.render.bake.use_clear
        self.original_use_bake_selected_to_active = sce.render.use_bake_selected_to_active
        #self.original_bake_use_selected_to_active = sce.render.bake.use_selected_to_active
        opt.original_color_space = sce.display_settings.display_device

        # Remember scene setting
        self.original_use_simplify = sce.render.use_simplify

        self.original_slot_colors = {}
        self.original_pose_position = {}
        self.original_object_layers = {}
        self.original_object_active_uv = {}

        # Remember world settings
        self.use_ao = world.light_settings.use_ambient_occlusion
        self.use_env_light = world.light_settings.use_environment_light
        self.use_indir_light = world.light_settings.use_indirect_light

        for o in sce.objects:

            # Remember object layers
            self.original_object_layers[o.name] = []
            for i, layer in enumerate(o.layers):
                if layer:
                    self.original_object_layers[o.name].append(i)

            if o.type == 'ARMATURE':
                self.original_pose_position[o.name] = o.data.pose_position

            if o.type == 'MESH':
                # Remember active UV
                if o.data.uv_layers.active:
                    self.original_object_active_uv[o.name] = o.data.uv_layers.active.name

            if o.type in {'MESH', 'CURVE'}:

                # Remember material properties
                for m in o.data.materials:
                    if not m: continue
                    m.bt_props.original_diffuse_intensity = m.diffuse_intensity
                    m.bt_props.original_diffuse_color = m.diffuse_color
                    m.bt_props.original_use_nodes = m.use_nodes
                    m.bt_props.original_use_shadeless = m.use_shadeless
                    m.bt_props.original_use_diffuse_ramp = m.use_diffuse_ramp

                    # Remember material active slot
                    for i, ts in enumerate(m.texture_slots):
                        if not ts or not ts.texture or not m.use_textures[i]: continue
                        m.bt_props.original_active_slots += str(i) + ';'

                        if not ts.use_map_color_diffuse:
                            m.bt_props.original_not_use_diffuse_color += str(i) + ';'

                        m.bt_props.original_diffuse_color_factor += str(i) + '#' + str(ts.diffuse_color_factor) + ';'
                        m.bt_props.original_specular_color_factor += str(i) + '#' + str(ts.specular_color_factor) + ';'

                        self.original_slot_colors[m.name + '___' + str(i)] = ts.color.copy()

                # Remember modifier show render value
                for i, mod in enumerate(o.modifiers):
                    if mod.show_render: o.bt_props.original_modifiers_show_render += str(i) + ';'
                    if mod.show_viewport: o.bt_props.original_modifiers_show_viewport += str(i) + ';'

                # Remember multires modifier properties
                for mod in o.modifiers:
                    if mod.type in {'MULTIRES', 'SUBSURF'}:
                        o.bt_props.original_multires_preview = mod.levels
                        o.bt_props.original_multires_render = mod.render_levels
                        break

    # RECOVER many stuffs
    def recover_stuffs(self, context):
        sce = context.scene
        opt = sce.bt_props
        world = sce.world

        # Delete unused data
        self.delete_stuffs()

        # Recover bake setting
        sce.render.bake_margin = self.original_margin
        #sce.render.bake.margin = self.original_margin
        sce.render.use_bake_clear = self.original_use_bake_clear
        #sce.render.bake.use_clear = self.original_bake_use_clear
        sce.render.use_bake_selected_to_active = self.original_use_bake_selected_to_active
        sce.render.use_bake_multires = self.original_use_bake_multires
        #sce.render.bake.use_selected_to_active = self.original_bake_use_selected_to_active
        sce.display_settings.display_device = opt.original_color_space
        sce.render.use_simplify = self.original_use_simplify

        # Recover world settings
        world.light_settings.use_ambient_occlusion = self.use_ao
        world.light_settings.use_environment_light = self.use_env_light
        world.light_settings.use_indirect_light = self.use_indir_light
        
        # Recover scene layers
        for i, layer in enumerate(sce.layers):
            if i in self.old_active_layers:
                sce.layers[i] = True
        for i, layer in enumerate(sce.layers):
            if i not in self.old_active_layers:
                sce.layers[i] = False

        bpy.ops.object.select_all(action='DESELECT')
        sce.objects.active = self.original_active_object
        for o in sce.objects:

            # Recover selection
            if o in self.original_selected_objects:
                o.select = True
            else: o.select = False

            # Recover hide
            if o in self.original_object_hide:
                o.hide = True
            else: o.hide = False

            # Recover object layers
            if o.name in self.original_object_layers:
                # Set active layer
                for i, layer in enumerate(o.layers):
                    if i in self.original_object_layers[o.name]:
                        o.layers[i] = True
                # Set inactive layer
                for i, layer in enumerate(o.layers):
                    if i not in self.original_object_layers[o.name]:
                        o.layers[i] = False

            if o.type == 'ARMATURE':
                o.data.pose_position = self.original_pose_position[o.name]

            if o.type == 'MESH':
                # Recover active uv
                if o.name in self.original_object_active_uv:
                    uv = o.data.uv_textures.get(self.original_object_active_uv[o.name])
                    if uv: uv.active = True

            if o.type in {'MESH', 'CURVE'}:

                original_modifiers_show_render = [int(i) for i in o.bt_props.original_modifiers_show_render.split(';') if i != '']
                original_modifiers_show_viewport = [int(i) for i in o.bt_props.original_modifiers_show_viewport.split(';') if i != '']
                for i, mod in enumerate(o.modifiers):

                    if i in original_modifiers_show_render:
                        o.modifiers[i].show_render = True
                    else: o.modifiers[i].show_render = False

                    if i in original_modifiers_show_viewport:
                        o.modifiers[i].show_viewport = True
                    else: o.modifiers[i].show_viewport = False

                    if mod.type in {'MULTIRES', 'SUBSURF'}: 
                        if not opt.set_multires_level_to_base or self.type in {'AO'}: #, 'LIGHTS'}:
                            mod.levels = o.bt_props.original_multires_preview
                            mod.render_levels = o.bt_props.original_multires_render

                o.bt_props.original_modifiers_show_render = ''
                o.bt_props.original_modifiers_show_viewport = ''

                for m in o.data.materials:
                    if not m: continue
                    m.diffuse_intensity = m.bt_props.original_diffuse_intensity
                    m.diffuse_color = m.bt_props.original_diffuse_color
                    m.use_diffuse_ramp = m.bt_props.original_use_diffuse_ramp
                    m.use_nodes = m.bt_props.original_use_nodes
                    if ((self.type == 'LIGHTS' and opt.set_shadeless_after_baking_lights) or
                        (self.type == 'FULL_RENDER' and opt.set_shadeless_after_baking_full_render)
                        ):
                        pass
                    else: m.use_shadeless = m.bt_props.original_use_shadeless

                    original_active_slots = [int(i) for i in m.bt_props.original_active_slots.split(';') if i != '']
                    original_not_use_diffuse_color = [int(i) for i in m.bt_props.original_not_use_diffuse_color.split(';') if i != '']
                    original_diffuse_color_factor = {int(a.split('#')[0]) : float(a.split('#')[1]) for a in m.bt_props.original_diffuse_color_factor.split(';') if a != ''}
                    original_specular_color_factor = {int(a.split('#')[0]) : float(a.split('#')[1]) for a in m.bt_props.original_specular_color_factor.split(';') if a != ''}

                    for i, ts in enumerate(m.texture_slots):

                        if not ts: continue

                        # Recover original active slots
                        if i in original_active_slots:
                            m.use_textures[i] = True

                        if i in original_not_use_diffuse_color:
                            ts.use_map_color_diffuse = False

                        if i in original_diffuse_color_factor:
                            ts.diffuse_color_factor = original_diffuse_color_factor[i]

                        if i in original_specular_color_factor:
                            ts.specular_color_factor = original_specular_color_factor[i]

                        # Recover original slot color
                        if m.name + '___' + str(i) in self.original_slot_colors:
                            col = self.original_slot_colors[m.name + '___' + str(i)]
                            ts.color[0] = col[0]
                            ts.color[1] = col[1]
                            ts.color[2] = col[2]

                    m.bt_props.original_active_slots = ''
                    m.bt_props.original_not_use_diffuse_color = ''
    
    def execute(self, context):
        # Start timer
        start_time = time.time()

        # Get active scene
        sce = context.scene

        # Halt material override update
        sce.mo_props.halt_update = True

        # Pointer to target image
        self.target_img = None

        # Number of baked images
        self.baked_count = 0

        # Go to object mode
        old_hide = context.object.hide
        old_mode = context.object.mode
        context.object.hide = False
        bpy.ops.object.mode_set(mode='OBJECT') 

        # Turn off material override
        original_mo_mode = 'OFF'
        if sce.mo_props.override_mode != 'OFF':
            original_mo_mode = sce.mo_props.override_mode
            bpy.ops.material.override_material(mode='OFF')

        # Remember selection
        self.remember_stuffs(context)

        # Target Objects
        if sce.bt_props.all_selected:
            objs = [o for o in sce.objects if o.select and in_active_layer(o)]
        else: objs = [context.object]

        # Bake!
        print('Baking begins...')
        self.bake_internal(objs)

        #return {'FINISHED'}

        # Recover selection
        self.recover_stuffs(context)

        # Refresh paint slots
        bpy.ops.material.yp_refresh_paint_slots()

        # Redo material override
        if original_mo_mode != 'OFF':
            bpy.ops.material.override_material(mode=original_mo_mode)

        # Go back to old mode
        bpy.ops.object.mode_set(mode=old_mode)
        context.object.hide = old_hide

        # Select target image
        mat = context.object.active_material
        if mat: 
            for i, img in enumerate(mat.texture_paint_images):
                if img == self.target_img:
                    mat.paint_active_slot = i
        
        # Reactivate material override update
        sce.mo_props.halt_update = False

        if self.baked_count == 0:
            #if self.type == 'NORMALS':
            #    self.report({'ERROR'}, "Bake failed! You need multires modifier or high poly object for baking normal.")
            #else:
            self.report({'ERROR'}, "Bake failed! There's something wrong!")
            return {'CANCELLED'}

        # End timer
        print('Congrats! You bake ' + self.type + '!')
        self.report({'INFO'}, "Bake completed in %.2f seconds!" % (time.time() - start_time)) 

        return {'FINISHED'}

class YPBakeToolsSetting(bpy.types.PropertyGroup):
    antialias = BoolProperty(
        name = "Antialias",
        description = "Use supersample antialiasing to bake result. WARNING! REALLY SLOW!!",
        default = True)

    bake_type = EnumProperty(
        name = "Bake Type",
        description="Type of bake", 
        items=(
            ('NORMALS', "Normal", ""),
            ('AO', "AO", ""),
            ('DIRTY', "Dirty Vertex Color", ""),
            ('LIGHTS', "Lights", ""),
            ('DIFFUSE_COLOR', "Diffuse Color", ""),
            ('SPECULAR_COLOR', "Specular Color", ""),
            ('FULL_RENDER', "Full Render", ""),
            #('POINTINESS', "Pointiness", ""),
            ), 
        default='AO',
        )

    res_x = EnumProperty(
            name = "Resolution X",
            #description = "Width of the bake texture, does not effect anything if normal map is already used",
            items=(
                ('8', '8', ''),
                ('16', '16', ''),
                ('32', '32', ''),
                ('64', '64', ''),
                ('128', '128', ''),
                ('256', '256', ''),
                ('512', '512', ''),
                ('1024', '1024', ''),
                ('2048', '2048', ''),
                ('4096', '4096', '')),
            default = '1024')

    res_y = EnumProperty(
            name = "Resolution Y",
            #description = "Height of the bake texture, does not effect anything if normal map is already used",
            items=(
                ('8', '8', ''),
                ('16', '16', ''),
                ('32', '32', ''),
                ('64', '64', ''),
                ('128', '128', ''),
                ('256', '256', ''),
                ('512', '512', ''),
                ('1024', '1024', ''),
                ('2048', '2048', ''),
                ('4096', '4096', '')),
            default = '1024')

    sample = EnumProperty(
            name = "AA Sample",
            description = "Sample for antialiasing. WARNING! REALLY SLOW!!",
            items=(('2', "2x", "2x supersampling"),
                ('3', "3x", "3x supersampling"),
                ('4', "4x", "4x supersampling")),
            default = '2')

    bake_light_type = EnumProperty(
            name = "Bake Lights Type",
            description = "Type of baking lights",
            items=(('AVAILABLE', "Scene Lights", ""),
                ('SUN', "Sun", ""),
                ('HEMI', "Hemi", "")),
            default = 'AVAILABLE')

    bake_light_direction = EnumProperty(
            name = "Light Direction",
            description = "Direction of defined light",
            items=(
                ('TOP', "Top", ""),
                ('DOWN', "Down", ""),
                ('FRONT', "Front", ""),
                ('BACK', "Back", ""),
                ('LEFT', "Left", ""),
                ('RIGHT', "Right", "")
                ),
            default = 'TOP')

    bake_light_linear = BoolProperty(default=True)
    original_color_space = StringProperty(default='sRGB')

    overwrite = BoolProperty(default=True)
    use_highpoly = BoolProperty(default=False)
    use_rest_pose = BoolProperty(
            name='Use Rest Pose',
            description = 'Use rest pose for all armatures',
            default = True)

    highpoly_prefix = StringProperty(default='HP-')
    ao_suffix = StringProperty(default='_AO')
    normals_suffix = StringProperty(default='_N')
    dirty_suffix = StringProperty(default='_DVC')
    lights_suffix = StringProperty(default='_L')
    diffuse_color_suffix = StringProperty(default='_D')
    specular_color_suffix = StringProperty(default='_S')
    full_render_suffix = StringProperty(default='_F')

    others_influence = BoolProperty(default=True)

    all_selected = BoolProperty(default=False, 
            description="Bake all selected objects with all it's material")

    dirt_blur_strength = FloatProperty(name='Blur Strength', default=1, min=0.01, max=1)
    dirt_blur_iterations = IntProperty(name='Blur Iterations', default=1, min=0, max=40)
    dirt_clean_angle = FloatProperty(name='Highlight Angle', 
            default=math.radians(180), min=0, max=math.radians(180), subtype='ANGLE')
    dirt_angle = FloatProperty(name='Dirt Angle',
            default=math.radians(90), min=0, max=math.radians(180), subtype='ANGLE')
    dirt_only = BoolProperty(name='Dirt Only', default=True)

    ao_blend = EnumProperty(items = blend_type_items, default = 'MULTIPLY')
    dirty_blend = EnumProperty(items = blend_type_items, default = 'ADD')
    lights_blend = EnumProperty(items = blend_type_items, default = 'MULTIPLY')
    color_blend = EnumProperty(items = blend_type_items, default = 'MIX')
    specular_blend = EnumProperty(items = blend_type_items, default = 'MIX')
    full_render_blend = EnumProperty(items = blend_type_items, default = 'MIX')

    #multires_base = IntProperty(name='Multires Base', default=0, min=0, max=9)
    subdiv_base = IntProperty(
            name='Subdivision Base',
            description = 'Set subdivision level for bake target (Only works if using own multires)',
            default=1, min=0, max=9)

    set_multires_level_to_base = BoolProperty(
            name = 'Set Multires Level to Base',
            description = 'Set Multires level to subdivision base after baking (Only works if using own multires)',
            default = True)

    set_shadeless_after_baking_lights = BoolProperty(name='Set Shadeless after Baking', default=True)
    set_shadeless_after_baking_full_render = BoolProperty(name='Set Shadeless after Baking', default=True)

    isolated_ao = BoolProperty(name="Isolate object so other objects won't affect the ao result", default=False)
    isolated_light = BoolProperty(name="Isolate object so other objects won't affect the baked light result", default=False)

    light_color = FloatVectorProperty(name='Light Color', size=3, subtype='COLOR', default=(1.0,1.0,1.0), min=0.0, max=1.0)

class YPObjectBakeToolsProps(bpy.types.PropertyGroup):
    #original_layers = StringProperty(default='')
    original_modifiers_show_render = StringProperty(default='')
    original_modifiers_show_viewport = StringProperty(default='')
    original_multires_preview = IntProperty(default=0)
    original_multires_render = IntProperty(default=0)

class YPMaterialBakeToolsProps(bpy.types.PropertyGroup):
    original_active_slots = StringProperty(default='')
    original_diffuse_intensity = FloatProperty(default=0.0, min=0.0, max=1.0)
    original_use_diffuse_ramp = BoolProperty(default=False)
    original_diffuse_color = FloatVectorProperty(
            size=3, subtype='COLOR', default=(0.0,0.0,0.0), min=0.0, max=1.0)
    original_use_nodes = BoolProperty(default=False)
    original_use_shadeless = BoolProperty(default=False)
    original_not_use_diffuse_color = StringProperty(default='')
    original_diffuse_color_factor = StringProperty(default='')
    original_specular_color_factor = StringProperty(default='')

def register():
    bpy.types.Object.bt_props = PointerProperty(type=YPObjectBakeToolsProps)
    bpy.types.Material.bt_props = PointerProperty(type=YPMaterialBakeToolsProps)
    bpy.types.Scene.bt_props = PointerProperty(type=YPBakeToolsSetting)

def unregister():
    pass
