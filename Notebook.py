import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import os

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
		
		# Create tk.Text widget inside frame
		self.text_widget = tk.Text(
			self.frame,
			bg=self.page_color,
			fg="#3d2c1e",
			font=("Arial", 11),
			relief="flat",
			wrap="word",
			borderwidth=0,
			highlightthickness=0,
			insertbackground="#3d2c1e"
		)
		self.text_widget.pack(fill="both", expand=True, padx=0, pady=0)
		self.text_widget.insert("1.0", "Click to edit...")
		
		# Configure text tags for formatting
		self.text_widget.tag_configure("bold", font=("Arial", 11, "bold"))
		self.text_widget.tag_configure("italic", font=("Arial", 11, "italic"))
		self.text_widget.tag_configure("bolditalic", font=("Arial", 11, "bold italic"))
		
		# Store position and size
		self.is_dragging = False
		self.is_resizing = False
		
		# Create resize handle
		self.create_resize_handle()
		
		# Bind events
		self.setup_event_bindings()
		
	def create_resize_handle(self):
		"""Create a resize handle in bottom-right corner"""
		self.resize_handle = ctk.CTkFrame(
			self.frame,
			fg_color="#a08c6e",
			width=12,
			height=12,
			corner_radius=3
		)
		self.resize_handle.place(relx=1.0, rely=1.0, anchor="se")
		self.resize_handle.lower()
		
	def setup_event_bindings(self):
		"""Setup drag and resize event bindings"""
		# Dragging works by clicking anywhere in the frame or text widget
		for widget in [self.frame, self.text_widget]:
			widget.bind("<Button-1>", self.start_drag)
			widget.bind("<B1-Motion>", self.do_drag)
			widget.bind("<ButtonRelease-1>", self.stop_drag)

		# Resize handle events
		self.resize_handle.bind("<Button-1>", self.start_resize)
		self.resize_handle.bind("<B1-Motion>", self.do_resize)
		self.resize_handle.bind("<ButtonRelease-1>", self.stop_resize)
		
	def on_focus_in(self, event=None):
		"""Handle focus in - show border and resize handle"""
		self.has_focus = True
		self.frame.configure(border_color="#5d4037", border_width=2)
		self.text_widget.configure(bg="#f5e8c8")
		self.resize_handle.lift()
		self.resize_handle.configure(fg_color="#5d4037")
		
	def on_focus_out(self, event=None):
		"""Handle focus out - hide border and resize handle"""
		self.has_focus = False
		self.frame.configure(border_color=self.page_color, border_width=0)
		self.text_widget.configure(bg=self.page_color)
		self.resize_handle.lower()
		self.resize_handle.configure(fg_color=self.page_color)
		
	def start_drag(self, event):
		"""Start dragging the widget"""
		self.is_dragging = True
		self.drag_start_x = event.x_root
		self.drag_start_y = event.y_root
		self.drag_start_frame_x = self.frame.winfo_x()
		self.drag_start_frame_y = self.frame.winfo_y()
		
	def do_drag(self, event):
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
		
	def start_resize(self, event):
		"""Start resizing the widget"""
		self.is_resizing = True
		self.resize_start_x = event.x_root
		self.resize_start_y = event.y_root
		self.resize_start_width = self.width
		self.resize_start_height = self.height
		
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
		
		self.resize_handle.place(relx=1.0, rely=1.0, anchor="se")
		
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
	"""Canvas-based image that supports transparency and floating over text"""
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

		# Create resize handle (larger and clickable)
		handle_size = 15
		self.handle_id = self.canvas.create_rectangle(
			x + self.width - handle_size,
			y + self.height - handle_size,
			x + self.width,
			y + self.height,
			fill="#a08c6e",
			outline="#5d4037",
			tags="handle"
		)

		# Bring handle above image
		self.canvas.tag_raise(self.handle_id, self.image_id)

		# Bind both image and handle
		for tag in [self.image_id, self.handle_id]:
			self.canvas.tag_bind(tag, "<Button-1>", self.start_drag)
			self.canvas.tag_bind(tag, "<B1-Motion>", self.do_drag)
			self.canvas.tag_bind(tag, "<ButtonRelease-1>", self.stop_drag)

			self.canvas.tag_bind(tag, "<Button-3>", self.delete)

		# Bind handle resize separately
		self.canvas.tag_bind(self.handle_id, "<Button-1>", self.start_resize)
		self.canvas.tag_bind(self.handle_id, "<B1-Motion>", self.do_resize)
		self.canvas.tag_bind(self.handle_id, "<ButtonRelease-1>", self.stop_resize)

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
		self.canvas.move(self.handle_id, dx, dy)
		self.drag_start_x = event.x
		self.drag_start_y = event.y

	def stop_drag(self, event):
		self.is_dragging = False

	def start_resize(self, event):
		if not self.canvas.coords(self.image_id):
			self.is_resizing = False
			return
		self.is_resizing = True
		self.resize_start_x = self.canvas.canvasx(event.x)
		self.resize_start_y = self.canvas.canvasy(event.y)
		self.start_width = self.width
		self.start_height = self.height

	def do_resize(self, event):
		if not self.is_resizing: return

		coords = self.canvas.coords(self.image_id)
		if not coords:
			return  # Nothing to resize (maybe deleted)
		x, y = coords

		dx = self.canvas.canvasx(event.x) - self.resize_start_x
		scale = 1 + dx / max(self.start_width, 1)
		new_width = max(50, int(self.start_width * scale))
		new_height = max(50, int(self.start_height * scale))
		self.width, self.height = new_width, new_height

		resized_img = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
		self.tk_image = ImageTk.PhotoImage(resized_img)
		self.canvas.itemconfig(self.image_id, image=self.tk_image)

		self.canvas.coords(
			self.handle_id,
			x + new_width - 15,
			y + new_height - 15,
			x + new_width,
			y + new_height
		)

	def stop_resize(self, event):
		self.is_resizing = False
		# Update original image to current size
		self.original_image = self.original_image.resize((self.width, self.height), Image.Resampling.LANCZOS)

	def delete(self, event=None):
		self.canvas.delete(self.image_id)
		self.canvas.delete(self.handle_id)



class NotebookApp:
	def __init__(self):
		ctk.set_appearance_mode("light")
		
		self.root = TkinterDnD.Tk()
		ctk.set_appearance_mode("light")
		self.root.title("Notebook App with Images")
		
		self.setup_sidebar_close_binding()

		# Set max size to 1920x1080
		self.root.maxsize(1920, 1080)
		self.root.geometry("800x600")
		self.root.configure(background="#c1a273")
		
		# Hidden top bar
		self.top_bar_visible = False
		self.top_bar = None
		self.sidebar_visible = False
		
		# Text box creation state
		self.creating_textbox = False
		self.selection_start = None
		self.selection_rect = None
		self.current_page = None
		
		# Store all widgets
		self.textboxes = []  # FormattedTextWidget objects
		self.image_widgets = []  # ImageWidget objects
		
		# Track current page for widget placement
		self.current_left_page_num = 0
		self.current_right_page_num = 1
		
		# Main page container
		self.page_container = ctk.CTkFrame(
			self.root,
			fg_color="#c1a273",
			border_width=0,
			corner_radius=0
		)
		self.page_container.pack(fill="both", expand=True, padx=0, pady=0)
		
		# Two pages - left and right of seam
		self.left_page = ctk.CTkFrame(
			self.page_container,
			fg_color="#c1a273",
			border_width=0,
			corner_radius=0
		)
		self.left_page.place(relx=0, rely=0, relwidth=0.5, relheight=1.0)
		
		self.right_page = ctk.CTkFrame(
			self.page_container,
			fg_color="#c1a273",
			border_width=0,
			corner_radius=0
		)
		self.right_page.place(relx=0.5, rely=0, relwidth=0.5, relheight=1.0)
		
		# Black book seam in the middle (on top of pages)
		self.seam = ctk.CTkFrame(
			self.page_container,
			fg_color="#000000",
			width=3,
			corner_radius=0
		)
		self.seam.pack_propagate(False)
		self.seam.place(relx=0.5, rely=0, relheight=1.0, anchor="n")
		
		# Bind text box creation events
		self.setup_textbox_creation()
		
		# Setup image drag and drop
		self.setup_image_drag_drop()
		
		# Setup clipboard paste
		self.setup_clipboard_paste()
		
		# Sidebar for page selector
		self.sidebar = None
		
		# Bind mouse movement to show/hide bar
		self.root.bind("<Motion>", self.check_mouse_position)
		
		# Create hidden top bar initially
		self.create_top_bar()
		self.top_bar.place_forget()
		
		# Create sidebar
		self.create_sidebar()

	def setup_image_drag_drop(self):
		for page in [self.left_page, self.right_page]:
			page.drop_target_register(DND_FILES)
			page.dnd_bind("<<Drop>>", self.on_image_drop)
			
	def setup_clipboard_paste(self):
		"""Setup Ctrl+V paste for images"""
		self.root.bind('<Control-v>', self.paste_from_clipboard)
		self.root.bind('<Control-V>', self.paste_from_clipboard)
		
	def on_image_drop(self, event):
		files = self.root.tk.splitlist(event.data)

		for file_path in files:
			file_path = file_path.strip("{}")
			if not file_path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
				continue

			# Use the correct canvas
			if event.widget == self.left_page:
				canvas = self.left_canvas
				page_x = self.left_page.winfo_rootx()
				page_y = self.left_page.winfo_rooty()
			else:
				canvas = self.right_canvas
				page_x = self.right_page.winfo_rootx()
				page_y = self.right_page.winfo_rooty()

			x = event.x_root - page_x
			y = event.y_root - page_y

			self.create_image_widget(canvas, x, y, file_path)

			
	def paste_from_clipboard(self, event):
		"""Handle Ctrl+V paste safely (text only, no image)"""
		try:
			# Try to get text from clipboard
			text = self.root.clipboard_get()
			# Optionally, insert text somewhere, e.g., current page or textbox
			# For example: insert at top-left of left page
			self.create_text_widget(self.left_page, 10, 10, text)
			return "break"  # Prevent default paste
		except tk.TclError:
			# Nothing in clipboard, ignore
			pass

			
	def create_image_widget(self, canvas, x, y, image_path):
		image_widget = ImageWidget(canvas, x, y, image_path)
		self.image_widgets.append(image_widget)
			
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
			
	def setup_textbox_creation(self):
		"""Set up event bindings for creating text boxes"""
		# Create canvas for drawing selection box (on each page)
		self.left_canvas = ctk.CTkCanvas(
			self.left_page,
			bg="#c1a273",
			highlightthickness=0
		)
		self.left_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

		self.right_canvas = ctk.CTkCanvas(
			self.right_page,
			bg="#c1a273",
			highlightthickness=0
		)
		self.right_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

		# Bind events to the canvases
		for canvas in [self.left_canvas, self.right_canvas]:
			canvas.bind("<Double-Button-1>", self.start_textbox_creation)
			canvas.bind("<B1-Motion>", self.draw_selection_box)
			canvas.bind("<ButtonRelease-1>", self.finish_textbox_creation)
			canvas.bind("<Button-1>", self.remove_textbox_focus)
			
	def remove_textbox_focus(self, event):
		# Hide formatting toolbar for all textboxes
		for textbox in self.textboxes:
			if hasattr(textbox, 'formatting_frame') and textbox.formatting_frame.winfo_ismapped():
				textbox.formatting_frame.place_forget()
			if hasattr(textbox, 'has_focus') and textbox.has_focus:
				textbox.on_focus_out()
		self.root.focus()

		# Remove hover effects from images (skip if not defined)
		for image_widget in self.image_widgets:
			if hasattr(image_widget, "on_hover_out"):
				image_widget.on_hover_out()

	def start_textbox_creation(self, event):
		"""Start creating a text box on double-click"""
		self.creating_textbox = True
		self.selection_start = (event.x, event.y)

		# Determine which page the canvas belongs to
		if event.widget == self.left_canvas:
			self.current_page = self.left_page
			canvas = self.left_canvas
			page_color = "#c1a273"
		else:
			self.current_page = self.right_page
			canvas = self.right_canvas
			page_color = "#c1a273"

		self.clear_selection_rect()

		self.selection_rect = canvas.create_rectangle(
			event.x, event.y, event.x, event.y,
			outline="#000000",
			dash=(4, 2),
			width=2,
			tags="selection"
		)

	def draw_selection_box(self, event):
		"""Draw the selection box while dragging"""
		if not self.creating_textbox or not self.selection_start:
			return

		start_x, start_y = self.selection_start

		canvas = self.left_canvas if self.current_page == self.left_page else self.right_canvas
		canvas.coords(self.selection_rect, start_x, start_y, event.x, event.y)
		
	def finish_textbox_creation(self, event):
		if not self.creating_textbox or not self.selection_start:
			return

		start_x, start_y = self.selection_start
		end_x, end_y = event.x, event.y

		width = abs(end_x - start_x)
		height = abs(end_y - start_y)

		if width < 100: width = 200
		if height < 60: height = 100

		parent = self.current_page
		canvas = self.left_canvas if parent == self.left_page else self.right_canvas

		self.clear_selection_rect()

		x = min(start_x, end_x)
		y = min(start_y, end_y)

		# Create custom text widget
		text_widget = FormattedTextWidget(parent, x, y, width, height, page_color="#c1a273")
		
		# Create formatting toolbar
		formatting_frame = self.create_formatting_toolbar(parent, text_widget)
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
				self.textboxes.remove(text_widget)
				
		text_widget.frame.bind("<Button-3>", delete_textbox)
		text_widget.text_widget.bind("<Button-3>", delete_textbox)
		
		# Store reference
		self.textboxes.append(text_widget)
		
		self.creating_textbox = False
		self.selection_start = None
		self.current_page = None
		
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
		
		# Bold button
		bold_btn = ctk.CTkButton(
			formatting_frame,
			text="B",
			width=30,
			height=25,
			fg_color="#e0d0b0",
			hover_color="#d0c0a0",
			text_color="#3d2c1e",
			font=("Arial", 11, "bold"),
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
			font=("Arial", 11, "italic"),
			corner_radius=2,
			command=text_widget.toggle_italic
		)
		italic_btn.pack(side="left", padx=2, pady=5)
		
		# Font size dropdown
		font_sizes = ["8", "10", "11", "12", "14", "16", "18", "20", "24"]
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
			font=("Arial", 10),
			corner_radius=2,
			command=lambda size: text_widget.change_font_size(size)
		)
		font_size_menu.pack(side="left", padx=(2, 5), pady=5)
		
		return formatting_frame

	def clear_selection_rect(self):
		"""Clear the selection rectangle from canvases"""
		self.left_canvas.delete("selection")
		self.right_canvas.delete("selection")

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
		
		# File button with image import option
		file_btn = ctk.CTkButton(
			self.top_bar,
			text="Import Image",
			fg_color="transparent",
			hover_color="#e0d0b0",
			text_color="#5d4037",
			font=("Segoe UI", 11),
			width=100,
			height=25,
			corner_radius=3,
			border_width=1,
			border_color="#d4b98c",
			command=self.import_image_file
		)
		file_btn.pack(side="left", padx=(10, 5), pady=5)
		
		# Save button
		save_btn = ctk.CTkButton(
			self.top_bar,
			text="Save",
			fg_color="transparent",
			hover_color="#e0d0b0",
			text_color="#5d4037",
			font=("Segoe UI", 11),
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
		
	def import_image_file(self):
		"""Open file dialog to import image"""
		file_path = filedialog.askopenfilename(
			title="Select Image",
			filetypes=[
				("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
				("PNG files", "*.png"),
				("All files", "*.*")
			]
		)
		
		if file_path:
			# Place image in center of current view
			parent = self.left_page  # Default to left page
			x = parent.winfo_width() // 2 - 100
			y = parent.winfo_height() // 2 - 100
			
			self.create_image_widget(parent, x, y, file_path)
	
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
		
		# Sidebar header
		sidebar_header = ctk.CTkLabel(
			self.sidebar,
			text="Pages",
			font=("Segoe UI", 14, "bold"),
			text_color="#3d2c1e",
			height=40
		)
		sidebar_header.pack(fill="x", pady=(10, 0))
		
		# Empty page list
		self.page_list = ctk.CTkScrollableFrame(
			self.sidebar,
			fg_color="#b5a184",
			corner_radius=0
		)
		self.page_list.pack(fill="both", expand=True, padx=10, pady=10)
		
		# Empty label
		empty_label = ctk.CTkLabel(
			self.page_list,
			text="No pages yet",
			font=("Segoe UI", 12),
			text_color="#5d4c3e"
		)
		empty_label.pack(pady=20)
	
	def toggle_sidebar(self, event=None):
		if self.sidebar_visible:
			self.close_sidebar()
		else:
			self.open_sidebar()
	
	def open_sidebar(self):
		if not self.sidebar_visible:
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
		for textbox in self.textboxes:
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