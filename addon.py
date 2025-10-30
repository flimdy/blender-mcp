# Enhanced Blender MCP Server with Comprehensive Modeling Tools
# Based on original by Siddharth Ahuja © 2025
# Extended with comprehensive Blender operations

import bpy
import mathutils
import json
import threading
import socket
import time
import requests
import tempfile
import traceback
import os
import shutil
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty
import io
from contextlib import redirect_stdout

bl_info = {
    "name": "Blender MCP Enhanced",
    "author": "BlenderMCP Enhanced",
    "version": (2, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > BlenderMCP",
    "description": "Enhanced Blender MCP with comprehensive modeling tools",
    "category": "Interface",
}

RODIN_FREE_TRIAL_KEY = "k9TcfFoEhNd9cCPP2guHAHHHkctZHIRhZDywZ1euGUXwihbYLpOjQhofby80NJez"

class BlenderMCPServer:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None
    
    def start(self):
        if self.running:
            print("Server is already running")
            return
            
        self.running = True
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            print(f"Enhanced BlenderMCP server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to start server: {str(e)}")
            self.stop()
            
    def stop(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        if self.server_thread:
            try:
                if self.server_thread.is_alive():
                    self.server_thread.join(timeout=1.0)
            except:
                pass
            self.server_thread = None
        print("Enhanced BlenderMCP server stopped")
    
    def _server_loop(self):
        """Main server loop in a separate thread"""
        print("Server thread started")
        self.socket.settimeout(1.0)
        
        while self.running:
            try:
                try:
                    client, address = self.socket.accept()
                    print(f"Connected to client: {address}")
                    client_thread = threading.Thread(target=self._handle_client, args=(client,))
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error accepting connection: {str(e)}")
                    time.sleep(0.5)
            except Exception as e:
                print(f"Error in server loop: {str(e)}")
                if not self.running:
                    break
                time.sleep(0.5)
        print("Server thread stopped")
    
    def _handle_client(self, client):
        """Handle connected client"""
        print("Client handler started")
        client.settimeout(None)
        buffer = b''
        
        try:
            while self.running:
                try:
                    data = client.recv(8192)
                    if not data:
                        print("Client disconnected")
                        break
                    
                    buffer += data
                    try:
                        command = json.loads(buffer.decode('utf-8'))
                        buffer = b''
                        
                        def execute_wrapper():
                            try:
                                response = self.execute_command(command)
                                response_json = json.dumps(response)
                                try:
                                    client.sendall(response_json.encode('utf-8'))
                                except:
                                    print("Failed to send response - client disconnected")
                            except Exception as e:
                                print(f"Error executing command: {str(e)}")
                                traceback.print_exc()
                                try:
                                    error_response = {"status": "error", "message": str(e)}
                                    client.sendall(json.dumps(error_response).encode('utf-8'))
                                except:
                                    pass
                            return None
                        
                        bpy.app.timers.register(execute_wrapper, first_interval=0.0)
                    except json.JSONDecodeError:
                        pass
                except Exception as e:
                    print(f"Error receiving data: {str(e)}")
                    break
        except Exception as e:
            print(f"Error in client handler: {str(e)}")
        finally:
            try:
                client.close()
            except:
                pass
            print("Client handler stopped")

    def execute_command(self, command):
        """Execute a command in the main Blender thread"""
        try:            
            return self._execute_command_internal(command)
        except Exception as e:
            print(f"Error executing command: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def _execute_command_internal(self, command):
        """Internal command execution with proper context"""
        cmd_type = command.get("type")
        params = command.get("params", {})

        # Base handlers always available
        handlers = {
            # Scene & Object Info
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "execute_code": self.execute_code,
            
            # Object Creation
            "add_primitive": self.add_primitive,
            "add_curve": self.add_curve,
            "add_text": self.add_text,
            "add_empty": self.add_empty,
            "add_light": self.add_light,
            "add_camera": self.add_camera,
            
            # Object Manipulation
            "transform_object": self.transform_object,
            "duplicate_object": self.duplicate_object,
            "delete_object": self.delete_object,
            "rename_object": self.rename_object,
            "parent_object": self.parent_object,
            "join_objects": self.join_objects,
            
            # Mesh Editing
            "enter_edit_mode": self.enter_edit_mode,
            "exit_edit_mode": self.exit_edit_mode,
            "select_all": self.select_all,
            "extrude_mesh": self.extrude_mesh,
            "subdivide_mesh": self.subdivide_mesh,
            "bevel_mesh": self.bevel_mesh,
            "inset_faces": self.inset_faces,
            "loop_cut": self.loop_cut,
            "merge_vertices": self.merge_vertices,
            
            # Modifiers
            "add_modifier": self.add_modifier,
            "remove_modifier": self.remove_modifier,
            "apply_modifier": self.apply_modifier,
            "list_modifiers": self.list_modifiers,
            
            # Materials & Shading
            "create_material": self.create_material,
            "assign_material": self.assign_material,
            "set_material_color": self.set_material_color,
            "set_smooth_shading": self.set_smooth_shading,
            
            # Animation
            "set_keyframe": self.set_keyframe,
            "set_frame": self.set_frame,
            "get_frame_range": self.get_frame_range,
            
            # Rendering
            "set_render_settings": self.set_render_settings,
            "render_image": self.render_image,
            "render_animation": self.render_animation,
            
            # Collections
            "create_collection": self.create_collection,
            "link_to_collection": self.link_to_collection,
            
            # Utilities
            "get_polyhaven_status": self.get_polyhaven_status,
            "get_hyper3d_status": self.get_hyper3d_status,
        }
        
        # Add Polyhaven handlers if enabled
        if bpy.context.scene.blendermcp_use_polyhaven:
            polyhaven_handlers = {
                "get_polyhaven_categories": self.get_polyhaven_categories,
                "search_polyhaven_assets": self.search_polyhaven_assets,
                "download_polyhaven_asset": self.download_polyhaven_asset,
                "set_texture": self.set_texture,
            }
            handlers.update(polyhaven_handlers)
        
        # Add Hyper3d handlers if enabled
        if bpy.context.scene.blendermcp_use_hyper3d:
            hyper3d_handlers = {
                "create_rodin_job": self.create_rodin_job,
                "poll_rodin_job_status": self.poll_rodin_job_status,
                "import_generated_asset": self.import_generated_asset,
            }
            handlers.update(hyper3d_handlers)

        handler = handlers.get(cmd_type)
        if handler:
            try:
                print(f"Executing handler for {cmd_type}")
                result = handler(**params)
                print(f"Handler execution complete")
                return {"status": "success", "result": result}
            except Exception as e:
                print(f"Error in handler: {str(e)}")
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}

    # ===== SCENE & OBJECT INFO =====
    
    def get_scene_info(self):
        """Get comprehensive information about the current scene"""
        try:
            print("Getting scene info...")
            scene_info = {
                "name": bpy.context.scene.name,
                "frame_current": bpy.context.scene.frame_current,
                "frame_start": bpy.context.scene.frame_start,
                "frame_end": bpy.context.scene.frame_end,
                "object_count": len(bpy.context.scene.objects),
                "objects": [],
                "materials_count": len(bpy.data.materials),
                "collections": [c.name for c in bpy.data.collections],
            }
            
            for i, obj in enumerate(bpy.context.scene.objects):
                if i >= 10:
                    break
                obj_info = {
                    "name": obj.name,
                    "type": obj.type,
                    "location": [round(float(obj.location.x), 2), 
                                round(float(obj.location.y), 2), 
                                round(float(obj.location.z), 2)],
                }
                scene_info["objects"].append(obj_info)
            
            print(f"Scene info collected: {len(scene_info['objects'])} objects")
            return scene_info
        except Exception as e:
            print(f"Error in get_scene_info: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}
    
    @staticmethod
    def _get_aabb(obj):
        """Returns the world-space axis-aligned bounding box (AABB) of an object."""
        if obj.type != 'MESH':
            raise TypeError("Object must be a mesh")
        local_bbox_corners = [mathutils.Vector(corner) for corner in obj.bound_box]
        world_bbox_corners = [obj.matrix_world @ corner for corner in local_bbox_corners]
        min_corner = mathutils.Vector(map(min, zip(*world_bbox_corners)))
        max_corner = mathutils.Vector(map(max, zip(*world_bbox_corners)))
        return [[*min_corner], [*max_corner]]

    def get_object_info(self, name):
        """Get detailed information about a specific object"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")
        
        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "location": [obj.location.x, obj.location.y, obj.location.z],
            "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
            "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            "visible": obj.visible_get(),
            "materials": [],
        }

        if obj.type == "MESH":
            bounding_box = self._get_aabb(obj)
            obj_info["world_bounding_box"] = bounding_box
        
        for slot in obj.material_slots:
            if slot.material:
                obj_info["materials"].append(slot.material.name)
        
        if obj.type == 'MESH' and obj.data:
            mesh = obj.data
            obj_info["mesh"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "polygons": len(mesh.polygons),
            }
        
        return obj_info
    
    def execute_code(self, code):
        """Execute arbitrary Blender Python code"""
        try:
            namespace = {"bpy": bpy}
            capture_buffer = io.StringIO()
            with redirect_stdout(capture_buffer):
                exec(code, namespace)
            captured_output = capture_buffer.getvalue()
            return {"executed": True, "result": captured_output}
        except Exception as e:
            raise Exception(f"Code execution error: {str(e)}")

    # ===== OBJECT CREATION =====
    
    def add_primitive(self, primitive_type="CUBE", location=[0, 0, 0], rotation=[0, 0, 0], scale=[1, 1, 1], name=None):
        """
        Add a primitive mesh object.
        Types: CUBE, SPHERE, CYLINDER, CONE, TORUS, MONKEY, PLANE, CIRCLE
        Example: add_primitive(primitive_type="SPHERE", location=[0, 0, 2], scale=[2, 2, 2])
        """
        primitive_ops = {
            "CUBE": lambda: bpy.ops.mesh.primitive_cube_add(),
            "SPHERE": lambda: bpy.ops.mesh.primitive_uv_sphere_add(),
            "CYLINDER": lambda: bpy.ops.mesh.primitive_cylinder_add(),
            "CONE": lambda: bpy.ops.mesh.primitive_cone_add(),
            "TORUS": lambda: bpy.ops.mesh.primitive_torus_add(),
            "MONKEY": lambda: bpy.ops.mesh.primitive_monkey_add(),
            "PLANE": lambda: bpy.ops.mesh.primitive_plane_add(),
            "CIRCLE": lambda: bpy.ops.mesh.primitive_circle_add(),
        }
        
        if primitive_type not in primitive_ops:
            raise ValueError(f"Invalid primitive type: {primitive_type}")
        
        primitive_ops[primitive_type]()
        obj = bpy.context.active_object
        obj.location = mathutils.Vector(location)
        obj.rotation_euler = mathutils.Euler(rotation)
        obj.scale = mathutils.Vector(scale)
        
        if name:
            obj.name = name
        
        return {"name": obj.name, "type": obj.type, "location": list(obj.location)}
    
    def add_curve(self, curve_type="BEZIER", location=[0, 0, 0], name=None):
        """Add a curve object. Types: BEZIER, CIRCLE, NURBS"""
        curve_ops = {
            "BEZIER": lambda: bpy.ops.curve.primitive_bezier_curve_add(),
            "CIRCLE": lambda: bpy.ops.curve.primitive_bezier_circle_add(),
            "NURBS": lambda: bpy.ops.curve.primitive_nurbs_curve_add(),
        }
        
        if curve_type not in curve_ops:
            raise ValueError(f"Invalid curve type: {curve_type}")
        
        curve_ops[curve_type]()
        obj = bpy.context.active_object
        obj.location = mathutils.Vector(location)
        
        if name:
            obj.name = name
        
        return {"name": obj.name, "type": obj.type}
    
    def add_text(self, text="Text", location=[0, 0, 0], name=None):
        """Add a text object"""
        bpy.ops.object.text_add()
        obj = bpy.context.active_object
        obj.data.body = text
        obj.location = mathutils.Vector(location)
        
        if name:
            obj.name = name
        
        return {"name": obj.name, "type": obj.type, "text": text}
    
    def add_empty(self, empty_type="PLAIN_AXES", location=[0, 0, 0], name=None):
        """Add an empty object. Types: PLAIN_AXES, ARROWS, SINGLE_ARROW, CIRCLE, CUBE, SPHERE, CONE"""
        bpy.ops.object.empty_add(type=empty_type)
        obj = bpy.context.active_object
        obj.location = mathutils.Vector(location)
        
        if name:
            obj.name = name
        
        return {"name": obj.name, "type": obj.type}
    
    def add_light(self, light_type="POINT", location=[0, 0, 0], energy=100, name=None):
        """Add a light. Types: POINT, SUN, SPOT, AREA"""
        bpy.ops.object.light_add(type=light_type)
        obj = bpy.context.active_object
        obj.location = mathutils.Vector(location)
        obj.data.energy = energy
        
        if name:
            obj.name = name
        
        return {"name": obj.name, "type": obj.type, "light_type": light_type}
    
    def add_camera(self, location=[0, 0, 0], rotation=[0, 0, 0], name=None):
        """Add a camera"""
        bpy.ops.object.camera_add()
        obj = bpy.context.active_object
        obj.location = mathutils.Vector(location)
        obj.rotation_euler = mathutils.Euler(rotation)
        
        if name:
            obj.name = name
        
        return {"name": obj.name, "type": obj.type}

    # ===== OBJECT MANIPULATION =====
    
    def transform_object(self, name, location=None, rotation=None, scale=None, relative=False):
        """Transform an object (move, rotate, scale)"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")
        
        if location:
            if relative:
                obj.location += mathutils.Vector(location)
            else:
                obj.location = mathutils.Vector(location)
        
        if rotation:
            if relative:
                obj.rotation_euler.rotate(mathutils.Euler(rotation))
            else:
                obj.rotation_euler = mathutils.Euler(rotation)
        
        if scale:
            if relative:
                obj.scale = mathutils.Vector([obj.scale[i] * scale[i] for i in range(3)])
            else:
                obj.scale = mathutils.Vector(scale)
        
        return {
            "name": obj.name,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale)
        }
    
    def duplicate_object(self, name, linked=False):
        """Duplicate an object"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")
        
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        bpy.ops.object.duplicate(linked=linked)
        new_obj = bpy.context.active_object
        
        return {"name": new_obj.name, "original": name}
    
    def delete_object(self, name):
        """Delete an object"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object not found: {name}")
        
        bpy.data.objects.remove(obj, do_unlink=True)
        return {"deleted": name}
    
    def rename_object(self, old_name, new_name):
        """Rename an object"""
        obj = bpy.data.objects.get(old_name)
        if not obj:
            raise ValueError(f"Object not found: {old_name}")
        
        obj.name = new_name
        return {"old_name": old_name, "new_name": obj.name}
    
    def parent_object(self, child_name, parent_name, keep_transform=True):
        """Parent one object to another"""
        child = bpy.data.objects.get(child_name)
        parent = bpy.data.objects.get(parent_name)
        
        if not child or not parent:
            raise ValueError("Child or parent object not found")
        
        child.parent = parent
        if keep_transform:
            child.matrix_parent_inverse = parent.matrix_world.inverted()
        
        return {"child": child_name, "parent": parent_name}
    
    def join_objects(self, object_names):
        """Join multiple objects into one"""
        objects = [bpy.data.objects.get(name) for name in object_names]
        if any(obj is None for obj in objects):
            raise ValueError("One or more objects not found")
        
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        
        bpy.ops.object.join()
        result_obj = bpy.context.active_object
        
        return {"name": result_obj.name, "joined_count": len(object_names)}

    # ===== MESH EDITING =====
    
    def enter_edit_mode(self, object_name):
        """Enter edit mode for an object"""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")
        
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        
        return {"object": object_name, "mode": "EDIT"}
    
    def exit_edit_mode(self):
        """Exit edit mode and return to object mode"""
        bpy.ops.object.mode_set(mode='OBJECT')
        return {"mode": "OBJECT"}
    
    def select_all(self, action='TOGGLE'):
        """Select all elements. Actions: TOGGLE, SELECT, DESELECT, INVERT"""
        if bpy.context.mode == 'EDIT_MESH':
            bpy.ops.mesh.select_all(action=action)
            return {"action": action, "context": "EDIT_MESH"}
        else:
            bpy.ops.object.select_all(action=action)
            return {"action": action, "context": "OBJECT"}
    
    def extrude_mesh(self, object_name, distance=1.0, direction=[0, 0, 1]):
        """Extrude selected faces/edges/vertices"""
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != 'MESH':
            raise ValueError(f"Mesh object not found: {object_name}")
        
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        if bpy.context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')
        
        bpy.ops.mesh.extrude_region_move(
            TRANSFORM_OT_translate={
                "value": tuple(d * distance for d in direction)
            }
        )
        
        bpy.ops.object.mode_set(mode='OBJECT')
        return {"object": object_name, "extruded": True}
    
    def subdivide_mesh(self, object_name, cuts=1):
        """Subdivide selected faces"""
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != 'MESH':
            raise ValueError(f"Mesh object not found: {object_name}")
        
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        if bpy.context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
        
        bpy.ops.mesh.subdivide(number_cuts=cuts)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        return {"object": object_name, "cuts": cuts}
    
    def bevel_mesh(self, object_name, offset=0.1, segments=1):
        """Bevel selected edges"""
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != 'MESH':
            raise ValueError(f"Mesh object not found: {object_name}")
        
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        if bpy.context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
        
        bpy.ops.mesh.bevel(offset=offset, segments=segments)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        return {"object": object_name, "bevel_offset": offset}
    
    def inset_faces(self, object_name, thickness=0.1):
        """Inset selected faces"""
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != 'MESH':
            raise ValueError(f"Mesh object not found: {object_name}")
        
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        if bpy.context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
        
        bpy.ops.mesh.inset(thickness=thickness)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        return {"object": object_name, "thickness": thickness}
    
    def loop_cut(self, object_name, number_cuts=1):
        """Add loop cuts to a mesh"""
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != 'MESH':
            raise ValueError(f"Mesh object not found: {object_name}")
        
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        if bpy.context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')
        
        # Note: loopcut_slide requires interactive mode, use subdivide for programmatic approach
        return {"message": "Loop cuts require interactive mode. Use subdivide_mesh or execute_code for programmatic mesh editing."}
    
    def merge_vertices(self, object_name, merge_type='CENTER'):
        """Merge selected vertices. Types: CENTER, CURSOR, COLLAPSE, FIRST, LAST"""
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != 'MESH':
            raise ValueError(f"Mesh object not found: {object_name}")
        
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        if bpy.context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')
        
        bpy.ops.mesh.merge(type=merge_type)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        return {"object": object_name, "merge_type": merge_type}

    # ===== MODIFIERS =====
    
    def add_modifier(self, object_name, modifier_type, **kwargs):
        """
        Add a modifier to an object.
        Common types: SUBSURF, MIRROR, ARRAY, BEVEL, BOOLEAN, SOLIDIFY, DISPLACE, SHRINKWRAP
        Example: add_modifier(object_name="Cube", modifier_type="SUBSURF", levels=2)
        """
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")
        
        mod = obj.modifiers.new(name=modifier_type, type=modifier_type)
        
        for key, value in kwargs.items():
            if hasattr(mod, key):
                setattr(mod, key, value)
        
        return {"object": object_name, "modifier": mod.name, "type": modifier_type}
    
    def remove_modifier(self, object_name, modifier_name):
        """Remove a modifier from an object"""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")
        
        mod = obj.modifiers.get(modifier_name)
        if not mod:
            raise ValueError(f"Modifier not found: {modifier_name}")
        
        obj.modifiers.remove(mod)
        return {"object": object_name, "removed": modifier_name}
    
    def apply_modifier(self, object_name, modifier_name):
        """Apply a modifier to an object"""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")
        
        mod = obj.modifiers.get(modifier_name)
        if not mod:
            raise ValueError(f"Modifier not found: {modifier_name}")
        
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        bpy.ops.object.modifier_apply(modifier=modifier_name)
        return {"object": object_name, "applied": modifier_name}
    
    def list_modifiers(self, object_name):
        """List all modifiers on an object"""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")
        
        modifiers = []
        for mod in obj.modifiers:
            mod_info = {
                "name": mod.name,
                "type": mod.type,
                "show_viewport": mod.show_viewport,
                "show_render": mod.show_render,
            }
            modifiers.append(mod_info)
        
        return {"object": object_name, "modifiers": modifiers}

    # ===== MATERIALS & SHADING =====
    
    def create_material(self, name, color=[0.8, 0.8, 0.8, 1.0], metallic=0.0, roughness=0.5):
        """Create a new material with basic properties"""
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        
        nodes = mat.node_tree.nodes
        principled = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled = node
                break
        
        if principled:
            principled.inputs['Base Color'].default_value = color
            principled.inputs['Metallic'].default_value = metallic
            principled.inputs['Roughness'].default_value = roughness
        
        return {"material": mat.name, "color": color}
    
    def assign_material(self, object_name, material_name):
        """Assign a material to an object"""
        obj = bpy.data.objects.get(object_name)
        mat = bpy.data.materials.get(material_name)
        
        if not obj:
            raise ValueError(f"Object not found: {object_name}")
        if not mat:
            raise ValueError(f"Material not found: {material_name}")
        
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
        
        return {"object": object_name, "material": material_name}
    
    def set_material_color(self, material_name, color):
        """Set the base color of a material"""
        mat = bpy.data.materials.get(material_name)
        if not mat:
            raise ValueError(f"Material not found: {material_name}")
        
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    node.inputs['Base Color'].default_value = color
                    break
        
        return {"material": material_name, "color": color}
    
    def set_smooth_shading(self, object_name, smooth=True):
        """Set smooth or flat shading for an object"""
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != 'MESH':
            raise ValueError(f"Mesh object not found: {object_name}")
        
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        if smooth:
            bpy.ops.object.shade_smooth()
        else:
            bpy.ops.object.shade_flat()
        
        return {"object": object_name, "smooth": smooth}

    # ===== ANIMATION =====
    
    def set_keyframe(self, object_name, data_path, frame=None, value=None):
        """
        Set a keyframe for an object property.
        data_path examples: 'location', 'rotation_euler', 'scale', 'hide_viewport'
        """
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object not found: {object_name}")
        
        if frame is not None:
            bpy.context.scene.frame_set(frame)
        
        if value is not None:
            if hasattr(obj, data_path):
                setattr(obj, data_path, value)
        
        obj.keyframe_insert(data_path=data_path)
        
        return {
            "object": object_name,
            "data_path": data_path,
            "frame": bpy.context.scene.frame_current
        }
    
    def set_frame(self, frame):
        """Set the current frame"""
        bpy.context.scene.frame_set(frame)
        return {"frame": frame}
    
    def get_frame_range(self):
        """Get the frame range of the scene"""
        return {
            "start": bpy.context.scene.frame_start,
            "end": bpy.context.scene.frame_end,
            "current": bpy.context.scene.frame_current,
        }

    # ===== RENDERING =====
    
    def set_render_settings(self, engine='CYCLES', samples=128, resolution_x=1920, resolution_y=1080):
        """
        Set render settings.
        engine: CYCLES, BLENDER_EEVEE, BLENDER_WORKBENCH
        """
        scene = bpy.context.scene
        scene.render.engine = engine
        
        if engine == 'CYCLES':
            scene.cycles.samples = samples
        elif engine == 'BLENDER_EEVEE':
            scene.eevee.taa_render_samples = samples
        
        scene.render.resolution_x = resolution_x
        scene.render.resolution_y = resolution_y
        
        return {
            "engine": engine,
            "samples": samples,
            "resolution": [resolution_x, resolution_y]
        }
    
    def render_image(self, filepath=None):
        """Render the current frame"""
        if filepath:
            bpy.context.scene.render.filepath = filepath
        
        bpy.ops.render.render(write_still=True)
        
        return {
            "rendered": True,
            "filepath": bpy.context.scene.render.filepath
        }
    
    def render_animation(self, filepath=None):
        """Render the animation"""
        if filepath:
            bpy.context.scene.render.filepath = filepath
        
        bpy.ops.render.render(animation=True)
        
        return {
            "rendered": True,
            "filepath": bpy.context.scene.render.filepath
        }

    # ===== COLLECTIONS =====
    
    def create_collection(self, name):
        """Create a new collection"""
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
        return {"collection": collection.name}
    
    def link_to_collection(self, object_name, collection_name):
        """Link an object to a collection"""
        obj = bpy.data.objects.get(object_name)
        collection = bpy.data.collections.get(collection_name)
        
        if not obj:
            raise ValueError(f"Object not found: {object_name}")
        if not collection:
            raise ValueError(f"Collection not found: {collection_name}")
        
        collection.objects.link(obj)
        return {"object": object_name, "collection": collection_name}

    # ===== POLYHAVEN INTEGRATION (COMPLETE ORIGINAL) =====
    
    def get_polyhaven_categories(self, asset_type):
        """Get categories for a specific asset type from Polyhaven"""
        try:
            if asset_type not in ["hdris", "textures", "models", "all"]:
                return {"error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"}
                
            response = requests.get(f"https://api.polyhaven.com/categories/{asset_type}")
            if response.status_code == 200:
                return {"categories": response.json()}
            else:
                return {"error": f"API request failed with status code {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def search_polyhaven_assets(self, asset_type=None, categories=None):
        """Search for assets from Polyhaven with optional filtering"""
        try:
            url = "https://api.polyhaven.com/assets"
            params = {}
            
            if asset_type and asset_type != "all":
                if asset_type not in ["hdris", "textures", "models"]:
                    return {"error": f"Invalid asset type: {asset_type}. Must be one of: hdris, textures, models, all"}
                params["type"] = asset_type
                
            if categories:
                params["categories"] = categories
                
            response = requests.get(url, params=params)
            if response.status_code == 200:
                assets = response.json()
                limited_assets = {}
                for i, (key, value) in enumerate(assets.items()):
                    if i >= 20:
                        break
                    limited_assets[key] = value
                
                return {"assets": limited_assets, "total_count": len(assets), "returned_count": len(limited_assets)}
            else:
                return {"error": f"API request failed with status code {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def download_polyhaven_asset(self, asset_id, asset_type, resolution="1k", file_format=None):
        try:
            files_response = requests.get(f"https://api.polyhaven.com/files/{asset_id}")
            if files_response.status_code != 200:
                return {"error": f"Failed to get asset files: {files_response.status_code}"}
            
            files_data = files_response.json()
            
            if asset_type == "hdris":
                if not file_format:
                    file_format = "hdr"
                
                if "hdri" in files_data and resolution in files_data["hdri"] and file_format in files_data["hdri"][resolution]:
                    file_info = files_data["hdri"][resolution][file_format]
                    file_url = file_info["url"]
                    
                    with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                        response = requests.get(file_url)
                        if response.status_code != 200:
                            return {"error": f"Failed to download HDRI: {response.status_code}"}
                        
                        tmp_file.write(response.content)
                        tmp_path = tmp_file.name
                    
                    try:
                        if not bpy.data.worlds:
                            bpy.data.worlds.new("World")
                        
                        world = bpy.data.worlds[0]
                        world.use_nodes = True
                        node_tree = world.node_tree
                        
                        for node in node_tree.nodes:
                            node_tree.nodes.remove(node)
                        
                        tex_coord = node_tree.nodes.new(type='ShaderNodeTexCoord')
                        tex_coord.location = (-800, 0)
                        
                        mapping = node_tree.nodes.new(type='ShaderNodeMapping')
                        mapping.location = (-600, 0)
                        
                        env_tex = node_tree.nodes.new(type='ShaderNodeTexEnvironment')
                        env_tex.location = (-400, 0)
                        env_tex.image = bpy.data.images.load(tmp_path)
                        
                        if file_format.lower() == 'exr':
                            try:
                                env_tex.image.colorspace_settings.name = 'Linear'
                            except:
                                env_tex.image.colorspace_settings.name = 'Non-Color'
                        else:
                            for color_space in ['Linear', 'Linear Rec.709', 'Non-Color']:
                                try:
                                    env_tex.image.colorspace_settings.name = color_space
                                    break
                                except:
                                    continue
                        
                        background = node_tree.nodes.new(type='ShaderNodeBackground')
                        background.location = (-200, 0)
                        
                        output = node_tree.nodes.new(type='ShaderNodeOutputWorld')
                        output.location = (0, 0)
                        
                        node_tree.links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
                        node_tree.links.new(mapping.outputs['Vector'], env_tex.inputs['Vector'])
                        node_tree.links.new(env_tex.outputs['Color'], background.inputs['Color'])
                        node_tree.links.new(background.outputs['Background'], output.inputs['Surface'])
                        
                        bpy.context.scene.world = world
                        
                        try:
                            tempfile._cleanup()
                        except:
                            pass
                        
                        return {
                            "success": True, 
                            "message": f"HDRI {asset_id} imported successfully",
                            "image_name": env_tex.image.name
                        }
                    except Exception as e:
                        return {"error": f"Failed to set up HDRI in Blender: {str(e)}"}
                else:
                    return {"error": f"Requested resolution or format not available for this HDRI"}
                    
            elif asset_type == "textures":
                if not file_format:
                    file_format = "jpg"
                
                downloaded_maps = {}
                
                try:
                    for map_type in files_data:
                        if map_type not in ["blend", "gltf"]:
                            if resolution in files_data[map_type] and file_format in files_data[map_type][resolution]:
                                file_info = files_data[map_type][resolution][file_format]
                                file_url = file_info["url"]
                                
                                with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                                    response = requests.get(file_url)
                                    if response.status_code == 200:
                                        tmp_file.write(response.content)
                                        tmp_path = tmp_file.name
                                        
                                        image = bpy.data.images.load(tmp_path)
                                        image.name = f"{asset_id}_{map_type}.{file_format}"
                                        image.pack()
                                        
                                        if map_type in ['color', 'diffuse', 'albedo']:
                                            try:
                                                image.colorspace_settings.name = 'sRGB'
                                            except:
                                                pass
                                        else:
                                            try:
                                                image.colorspace_settings.name = 'Non-Color'
                                            except:
                                                pass
                                        
                                        downloaded_maps[map_type] = image
                                        
                                        try:
                                            os.unlink(tmp_path)
                                        except:
                                            pass
                
                    if not downloaded_maps:
                        return {"error": f"No texture maps found for the requested resolution and format"}
                    
                    mat = bpy.data.materials.new(name=asset_id)
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links
                    
                    for node in nodes:
                        nodes.remove(node)
                    
                    output = nodes.new(type='ShaderNodeOutputMaterial')
                    output.location = (300, 0)
                    
                    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
                    principled.location = (0, 0)
                    links.new(principled.outputs[0], output.inputs[0])
                    
                    tex_coord = nodes.new(type='ShaderNodeTexCoord')
                    tex_coord.location = (-800, 0)
                    
                    mapping = nodes.new(type='ShaderNodeMapping')
                    mapping.location = (-600, 0)
                    mapping.vector_type = 'TEXTURE'
                    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
                    
                    x_pos = -400
                    y_pos = 300
                    
                    for map_type, image in downloaded_maps.items():
                        tex_node = nodes.new(type='ShaderNodeTexImage')
                        tex_node.location = (x_pos, y_pos)
                        tex_node.image = image
                        
                        if map_type.lower() in ['color', 'diffuse', 'albedo']:
                            try:
                                tex_node.image.colorspace_settings.name = 'sRGB'
                            except:
                                pass
                        else:
                            try:
                                tex_node.image.colorspace_settings.name = 'Non-Color'
                            except:
                                pass
                        
                        links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])
                        
                        if map_type.lower() in ['color', 'diffuse', 'albedo']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
                        elif map_type.lower() in ['roughness', 'rough']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
                        elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                            links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
                        elif map_type.lower() in ['normal', 'nor']:
                            normal_map = nodes.new(type='ShaderNodeNormalMap')
                            normal_map.location = (x_pos + 200, y_pos)
                            links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                            links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
                        elif map_type in ['displacement', 'disp', 'height']:
                            disp_node = nodes.new(type='ShaderNodeDisplacement')
                            disp_node.location = (x_pos + 200, y_pos - 200)
                            links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                            links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                        
                        y_pos -= 250
                    
                    return {
                        "success": True, 
                        "message": f"Texture {asset_id} imported as material",
                        "material": mat.name,
                        "maps": list(downloaded_maps.keys())
                    }
                
                except Exception as e:
                    return {"error": f"Failed to process textures: {str(e)}"}
                
            elif asset_type == "models":
                if not file_format:
                    file_format = "gltf"
                
                if file_format in files_data and resolution in files_data[file_format]:
                    file_info = files_data[file_format][resolution][file_format]
                    file_url = file_info["url"]
                    
                    temp_dir = tempfile.mkdtemp()
                    main_file_path = ""
                    
                    try:
                        main_file_name = file_url.split("/")[-1]
                        main_file_path = os.path.join(temp_dir, main_file_name)
                        
                        response = requests.get(file_url)
                        if response.status_code != 200:
                            return {"error": f"Failed to download model: {response.status_code}"}
                        
                        with open(main_file_path, "wb") as f:
                            f.write(response.content)
                        
                        if "include" in file_info and file_info["include"]:
                            for include_path, include_info in file_info["include"].items():
                                include_url = include_info["url"]
                                include_file_path = os.path.join(temp_dir, include_path)
                                os.makedirs(os.path.dirname(include_file_path), exist_ok=True)
                                
                                include_response = requests.get(include_url)
                                if include_response.status_code == 200:
                                    with open(include_file_path, "wb") as f:
                                        f.write(include_response.content)
                                else:
                                    print(f"Failed to download included file: {include_path}")
                        
                        if file_format == "gltf" or file_format == "glb":
                            bpy.ops.import_scene.gltf(filepath=main_file_path)
                        elif file_format == "fbx":
                            bpy.ops.import_scene.fbx(filepath=main_file_path)
                        elif file_format == "obj":
                            bpy.ops.import_scene.obj(filepath=main_file_path)
                        elif file_format == "blend":
                            with bpy.data.libraries.load(main_file_path, link=False) as (data_from, data_to):
                                data_to.objects = data_from.objects
                            
                            for obj in data_to.objects:
                                if obj is not None:
                                    bpy.context.collection.objects.link(obj)
                        else:
                            return {"error": f"Unsupported model format: {file_format}"}
                        
                        imported_objects = [obj.name for obj in bpy.context.selected_objects]
                        
                        return {
                            "success": True, 
                            "message": f"Model {asset_id} imported successfully",
                            "imported_objects": imported_objects
                        }
                    except Exception as e:
                        return {"error": f"Failed to import model: {str(e)}"}
                    finally:
                        try:
                            shutil.rmtree(temp_dir)
                        except:
                            print(f"Failed to clean up temporary directory: {temp_dir}")
                else:
                    return {"error": f"Requested format or resolution not available for this model"}
                
            else:
                return {"error": f"Unsupported asset type: {asset_type}"}
                
        except Exception as e:
            return {"error": f"Failed to download asset: {str(e)}"}

    def set_texture(self, object_name, texture_id):
        """Apply a previously downloaded Polyhaven texture to an object by creating a new material"""
        try:
            obj = bpy.data.objects.get(object_name)
            if not obj:
                return {"error": f"Object not found: {object_name}"}
            
            if not hasattr(obj, 'data') or not hasattr(obj.data, 'materials'):
                return {"error": f"Object {object_name} cannot accept materials"}
            
            texture_images = {}
            for img in bpy.data.images:
                if img.name.startswith(texture_id + "_"):
                    map_type = img.name.split('_')[-1].split('.')[0]
                    img.reload()
                    
                    if map_type.lower() in ['color', 'diffuse', 'albedo']:
                        try:
                            img.colorspace_settings.name = 'sRGB'
                        except:
                            pass
                    else:
                        try:
                            img.colorspace_settings.name = 'Non-Color'
                        except:
                            pass
                    
                    if not img.packed_file:
                        img.pack()
                    
                    texture_images[map_type] = img

            if not texture_images:
                return {"error": f"No texture images found for: {texture_id}. Please download the texture first."}
            
            new_mat_name = f"{texture_id}_material_{object_name}"
            existing_mat = bpy.data.materials.get(new_mat_name)
            if existing_mat:
                bpy.data.materials.remove(existing_mat)
            
            new_mat = bpy.data.materials.new(name=new_mat_name)
            new_mat.use_nodes = True
            
            nodes = new_mat.node_tree.nodes
            links = new_mat.node_tree.links
            nodes.clear()
            
            output = nodes.new(type='ShaderNodeOutputMaterial')
            output.location = (600, 0)
            
            principled = nodes.new(type='ShaderNodeBsdfPrincipled')
            principled.location = (300, 0)
            links.new(principled.outputs[0], output.inputs[0])
            
            tex_coord = nodes.new(type='ShaderNodeTexCoord')
            tex_coord.location = (-800, 0)
            
            mapping = nodes.new(type='ShaderNodeMapping')
            mapping.location = (-600, 0)
            mapping.vector_type = 'TEXTURE'
            links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
            
            x_pos = -400
            y_pos = 300
            
            texture_nodes = {}
            for map_type, image in texture_images.items():
                tex_node = nodes.new(type='ShaderNodeTexImage')
                tex_node.location = (x_pos, y_pos)
                tex_node.image = image
                
                if map_type.lower() in ['color', 'diffuse', 'albedo']:
                    try:
                        tex_node.image.colorspace_settings.name = 'sRGB'
                    except:
                        pass
                else:
                    try:
                        tex_node.image.colorspace_settings.name = 'Non-Color'
                    except:
                        pass
                
                links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])
                texture_nodes[map_type] = tex_node
                y_pos -= 250
            
            # Connect texture nodes
            for map_name in ['color', 'diffuse', 'albedo']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Base Color'])
                    break
            
            for map_name in ['roughness', 'rough']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Roughness'])
                    break
            
            for map_name in ['metallic', 'metalness', 'metal']:
                if map_name in texture_nodes:
                    links.new(texture_nodes[map_name].outputs['Color'], principled.inputs['Metallic'])
                    break
            
            for map_name in ['gl', 'dx', 'nor']:
                if map_name in texture_nodes:
                    normal_map_node = nodes.new(type='ShaderNodeNormalMap')
                    normal_map_node.location = (100, 100)
                    links.new(texture_nodes[map_name].outputs['Color'], normal_map_node.inputs['Color'])
                    links.new(normal_map_node.outputs['Normal'], principled.inputs['Normal'])
                    break
            
            for map_name in ['displacement', 'disp', 'height']:
                if map_name in texture_nodes:
                    disp_node = nodes.new(type='ShaderNodeDisplacement')
                    disp_node.location = (300, -200)
                    disp_node.inputs['Scale'].default_value = 0.1
                    links.new(texture_nodes[map_name].outputs['Color'], disp_node.inputs['Height'])
                    links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
                    break
            
            if 'arm' in texture_nodes:
                separate_rgb = nodes.new(type='ShaderNodeSeparateRGB')
                separate_rgb.location = (-200, -100)
                links.new(texture_nodes['arm'].outputs['Color'], separate_rgb.inputs['Image'])
                
                if not any(map_name in texture_nodes for map_name in ['roughness', 'rough']):
                    links.new(separate_rgb.outputs['G'], principled.inputs['Roughness'])
                
                if not any(map_name in texture_nodes for map_name in ['metallic', 'metalness', 'metal']):
                    links.new(separate_rgb.outputs['B'], principled.inputs['Metallic'])
                
                base_color_node = None
                for map_name in ['color', 'diffuse', 'albedo']:
                    if map_name in texture_nodes:
                        base_color_node = texture_nodes[map_name]
                        break
                
                if base_color_node:
                    mix_node = nodes.new(type='ShaderNodeMixRGB')
                    mix_node.location = (100, 200)
                    mix_node.blend_type = 'MULTIPLY'
                    mix_node.inputs['Fac'].default_value = 0.8
                    
                    for link in base_color_node.outputs['Color'].links:
                        if link.to_socket == principled.inputs['Base Color']:
                            links.remove(link)
                    
                    links.new(base_color_node.outputs['Color'], mix_node.inputs[1])
                    links.new(texture_nodes['ao'].outputs['Color'], mix_node.inputs[2])
                    links.new(mix_node.outputs['Color'], principled.inputs['Base Color'])
            
            # Clear existing materials and assign new one
            while len(obj.data.materials) > 0:
                obj.data.materials.pop(index=0)
            
            obj.data.materials.append(new_mat)
            
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.context.view_layer.update()
            
            texture_maps = list(texture_images.keys())
            
            material_info = {
                "name": new_mat.name,
                "has_nodes": new_mat.use_nodes,
                "node_count": len(new_mat.node_tree.nodes),
                "texture_nodes": []
            }
            
            for node in new_mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    connections = []
                    for output in node.outputs:
                        for link in output.links:
                            connections.append(f"{output.name} → {link.to_node.name}.{link.to_socket.name}")
                    
                    material_info["texture_nodes"].append({
                        "name": node.name,
                        "image": node.image.name,
                        "colorspace": node.image.colorspace_settings.name,
                        "connections": connections
                    })
            
            return {
                "success": True,
                "message": f"Created new material and applied texture {texture_id} to {object_name}",
                "material": new_mat.name,
                "maps": texture_maps,
                "material_info": material_info
            }
            
        except Exception as e:
            print(f"Error in set_texture: {str(e)}")
            traceback.print_exc()
            return {"error": f"Failed to apply texture: {str(e)}"}

    def get_polyhaven_status(self):
        """Get the current status of PolyHaven integration"""
        enabled = bpy.context.scene.blendermcp_use_polyhaven
        if enabled:
            return {"enabled": True, "message": "PolyHaven integration is enabled and ready to use."}
        else:
            return {
                "enabled": False, 
                "message": """PolyHaven integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                            2. Check the 'Use assets from Poly Haven' checkbox
                            3. Restart the connection to Claude"""
        }

    # ===== HYPER3D INTEGRATION (COMPLETE ORIGINAL) =====
    
    def get_hyper3d_status(self):
        """Get the current status of Hyper3D Rodin integration"""
        enabled = bpy.context.scene.blendermcp_use_hyper3d
        if enabled:
            if not bpy.context.scene.blendermcp_hyper3d_api_key:
                return {
                    "enabled": False, 
                    "message": """Hyper3D Rodin integration is currently enabled, but API key is not given. To enable it:
                                1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                                2. Keep the 'Use Hyper3D Rodin 3D model generation' checkbox checked
                                3. Choose the right plaform and fill in the API Key
                                4. Restart the connection to Claude"""
                }
            mode = bpy.context.scene.blendermcp_hyper3d_mode
            message = f"Hyper3D Rodin integration is enabled and ready to use. Mode: {mode}. " + \
                f"Key type: {'private' if bpy.context.scene.blendermcp_hyper3d_api_key != RODIN_FREE_TRIAL_KEY else 'free_trial'}"
            return {
                "enabled": True,
                "message": message
            }
        else:
            return {
                "enabled": False, 
                "message": """Hyper3D Rodin integration is currently disabled. To enable it:
                            1. In the 3D Viewport, find the BlenderMCP panel in the sidebar (press N if hidden)
                            2. Check the 'Use Hyper3D Rodin 3D model generation' checkbox
                            3. Restart the connection to Claude"""
            }

    def create_rodin_job(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.create_rodin_job_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.create_rodin_job_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def create_rodin_job_main_site(
            self,
            text_prompt: str=None,
            images: list=None,
            bbox_condition=None
        ):
        try:
            if images is None:
                images = []
            files = [
                *[("images", (f"{i:04d}{img_suffix}", img)) for i, (img_suffix, img) in enumerate(images)],
                ("tier", (None, "Sketch")),
                ("mesh_mode", (None, "Raw")),
            ]
            if text_prompt:
                files.append(("prompt", (None, text_prompt)))
            if bbox_condition:
                files.append(("bbox_condition", (None, json.dumps(bbox_condition))))
            response = requests.post(
                "https://hyperhuman.deemos.com/api/v2/rodin",
                headers={
                    "Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}",
                },
                files=files
            )
            data = response.json()
            return data
        except Exception as e:
            return {"error": str(e)}
    
    def create_rodin_job_fal_ai(
            self,
            text_prompt: str=None,
            images: list=None,
            bbox_condition=None
        ):
        try:
            req_data = {
                "tier": "Sketch",
            }
            if images:
                req_data["input_image_urls"] = images
            if text_prompt:
                req_data["prompt"] = text_prompt
            if bbox_condition:
                req_data["bbox_condition"] = bbox_condition
            response = requests.post(
                "https://queue.fal.run/fal-ai/hyper3d/rodin",
                headers={
                    "Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}",
                    "Content-Type": "application/json",
                },
                json=req_data
            )
            data = response.json()
            return data
        except Exception as e:
            return {"error": str(e)}

    def poll_rodin_job_status(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.poll_rodin_job_status_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.poll_rodin_job_status_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def poll_rodin_job_status_main_site(self, subscription_key: str):
        """Call the job status API to get the job status"""
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/status",
            headers={
                "Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
            json={
                "subscription_key": subscription_key,
            },
        )
        data = response.json()
        return {
            "status_list": [i["status"] for i in data["jobs"]]
        }
    
    def poll_rodin_job_status_fal_ai(self, request_id: str):
        """Call the job status API to get the job status"""
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}/status",
            headers={
                "Authorization": f"KEY {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
        )
        data = response.json()
        return data

    @staticmethod
    def _clean_imported_glb(filepath, mesh_name=None):
        existing_objects = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=filepath)
        bpy.context.view_layer.update()
        imported_objects = list(set(bpy.data.objects) - existing_objects)
        
        if not imported_objects:
            print("Error: No objects were imported.")
            return
        
        mesh_obj = None
        
        if len(imported_objects) == 1 and imported_objects[0].type == 'MESH':
            mesh_obj = imported_objects[0]
            print("Single mesh imported, no cleanup needed.")
        else:
            if len(imported_objects) == 2:
                empty_objs = [i for i in imported_objects if i.type == "EMPTY"]
                if len(empty_objs) != 1:
                    print("Error: Expected an empty node with one mesh child or a single mesh object.")
                    return
                parent_obj = empty_objs.pop()
                if len(parent_obj.children) == 1:
                    potential_mesh = parent_obj.children[0]
                    if potential_mesh.type == 'MESH':
                        print("GLB structure confirmed: Empty node with one mesh child.")
                        potential_mesh.parent = None
                        bpy.data.objects.remove(parent_obj)
                        print("Removed empty node, keeping only the mesh.")
                        mesh_obj = potential_mesh
                    else:
                        print("Error: Child is not a mesh object.")
                        return
                else:
                    print("Error: Expected an empty node with one mesh child or a single mesh object.")
                    return
            else:
                print("Error: Expected an empty node with one mesh child or a single mesh object.")
                return
        
        try:
            if mesh_obj and mesh_obj.name is not None and mesh_name:
                mesh_obj.name = mesh_name
                if mesh_obj.data.name is not None:
                    mesh_obj.data.name = mesh_name
                print(f"Mesh renamed to: {mesh_name}")
        except Exception as e:
            print("Having issue with renaming, give up renaming.")

        return mesh_obj

    def import_generated_asset(self, *args, **kwargs):
        match bpy.context.scene.blendermcp_hyper3d_mode:
            case "MAIN_SITE":
                return self.import_generated_asset_main_site(*args, **kwargs)
            case "FAL_AI":
                return self.import_generated_asset_fal_ai(*args, **kwargs)
            case _:
                return f"Error: Unknown Hyper3D Rodin mode!"

    def import_generated_asset_main_site(self, task_uuid: str, name: str):
        """Fetch the generated asset, import into blender"""
        response = requests.post(
            "https://hyperhuman.deemos.com/api/v2/download",
            headers={
                "Authorization": f"Bearer {bpy.context.scene.blendermcp_hyper3d_api_key}",
            },
            json={
                'task_uuid': task_uuid
            }
        )
        data_ = response.json()
        temp_file = None
        for i in data_["list"]:
            if i["name"].endswith(".glb"):
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    prefix=task_uuid,
                    suffix=".glb",
                )
    
                try:
                    response = requests.get(i["url"], stream=True)
                    response.raise_for_status()
                    
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                        
                    temp_file.close()
                    
                except Exception as e:
                    temp_file.close()
                    os.unlink(temp_file.name)
                    return {"succeed": False, "error": str(e)}
                
                break
        else:
            return {"succeed": False, "error": "Generation failed. Please first make sure that all jobs of the task are done and then try again later."}

        try:
            obj = self._clean_imported_glb(
                filepath=temp_file.name,
                mesh_name=name
            )
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box
            
            return {
                "succeed": True, **result
            }
        except Exception as e:
            return {"succeed": False, "error": str(e)}
    
    def import_generated_asset_fal_ai(self, request_id: str, name: str):
        """Fetch the generated asset, import into blender"""
        response = requests.get(
            f"https://queue.fal.run/fal-ai/hyper3d/requests/{request_id}",
            headers={
                "Authorization": f"Key {bpy.context.scene.blendermcp_hyper3d_api_key}",
            }
        )
        data_ = response.json()
        temp_file = None
        
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            prefix=request_id,
            suffix=".glb",
        )

        try:
            response = requests.get(data_["model_mesh"]["url"], stream=True)
            response.raise_for_status()
            
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
                
            temp_file.close()
            
        except Exception as e:
            temp_file.close()
            os.unlink(temp_file.name)
            return {"succeed": False, "error": str(e)}

        try:
            obj = self._clean_imported_glb(
                filepath=temp_file.name,
                mesh_name=name
            )
            result = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location.x, obj.location.y, obj.location.z],
                "rotation": [obj.rotation_euler.x, obj.rotation_euler.y, obj.rotation_euler.z],
                "scale": [obj.scale.x, obj.scale.y, obj.scale.z],
            }

            if obj.type == "MESH":
                bounding_box = self._get_aabb(obj)
                result["world_bounding_box"] = bounding_box
            
            return {
                "succeed": True, **result
            }
        except Exception as e:
            return {"succeed": False, "error": str(e)}

# ===== BLENDER UI PANEL =====

class BLENDERMCP_PT_Panel(bpy.types.Panel):
    bl_label = "Blender MCP Enhanced"
    bl_idname = "BLENDERMCP_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BlenderMCP'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.prop(scene, "blendermcp_port")
        layout.prop(scene, "blendermcp_use_polyhaven", text="Use assets from Poly Haven")

        layout.prop(scene, "blendermcp_use_hyper3d", text="Use Hyper3D Rodin 3D model generation")
        if scene.blendermcp_use_hyper3d:
            layout.prop(scene, "blendermcp_hyper3d_mode", text="Rodin Mode")
            layout.prop(scene, "blendermcp_hyper3d_api_key", text="API Key")
            layout.operator("blendermcp.set_hyper3d_free_trial_api_key", text="Set Free Trial API Key")
        
        if not scene.blendermcp_server_running:
            layout.operator("blendermcp.start_server", text="Connect to MCP server")
        else:
            layout.operator("blendermcp.stop_server", text="Disconnect from MCP server")
            layout.label(text=f"Running on port {scene.blendermcp_port}")

# ===== OPERATORS =====

class BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey(bpy.types.Operator):
    bl_idname = "blendermcp.set_hyper3d_free_trial_api_key"
    bl_label = "Set Free Trial API Key"
    
    def execute(self, context):
        context.scene.blendermcp_hyper3d_api_key = RODIN_FREE_TRIAL_KEY
        context.scene.blendermcp_hyper3d_mode = 'MAIN_SITE'
        self.report({'INFO'}, "API Key set successfully!")
        return {'FINISHED'}

class BLENDERMCP_OT_StartServer(bpy.types.Operator):
    bl_idname = "blendermcp.start_server"
    bl_label = "Connect to Claude"
    bl_description = "Start the Enhanced BlenderMCP server to connect with Claude"
    
    def execute(self, context):
        scene = context.scene
        
        if not hasattr(bpy.types, "blendermcp_server") or not bpy.types.blendermcp_server:
            bpy.types.blendermcp_server = BlenderMCPServer(port=scene.blendermcp_port)
        
        bpy.types.blendermcp_server.start()
        scene.blendermcp_server_running = True
        
        return {'FINISHED'}

class BLENDERMCP_OT_StopServer(bpy.types.Operator):
    bl_idname = "blendermcp.stop_server"
    bl_label = "Stop the connection to Claude"
    bl_description = "Stop the connection to Claude"
    
    def execute(self, context):
        scene = context.scene
        
        if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
            bpy.types.blendermcp_server.stop()
            del bpy.types.blendermcp_server
        
        scene.blendermcp_server_running = False
        
        return {'FINISHED'}

# ===== REGISTRATION =====

def register():
    bpy.types.Scene.blendermcp_port = IntProperty(
        name="Port",
        description="Port for the BlenderMCP server",
        default=9876,
        min=1024,
        max=65535
    )
    
    bpy.types.Scene.blendermcp_server_running = BoolProperty(
        name="Server Running",
        default=False
    )
    
    bpy.types.Scene.blendermcp_use_polyhaven = BoolProperty(
        name="Use Poly Haven",
        description="Enable Poly Haven asset integration",
        default=False
    )

    bpy.types.Scene.blendermcp_use_hyper3d = BoolProperty(
        name="Use Hyper3D Rodin",
        description="Enable Hyper3D Rodin generation integration",
        default=False
    )

    bpy.types.Scene.blendermcp_hyper3d_mode = EnumProperty(
        name="Rodin Mode",
        description="Choose the platform used to call Rodin APIs",
        items=[
            ("MAIN_SITE", "hyper3d.ai", "hyper3d.ai"),
            ("FAL_AI", "fal.ai", "fal.ai"),
        ],
        default="MAIN_SITE"
    )

    bpy.types.Scene.blendermcp_hyper3d_api_key = StringProperty(
        name="Hyper3D API Key",
        subtype="PASSWORD",
        description="API Key provided by Hyper3D",
        default=""
    )
    
    bpy.utils.register_class(BLENDERMCP_PT_Panel)
    bpy.utils.register_class(BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey)
    bpy.utils.register_class(BLENDERMCP_OT_StartServer)
    bpy.utils.register_class(BLENDERMCP_OT_StopServer)
    
    print("Enhanced BlenderMCP addon registered with 40+ comprehensive tools")

def unregister():
    if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
        bpy.types.blendermcp_server.stop()
        del bpy.types.blendermcp_server
    
    bpy.utils.unregister_class(BLENDERMCP_PT_Panel)
    bpy.utils.unregister_class(BLENDERMCP_OT_SetFreeTrialHyper3DAPIKey)
    bpy.utils.unregister_class(BLENDERMCP_OT_StartServer)
    bpy.utils.unregister_class(BLENDERMCP_OT_StopServer)
    
    del bpy.types.Scene.blendermcp_port
    del bpy.types.Scene.blendermcp_server_running
    del bpy.types.Scene.blendermcp_use_polyhaven
    del bpy.types.Scene.blendermcp_use_hyper3d
    del bpy.types.Scene.blendermcp_hyper3d_mode
    del bpy.types.Scene.blendermcp_hyper3d_api_key

    print("Enhanced BlenderMCP addon unregistered")

if __name__ == "__main__":
    register()
