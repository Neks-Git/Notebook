import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import os
import sys
import pygame  # Add pygame for sound playback

def resource_path(relative_path):
	"""Get absolute path to resource, works for dev and for PyInstaller"""
	try:
		# PyInstaller creates a temp folder and stores path in _MEIPASS
		base_path = sys._MEIPASS
	except Exception:
		base_path = os.path.abspath(".")
	
	return os.path.join(base_path, relative_path)
# Try to load custom fonts
def load_custom_fonts():
	"""Load custom fonts if they exist"""
	font_files = [
		"Adeliz-Regular.ttf",
		"Adeliz-Regular.otf"
	]
	
	loaded_fonts = []
	
	for font_file in font_files:
		try:
			# Try both in executable directory and bundled resources
			paths_to_try = [
				font_file,  # Current directory
				resource_path(font_file),  # Bundled resources
				os.path.join(os.path.dirname(__file__), font_file)  # Script directory
			]
			
			for path in paths_to_try:
				if os.path.exists(path):
					print(f"Found font file: {path}")
					loaded_fonts.append(path)
					break
		except Exception as e:
			print(f"Could not load font {font_file}: {e}")
	
	return loaded_fonts

# Load fonts at module level
CUSTOM_FONTS = load_custom_fonts()
HAS_CUSTOM_FONT = len(CUSTOM_FONTS) > 0

class FormattedTextWidget:
	"""Custom widget that combines CTkFrame with tk.Text for formatting"""
	def __init__(self, parent, x, y, width, height, page_color="#c1a273"):
		self.parent = parent
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.page_color = page_color
		self.has_focus = False
		
		# Create container frame
		self.frame = ctk.CTkFrame(
			parent,
			fg_color="transparent",
			border_width=0,
			corner_radius=3,
			width=width,
			height=height
		)
		self.frame.place(x=x, y=y)
		self.frame.pack_propagate(False)
		
		# Set font based on availability
		if HAS_CUSTOM_FONT:
			text_font = ("Adeliz", 45)
			# Try to create the font object
			try:
				# Create a tkinter font object for the text widget
				self.custom_font = tk.font.Font(family="Adeliz", size=45)
				text_font = self.custom_font
			except:
				text_font = ("Adeliz", 45)
		else:
			text_font = ("Arial", 45)
		
		# Create tk.Text widget inside frame
		self.text_widget = tk.Text(
			self.frame,
			bg=self.page_color,
			fg="#3d2c1e",
			font=text_font,
			relief="flat",
			wrap="word",
			borderwidth=0,
			highlightthickness=0,
			insertbackground="#3d2c1e",
			cursor="xterm"  # Regular text cursor
		)
		self.text_widget.pack(fill="both", expand=True, padx=0, pady=0)
		self.text_widget.insert("1.0", "Click to edit...")
		
		# Configure text tags for formatting
		if HAS_CUSTOM_FONT:
			# For custom font, we'll use normal font and simulate bold/italic
			self.text_widget.tag_configure("bold", font=(text_font if isinstance(text_font, str) else "Adeliz", 11, "bold"))
			self.text_widget.tag_configure("italic", font=(text_font if isinstance(text_font, str) else "Adeliz", 11, "italic"))
			self.text_widget.tag_configure("bolditalic", font=(text_font if isinstance(text_font, str) else "Adeliz", 11, "bold italic"))
		else:
			self.text_widget.tag_configure("bold", font=("Arial", 11, "bold"))
			self.text_widget.tag_configure("italic", font=("Arial", 11, "italic"))
			self.text_widget.tag_configure("bolditalic", font=("Arial", 11, "bold italic"))
		
		# Store position and size
		self.is_dragging = False
		self.is_resizing = False
		
		# Create resize and move handles
		self.create_handles()
		
		# Bind events
		self.setup_event_bindings()
		
	def create_handles(self):
		"""Create resize and move handles"""
		# Create a handles container frame (top of the text box) - use regular tk.Frame
		self.handles_frame = tk.Frame(
			self.frame,
			bg="#a08c6e",
			height=15,
			relief="flat",
			borderwidth=0
		)
		self.handles_frame.pack(side="top", fill="x", padx=0, pady=0)
		self.handles_frame.pack_propagate(False)  # Don't let children resize
		
		# Create move handle (left side) - hand icon or text
		self.move_handle = tk.Label(
			self.handles_frame,
			text="☝",  # Hand emoji
			bg="#a08c6e",
			fg="#3d2c1e",
			font=("Arial", 10),
			relief="raised",
			borderwidth=1,
			cursor="hand2"
		)
		self.move_handle.pack(side="left", padx=(2, 0), pady=1)
		
		# Spacer to push resize to right
		spacer = tk.Frame(self.handles_frame, bg="#a08c6e")
		spacer.pack(side="left", fill="x", expand=True)
		
		# Create resize handle (right side)
		self.resize_handle = tk.Label(
			self.handles_frame,
			text="↘",  # Resize emoji
			bg="#a08c6e",
			fg="#3d2c1e",
			font=("Arial", 10),
			relief="raised",
			borderwidth=1,
			cursor="sizing"
		)
		self.resize_handle.pack(side="right", padx=(0, 2), pady=1)
		
		# Hide handles initially (only show on hover/focus)
		self.handles_frame.pack_forget()
		
	def focus_for_move(self):
		"""Prepare widget for moving"""
		self.on_focus_in()
		self.is_dragging = True
		self.frame.configure(cursor="fleur" if sys.platform != "darwin" else "hand2")
		
	def focus_for_resize(self):
		"""Prepare widget for resizing"""
		self.on_focus_in()
		self.is_resizing = True
		self.frame.configure(cursor="sizing" if sys.platform != "darwin" else "bottom_right_corner")
		
	def setup_event_bindings(self):
		"""Setup event bindings for text widget and handles"""
		# TEXT WIDGET: Only for text editing, not moving
		self.text_widget.bind("<Button-1>", self.on_text_click)
		self.text_widget.bind("<B1-Motion>", self.on_text_motion)
		
		# FRAME: For moving via the frame itself (alternative to button)
		self.frame.bind("<Button-1>", self.start_drag_via_frame)
		self.frame.bind("<B1-Motion>", self.do_drag)
		self.frame.bind("<ButtonRelease-1>", self.stop_drag)
		
		# RESIZE HANDLE events
		self.resize_handle.bind("<Button-1>", self.start_resize)
		self.resize_handle.bind("<B1-Motion>", self.do_resize)
		self.resize_handle.bind("<ButtonRelease-1>", self.stop_resize)
		
		# MOVE HANDLE events
		self.move_handle.bind("<Button-1>", self.start_drag)
		self.move_handle.bind("<B1-Motion>", self.do_drag)
		self.move_handle.bind("<ButtonRelease-1>", self.stop_drag)
		
		# Show/hide handles on hover
		self.frame.bind("<Enter>", self.show_handles)
		self.frame.bind("<Leave>", self.hide_handles)
		self.text_widget.bind("<Enter>", self.show_handles)
		self.text_widget.bind("<Leave>", self.hide_handles)
		
	def on_text_click(self, event):
		"""Handle click inside text widget - only for text selection"""
		# Don't start drag when clicking in text widget
		self.is_dragging = False
		# Let tkinter handle text selection normally
		return
	
	def on_text_motion(self, event):
		"""Handle motion in text widget - only for text selection"""
		# Don't drag when selecting text
		return
	
	def start_drag_via_frame(self, event):
		"""Start dragging when clicking on frame (not text)"""
		# Check if we're clicking on the frame background, not text widget
		if event.widget == self.frame:
			self.start_drag(event)
	
	def show_handles(self, event=None):
		"""Show move and resize handles"""
		if not self.has_focus:
			self.handles_frame.pack(side="bottom", fill="x", padx=0, pady=0, before=self.text_widget)
	
	def hide_handles(self, event=None):
		"""Hide move and resize handles"""
		if not self.has_focus:
			self.handles_frame.pack_forget()
	
	def on_focus_in(self, event=None):
		"""Handle focus in - show border and handles"""
		self.has_focus = True
		self.frame.configure(border_color="#5d4037", border_width=2)
		self.text_widget.configure(bg="#f5e8c8")
		# Show handles when focused
		self.handles_frame.pack(side="bottom", fill="x", padx=0, pady=0, before=self.text_widget)
		self.handles_frame.configure(bg="#5d4037")
		self.move_handle.configure(bg="#5d4037")
		self.resize_handle.configure(bg="#5d4037")
		
		# Move toolbar if visible
		if hasattr(self, "formatting_frame") and self.formatting_frame.winfo_ismapped():
			self.formatting_frame.place(x=self.x, y=self.y-40)
	
	def on_focus_out(self, event=None):
		"""Handle focus out - hide border and handles"""
		self.has_focus = False
		self.is_dragging = False
		self.is_resizing = False
		self.frame.configure(border_color=self.page_color, border_width=0)
		self.text_widget.configure(bg=self.page_color)
		# Hide handles when not focused
		self.handles_frame.pack_forget()
		self.handles_frame.configure(bg="#a08c6e")
		self.move_handle.configure(bg="#a08c6e")
		self.resize_handle.configure(bg="#a08c6e")
		
	def start_drag(self, event):
		"""Start dragging the widget"""
		self.is_dragging = True
		self.is_resizing = False
		self.drag_start_x = event.x_root
		self.drag_start_y = event.y_root
		self.drag_start_frame_x = self.frame.winfo_x()
		self.drag_start_frame_y = self.frame.winfo_y()
		
		# Change cursor to move cursor
		self.frame.configure(cursor="fleur" if sys.platform != "darwin" else "hand2")
		self.text_widget.configure(cursor="fleur" if sys.platform != "darwin" else "hand2")
		
	def do_drag(self, event):
		"""Drag the widget"""
		if not self.is_dragging:
			return

		dx = event.x_root - self.drag_start_x
		dy = event.y_root - self.drag_start_y

		new_x = self.drag_start_frame_x + dx
		new_y = self.drag_start_frame_y + dy

		parent_width = self.parent.winfo_width()
		parent_height = self.parent.winfo_height()

		new_x = max(0, min(new_x, parent_width - self.width))
		new_y = max(0, min(new_y, parent_height - self.height))

		self.frame.place(x=new_x, y=new_y)
		self.x = new_x
		self.y = new_y

		# Move toolbar if visible
		if hasattr(self, "formatting_frame") and self.formatting_frame.winfo_ismapped():
			self.formatting_frame.place(x=self.x, y=self.y-40)

		self.drag_start_x = event.x_root
		self.drag_start_y = event.y_root
		self.drag_start_frame_x = new_x
		self.drag_start_frame_y = new_y
		
	def stop_drag(self, event):
		"""Stop dragging"""
		self.is_dragging = False
		# Reset cursor
		self.frame.configure(cursor="")
		self.text_widget.configure(cursor="xterm")
		
	def start_resize(self, event):
		"""Start resizing the widget"""
		self.is_resizing = True
		self.is_dragging = False
		self.resize_start_x = event.x_root
		self.resize_start_y = event.y_root
		self.resize_start_width = self.width
		self.resize_start_height = self.height
		
		# Change cursor to resize cursor
		self.frame.configure(cursor="sizing" if sys.platform != "darwin" else "bottom_right_corner")
		self.text_widget.configure(cursor="sizing" if sys.platform != "darwin" else "bottom_right_corner")
		
	def do_resize(self, event):
		"""Resize the widget"""
		if not self.is_resizing:
			return
			
		dx = event.x_root - self.resize_start_x
		dy = event.y_root - self.resize_start_y
		
		new_width = max(100, self.resize_start_width + dx)
		new_height = max(60, self.resize_start_height + dy)
		
		self.width = new_width
		self.height = new_height
		self.frame.configure(width=new_width, height=new_height)

		if hasattr(self, "formatting_frame") and self.formatting_frame.winfo_ismapped():
			self.formatting_frame.place(x=self.x, y=self.y-40)
		
		chars = max(10, int(new_width / 7))
		lines = max(3, int(new_height / 20))
		self.text_widget.configure(width=chars, height=lines)
		
		current_x = self.frame.winfo_x()
		current_y = self.frame.winfo_y()
		parent_width = self.parent.winfo_width()
		parent_height = self.parent.winfo_height()
		
		if current_x + new_width > parent_width:
			new_width = parent_width - current_x
			self.width = new_width
			self.frame.configure(width=new_width)
			chars = max(10, int(new_width / 7))
			self.text_widget.configure(width=chars)
			
		if current_y + new_height > parent_height:
			new_height = parent_height - current_y
			self.height = new_height
			self.frame.configure(height=new_height)
			lines = max(3, int(new_height / 20))
			self.text_widget.configure(height=lines)
		
	def stop_resize(self, event):
		"""Stop resizing"""
		self.is_resizing = False
		# Reset cursor
		self.frame.configure(cursor="")
		self.text_widget.configure(cursor="xterm")
	def get_text(self):
		"""Get text content"""
		return self.text_widget.get("1.0", "end-1c")
		
	def set_text(self, text):
		"""Set text content"""
		self.text_widget.delete("1.0", "end")
		self.text_widget.insert("1.0", text)
		
	def toggle_bold(self):
		"""Toggle bold formatting for selected text"""
		try:
			sel_start = self.text_widget.index("sel.first")
			sel_end = self.text_widget.index("sel.last")
			
			tags = self.text_widget.tag_names(sel_start)
			
			if "bold" in tags or "bolditalic" in tags:
				self.text_widget.tag_remove("bold", sel_start, sel_end)
				self.text_widget.tag_remove("bolditalic", sel_start, sel_end)
				if "bolditalic" in tags:
					self.text_widget.tag_add("italic", sel_start, sel_end)
			else:
				if "italic" in tags:
					self.text_widget.tag_remove("italic", sel_start, sel_end)
					self.text_widget.tag_add("bolditalic", sel_start, sel_end)
				else:
					self.text_widget.tag_add("bold", sel_start, sel_end)
					
		except tk.TclError:
			pass
			
	def toggle_italic(self):
		"""Toggle italic formatting for selected text"""
		try:
			sel_start = self.text_widget.index("sel.first")
			sel_end = self.text_widget.index("sel.last")
			
			tags = self.text_widget.tag_names(sel_start)
			
			if "italic" in tags or "bolditalic" in tags:
				self.text_widget.tag_remove("italic", sel_start, sel_end)
				self.text_widget.tag_remove("bolditalic", sel_start, sel_end)
				if "bolditalic" in tags:
					self.text_widget.tag_add("bold", sel_start, sel_end)
			else:
				if "bold" in tags:
					self.text_widget.tag_remove("bold", sel_start, sel_end)
					self.text_widget.tag_add("bolditalic", sel_start, sel_end)
				else:
					self.text_widget.tag_add("italic", sel_start, sel_end)
					
		except tk.TclError:
			pass
			
	def change_font_size(self, size):
		"""Change font size for selected text"""
		try:
			size = int(size)
			sel_start = self.text_widget.index("sel.first")
			sel_end = self.text_widget.index("sel.last")
			
			tags = self.text_widget.tag_names(sel_start)
			
			if HAS_CUSTOM_FONT:
				font_config = "Adeliz"
				if "bold" in tags and "italic" in tags:
					font_config += " bold italic"
					tag_name = f"size{size}_bold_italic"
				elif "bold" in tags:
					font_config += " bold"
					tag_name = f"size{size}_bold"
				elif "italic" in tags:
					font_config += " italic"
					tag_name = f"size{size}_italic"
				else:
					tag_name = f"size{size}_normal"
			else:
				font_config = "Arial"
				if "bold" in tags and "italic" in tags:
					font_config += " bold italic"
					tag_name = f"size{size}_bold_italic"
				elif "bold" in tags:
					font_config += " bold"
					tag_name = f"size{size}_bold"
				elif "italic" in tags:
					font_config += " italic"
					tag_name = f"size{size}_italic"
				else:
					tag_name = f"size{size}_normal"
			
			if tag_name not in self.text_widget.tag_names():
				self.text_widget.tag_configure(tag_name, font=(font_config, size))
			
			self.text_widget.tag_add(tag_name, sel_start, sel_end)
			
		except tk.TclError:
			pass


class ImageWidget:
	"""Canvas-based image that supports floating over text (no resize)"""
	def __init__(self, canvas, x, y, image_path):
		self.canvas = canvas
		self.x = x
		self.y = y
		self.image_path = image_path

		# Load image
		self.original_image = Image.open(image_path)
		self.width, self.height = self.original_image.size
		max_size = 300
		if self.width > max_size or self.height > max_size:
			ratio = min(max_size / self.width, max_size / self.height)
			self.width = int(self.width * ratio)
			self.height = int(self.height * ratio)
			self.original_image = self.original_image.resize((self.width, self.height), Image.Resampling.LANCZOS)

		self.tk_image = ImageTk.PhotoImage(self.original_image)
		self.image_id = self.canvas.create_image(x, y, image=self.tk_image, anchor="nw")

		# Bind image for dragging and deletion
		self.canvas.tag_bind(self.image_id, "<Button-1>", self.start_drag)
		self.canvas.tag_bind(self.image_id, "<B1-Motion>", self.do_drag)
		self.canvas.tag_bind(self.image_id, "<ButtonRelease-1>", self.stop_drag)
		self.canvas.tag_bind(self.image_id, "<Button-3>", self.delete)

	def start_drag(self, event):
		self.is_dragging = True
		self.drag_start_x = event.x
		self.drag_start_y = event.y

	def do_drag(self, event):
		if not self.is_dragging:
			return
		dx = event.x - self.drag_start_x
		dy = event.y - self.drag_start_y
		self.canvas.move(self.image_id, dx, dy)
		self.drag_start_x = event.x
		self.drag_start_y = event.y

	def stop_drag(self, event):
		self.is_dragging = False

	def delete(self, event=None):
		self.canvas.delete(self.image_id)


class Page:
	"""Represents a single page in the notebook"""
	def __init__(self, parent, is_left_page, page_number):
		self.parent = parent
		self.is_left_page = is_left_page
		self.page_number = page_number
		
		# Create page frame
		self.frame = ctk.CTkFrame(
			parent,
			fg_color="#c1a273",
			border_width=0,
			corner_radius=0
		)
		
		# Canvas for drawing selection boxes and images
		self.canvas = tk.Canvas(
			self.frame,
			bg="#c1a273",
			highlightthickness=0
		)
		self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
		
		# Store widgets on this page
		self.textboxes = []  # FormattedTextWidget objects
		self.images = []     # ImageWidget objects
		
		# Set font for page label
		if HAS_CUSTOM_FONT:
			label_font = ("Adeliz", 24)
		else:
			label_font = ("Arial", 24)
		
		# Page number label (bottom corner)
		self.page_label = ctk.CTkLabel(
			self.frame,
			text=f"Page {page_number + 1}",
			text_color="#5d4037",
			font=label_font
		)
		
		# Place label based on page side
		if is_left_page:
			self.page_label.place(relx=0.02, rely=0.97, anchor="sw")
		else:
			self.page_label.place(relx=0.98, rely=0.97, anchor="se")
	
	def show(self):
		"""Show this page"""
		if self.is_left_page:
			self.frame.place(relx=0, rely=0, relwidth=0.5, relheight=1.0)
		else:
			self.frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1.0)
	
	def hide(self):
		"""Hide this page"""
		self.frame.place_forget()
	
	def add_textbox(self, x, y, width, height):
		"""Add a textbox to this page"""
		textbox = FormattedTextWidget(self.frame, x, y, width, height, page_color="#c1a273")
		self.textboxes.append(textbox)
		return textbox
	
	def add_image(self, x, y, image_path):
		"""Add an image to this page"""
		image_widget = ImageWidget(self.canvas, x, y, image_path)
		self.images.append(image_widget)
		return image_widget
	
	def clear(self):
		"""Clear all widgets from this page"""
		for textbox in self.textboxes:
			textbox.frame.destroy()
			if hasattr(textbox, 'formatting_frame'):
				textbox.formatting_frame.destroy()
		self.textboxes.clear()
		
		for image in self.images:
			image.canvas.delete(image.image_id)
		self.images.clear()


class PageCornerButton:
	"""Custom button that looks like a folded page corner - invisible until hovered"""
	def __init__(self, parent, is_previous=True, command=None, sound_player=None):
		self.parent = parent
		self.is_previous = is_previous  # True for previous, False for next
		self.command = command
		self.sound_player = sound_player  # Reference to sound player
		
		# Colors for the button
		self.base_color = "#c1a273"  # Page color
		self.shadow_color = "#8c704c"  # Darker shadow
		self.highlight_color = "#d4b98c"  # Lighter highlight
		self.hover_color = "#e0d0b0"  # Hover effect
		
		# Get parent's background color
		try:
			parent_bg = parent.cget("background")
		except:
			try:
				parent_bg = parent.cget("bg")
			except:
				parent_bg = "#c1a273"  # Default page color
		
		# Create a canvas for the custom button shape with matching background
		self.canvas = tk.Canvas(
			parent,
			bg=parent_bg,
			highlightthickness=0,
			width=60,
			height=60
		)
		
		# Bind click events
		self.canvas.bind("<Button-1>", self.on_click)
		self.canvas.bind("<Enter>", self.on_enter)
		self.canvas.bind("<Leave>", self.on_leave)
		
		# Start with empty canvas (invisible)
		self.canvas.delete("all")
	
	def draw_corner(self, hover=False):
		"""Draw the folded page corner"""
		self.canvas.delete("all")
		
		# If not hovering, leave canvas empty (invisible)
		if not hover:
			return
		
		# Base triangle (the visible corner)
		if self.is_previous:
			# Left corner (previous button) - triangle pointing right
			points = [0, 0, 60, 0, 0, 60]
		else:
			# Right corner (next button) - triangle pointing left
			points = [60, 0, 60, 60, 0, 60]
		
		# Draw shadow/highlight triangles for 3D effect
		if self.is_previous:
			# Previous button shadows/highlights
			shadow_points1 = [0, 0, 60, 0, 60, 5, 5, 5, 5, 60, 0, 60]
			shadow_points2 = [0, 0, 5, 5, 5, 60, 0, 60]
			highlight_points = [0, 0, 0, 60, 55, 60, 55, 5, 60, 0]
		else:
			# Next button shadows/highlights
			shadow_points1 = [60, 0, 60, 60, 0, 60, 55, 60, 55, 5, 60, 0]
			shadow_points2 = [60, 0, 60, 60, 55, 55, 55, 5, 60, 0]
			highlight_points = [60, 0, 60, 60, 5, 60, 5, 5, 0, 0]
		
		# Fill color based on hover state
		fill_color = self.hover_color
		
		# Draw the main triangle
		self.canvas.create_polygon(points, fill=fill_color, outline="", tags="corner")
		
		# Draw shadow triangles for 3D effect
		self.canvas.create_polygon(shadow_points1, fill=self.shadow_color, outline="", tags="shadow")
		self.canvas.create_polygon(shadow_points2, fill=self.shadow_color, outline="", tags="shadow")
		
		# Draw highlight triangle
		self.canvas.create_polygon(highlight_points, fill=self.highlight_color, outline="", tags="highlight")
		
		# Add fold line
		if self.is_previous:
			# Diagonal line for previous button
			self.canvas.create_line(0, 0, 60, 60, fill=self.shadow_color, width=1, tags="fold")
		else:
			# Diagonal line for next button
			self.canvas.create_line(60, 0, 0, 60, fill=self.shadow_color, width=1, tags="fold")
	
	def on_click(self, event):
		"""Handle click event - play sound and execute command"""
		if self.sound_player:
			self.sound_player.play_flip_sound()
		if self.command:
			self.command()
	
	def on_enter(self, event):
		"""Handle mouse enter event"""
		self.draw_corner(hover=True)
	
	def on_leave(self, event):
		"""Handle mouse leave event"""
		self.draw_corner(hover=False)
	
	def pack(self, **kwargs):
		"""Pack the canvas widget"""
		self.canvas.pack(**kwargs)
	
	def place(self, **kwargs):
		"""Place the canvas widget"""
		self.canvas.place(**kwargs)
	
	def configure(self, **kwargs):
		"""Configure the canvas widget"""
		self.canvas.configure(**kwargs)


class SoundPlayer:
	"""Handles playing sound effects"""
	def __init__(self):
		self.sound_loaded = False
		self.flip_sound = None
		
		# Initialize pygame mixer
		try:
			pygame.mixer.init()
			self.sound_loaded = True
			print("Sound system initialized successfully")
		except Exception as e:
			print(f"Failed to initialize sound system: {e}")
			self.sound_loaded = False
	
	def load_flip_sound(self, sound_path="flip.mp3"):
		"""Load the flip sound from file"""
		if not self.sound_loaded:
			return False
		
		try:
			# Try multiple locations
			paths_to_try = [
				sound_path,
				resource_path(sound_path),
				os.path.join(os.path.dirname(__file__), sound_path)
			]
			
			for path in paths_to_try:
				if os.path.exists(path):
					self.flip_sound = pygame.mixer.Sound(path)
					print(f"Loaded sound: {path}")
					return True
			
			print(f"Sound file not found in any location")
			return False
		except Exception as e:
			print(f"Failed to load sound: {e}")
			return False
	
	def play_flip_sound(self):
		"""Play the flip sound"""
		if self.sound_loaded and self.flip_sound:
			try:
				pygame.mixer.Sound.play(self.flip_sound)
			except Exception as e:
				print(f"Failed to play sound: {e}")


class NotebookApp:
	def __init__(self):
		ctk.set_appearance_mode("light")
		
		self.root = TkinterDnD.Tk()
		ctk.set_appearance_mode("light")
		self.root.title("Notebook App with Pages")
		
		self.setup_sidebar_close_binding()

		# Set max size to 1920x1080
		self.root.maxsize(1920, 1080)
		self.root.geometry("800x600")
		self.root.configure(background="#c1a273")
		
		# Print font status
		if HAS_CUSTOM_FONT:
			print(f"Using custom font: {CUSTOM_FONTS[0]}")
		else:
			print("Using default fonts")
		
		# Initialize sound player
		self.sound_player = SoundPlayer()
		self.sound_player.load_flip_sound("flip.mp3")
		
		# Hidden top bar
		self.top_bar_visible = False
		self.top_bar = None
		self.sidebar_visible = False
		
		# Text box creation state
		self.creating_textbox = False
		self.selection_start = None
		self.selection_rect = None
		
		# Page system
		self.pages = []  # List of Page objects
		self.current_left_page_index = 0
		self.current_right_page_index = 1
		
		# Main page container
		self.page_container = ctk.CTkFrame(
			self.root,
			fg_color="#c1a273",
			border_width=0,
			corner_radius=0
		)
		self.page_container.pack(fill="both", expand=True, padx=0, pady=0)
		
		# Create page corner buttons with sound player reference
		self.prev_corner = PageCornerButton(self.root, is_previous=True, 
										   command=self.previous_page, 
										   sound_player=self.sound_player)
		self.prev_corner.place(x=0, rely=1.0, anchor="sw")  
		
		self.next_corner = PageCornerButton(self.root, is_previous=False, 
										   command=self.next_page, 
										   sound_player=self.sound_player)
		self.next_corner.place(relx=1.0, rely=1.0, anchor="se")
		
		# Initialize pages
		self.initialize_pages()
		
		# Bind text box creation events
		self.setup_textbox_creation()
		
		# Setup image drag and drop
		self.setup_image_drag_drop()
		
		# Setup clipboard paste
		self.setup_clipboard_paste()
		
		# Create seam (must be after pages are initialized)
		self.create_seam()
		
		# Sidebar for page selector
		self.sidebar = None
		
		# Bind mouse movement to show/hide bar
		self.root.bind("<Motion>", self.check_mouse_position)
		
		# Create hidden top bar initially
		self.create_top_bar()
		self.top_bar.place_forget()
		
		# Create sidebar
		self.create_sidebar()

	def setup_custom_font(self):
		"""Try to install custom font system-wide"""
		global HAS_CUSTOM_FONT
		
		if not HAS_CUSTOM_FONT:
			print("No custom font files found in directory")
			return
		
		# Try to install the font
		font_file = CUSTOM_FONTS[0]  # Use the first available font
		try:
			# For Windows, we can try to install the font
			import ctypes
			from ctypes import wintypes
			
			# Constants for AddFontResource
			FR_PRIVATE = 0x10
			
			# Load the AddFontResource function
			gdi32 = ctypes.WinDLL('gdi32')
			AddFontResource = gdi32.AddFontResourceW
			AddFontResource.argtypes = [wintypes.LPCWSTR]
			AddFontResource.restype = wintypes.INT
			
			# Add the font resource
			result = AddFontResource(os.path.abspath(font_file))
			if result > 0:
				print(f"Successfully installed font: {font_file}")
				# Broadcast font change notification
				HWND_BROADCAST = 0xFFFF
				WM_FONTCHANGE = 0x001D
				user32 = ctypes.WinDLL('user32')
				SendMessage = user32.SendMessageW
				SendMessage(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)
			else:
				print(f"Failed to install font: {font_file}")
		except Exception as e:
			print(f"Could not install font system-wide: {e}")
			print("Font will be used locally within the application")

	def initialize_pages(self):
		"""Create initial pages"""
		# Create first two pages
		left_page = Page(self.page_container, True, 0)
		right_page = Page(self.page_container, False, 1)
		
		self.pages.append(left_page)
		self.pages.append(right_page)
		
		# Show initial pages
		left_page.show()
		right_page.show()
		
		# Setup canvas events for these pages
		self.setup_page_canvas_events(left_page)
		self.setup_page_canvas_events(right_page)
		
		# Update navigation
		self.update_navigation()


	def create_seam(self):
		"""Create a simple, efficient seam that stays within the app"""
		# Create seam directly on the root window
		self.seam = tk.Frame(
			self.root,
			bg="#000000",
			width=3
		)
		
		# Place it at the center of the window
		self.seam.place(relx=0.5, rely=0, relheight=1.0, anchor="n")
		
		# Make sure it's above everything
		self.seam.lift()
		
		# Force seam to be above pages
		def raise_seam_above_pages():
			self.seam.lift()
			for page in self.pages:
				if page.frame.winfo_exists():
					self.seam.lift(page.frame)
		
		# Raise initially and after page changes
		self.root.after(100, raise_seam_above_pages)
		
		# Also raise when pages change
		original_next_page = self.next_page
		original_previous_page = self.previous_page
		
		def wrapped_next_page():
			original_next_page()
			raise_seam_above_pages()
		
		def wrapped_previous_page():
			original_previous_page()
			raise_seam_above_pages()
		
		self.next_page = wrapped_next_page
		self.previous_page = wrapped_previous_page
		
	def setup_image_drag_drop(self):
		"""Setup drag and drop for images"""
		# We'll handle this in the page-specific canvases
		pass
	
	def setup_clipboard_paste(self):
		"""Setup Ctrl+V paste for images"""
		self.root.bind('<Control-v>', self.paste_from_clipboard)
		self.root.bind('<Control-V>', self.paste_from_clipboard)
	
	def paste_from_clipboard(self, event):
		"""Handle Ctrl+V paste safely (text only, no image)"""
		try:
			# Try to get text from clipboard
			text = self.root.clipboard_get()
			# Insert text at center of left page
			self.create_text_widget(self.pages[self.current_left_page_index], 50, 50, text)
			return "break"  # Prevent default paste
		except tk.TclError:
			# Nothing in clipboard, ignore
			pass
	
	def setup_textbox_creation(self):
		"""Set up event bindings for creating text boxes"""
		# We'll bind to the current page canvases dynamically
		pass
	
	def get_current_left_page(self):
		"""Get the current left page object"""
		if self.current_left_page_index < len(self.pages):
			return self.pages[self.current_left_page_index]
		return None
	
	def get_current_right_page(self):
		"""Get the current right page object"""
		if self.current_right_page_index < len(self.pages):
			return self.pages[self.current_right_page_index]
		return None
	
	def create_text_widget(self, page, x, y, text=""):
		"""Create a text widget on a specific page"""
		text_widget = page.add_textbox(x, y, 200, 100)
		if text:
			text_widget.set_text(text)
		
		# Create formatting toolbar
		formatting_frame = self.create_formatting_toolbar(page.frame, text_widget)
		text_widget.formatting_frame = formatting_frame
		
		# Setup focus behavior
		def on_focus_in(e):
			text_widget.on_focus_in()
			formatting_frame.place(x=text_widget.x, y=text_widget.y-40)
			
		def on_focus_out(e):
			text_widget.on_focus_out()
			formatting_frame.place_forget()
			
		text_widget.text_widget.bind("<FocusIn>", on_focus_in)
		text_widget.text_widget.bind("<FocusOut>", on_focus_out)
		
		# Clear placeholder on focus
		def clear_placeholder(e):
			if text_widget.get_text() == "Click to edit...":
				text_widget.set_text("")
				
		text_widget.text_widget.bind("<FocusIn>", clear_placeholder, add="+")
		
		# Add delete on right-click
		def delete_textbox(event):
			if event.num == 3:  # Right click
				text_widget.frame.destroy()
				formatting_frame.destroy()
				page.textboxes.remove(text_widget)
				
		text_widget.frame.bind("<Button-3>", delete_textbox)
		text_widget.text_widget.bind("<Button-3>", delete_textbox)
		
		# Bind textbox creation events to this page's canvas
		self.setup_page_canvas_events(page)
		
		return text_widget
	
	def setup_page_canvas_events(self, page):
		"""Setup event bindings for a page's canvas"""
		canvas = page.canvas
		
		# Remove existing bindings to avoid duplicates
		canvas.unbind("<Double-Button-1>")
		canvas.unbind("<B1-Motion>")
		canvas.unbind("<ButtonRelease-1>")
		canvas.unbind("<Button-1>")
		
		# Add new bindings
		canvas.bind("<Double-Button-1>", lambda e: self.start_textbox_creation(e, page))
		canvas.bind("<B1-Motion>", lambda e: self.draw_selection_box(e, page))
		canvas.bind("<ButtonRelease-1>", lambda e: self.finish_textbox_creation(e, page))
		canvas.bind("<Button-1>", lambda e: self.remove_textbox_focus(e))
	
	def start_textbox_creation(self, event, page):
		"""Start creating a text box on double-click"""
		print(f"Double-click detected at ({event.x}, {event.y}) on page {page.page_number}")
		self.creating_textbox = True
		self.selection_start = (event.x, event.y)
		self.current_page = page
		
		canvas = page.canvas
		self.clear_selection_rect(canvas)

		self.selection_rect = canvas.create_rectangle(
			event.x, event.y, event.x, event.y,
			outline="#000000",
			dash=(4, 2),
			width=2,
			tags="selection"
		)
	
	def draw_selection_box(self, event, page):
		"""Draw the selection box while dragging"""
		if not self.creating_textbox or not self.selection_start:
			return

		start_x, start_y = self.selection_start
		canvas = page.canvas
		canvas.coords(self.selection_rect, start_x, start_y, event.x, event.y)
	
	def finish_textbox_creation(self, event, page):
		if not self.creating_textbox or not self.selection_start:
			return

		start_x, start_y = self.selection_start
		end_x, end_y = event.x, event.y

		width = abs(end_x - start_x)
		height = abs(end_y - start_y)

		if width < 100: width = 200
		if height < 60: height = 100

		x = min(start_x, end_x)
		y = min(start_y, end_y)

		# Create text widget
		self.create_text_widget(page, x, y)
		
		# Clear selection
		canvas = page.canvas
		canvas.delete("selection")
		
		self.creating_textbox = False
		self.selection_start = None
		self.current_page = None
	
	def clear_selection_rect(self, canvas):
		"""Clear the selection rectangle from a canvas"""
		canvas.delete("selection")
	
	def remove_textbox_focus(self, event):
		"""Remove focus from all textboxes"""
		# Hide formatting toolbar for all textboxes
		for page in self.pages:
			for textbox in page.textboxes:
				if hasattr(textbox, 'formatting_frame') and textbox.formatting_frame.winfo_ismapped():
					textbox.formatting_frame.place_forget()
				if hasattr(textbox, 'has_focus') and textbox.has_focus:
					textbox.on_focus_out()
		self.root.focus()
	
	def create_formatting_toolbar(self, parent, text_widget):
		"""Create formatting toolbar for a text widget"""
		formatting_frame = ctk.CTkFrame(
			parent,
			fg_color="#f5e8c8",
			width=120,
			height=35,
			corner_radius=3,
			border_width=1,
			border_color="#a08c6e"
		)
		formatting_frame.pack_propagate(False)
		formatting_frame.place_forget()
		
		# Set font for toolbar buttons
		if HAS_CUSTOM_FONT:
			toolbar_font = ("Adeliz", 24)
		else:
			toolbar_font = ("Arial", 24)
		
		# Bold button
		bold_btn = ctk.CTkButton(
			formatting_frame,
			text="B",
			width=30,
			height=25,
			fg_color="#e0d0b0",
			hover_color="#d0c0a0",
			text_color="#3d2c1e",
			font=(toolbar_font[0], toolbar_font[1], "bold"),
			corner_radius=2,
			command=text_widget.toggle_bold
		)
		bold_btn.pack(side="left", padx=(5, 2), pady=5)
		
		# Italic button
		italic_btn = ctk.CTkButton(
			formatting_frame,
			text="I",
			width=30,
			height=25,
			fg_color="#e0d0b0",
			hover_color="#d0c0a0",
			text_color="#3d2c1e",
			font=(toolbar_font[0], toolbar_font[1], "italic"),
			corner_radius=2,
			command=text_widget.toggle_italic
		)
		italic_btn.pack(side="left", padx=2, pady=5)
		
		# Font size dropdown
		font_sizes = ["8", "10", "11", "12", "14", "16", "18", "20", "24", "32", "45"]
		font_size_var = ctk.StringVar(value="11")
		
		font_size_menu = ctk.CTkOptionMenu(
			formatting_frame,
			values=font_sizes,
			variable=font_size_var,
			width=50,
			height=25,
			fg_color="#e0d0b0",
			button_color="#d0c0a0",
			button_hover_color="#c0b090",
			text_color="#3d2c1e",
			font=(toolbar_font[0], 10),
			corner_radius=2,
			command=lambda size: text_widget.change_font_size(size)
		)
		font_size_menu.pack(side="left", padx=(2, 5), pady=5)
		
		return formatting_frame

	def previous_page(self):
		"""Go to previous page"""
		if self.current_left_page_index > 0:
			# Hide current pages
			left_page = self.get_current_left_page()
			right_page = self.get_current_right_page()
			if left_page: left_page.hide()
			if right_page: right_page.hide()
			
			# Update indices
			self.current_left_page_index -= 2
			self.current_right_page_index -= 2
			
			# Show new pages
			left_page = self.get_current_left_page()
			right_page = self.get_current_right_page()
			if left_page: left_page.show()
			if right_page: right_page.show()
			
			# Update navigation
			self.update_navigation()
	
	def next_page(self):
		"""Go to next page"""
		# Check if we need to create new pages
		if self.current_right_page_index + 1 >= len(self.pages):
			self.add_new_pages()
		
		# Hide current pages
		left_page = self.get_current_left_page()
		right_page = self.get_current_right_page()
		if left_page: left_page.hide()
		if right_page: right_page.hide()
		
		# Update indices
		self.current_left_page_index += 2
		self.current_right_page_index += 2
		
		# Show new pages
		left_page = self.get_current_left_page()
		right_page = self.get_current_right_page()
		if left_page: left_page.show()
		if right_page: right_page.show()
		
		# Update navigation
		self.update_navigation()
	
	def add_new_pages(self):
		"""Add two new pages to the notebook"""
		page_count = len(self.pages)
		left_page = Page(self.page_container, True, page_count)
		right_page = Page(self.page_container, False, page_count + 1)
		
		self.pages.append(left_page)
		self.pages.append(right_page)
		
		# Setup canvas events for new pages
		self.setup_page_canvas_events(left_page)
		self.setup_page_canvas_events(right_page)
	
	def update_navigation(self):
		"""Update navigation buttons and indicator"""
		# Update button states
		# The corner buttons will handle their own visual state
		pass
	
	def create_top_bar(self):
		# Create top bar
		self.top_bar = ctk.CTkFrame(
			self.root,
			fg_color="#f5e8c8",
			height=35,
			corner_radius=0
		)
		self.top_bar.pack_propagate(False)
		
		# Hamburger menu icon (3 lines) - LEFT SIDE
		menu_frame = ctk.CTkFrame(
			self.top_bar,
			fg_color="transparent",
			width=40,
			height=25
		)
		menu_frame.pack_propagate(False)
		menu_frame.pack(side="left", padx=(10, 0), pady=5)
		
		# Draw 3 lines for hamburger menu
		canvas = ctk.CTkCanvas(
			menu_frame,
			bg="#f5e8c8",
			highlightthickness=0,
			width=30,
			height=25
		)
		canvas.pack()
		
		# Draw 3 horizontal lines
		line_color = "#5d4037"
		canvas.create_line(5, 8, 25, 8, fill=line_color, width=2)
		canvas.create_line(5, 13, 25, 13, fill=line_color, width=2)
		canvas.create_line(5, 18, 25, 18, fill=line_color, width=2)
		
		# Make the canvas clickable
		canvas.bind("<Button-1>", self.toggle_sidebar)
		menu_frame.bind("<Button-1>", self.toggle_sidebar)
		
		# Set font for top bar buttons
		if HAS_CUSTOM_FONT:
			topbar_font = ("Adeliz", 24)
		else:
			topbar_font = ("Segoe UI", 24)
		
		# File button with image import option
		file_btn = ctk.CTkButton(
			self.top_bar,
			text="Import Image",
			fg_color="transparent",
			hover_color="#e0d0b0",
			text_color="#5d4037",
			font=topbar_font,
			width=100,
			height=25,
			corner_radius=3,
			border_width=1,
			border_color="#d4b98c",
			command=self.import_image_file
		)
		file_btn.pack(side="left", padx=(10, 5), pady=5)
		
		# Add Page button
		add_page_btn = ctk.CTkButton(
			self.top_bar,
			text="Add Page",
			fg_color="transparent",
			hover_color="#e0d0b0",
			text_color="#5d4037",
			font=topbar_font,
			width=80,
			height=25,
			corner_radius=3,
			border_width=1,
			border_color="#d4b98c",
			command=self.add_new_pages_and_go
		)
		add_page_btn.pack(side="left", padx=5, pady=5)
		
		# Save button
		save_btn = ctk.CTkButton(
			self.top_bar,
			text="Save",
			fg_color="transparent",
			hover_color="#e0d0b0",
			text_color="#5d4037",
			font=topbar_font,
			width=60,
			height=25,
			corner_radius=3,
			border_width=1,
			border_color="#d4b98c"
		)
		save_btn.pack(side="left", padx=5, pady=5)
		
		# Spacer
		spacer = ctk.CTkFrame(self.top_bar, fg_color="transparent")
		spacer.pack(side="left", fill="x", expand=True)
	
	def add_new_pages_and_go(self):
		"""Add new pages and navigate to them"""
		self.add_new_pages()
		self.next_page()
	
	def import_image_file(self):
		file_path = filedialog.askopenfilename(
			title="Select Image",
			filetypes=[
				("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
				("PNG files", "*.png"),
				("All files", "*.*")
			]
		)
		
		if file_path:
			# Place image in center of current left page
			page = self.get_current_left_page()
			if page:
				canvas = page.canvas
				x = canvas.winfo_width() // 2 - 100
				y = canvas.winfo_height() // 2 - 100
				
				page.add_image(x, y, file_path)
	
	def create_sidebar(self):
		# Create left sidebar - slightly darker than page color
		self.sidebar = ctk.CTkFrame(
			self.root,
			fg_color="#a08c6e",
			width=200,
			corner_radius=0
		)
		self.sidebar.pack_propagate(False)
		self.sidebar.place(x=-200, y=0, relheight=1.0)
		
		# Set font for sidebar
		if HAS_CUSTOM_FONT:
			sidebar_font = ("Adeliz", 24, "bold")
			page_list_font = ("Adeliz", 24)
		else:
			sidebar_font = ("Segoe UI", 24, "bold")
			page_list_font = ("Segoe UI", 24)
		
		# Sidebar header
		sidebar_header = ctk.CTkLabel(
			self.sidebar,
			text="Pages",
			font=sidebar_font,
			text_color="#3d2c1e",
			height=40
		)
		sidebar_header.pack(fill="x", pady=(10, 0))
		
		# Page list
		self.page_list = ctk.CTkScrollableFrame(
			self.sidebar,
			fg_color="#b5a184",
			corner_radius=0
		)
		self.page_list.pack(fill="both", expand=True, padx=10, pady=10)
		
		# Update page list
		self.update_sidebar_page_list()
	
	def update_sidebar_page_list(self):
		"""Update the page list in sidebar"""
		# Clear current list
		for widget in self.page_list.winfo_children():
			widget.destroy()
		
		# Set font for page buttons
		if HAS_CUSTOM_FONT:
			page_btn_font = ("Adeliz", 11)
		else:
			page_btn_font = ("Segoe UI", 11)
		
		# Add page buttons
		for i, page in enumerate(self.pages):
			page_btn = ctk.CTkButton(
				self.page_list,
				text=f"Page {i + 1}",
				fg_color="#e0d0b0",
				hover_color="#d0c0a0",
				text_color="#3d2c1e",
				font=page_btn_font,
				height=30,
				command=lambda idx=i: self.go_to_page(idx)
			)
			page_btn.pack(fill="x", pady=2)
	
	def go_to_page(self, page_index):
		"""Go to a specific page"""
		# Calculate which pages to show
		if page_index % 2 == 0:  # Even index = left page
			self.current_left_page_index = page_index
			self.current_right_page_index = page_index + 1
		else:  # Odd index = right page
			self.current_left_page_index = page_index - 1
			self.current_right_page_index = page_index
		
		# Ensure indices are valid
		if self.current_right_page_index >= len(self.pages):
			self.add_new_pages()
		
		# Hide all pages
		for page in self.pages:
			page.hide()
		
		# Show selected pages
		left_page = self.get_current_left_page()
		right_page = self.get_current_right_page()
		if left_page: left_page.show()
		if right_page: right_page.show()
		
		# Update navigation
		self.update_navigation()
		
		# Close sidebar
		self.close_sidebar()
	
	def setup_sidebar_close_binding(self):
		# Bind left-click anywhere on the root
		self.root.bind("<Button-1>", self.check_click_outside_sidebar)

	def check_click_outside_sidebar(self, event):
		if not self.sidebar_visible:
			return

		# Ignore clicks inside sidebar
		if self.sidebar is not None:
			sx1 = self.sidebar.winfo_x()
			sy1 = self.sidebar.winfo_y()
			sx2 = sx1 + self.sidebar.winfo_width()
			sy2 = sy1 + self.sidebar.winfo_height()
			if sx1 <= event.x <= sx2 and sy1 <= event.y <= sy2:
				return

		# Ignore clicks inside top bar
		if self.top_bar is not None and self.top_bar_visible:
			tx1 = self.top_bar.winfo_x()
			ty1 = self.top_bar.winfo_y()
			tx2 = tx1 + self.top_bar.winfo_width()
			ty2 = ty1 + self.top_bar.winfo_height()
			if tx1 <= event.x <= tx2 and ty1 <= event.y <= ty2:
				return

		# Otherwise, click is outside sidebar → close it
		self.close_sidebar()
	
	def is_mouse_over_widget(self, widget, event):
		"""Check if mouse is over a widget using relative coordinates"""
		try:
			widget_x = widget.winfo_x()
			widget_y = widget.winfo_y()
			widget_width = widget.winfo_width()
			widget_height = widget.winfo_height()
			
			return (widget_x <= event.x <= widget_x + widget_width and 
					widget_y <= event.y <= widget_y + widget_height)
		except:
			return False
	
	def toggle_sidebar(self, event=None):
		if self.sidebar_visible:
			self.close_sidebar()
		else:
			self.open_sidebar()
	
	def open_sidebar(self):
		if not self.sidebar_visible:
			# Update page list before showing
			self.update_sidebar_page_list()
			self.sidebar.place(x=0, y=0, relheight=1.0)
			self.sidebar_visible = True
	
	def close_sidebar(self, event=None):
		if self.sidebar_visible:
			self.sidebar.place(x=-200, y=0, relheight=1.0)
			self.sidebar_visible = False
	
	def check_mouse_position(self, event):
		# Don't show top bar if sidebar is open
		if self.sidebar_visible and event.x < 200:
			if not self.top_bar_visible:
				self.show_top_bar()
			return

		# Check if cursor is over any formatting toolbar
		for page in self.pages:
			for textbox in page.textboxes:
				if hasattr(textbox, 'formatting_frame') and textbox.formatting_frame.winfo_ismapped():
					if self.is_mouse_over_widget(textbox.formatting_frame, event):
						return

		# Original behavior
		if event.y < 30:
			if not self.top_bar_visible:
				self.show_top_bar()
		else:
			if self.top_bar_visible and event.y > 70:
				self.hide_top_bar()

	def show_top_bar(self):
		self.top_bar.place(x=0, y=0, relwidth=1.0)
		self.top_bar_visible = True
	
	def hide_top_bar(self):
		self.top_bar.place_forget()
		self.top_bar_visible = False
	
	def run(self):
		self.root.mainloop()

if __name__ == "__main__":
	app = NotebookApp()
	app.run()
