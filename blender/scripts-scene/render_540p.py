import bpy, os

s = bpy.context.scene
s.render.resolution_x = 960
s.render.resolution_y = 540
s.render.resolution_percentage = 100
s.render.image_settings.file_format = "PNG"
s.render.image_settings.color_mode = "RGB"
s.render.filepath = os.environ.get("TAIWEI_FRAMES_DIR", "//frames_540p/")
s.render.use_file_extension = True
print("[render_540p] %dx%d -> %s" % (s.render.resolution_x, s.render.resolution_y, s.render.filepath))
