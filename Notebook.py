import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import os
import sys
import pygame
import json
import base64
import pickle
import zlib
from datetime import datetime
import shutil
import uuid  # Added for proper widget IDs

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
    def __init__(self, parent, x, y, width, height, page_color="#c1a273", widget_id=None):
        self.parent = parent
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.page_color = page_color
        self.has_focus = False
        # Use UUID for permanent, portable widget IDs
        self.widget_id = widget_id or str(uuid.uuid4())
        
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
        
        # Store all created tags for serialization
        self.created_tags = set()
        

        
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
        
        # NEW: Bind focus events directly to the text widget
        self.text_widget.bind("<FocusIn>", self.on_focus_in)
        self.text_widget.bind("<FocusOut>", self.on_focus_out)
        
        # NEW: Clear placeholder on first click
        self.text_widget.bind("<Button-1>", self.clear_placeholder_on_first_click, add="+")
        
        # NEW: Track text selection
        self.text_widget.bind("<Button-1>", self.handle_text_selection, add="+")

    def clear_placeholder_on_first_click(self, event):
        """Clear placeholder text on first click"""
        if self.get_text() == "Click to edit...":
            self.set_text("")
            # Ensure cursor is at the beginning - use mark_set for Text widget
            self.text_widget.mark_set("insert", "1.0")
            self.text_widget.focus_set()

    def handle_text_selection(self, event):
        """Handle text selection - let tkinter handle it normally"""
        # Don't start drag when clicking in text widget
        self.is_dragging = False
        # Focus the text widget
        self.text_widget.focus_set()
        return "continue"  # Let tkinter continue with normal text selection
        
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
    
    def get_formatted_text(self):
        """Get text with formatting - ULTRA SIMPLE VERSION"""
        text_content = self.get_text()
        
        # Return empty if placeholder
        if not text_content or text_content == "Click to edit...":
            return {
                "content": "",
                "segments": []
            }
        
        # Use tkinter's built-in dump() method - it's designed for this!
        # This returns ALL formatting information in a structured way
        try:
            dump_data = self.text_widget.dump("1.0", "end-1c", tag=True, text=True)
            
            segments = []
            current_text = ""
            current_tags = []
            
            for item in dump_data:
                item_type = item[0]
                
                if item_type == "text":
                    # Text content
                    if current_text:
                        segments.append({
                            "text": current_text,
                            "tags": current_tags.copy()
                        })
                        current_text = ""
                        current_tags = []
                    
                    current_text = item[1]
                    
                elif item_type == "tagon":
                    # Tag starts here
                    tag = item[1]
                    if not tag.startswith("sel") and tag != "tk::anchor1":
                        current_tags.append(tag)
                        
                elif item_type == "tagoff":
                    # Tag ends here
                    tag = item[1]
                    if not tag.startswith("sel") and tag != "tk::anchor1":
                        # End this segment and start a new one
                        if current_text:
                            segments.append({
                                "text": current_text,
                                "tags": current_tags.copy()
                            })
                            current_text = ""
                            current_tags = []
            
            # Add the last segment
            if current_text:
                segments.append({
                    "text": current_text,
                    "tags": current_tags
                })
            
            return {
                "content": text_content,
                "segments": segments
            }
            
        except Exception as e:
            print(f"Error in get_formatted_text: {e}")
            # Fallback to plain text
            return {
                "content": text_content,
                "segments": [{"text": text_content, "tags": []}]
            }
    def set_text(self, text):
        """Set text content"""
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", text)
        
    def set_formatted_text(self, formatted_data):
        """Set text with formatting - FIXED for font sizes"""
        self.text_widget.delete("1.0", "end")
        
        if isinstance(formatted_data, dict) and "segments" in formatted_data:
            for segment in formatted_data["segments"]:
                if not segment["text"]:
                    continue
                    
                start_pos = self.text_widget.index("end-1c")
                if start_pos == "1.0":
                    start_pos = "1.0"
                
                # Insert text
                self.text_widget.insert(start_pos, segment["text"])
                end_pos = self.text_widget.index(f"{start_pos}+{len(segment['text'])}c")
                
                # Apply tags
                for tag_name in segment["tags"]:
                    # Ensure the tag exists
                    self._ensure_tag_exists(tag_name)
                    # Apply it
                    self.text_widget.tag_add(tag_name, start_pos, end_pos)
        else:
            # Plain text (backward compatibility)
            self.text_widget.insert("1.0", formatted_data)

    def _ensure_tag_exists(self, tag_name):
        """Make sure a tag exists, creating it if necessary"""
        if tag_name not in self.created_tags:
            # Parse and create the tag
            if tag_name.startswith("size"):
                # Font size tag like "size24_bold"
                self._create_font_size_tag(tag_name)
            else:
                # Unknown tag, create with defaults
                self.text_widget.tag_configure(tag_name, font=("Arial", 11))
            
            self.created_tags.add(tag_name)

    def _create_font_size_tag(self, tag_name):
        """Create a font size tag from its name - ONLY NORMAL STYLE"""
        try:
            parts = tag_name.split("_")
            size_str = parts[0][4:]  # Remove "size"
            size = int(size_str)
            
            # Determine font family - ALWAYS NORMAL STYLE
            font_family = "Adeliz" if HAS_CUSTOM_FONT else "Arial"
            
            # Create the tag with normal style only
            self.text_widget.tag_configure(tag_name, font=(font_family, size))
                
        except (ValueError, IndexError):
            # Fallback to default
            self.text_widget.tag_configure(tag_name, font=("Arial", 11))



    

            
    def change_font_size(self, size):
        """Change font size for selected text - WITHOUT BOLD/ITALIC"""
        try:
            size = int(size)
            sel_start = self.text_widget.index("sel.first")
            sel_end = self.text_widget.index("sel.last")
            
            # Determine font family
            if HAS_CUSTOM_FONT:
                font_family = "Adeliz"
            else:
                font_family = "Arial"
            
            # Always use normal style (no bold/italic)
            tag_name = f"size{size}_normal"
            
            # Remove existing font size tags (if any)
            for tag in list(self.created_tags):
                if tag.startswith("size"):
                    self.text_widget.tag_remove(tag, sel_start, sel_end)
            
            # Create the tag if it doesn't exist
            if tag_name not in self.text_widget.tag_names():
                self.text_widget.tag_configure(tag_name, font=(font_family, size))
                self.created_tags.add(tag_name)
            
            # Apply the tag
            self.text_widget.tag_add(tag_name, sel_start, sel_end)
            
        except tk.TclError:
            pass

    def serialize(self):
        """Serialize widget data for saving"""
        try:
            formatted_text = self.get_formatted_text()
        except Exception as e:
            print(f"Warning: Could not get formatted text for widget {self.widget_id}: {e}")
            # Fallback to plain text
            formatted_text = {
                "content": self.get_text(),
                "segments": [{
                    "text": self.get_text(),
                    "tags": []
                }]
            }
        
        return {
            "id": self.widget_id,
            "type": "text_widget",
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "text": formatted_text,
            "properties": {
                "page_color": self.page_color
            }
        }


class ImageWidget:
    """Canvas-based image that supports floating over text WITH RESIZE (locked aspect ratio)"""
    def __init__(self, canvas, x, y, image_path, widget_id=None, width=None, height=None):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.image_path = image_path
        self.widget_id = widget_id or str(uuid.uuid4())
        self.is_dragging = False
        self.is_resizing = False
        self.has_focus = False
        self.parent_page = None
        
        # Load image
        self.original_image = Image.open(image_path)
        self.original_width, self.original_height = self.original_image.size
        
        # Store original aspect ratio
        self.aspect_ratio = self.original_height / self.original_width
        
        # Use provided dimensions or calculate scaled size
        if width is not None and height is not None:
            self.width = width
            self.height = height
            # Ensure aspect ratio matches if both dimensions provided
            if abs((height / width) - self.aspect_ratio) > 0.01:  # Allow small floating point differences
                # Recalculate height based on width to maintain aspect ratio
                self.height = int(width * self.aspect_ratio)
        else:
            # Default scaling: 40% of canvas width, maintain aspect ratio
            canvas_width = self.canvas.winfo_width() if self.canvas.winfo_exists() else 800
            max_width = int(canvas_width * 0.4)
            
            # Calculate height to maintain aspect ratio
            self.width = min(self.original_width, max_width)
            self.height = int(self.width * self.aspect_ratio)
            
            # Also limit height (60% of canvas height)
            max_height = int(canvas_width * 0.6)  # canvas is square-ish
            if self.height > max_height:
                self.height = max_height
                self.width = int(self.height / self.aspect_ratio)
        
        # Minimum size
        self.min_width = 50
        self.min_height = int(self.min_width * self.aspect_ratio)
        
        # Resize image for display
        if (self.width, self.height) != (self.original_width, self.original_height):
            self.display_image = self.original_image.resize((self.width, self.height), Image.Resampling.LANCZOS)
        else:
            self.display_image = self.original_image.copy()
        
        self.tk_image = ImageTk.PhotoImage(self.display_image)
        self.image_id = self.canvas.create_image(x, y, image=self.tk_image, anchor="nw")
        
        # Create selection border (invisible until selected)
        self.border_id = self.canvas.create_rectangle(
            x, y, x + self.width, y + self.height,
            outline="",  # Empty by default
            width=2,
            tags="border"
        )
        
        # Create resize handle (bottom-right corner)
        self.resize_handle_size = 12
        self.resize_handle_id = self.canvas.create_oval(
            x + self.width - self.resize_handle_size,
            y + self.height - self.resize_handle_size,
            x + self.width,
            y + self.height,
            fill="",  # Empty by default
            outline="",
            tags="resize_handle"
        )
        
        # Bind events
        self.setup_event_bindings()
        
    def setup_event_bindings(self):
        """Setup event bindings for the image"""
        # Click on image to select/focus
        self.canvas.tag_bind(self.image_id, "<Button-1>", self.on_image_click)
        self.canvas.tag_bind(self.border_id, "<Button-1>", self.on_image_click)
        
        # Drag image
        self.canvas.tag_bind(self.image_id, "<B1-Motion>", self.do_drag)
        self.canvas.tag_bind(self.image_id, "<ButtonRelease-1>", self.stop_drag)
        
        # Resize handle events
        self.canvas.tag_bind(self.resize_handle_id, "<Button-1>", self.start_resize)
        self.canvas.tag_bind(self.resize_handle_id, "<B1-Motion>", self.do_resize)
        self.canvas.tag_bind(self.resize_handle_id, "<ButtonRelease-1>", self.stop_resize)
        
        # Right-click to delete
        self.canvas.tag_bind(self.image_id, "<Button-3>", self.delete)
        self.canvas.tag_bind(self.border_id, "<Button-3>", self.delete)
        self.canvas.tag_bind(self.resize_handle_id, "<Button-3>", self.delete)
        
        # Change cursor when over resize handle
        self.canvas.tag_bind(self.resize_handle_id, "<Enter>", 
                           lambda e: self.canvas.configure(cursor="sizing"))
        self.canvas.tag_bind(self.resize_handle_id, "<Leave>", 
                           lambda e: self.canvas.configure(cursor=""))
        
        # Show resize handle on hover when image is focused
        self.canvas.tag_bind(self.image_id, "<Enter>", self.show_handles_on_hover)
        self.canvas.tag_bind(self.image_id, "<Leave>", self.hide_handles_on_hover)
    
    def show_handles_on_hover(self, event=None):
        """Show resize handle when hovering over image (if focused)"""
        if self.has_focus:
            self.canvas.itemconfig(self.resize_handle_id, fill="#5d4037", outline="#3d2c1e")
    
    def hide_handles_on_hover(self, event=None):
        """Hide resize handle when not hovering (if not focused)"""
        if not self.has_focus:
            self.canvas.itemconfig(self.resize_handle_id, fill="", outline="")
    def on_image_click(self, event):
        """Handle click on image - select it"""
        # If another image is focused, unfocus it first
        if hasattr(self.canvas, 'focused_image') and self.canvas.focused_image:
            if self.canvas.focused_image != self:
                self.canvas.focused_image.unfocus()
        
        self.focus()
        self.start_drag(event)
    
    def focus(self):
        """Focus on this image widget"""
        # Remove focus from other images
        if hasattr(self.canvas, 'focused_image') and self.canvas.focused_image:
            self.canvas.focused_image.unfocus()
        
        # Focus this image
        self.has_focus = True
        self.canvas.focused_image = self
        
        # Show border and resize handle
        self.canvas.itemconfig(self.border_id, outline="#5d4037", fill="")
        self.canvas.itemconfig(self.resize_handle_id, fill="#5d4037", outline="#3d2c1e")
        
        # Raise above other canvas items
        self.canvas.tag_raise(self.image_id)
        self.canvas.tag_raise(self.border_id)
        self.canvas.tag_raise(self.resize_handle_id)
    
    def unfocus(self):
        """Remove focus from this image"""
        self.has_focus = False
        self.canvas.itemconfig(self.border_id, outline="", fill="")
        self.canvas.itemconfig(self.resize_handle_id, fill="", outline="")
    
    def start_drag(self, event):
        """Start dragging the image"""
        if not self.has_focus:
            self.focus()
        
        self.is_dragging = True
        self.is_resizing = False
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        # Change cursor
        self.canvas.configure(cursor="fleur" if sys.platform != "darwin" else "hand2")
    
    def do_drag(self, event):
        """Drag the image"""
        if not self.is_dragging:
            return
        
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        
        # Move all image components
        self.canvas.move(self.image_id, dx, dy)
        self.canvas.move(self.border_id, dx, dy)
        self.canvas.move(self.resize_handle_id, dx, dy)
        
        # Update position
        self.x += dx
        self.y += dy
        
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def stop_drag(self, event):
        """Stop dragging"""
        self.is_dragging = False
        self.canvas.configure(cursor="")
    
    def start_resize(self, event):
        """Start resizing the image"""
        if not self.has_focus:
            self.focus()
        
        self.is_resizing = True
        self.is_dragging = False
        self.resize_start_x = event.x
        self.resize_start_y = event.y
        self.resize_start_width = self.width
        self.resize_start_height = self.height
    
    def do_resize(self, event):
        """Resize the image - ALWAYS MAINTAIN ASPECT RATIO"""
        if not self.is_resizing:
            return
        
        dx = event.x - self.resize_start_x
        dy = event.y - self.resize_start_y
        
        # Calculate new width based on mouse movement
        # Use the larger of dx or dy to determine scale (so diagonal dragging works)
        if abs(dx) > abs(dy):
            # Scale based on width change
            new_width = max(self.min_width, self.resize_start_width + dx)
            new_height = int(new_width * self.aspect_ratio)
        else:
            # Scale based on height change
            new_height = max(self.min_height, self.resize_start_height + dy)
            new_width = int(new_height / self.aspect_ratio)
        
        # Ensure minimum size in both dimensions
        if new_width < self.min_width:
            new_width = self.min_width
            new_height = int(new_width * self.aspect_ratio)
        elif new_height < self.min_height:
            new_height = self.min_height
            new_width = int(new_height / self.aspect_ratio)
        
        # Only resize if dimensions changed
        if new_width != self.width or new_height != self.height:
            self.width = new_width
            self.height = new_height
            
            # Resize the image
            self.display_image = self.original_image.resize(
                (self.width, self.height), 
                Image.Resampling.LANCZOS
            )
            
            # Update tkinter image
            self.tk_image = ImageTk.PhotoImage(self.display_image)
            self.canvas.itemconfig(self.image_id, image=self.tk_image)
            
            # Update border and resize handle positions
            self.canvas.coords(
                self.border_id,
                self.x, self.y,
                self.x + self.width, self.y + self.height
            )
            
            self.canvas.coords(
                self.resize_handle_id,
                self.x + self.width - self.resize_handle_size,
                self.y + self.height - self.resize_handle_size,
                self.x + self.width,
                self.y + self.height
            )
    
    def stop_resize(self, event):
        """Stop resizing"""
        self.is_resizing = False
        self.canvas.configure(cursor="")
    
    def delete(self, event=None):
        """Delete the image"""
        # Remove from parent page's images list
        if self.parent_page and self in self.parent_page.images:
            self.parent_page.images.remove(self)
        
        # Then delete from canvas
        self.canvas.delete(self.image_id)
        self.canvas.delete(self.border_id)
        self.canvas.delete(self.resize_handle_id)
        
        # Clean up resources
        self.original_image.close()
        if hasattr(self, 'display_image'):
            self.display_image.close()
        del self.tk_image

    def serialize(self):
        """Serialize image data for saving"""
        return {
            "id": self.widget_id,
            "type": "image_widget",
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "image_path": self.image_path,
            "properties": {}
        }

# Page class
class Page:
    """Represents a single page in the notebook"""
    def __init__(self, parent, is_left_page, page_number, name=None):
        self.parent = parent
        self.is_left_page = is_left_page
        self.page_number = page_number
        self.name = name or f"Page {page_number + 1}"  # Default name
        
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
            highlightthickness=0
        )
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        ##self.try_load_background()
        self.canvas.configure(bg="#c1a273")
        
        # Store widgets on this page
        self.textboxes = []  # FormattedTextWidget objects
        self.images = []     # ImageWidget objects
    
    def set_name(self, name):
        """Set the page name"""
        self.name = name
        
    def get_display_text(self):
        """Get display text for buttons/labels"""
        return f"{self.page_number + 1}. {self.name}"
    
    def show(self):
        """Show this page"""
        if self.is_left_page:
            self.frame.place(relx=0, rely=0, relwidth=0.5, relheight=1.0)
        else:
            self.frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1.0)
    
    def hide(self):
        """Hide this page"""
        self.frame.place_forget()
    
    def add_textbox(self, x, y, width, height, widget_id=None):
        """Add a textbox to this page"""
        textbox = FormattedTextWidget(self.frame, x, y, width, height, page_color="#c1a273", widget_id=widget_id)
        self.textboxes.append(textbox)
        return textbox
    
    def add_image(self, x, y, image_path, widget_id=None, width=None, height=None):
        """Add an image to this page"""
        image_widget = ImageWidget(self.canvas, x, y, image_path, widget_id=widget_id, width=width, height=height)
        # Set the parent page reference
        image_widget.parent_page = self
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
            # Clean up image resources
            if hasattr(image, 'original_image'):
                image.original_image.close()
            if hasattr(image, 'tk_image'):
                del image.tk_image
        self.images.clear()
    def try_load_background(self):
        """Try to load background.png as page background"""
        bg_paths = [
            "background.png",  # Current dir
            os.path.join(os.path.dirname(__file__), "background.png"),  # App dir
        ]
        
        # Also check notebook directory if we have a current file
        app = self.get_app()
        if app and hasattr(app, 'current_file') and app.current_file:
            notebook_dir = os.path.dirname(app.current_file)
            bg_paths.insert(0, os.path.join(notebook_dir, "background.png"))
        
        for bg_path in bg_paths:
            if os.path.exists(bg_path):
                try:
                    self.bg_image = Image.open(bg_path)
                    # Schedule background application after canvas is sized
                    self.canvas.after(100, self.apply_background)
                    break
                except:
                    continue
        
        # If no image found, use default color
        if not hasattr(self, 'bg_image') or self.bg_image is None:
            self.canvas.configure(bg="#c1a273")

    def get_app(self):
        """Get reference to main app instance"""
        parent = self.parent
        while parent and not hasattr(parent, 'current_file'):
            parent = parent.master
        return parent

    def apply_background(self):
        """Apply the background image - handles 2-page spreads!"""
        if not hasattr(self, 'bg_image'):
            return
        
        try:
            # Get canvas size
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            # If canvas isn't ready yet, try again
            if width < 10 or height < 10:
                self.canvas.after(100, self.apply_background)
                return
            
            # Check if this is a 2-page spread background
            bg_width, bg_height = self.bg_image.size
            
            if bg_width >= 1920 and bg_height >= 1080:
                # This looks like a full-window background!
                # Calculate which half to show based on page position
                
                if self.is_left_page:
                    # Left page: show left half of image
                    crop_box = (0, 0, bg_width // 2, bg_height)
                else:
                    # Right page: show right half of image
                    crop_box = (bg_width // 2, 0, bg_width, bg_height)
                
                # Crop and resize
                cropped = self.bg_image.crop(crop_box)
                resized = cropped.resize((width, height), Image.Resampling.LANCZOS)
            else:
                # Normal single-page background - just resize
                resized = self.bg_image.resize((width, height), Image.Resampling.LANCZOS)
            
            self.bg_photo = ImageTk.PhotoImage(resized)
            
            # Create or update background
            if hasattr(self, 'bg_id'):
                self.canvas.itemconfig(self.bg_id, image=self.bg_photo)
            else:
                self.bg_id = self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
                self.canvas.tag_lower(self.bg_id)
                
        except Exception as e:
            print(f"Failed to apply background: {e}")
            # Fallback to color
            self.canvas.configure(bg="#c1a273")
    def serialize(self):
        """Serialize page data for saving"""
        return {
            "page_number": self.page_number,
            "name": self.name,
            "is_left_page": self.is_left_page,
            "textboxes": [tb.serialize() for tb in self.textboxes],
            "images": [img.serialize() for img in self.images]
        }
    
    def deserialize(self, data, notebook_app):
        """Restore page from serialized data"""
        # Clear existing widgets
        self.clear()
        
        # Set page name
        self.name = data.get("name", f"Page {self.page_number + 1}")
        
        # Restore textboxes
        for textbox_data in data.get("textboxes", []):
            textbox = self.add_textbox(
                x=textbox_data["x"],
                y=textbox_data["y"],
                width=textbox_data["width"],
                height=textbox_data["height"],
                widget_id=textbox_data.get("id")
            )
            
            # Set formatted text
            textbox.set_formatted_text(textbox_data["text"])
            
            # Create formatting toolbar
            formatting_frame = notebook_app.create_formatting_toolbar(self.frame, textbox)
            textbox.formatting_frame = formatting_frame
            
            # Setup focus behavior
            def on_focus_in(e, tb=textbox):
                tb.on_focus_in()
                formatting_frame.place(x=tb.x, y=tb.y-40)
                
            def on_focus_out(e, tb=textbox):
                tb.on_focus_out()
                formatting_frame.place_forget()
                
            textbox.text_widget.bind("<FocusIn>", on_focus_in)
            textbox.text_widget.bind("<FocusOut>", on_focus_out)
            
            # Clear placeholder on focus
            def clear_placeholder(e, tb=textbox):
                if tb.get_text() == "Click to edit...":
                    tb.set_text("")
                    
            textbox.text_widget.bind("<FocusIn>", clear_placeholder, add="+")
            
            # Add delete on right-click
            def delete_textbox(event, tb=textbox):
                if event.num == 3:  # Right click
                    tb.frame.destroy()
                    formatting_frame.destroy()
                    self.textboxes.remove(tb)
                    
            textbox.frame.bind("<Button-3>", delete_textbox)
            textbox.text_widget.bind("<Button-3>", delete_textbox)
        
        # Restore images
        for image_data in data.get("images", []):
            # Check if image file exists
            image_path = image_data["image_path"]
            if not os.path.exists(image_path):
                # Try to find in same directory as notebook file
                if hasattr(notebook_app, 'current_file'):
                    notebook_dir = os.path.dirname(notebook_app.current_file)
                    alt_path = os.path.join(notebook_dir, os.path.basename(image_path))
                    if os.path.exists(alt_path):
                        image_path = alt_path
                    else:
                        # Image not found, skip
                        print(f"Warning: Image not found: {image_data['image_path']}")
                        continue
            
            image_widget = self.add_image(
                x=image_data["x"],
                y=image_data["y"],
                image_path=image_path,
                widget_id=image_data.get("id"),
                width=image_data["width"],
                height=image_data["height"]
            )
            
            # IMPORTANT: Set the parent_page reference
            image_widget.parent_page = self


# PageCornerButton and SoundPlayer classes remain the same...
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
        self.root.title("Notebook App Version 0.9")
        
        self.setup_sidebar_close_binding()

        # Set max size to 1920x1080
        self.root.maxsize(1920, 1080)
        self.root.state('zoomed')
        self.root.configure(background="#c1a273")
        
        # Save/Load state
        self.current_file = None
        self.modified = False
        
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
        # Add focus mode state
        self.focus_mode = False  # False = normal two-page view, True = single page focused
        self.focused_page_index = None  # Which page is currently focused        
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
        
        # Create top bar FIRST
        self.create_top_bar()
        self.top_bar.place_forget()
        self.setup_keyboard_shortcuts()
        # Initialize pages AFTER creating top bar
        self.initialize_pages()
        
        # Bind text box creation events
        self.setup_textbox_creation()
        # NEW: Setup global click handler
        self.setup_global_click_handler()
        # Setup image drag and drop
        self.setup_image_drag_drop()
        
        # Setup clipboard paste
        self.setup_clipboard_paste()
        
        # Create seam (must be after pages are initialized)
        self.create_seam()
        
        # Sidebar for page selector
        self.sidebar = None
        
        # Bind mouse movement to show/hide bar
        self.setup_top_bar_behavior()
        
        # Create sidebar
        self.create_sidebar()
    
        # Initialize page name editor
        self.page_name_editor = None
        
        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Bind for modifications
        self.setup_modification_tracking()

    def setup_modification_tracking(self):
        """Setup tracking for modifications"""
        # Track text changes
        def on_text_change(event):
            self.set_modified(True)
        self.root.bind_all('<<Modified>>', on_text_change)
        
        # Track other modifications
        self.modified_callbacks = []

    def set_modified(self, modified=True):
        """Set modified flag and update window title"""
        if self.modified != modified:
            self.modified = modified
            self.update_window_title()
            
    def update_window_title(self):
        """Update window title with file name and modified status"""
        title = "Notebook App Version 1.0"
        if self.current_file:
            filename = os.path.basename(self.current_file)
            title = f"{filename} - Notebook App v1.0"
            if self.modified:
                title = f"*{title}"
        self.root.title(title)

    def on_closing(self):
        """Handle window closing"""
        if self.modified:
            response = messagebox.askyesnocancel(
                "Save Changes",
                "Do you want to save changes before closing?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                if not self.save_notebook():
                    return  # Save was cancelled
        
        # Clean up resources
        self.cleanup_resources()
        self.root.destroy()
    def setup_top_bar_behavior(self):
        """Setup top bar show/hide behavior"""
        # Remove the existing motion binding
        self.root.unbind("<Motion>")
        
        # New approach: Show top bar when mouse is at top, hide when mouse moves down
        def check_mouse_for_top_bar(event):
            # Always show if mouse is at very top (15 pixels)
            if event.y < 15:
                if not self.top_bar_visible:
                    self.show_top_bar()
            # Hide if mouse is below 70 pixels AND top bar is visible
            elif self.top_bar_visible and event.y > 70:
                # But only hide if not over sidebar
                if not (self.sidebar_visible and event.x < 250):
                    self.hide_top_bar()
        
        # Bind to root window (catches ALL mouse movements)
        self.root.bind("<Motion>", check_mouse_for_top_bar)
        
        # Also bind to all canvases to ensure events bubble up
        for page in self.pages:
            page.canvas.bind("<Motion>", check_mouse_for_top_bar)
    def cleanup_resources(self):
        """Clean up resources before closing"""
        try:
            if hasattr(self, 'sound_player') and self.sound_player.sound_loaded:
                pygame.mixer.quit()
        except:
            pass
        
        # Clear all pages
        for page in self.pages:
            page.clear()
            page.frame.destroy()

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
        # Update top bar with initial page names
        self.update_top_bar_page_name()
    def setup_font_size_scroll(self, text_widget, display_widget):
        """Setup mouse wheel scrolling for font size"""
        # Store references
        self.current_text_widget_for_scroll = text_widget
        self.current_font_size_display = display_widget
        
        # Bind mouse wheel events
        display_widget.bind("<MouseWheel>", self.on_font_size_scroll)
        display_widget.bind("<Button-4>", self.on_font_size_scroll)  # Linux up
        display_widget.bind("<Button-5>", self.on_font_size_scroll)  # Linux down
        
        # Change cursor to indicate scrollability
        display_widget.configure(cursor="sb_v_double_arrow")

    def cleanup_font_size_scroll(self):
        """Clean up mouse wheel bindings"""
        if hasattr(self, 'current_font_size_display') and self.current_font_size_display:
            self.current_font_size_display.unbind("<MouseWheel>")
            self.current_font_size_display.unbind("<Button-4>")
            self.current_font_size_display.unbind("<Button-5>")
            self.current_font_size_display.configure(cursor="")


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
            self.set_modified(True)
            return "break"  # Prevent default paste
        except tk.TclError:
            # Nothing in clipboard, ignore
            pass
    
    def setup_textbox_creation(self):
        """Set up event bindings for creating text boxes"""
        # We'll bind to the current page canvases dynamically
        pass

    def setup_global_click_handler(self):
        """Setup a global click handler for the entire app"""
        # Bind to root window for clicks outside text widgets
        self.root.bind("<Button-1>", self.handle_global_click)

    def handle_global_click(self, event):
        """Handle clicks anywhere in the application"""
        # Get the widget that was clicked
        clicked_widget = event.widget
        
        # Check if click was on a text widget or its components
        is_text_component = False
        
        for page in self.pages:
            for textbox in page.textboxes:
                # Check all components of the textbox
                components = [
                    textbox.text_widget,
                    textbox.frame,
                    textbox.handles_frame if hasattr(textbox, 'handles_frame') else None,
                    textbox.move_handle if hasattr(textbox, 'move_handle') else None,
                    textbox.resize_handle if hasattr(textbox, 'resize_handle') else None
                ]
                
                for component in components:
                    if component and clicked_widget == component:
                        is_text_component = True
                        break
                
                if is_text_component:
                    break
            
            if is_text_component:
                break
        
        # If click was NOT on a text component, remove focus from all textboxes
        if not is_text_component:
            self.remove_textbox_focus(event)
        
        # Check for sidebar clicks
        self.check_click_outside_sidebar(event)
        
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
    
    def create_text_widget(self, page, x, y, text="", width=200, height=100):
        """Create a text widget on a specific page"""
        text_widget = page.add_textbox(x, y, width, height)
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
                self.set_modified(True)
                
        text_widget.frame.bind("<Button-3>", delete_textbox)
        text_widget.text_widget.bind("<Button-3>", delete_textbox)
        
        # Track modifications
        def track_modification(event=None):
            self.set_modified(True)
            
        text_widget.text_widget.bind("<KeyRelease>", track_modification)
        text_widget.frame.bind("<Configure>", track_modification)
        
        # Bind textbox creation events to this page's canvas
        self.setup_page_canvas_events(page)
        
        self.set_modified(True)
        return text_widget
    def on_font_size_scroll(self, event, text_widget):
        """Handle mouse wheel scrolling for font size"""
        # Determine scroll direction
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):  # Scroll up
            delta = 1
        elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):  # Scroll down
            delta = -1
        else:
            return
        
        # Get current font size
        try:
            current_size = int(self.font_size_var.get())
        except:
            current_size = 45
        
        # Calculate new size (1-100 range)
        new_size = current_size + delta
        new_size = max(1, min(100, new_size))
        
        # Update display
        self.font_size_var.set(str(new_size))
        
        # Check if text is selected
        try:
            sel_start = text_widget.text_widget.index("sel.first")
            sel_end = text_widget.text_widget.index("sel.last")
            has_selection = True
        except tk.TclError:
            has_selection = False
        
        if has_selection:
            # Apply to selected text
            text_widget.change_font_size(new_size)
            self.set_modified(True)
        else:
            # No selection - set as default for new text
            if hasattr(text_widget, 'default_font_size'):
                text_widget.default_font_size = new_size
        
        # Visual feedback on the display
        original_color = text_widget.font_size_display.cget("fg_color")
        text_widget.font_size_display.configure(fg_color="#d0c0a0")  # Highlight
        text_widget.font_size_display.after(100, lambda: text_widget.font_size_display.configure(fg_color=original_color))
        
        return "break"
    
    def reset_font_size(self, text_widget):
        """Reset font size to default (11)"""
        DEFAULT_SIZE = 45
        
        # Update the display
        self.font_size_var.set(str(DEFAULT_SIZE))
        
        # Check if text is selected
        try:
            sel_start = text_widget.text_widget.index("sel.first")
            sel_end = text_widget.text_widget.index("sel.last")
            has_selection = True
        except tk.TclError:
            has_selection = False
        
        if has_selection:
            # Apply reset to selected text only
            text_widget.change_font_size(DEFAULT_SIZE)
        else:
            # No selection - reset ALL text in the widget
            # Remove all font size tags
            for tag in list(text_widget.created_tags):
                if tag.startswith("size"):
                    text_widget.text_widget.tag_remove(tag, "1.0", "end")
            
            # Apply default size to entire widget
            text_widget.change_font_size(DEFAULT_SIZE)
        
        self.set_modified(True)
        
        # Visual feedback
        original_color = text_widget.reset_button.cget("fg_color")
        text_widget.reset_button.configure(fg_color="#3d2c1e", text_color="#f5e8c8")
        text_widget.reset_button.after(200, lambda: text_widget.reset_button.configure(
            fg_color=original_color, 
            text_color="#3d2c1e"
        ))
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
        
        # NEW: Handle single click to remove focus from images/textboxes
        def on_canvas_click(event):
            # Only handle clicks directly on canvas (not on images)
            items = canvas.find_overlapping(event.x, event.y, event.x+1, event.y+1)
            
            # Check if click is directly on canvas (no items at that position)
            if not items:
                self.remove_textbox_focus(event)
                self.remove_image_focus()
            else:
                # Click is on an item - let the image handle it
                pass
        
        canvas.bind("<Button-1>", on_canvas_click)
    def remove_image_focus(self, event=None):
        """Remove focus from all images"""
        for page in self.pages:
            for image in page.images:
                if hasattr(image, 'has_focus') and image.has_focus:
                    image.unfocus()
            
            # Clear canvas focus reference
            if hasattr(page.canvas, 'focused_image'):
                page.canvas.focused_image = None
        
        # Also reset cursor
        if event and hasattr(event, 'widget'):
            if isinstance(event.widget, tk.Canvas):
                event.widget.configure(cursor="") 
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

        width = max(100, width)
        height = max(60, height)

        x = min(start_x, end_x)
        y = min(start_y, end_y)

        # Create text widget
        self.create_text_widget(page, x, y, width=width, height=height)
        
        # Clear selection
        canvas = page.canvas
        canvas.delete("selection")
        
        self.creating_textbox = False
        self.selection_start = None
        self.current_page = None
    
    def clear_selection_rect(self, canvas):
        """Clear the selection rectangle from a canvas"""
        canvas.delete("selection")
    
    def remove_textbox_focus(self, event=None):
        """Remove focus from all textboxes"""
        # Hide formatting toolbar for all textboxes
        for page in self.pages:
            for textbox in page.textboxes:
                if hasattr(textbox, 'formatting_frame') and textbox.formatting_frame.winfo_ismapped():
                    textbox.formatting_frame.place_forget()
                if hasattr(textbox, 'has_focus') and textbox.has_focus:
                    textbox.on_focus_out()
        
        # Set focus to root window to ensure all text widgets lose focus
        self.root.focus_set()
        
        # Update mouse cursor
        if event and hasattr(event, 'widget'):
            event.widget.configure(cursor="")
    
    def create_formatting_toolbar(self, parent, text_widget):
        """Create formatting toolbar for a text widget"""
        formatting_frame = ctk.CTkFrame(
            parent,
            fg_color="#f5e8c8",
            width=140,  # Increased from 120 to fit reset button
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
        
        # Font size control frame (contains display + reset button)
        font_size_frame = ctk.CTkFrame(
            formatting_frame,
            fg_color="transparent",
            width=85,  # Width for both elements
            height=25
        )
        font_size_frame.pack_propagate(False)
        font_size_frame.pack(side="left", padx=(2, 5), pady=5)
        
        # Font size display (scrollable)
        self.font_size_var = ctk.StringVar(value="45")  # Default font size
        
        font_size_display = ctk.CTkLabel(
            font_size_frame,
            textvariable=self.font_size_var,
            width=50,
            height=25,
            fg_color="#e0d0b0",
            text_color="#3d2c1e",
            font=("Arial", 10),
            corner_radius=2,
            anchor="center"
        )
        font_size_display.pack(side="left", padx=(0, 2))
        
        # Reset button (↺ symbol)
        reset_btn = ctk.CTkButton(
            font_size_frame,
            text="↺",  # Reset symbol
            width=25,
            height=25,
            fg_color="#a08c6e",
            hover_color="#8c704c",
            text_color="#3d2c1e",
            font=("Arial", 12, "bold"),
            corner_radius=2,
            command=lambda: self.reset_font_size(text_widget)
        )
        reset_btn.pack(side="left")
        
        # Bind mouse wheel events to the display label
        def setup_scroll_bindings():
            font_size_display.bind("<MouseWheel>", lambda e, tw=text_widget: self.on_font_size_scroll(e, tw))
            font_size_display.bind("<Button-4>", lambda e, tw=text_widget: self.on_font_size_scroll(e, tw))  # Linux up
            font_size_display.bind("<Button-5>", lambda e, tw=text_widget: self.on_font_size_scroll(e, tw))  # Linux down
            font_size_display.configure(cursor="sb_v_double_arrow")
        
        def cleanup_scroll_bindings():
            font_size_display.unbind("<MouseWheel>")
            font_size_display.unbind("<Button-4>")
            font_size_display.unbind("<Button-5>")
            font_size_display.configure(cursor="")
        
        font_size_display.bind("<Enter>", lambda e: setup_scroll_bindings())
        font_size_display.bind("<Leave>", lambda e: cleanup_scroll_bindings())
        
        # Store references
        text_widget.font_size_display = font_size_display
        text_widget.reset_button = reset_btn
        
        return formatting_frame

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
        
        # Update top bar name display
        self.update_top_bar_page_name()
    
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
            
            # Update top bar name display
            self.update_top_bar_page_name()
    
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

        # Update sidebar to show new pages
        self.update_sidebar_page_list()
        self.set_modified(True)
    
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
        
        # PAGE NAME DISPLAY (clickable to edit) - CENTER
        # Create a frame for the page name display
        page_name_frame = ctk.CTkFrame(
            self.top_bar,
            fg_color="transparent",
            height=25,
            corner_radius=3
        )
        page_name_frame.pack(side="left", padx=(20, 0), pady=5)
        
        # Get current page display text
        left_page = self.get_current_left_page()
        right_page = self.get_current_right_page()
        display_text = ""
        if left_page and right_page:
            display_text = f"{left_page.get_display_text()} | {right_page.get_display_text()}"
        elif left_page:
            display_text = left_page.get_display_text()
        elif right_page:
            display_text = right_page.get_display_text()
        
        # Create clickable page name label
        self.page_name_label = ctk.CTkLabel(
            page_name_frame,
            text=display_text,
            text_color="#5d4037",
            font=topbar_font,
            cursor="hand2"
        )
        self.page_name_label.pack()
        
        # Bind click event to edit page name
        self.page_name_label.bind("<Button-1>", self.start_page_name_edit)
        
        # Spacer between page name and other buttons
        spacer1 = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        spacer1.pack(side="left", fill="x", expand=True)
        
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
            command=self.import_image_with_page_chooser  # Changed to new method
        )
        file_btn.pack(side="left", padx=(10, 5), pady=5)
        focus_btn = ctk.CTkButton(
            self.top_bar,
            text="Focus",
            fg_color="transparent",
            hover_color="#e0d0b0",
            text_color="#5d4037",
            font=topbar_font,
            width=60,
            height=25,
            corner_radius=3,
            border_width=1,
            border_color="#d4b98c",
            command=self.toggle_focus_mode
        )
        focus_btn.pack(side="left", padx=5, pady=5)       
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
            border_color="#d4b98c",
            command=self.save_notebook
        )
        save_btn.pack(side="left", padx=5, pady=5)
        
        # Load button
        load_btn = ctk.CTkButton(
            self.top_bar,
            text="Load",
            fg_color="transparent",
            hover_color="#e0d0b0",
            text_color="#5d4037",
            font=topbar_font,
            width=60,
            height=25,
            corner_radius=3,
            border_width=1,
            border_color="#d4b98c",
            command=self.load_notebook
        )
        load_btn.pack(side="left", padx=5, pady=5)
        
        # New button
        new_btn = ctk.CTkButton(
            self.top_bar,
            text="New",
            fg_color="transparent",
            hover_color="#e0d0b0",
            text_color="#5d4037",
            font=topbar_font,
            width=60,
            height=25,
            corner_radius=3,
            border_width=1,
            border_color="#d4b98c",
            command=self.new_notebook
        )
        new_btn.pack(side="left", padx=5, pady=5)
        
        # Spacer
        spacer = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        spacer.pack(side="left", fill="x", expand=True)
        
    def start_page_name_edit(self, event):
        """Start editing the page name - detect which page was clicked"""
        # Hide the label
        self.page_name_label.pack_forget()
        
        # Create entry widget for editing
        page_name_frame = self.page_name_label.master
        
        # Get current pages
        left_page = self.get_current_left_page()
        right_page = self.get_current_right_page()
        
        # Determine which page was clicked based on mouse position
        label_width = self.page_name_label.winfo_width()
        click_x = event.x
        
        # If we have both pages, check which part was clicked
        if left_page and right_page:
            # Rough estimate: left half = left page, right half = right page
            if click_x < label_width / 2:
                current_page = left_page
            else:
                current_page = right_page
        else:
            # Only one page visible
            current_page = left_page if left_page else right_page
        
        if not current_page:
            return
            
        # Create entry with current name
        self.page_name_entry = ctk.CTkEntry(
            page_name_frame,
            fg_color="#f5e8c8",
            text_color="#5d4037",
            border_color="#d4b98c",
            font=("Adeliz", 24) if HAS_CUSTOM_FONT else ("Segoe UI", 24),
            width=300,
            height=25
        )
        self.page_name_entry.pack()
        self.page_name_entry.insert(0, current_page.name)
        self.page_name_entry.select_range(0, tk.END)
        self.page_name_entry.focus()
        
        # Bind Enter key to save
        self.page_name_entry.bind("<Return>", lambda e: self.save_page_name(current_page))
        # Bind Escape key to cancel
        self.page_name_entry.bind("<Escape>", self.cancel_page_name_edit)
        # Bind focus out to save
        self.page_name_entry.bind("<FocusOut>", lambda e: self.save_page_name(current_page))
        
        # Store which page we're editing
        self.editing_page = current_page
        
    def save_page_name(self, page):
        """Save the edited page name"""
        if not hasattr(self, 'page_name_entry'):
            return
            
        new_name = self.page_name_entry.get().strip()
        if new_name:
            page.set_name(new_name)
            self.set_modified(True)
            
            # Update top bar display
            self.update_top_bar_page_name()
            
            # Update sidebar
            self.update_sidebar_page_list()
        
        # Clean up
        self.cancel_page_name_edit()
        
    def cancel_page_name_edit(self, event=None):
        """Cancel page name editing"""
        if hasattr(self, 'page_name_entry'):
            self.page_name_entry.destroy()
            del self.page_name_entry
            
        if hasattr(self, 'editing_page'):
            del self.editing_page
            
        # Show the label again
        self.page_name_label.pack()
    def toggle_focus_mode(self, page_index=None):
        """Toggle between normal view and focused single-page view"""
        if self.focus_mode:
            # Exit focus mode - return to normal two-page view
            self.exit_focus_mode()
        else:
            # Enter focus mode - focus on specified page or current left page
            if page_index is None:
                # Focus on current left page by default
                page_to_focus = self.current_left_page_index
            else:
                page_to_focus = page_index
            self.enter_focus_mode(page_to_focus)

    def enter_focus_mode(self, page_index):
        """Enter single-page focus mode on a specific page"""
        if page_index >= len(self.pages):
            return
        
        self.focus_mode = True
        self.focused_page_index = page_index
        self.previous_left_index = self.current_left_page_index
        self.previous_right_index = self.current_right_page_index
        
        focused_page = self.pages[page_index]
        
        # Store original placement
        if not hasattr(focused_page, 'original_placement'):
            focused_page.original_placement = {
                'relx': 0 if focused_page.is_left_page else 0.5,
                'rely': 0,
                'relwidth': 0.5,
                'relheight': 1.0
            }
        
        # Hide all pages
        for page in self.pages:
            page.hide()
        
        # Store the original root background color
        self.original_root_bg = self.root.cget("background")
        
        # Change the ROOT WINDOW background to black
        self.root.configure(background="#000000")
        
        # Also change the page container background
        self.page_container.configure(fg_color="#000000")
        
        # Place the focused page - centered with black borders
        focused_page.frame.place(relx=0.25, rely=0, relwidth=0.5, relheight=1.0)
        
        # Make sure the page is visible
        focused_page.frame.lift()
        
        # Update UI
        self.update_top_bar_page_name()
        self.update_sidebar_page_list()
        
        # KEEP page corner buttons in focus mode, but update their commands
        self.prev_corner.command = lambda: self.previous_focus_page()
        self.next_corner.command = lambda: self.next_focus_page()
        
        # Update seam visibility
        self.update_seam_for_focus_mode()
        
        print(f"Entered focus mode on page {page_index + 1}")
    def next_focus_page(self):
        """Go to next page in focus mode"""
        if not self.focus_mode:
            return self.next_page()  # Fall back to normal navigation
        
        # Play sound
        if self.sound_player:
            self.sound_player.play_flip_sound()
        
        # Calculate next page index
        next_index = self.focused_page_index + 1
        
        # Check if we need to create new pages
        if next_index >= len(self.pages):
            self.add_new_pages()
        
        # Focus on the next page
        self.focus_on_page(next_index)

    def previous_focus_page(self):
        """Go to previous page in focus mode"""
        if not self.focus_mode:
            return self.previous_page()  # Fall back to normal navigation
        
        # Play sound
        if self.sound_player:
            self.sound_player.play_flip_sound()
        
        # Calculate previous page index
        prev_index = self.focused_page_index - 1
        
        # Only navigate if there is a previous page
        if prev_index >= 0:
            self.focus_on_page(prev_index)

    def exit_focus_mode(self):
        """Exit focus mode and return to normal two-page view"""
        if not self.focus_mode:
            return
        
        self.focus_mode = False
        
        # Restore the original root background color
        if hasattr(self, 'original_root_bg'):
            self.root.configure(background=self.original_root_bg)
            self.page_container.configure(fg_color=self.original_root_bg)
        
        # Hide all pages
        for page in self.pages:
            page.hide()
        
        # Restore the previously focused page to its original position
        focused_page = self.pages[self.focused_page_index]
        if hasattr(focused_page, 'original_placement'):
            # Remove the custom placement
            focused_page.frame.place_forget()
            # Restore the page to normal flow
            delattr(focused_page, 'original_placement')
        
        # Show the previous two-page view
        self.current_left_page_index = self.previous_left_index
        self.current_right_page_index = self.previous_right_index
        
        left_page = self.get_current_left_page()
        right_page = self.get_current_right_page()
        
        if left_page:
            left_page.show()
        if right_page:
            right_page.show()
        
        # Update UI
        self.update_top_bar_page_name()
        self.update_sidebar_page_list()
        
        # Restore original commands to page corner buttons
        self.prev_corner.command = self.previous_page
        self.next_corner.command = self.next_page
        
        # Update seam
        self.update_seam_for_focus_mode()
        
        print("Exited focus mode")

    def update_seam_for_focus_mode(self):
        """Update seam visibility based on focus mode"""
        if self.focus_mode:
            # Hide seam in focus mode
            self.seam.place_forget()
        else:
            # Show seam in normal mode
            self.seam.place(relx=0.5, rely=0, relheight=1.0, anchor="n") 
    def update_top_bar_page_name(self):
        """Update the page name display in top bar - modified for focus mode"""
        if self.focus_mode and self.focused_page_index is not None:
            # In focus mode, show only the focused page
            focused_page = self.pages[self.focused_page_index]
            display_text = f"🔍 {focused_page.get_display_text()}"
        else:
            # Normal two-page view
            left_page = self.get_current_left_page()
            right_page = self.get_current_right_page()
            display_text = ""
            
            if left_page and right_page:
                display_text = f"{left_page.get_display_text()} | {right_page.get_display_text()}"
            elif left_page:
                display_text = left_page.get_display_text()
            elif right_page:
                display_text = right_page.get_display_text()
        
        self.page_name_label.configure(text=display_text)
    
    def update_sidebar_page_list(self):
        """Update the page list in sidebar - modified for focus mode"""
        # Clear current list
        for widget in self.page_list.winfo_children():
            widget.destroy()
        
        # Set font for page buttons
        if HAS_CUSTOM_FONT:
            page_btn_font = ("Adeliz", 20)
        else:
            page_btn_font = ("Segoe UI", 20)
        
        # Add page buttons with names
        for i, page in enumerate(self.pages):
            # Create button text - add indicator if this page is focused
            button_text = page.get_display_text()
            if self.focus_mode and i == self.focused_page_index:
                button_text = f"🔍 {button_text}"
            
            # Button command depends on focus mode
            if self.focus_mode:
                # In focus mode, clicking a page navigates within focus mode
                command = lambda idx=i: self.focus_on_page(idx)
            else:
                # In normal mode, clicking a page goes to that page in normal view
                command = lambda idx=i: self.go_to_page(idx)
            
            page_btn = ctk.CTkButton(
                self.page_list,
                text=button_text,
                fg_color="#e0d0b0",
                hover_color="#d0c0a0",
                text_color="#3d2c1e",
                font=page_btn_font,
                height=50,
                corner_radius=5,
                command=command
            )
            
            # If this is the currently focused page, highlight it
            if self.focus_mode and i == self.focused_page_index:
                page_btn.configure(
                    fg_color="#5d4037",
                    text_color="#f5e8c8",
                    hover_color="#4d3027"
                )
            
            page_btn.pack(fill="x", pady=8, padx=5)
    def focus_on_page(self, page_index):
        """Focus on a specific page (within focus mode)"""
        if page_index >= len(self.pages):
            return
        
        # If not in focus mode, enter it
        if not self.focus_mode:
            self.enter_focus_mode(page_index)
            return
        
        # Play flip sound
        if self.sound_player:
            self.sound_player.play_flip_sound()
        
        # Already in focus mode, just switch pages
        self.focused_page_index = page_index
        
        # Hide all pages
        for page in self.pages:
            page.hide()
        
        # Show the new focused page
        focused_page = self.pages[page_index]
        focused_page.frame.place(relx=0.25, rely=0, relwidth=0.5, relheight=1.0)
        focused_page.frame.lift()
        
        # Update UI
        self.update_top_bar_page_name()
        self.update_sidebar_page_list()
        
        print(f"Switched focus to page {page_index + 1}")
    def add_new_pages_and_go(self):
        """Add new pages and navigate to them"""
        self.add_new_pages()
        self.next_page()

    # =============================================
    # NEW: IMAGE IMPORT WITH PAGE CHOOSER
    # =============================================
    
    def import_image_with_page_chooser(self):
        """Import image with simple left/right page selection"""
        # First, let user select an image file
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return  # User cancelled
            
        # Get current pages
        left_page = self.get_current_left_page()
        right_page = self.get_current_right_page()
        
        # Create a custom dialog with Left/Right buttons
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add Image")
        dialog.geometry("400x250")  # Made taller for info
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()  # Make dialog modal
        
        # Center the dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Dialog content
        ctk.CTkLabel(
            dialog,
            text="Add image to which page?",
            font=("Arial", 26) if not HAS_CUSTOM_FONT else ("Adeliz", 26),
            text_color="#3d4037"
        ).pack(pady=(20, 5))
        
        # Show image info
        try:
            with Image.open(file_path) as img:
                orig_width, orig_height = img.size
                
                # Calculate display size (40% of page)
                canvas_width = left_page.canvas.winfo_width() if left_page else 800
                display_width = int(canvas_width * 0.4)
                aspect_ratio = orig_height / orig_width
                display_height = int(display_width * aspect_ratio)
                
                info_text = (
                    f"Image: {orig_width}×{orig_height} pixels\n"
                    f"Will display at: {display_width}×{display_height} pixels\n"
                    f"(40% of page width, drag corners to resize)"
                )
        except:
            info_text = "Cannot read image dimensions"
        
        info_label = ctk.CTkLabel(
            dialog,
            text=info_text,
            font=("Arial", 12) if not HAS_CUSTOM_FONT else ("Adeliz", 12),
            text_color="#5d4037",
            justify="left"
        )
        info_label.pack(pady=10)
        
        # Show current page names
        pages_info = ctk.CTkLabel(
            dialog,
            text=f"• Left page: {left_page.get_display_text() if left_page else 'N/A'}\n"
                f"• Right page: {right_page.get_display_text() if right_page else 'N/A'}",
            font=("Arial", 14) if not HAS_CUSTOM_FONT else ("Adeliz", 14),
            text_color="#3d4037",
            justify="left"
        )
        pages_info.pack(pady=10)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(pady=20)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            width=80,
            height=35,
            fg_color="#a08c6e",
            hover_color="#8c704c",
            text_color="#3d4037",
            command=dialog.destroy
        )
        cancel_btn.pack(side="left", padx=(0, 10))
        
        # Left page button (if left page exists)
        if left_page:
            def add_to_left():
                # Place image in center of left page
                canvas = left_page.canvas
                x = canvas.winfo_width() // 2 - 100  # Will be centered by ImageWidget
                y = canvas.winfo_height() // 2 - 100
                
                # ImageWidget will automatically scale to 40%
                left_page.add_image(x, y, file_path)
                self.set_modified(True)
                dialog.destroy()
            
            left_btn = ctk.CTkButton(
                buttons_frame,
                text="Left Page",
                width=100,
                height=35,
                fg_color="#5d4037",
                hover_color="#3d4037",
                text_color="#f5e8c8",
                command=add_to_left
            )
            left_btn.pack(side="left", padx=5)
        
        # Right page button (if right page exists)
        if right_page:
            def add_to_right():
                # Place image in center of right page
                canvas = right_page.canvas
                x = canvas.winfo_width() // 2 - 100
                y = canvas.winfo_height() // 2 - 100
                
                right_page.add_image(x, y, file_path)
                self.set_modified(True)
                dialog.destroy()
            
            right_btn = ctk.CTkButton(
                buttons_frame,
                text="Right Page",
                width=100,
                height=35,
                fg_color="#5d4037",
                hover_color="#3d4037",
                text_color="#f5e8c8",
                command=add_to_right
            )
            right_btn.pack(side="left", padx=5)
        
        # If only one page is available, make it clearer
        if not right_page:
            ctk.CTkLabel(
                dialog,
                text="(Only left page is available in current view)",
                font=("Arial", 12, "italic") if not HAS_CUSTOM_FONT else ("Adeliz", 12, "italic"),
                text_color="#5d4037"
            ).pack(pady=5)
    
    def import_image_file(self):
        """Legacy method - imports to current left page (for backward compatibility)"""
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
                self.set_modified(True)
    
    def create_sidebar(self):
        # Create left sidebar - slightly darker than page color
        self.sidebar = ctk.CTkFrame(
            self.root,
            fg_color="#a08c6e",
            width=250,  # Increased width for bigger text
            corner_radius=0
        )
        self.sidebar.pack_propagate(False)
        self.sidebar.place(x=-250, y=0, relheight=1.0)  # Updated x position
        
        # Set font for sidebar - MUCH BIGGER for 1920x1080
        if HAS_CUSTOM_FONT:
            sidebar_font = ("Adeliz", 32, "bold")  # Increased from 24 to 32
            page_list_font = ("Adeliz", 28)        # Increased from 24 to 28
        else:
            sidebar_font = ("Segoe UI", 32, "bold")
            page_list_font = ("Segoe UI", 28)
        
        # Sidebar header
        sidebar_header = ctk.CTkLabel(
            self.sidebar,
            text="Pages",
            font=sidebar_font,
            text_color="#3d2c1e",
            height=60  # Increased height
        )
        sidebar_header.pack(fill="x", pady=(20, 10))  # More padding
        
        # Page list
        self.page_list = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="#b5a184",
            corner_radius=0,
            height=600  # Set a fixed height if needed
        )
        self.page_list.pack(fill="both", expand=True, padx=15, pady=10)  # More padding
        
        # Update page list
        self.update_sidebar_page_list()
    
    # Add keyboard shortcuts for focus mode
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts - add to __init__ or create a new method"""
        # Escape key to exit focus mode
        self.root.bind("<Escape>", lambda e: self.exit_focus_mode())
        
        # Arrow keys to navigate pages in BOTH modes
        def handle_left_key(e):
            if self.focus_mode:
                self.previous_focus_page()
            else:
                self.previous_page()
        
        def handle_right_key(e):
            if self.focus_mode:
                self.next_focus_page()
            else:
                self.next_page()
        
        self.root.bind("<Left>", handle_left_key)
        self.root.bind("<Right>", handle_right_key)

    def navigate_focus_left(self):
        """Navigate to previous page in focus mode"""
        if not self.focus_mode:
            return
        
        new_index = self.focused_page_index - 1
        if new_index >= 0:
            self.focus_on_page(new_index)

    def navigate_focus_right(self):
        """Navigate to next page in focus mode"""
        if not self.focus_mode:
            return
        
        new_index = self.focused_page_index + 1
        if new_index < len(self.pages):
            self.focus_on_page(new_index)
    def go_to_page(self, page_index):
        """Go to a specific page - modified to handle focus mode"""
        if self.focus_mode:
            # In focus mode, just focus on the selected page
            self.focus_on_page(page_index)
        else:
            # Original logic for normal mode
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
            
            # Update top bar name display
            self.update_top_bar_page_name()
            
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
            self.sidebar.place(x=-250, y=0, relheight=1.0)  # Updated from -200 to -250
            self.sidebar_visible = False

    def check_mouse_position(self, event):
        # Don't show top bar if sidebar is open
        if self.sidebar_visible and event.x < 250:
            if not self.top_bar_visible:
                self.show_top_bar()
            return
        
        # Get the widget under the cursor
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
        
        # List of widgets that should NOT trigger top bar
        no_top_bar_widgets = [
            self.prev_corner.canvas if hasattr(self.prev_corner, 'canvas') else None,
            self.next_corner.canvas if hasattr(self.next_corner, 'canvas') else None,
            # Add other widgets that should block top bar
        ]
        
        # Check all textbox components
        for page in self.pages:
            for textbox in page.textboxes:
                no_top_bar_widgets.extend([
                    textbox.frame,
                    textbox.text_widget,
                    textbox.handles_frame if hasattr(textbox, 'handles_frame') else None,
                    textbox.move_handle if hasattr(textbox, 'move_handle') else None,
                    textbox.resize_handle if hasattr(textbox, 'resize_handle') else None,
                    textbox.formatting_frame if hasattr(textbox, 'formatting_frame') else None
                ])
            
            # Check all image canvases
            for image in page.images:
                # Add the canvas that contains the image
                if hasattr(image, 'canvas') and image.canvas:
                    no_top_bar_widgets.append(image.canvas)
        
        # Special case: check if cursor is over formatting toolbar buttons
        # These are child widgets inside the formatting_frame
        if widget and hasattr(widget, 'master'):
            # Check if widget is inside a formatting toolbar
            parent = widget.master
            while parent:
                # Check all pages for formatting frames
                for page in self.pages:
                    for textbox in page.textboxes:
                        if hasattr(textbox, 'formatting_frame') and parent == textbox.formatting_frame:
                            # Widget is inside a formatting toolbar
                            if self.top_bar_visible and event.y > 50:
                                self.hide_top_bar()
                            return
                parent = parent.master if hasattr(parent, 'master') else None
        
        # Special case: check if cursor is over any canvas items (images, borders, handles)
        if isinstance(widget, tk.Canvas):
            # Get items at cursor position
            items = widget.find_overlapping(event.x, event.y, event.x+1, event.y+1)
            if items:
                # Check if any of these items belong to our images
                for page in self.pages:
                    for image in page.images:
                        if hasattr(image, 'image_id') and image.image_id in items:
                            # Cursor is over an image
                            if self.top_bar_visible and event.y > 50:
                                self.hide_top_bar()
                            return
        
        # Check if cursor is over any "no-top-bar" widget
        if widget in no_top_bar_widgets:
            # Don't show top bar when over interactive elements
            if self.top_bar_visible and event.y > 50:
                self.hide_top_bar()
            return
        
        # Also check if cursor position is inside any textbox frame
        for page in self.pages:
            for textbox in page.textboxes:
                if hasattr(textbox, 'frame') and textbox.frame.winfo_exists():
                    frame_x = textbox.frame.winfo_rootx() - self.root.winfo_rootx()
                    frame_y = textbox.frame.winfo_rooty() - self.root.winfo_rooty()
                    frame_width = textbox.frame.winfo_width()
                    frame_height = textbox.frame.winfo_height()
                    
                    if (frame_x <= event.x <= frame_x + frame_width and 
                        frame_y <= event.y <= frame_y + frame_height):
                        # Cursor is inside textbox frame
                        if self.top_bar_visible and event.y > 50:
                            self.hide_top_bar()
                        return
        
        # Original top bar behavior
        if event.y < 10:  # Very top edge only
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

    # =============================================
    # SAVE/LOAD FUNCTIONALITY WITH MIGRATION
    # =============================================
    
    def new_notebook(self):
        """Create a new notebook"""
        if self.modified:
            response = messagebox.askyesnocancel(
                "Save Changes",
                "Do you want to save changes before creating a new notebook?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                if not self.save_notebook():
                    return  # Save was cancelled
        
        # Clear all pages
        for page in self.pages:
            page.clear()
            page.frame.destroy()
        
        # Reset state
        self.pages = []
        self.current_left_page_index = 0
        self.current_right_page_index = 1
        self.current_file = None
        self.modified = False
        
        # Create new initial pages
        self.initialize_pages()
        
        # Update UI
        self.update_sidebar_page_list()
        self.update_top_bar_page_name()
        self.update_window_title()
    
    def save_notebook(self, filepath=None):
        """Save the current notebook to a file"""
        if not filepath:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".notebook",
                filetypes=[("Notebook files", "*.notebook"), ("All files", "*.*")],
                initialfile="my_notebook.notebook"
            )
            if not filepath:
                return False
        
        try:
            # Get notebook data
            notebook_data = self.get_notebook_data()
            
            # Handle image embedding/copying
            notebook_data = self.prepare_images_for_saving(notebook_data, filepath)
            
            # Save to JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(notebook_data, f, indent=2, ensure_ascii=False)
            
            # Update state
            self.current_file = filepath
            self.set_modified(False)
            
            messagebox.showinfo("Success", f"Notebook saved successfully to:\n{filepath}")
            return True
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save notebook:\n{str(e)}")
            return False
    
    def load_notebook(self, filepath=None):
        """Load a notebook from a file"""
        if not filepath:
            filepath = filedialog.askopenfilename(
                filetypes=[("Notebook files", "*.notebook"), ("All files", "*.*")]
            )
            if not filepath:
                return
        
        # Check if current notebook has unsaved changes
        if self.modified:
            response = messagebox.askyesnocancel(
                "Save Changes",
                "Do you want to save changes before loading a new notebook?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                if not self.save_notebook():
                    return  # Save was cancelled
        
        try:
            # Load JSON data
            with open(filepath, 'r', encoding='utf-8') as f:
                notebook_data = json.load(f)
            
            # Migrate data if needed
            notebook_data = self.migrate_data(notebook_data)
            
            # Clear existing pages
            for page in self.pages:
                page.clear()
                page.frame.destroy()
            
            self.pages = []
            
            # Restore pages from data
            for page_data in notebook_data.get("pages", []):
                page = Page(
                    self.page_container,
                    page_data.get("is_left_page", True),
                    page_data.get("page_number", len(self.pages)),
                    page_data.get("name", f"Page {len(self.pages) + 1}")
                )
                
                # Deserialize page content
                page.deserialize(page_data, self)
                
                self.pages.append(page)
            
            # Set current file
            self.current_file = filepath
            self.set_modified(False)
            
            # Reset view to first page
            self.current_left_page_index = 0
            self.current_right_page_index = 1
            
            # Hide all pages first
            for page in self.pages:
                page.hide()
            
            # Show first two pages
            if len(self.pages) > 0:
                self.pages[0].show()
            if len(self.pages) > 1:
                self.pages[1].show()
            
            # Update UI
            self.update_sidebar_page_list()
            self.update_top_bar_page_name()
            self.update_window_title()
            
            messagebox.showinfo("Success", f"Notebook loaded successfully from:\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load notebook:\n{str(e)}")
            # Restore default state
            self.new_notebook()
    
    def migrate_data(self, data):
        """Migrate data from older versions to current format"""
        version = data.get("version", 1)
        
        # Version 1 -> 2 migration
        if version == 1:
            print("Migrating from version 1 to 2")
            data["version"] = 2
            
            # Add missing fields
            if "metadata" not in data:
                data["metadata"] = {
                    "created": datetime.now().isoformat(),
                    "modified": datetime.now().isoformat(),
                    "app_version": "1.0"
                }
            
            # Ensure pages have proper structure
            for page in data.get("pages", []):
                # Add missing fields
                if "is_left_page" not in page:
                    page["is_left_page"] = (page.get("page_number", 0) % 2 == 0)
                
                # Migrate text widgets if needed
                for textbox in page.get("textboxes", []):
                    # Ensure text field has segments structure
                    if "text" in textbox and isinstance(textbox["text"], str):
                        # Convert plain text to segments format
                        textbox["text"] = {
                            "content": textbox["text"],
                            "segments": [{
                                "text": textbox["text"],
                                "tags": []
                            }]
                        }
        
        return data
    
    def get_notebook_data(self):
        """Serialize the entire notebook state"""
        notebook_data = {
            "version": 2,
            "metadata": {
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
                "app_version": "1.0",
                "min_compatible_version": 1
            },
            "pages": []
        }
        
        # Serialize all pages
        for page in self.pages:
            notebook_data["pages"].append(page.serialize())
        
        return notebook_data
    
    def prepare_images_for_saving(self, notebook_data, save_path):
        """Prepare images for saving - copy to notebook directory"""
        save_dir = os.path.dirname(save_path)
        images_dir = os.path.join(save_dir, "images")
        
        # Create images directory if it doesn't exist
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        
        # Track used images to avoid duplicates
        image_map = {}  # original_path -> (relative_path, absolute_path)
        
        # Process all images in notebook
        for page_data in notebook_data["pages"]:
            for image_data in page_data["images"]:
                original_path = image_data["image_path"]
                
                # Skip if already processed
                if original_path in image_map:
                    rel_path, abs_path = image_map[original_path]
                    image_data["image_path"] = abs_path  # Use existing absolute path
                    image_data["relative_path"] = rel_path  # Store relative path too
                    continue
                
                # Generate new filename with hash
                import hashlib
                try:
                    with open(original_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()[:8]
                except:
                    # Fallback to random name if can't read
                    import random
                    file_hash = f"{random.randint(1000, 9999)}"
                
                filename = os.path.basename(original_path)
                name, ext = os.path.splitext(filename)
                new_filename = f"{file_hash}{ext}"
                new_abs_path = os.path.join(images_dir, new_filename)
                rel_path = os.path.join("images", new_filename)
                
                # Copy image if needed
                if not os.path.exists(new_abs_path):
                    try:
                        shutil.copy2(original_path, new_abs_path)
                        print(f"Copied image: {original_path} -> {new_abs_path}")
                    except Exception as e:
                        print(f"Warning: Could not copy image {original_path}: {e}")
                        # Keep original path
                        new_abs_path = original_path
                        rel_path = original_path
                
                # Store both paths
                image_data["image_path"] = new_abs_path  # Absolute path for current session
                image_data["relative_path"] = rel_path   # Relative path for saving
                
                image_map[original_path] = (rel_path, new_abs_path)
        
        # Cleanup unused images in images directory
        self.cleanup_unused_images(notebook_data, save_path)
        
        return notebook_data

    def cleanup_unused_images(self, notebook_data, save_path):
        """Remove images not referenced in the notebook"""
        save_dir = os.path.dirname(save_path)
        images_dir = os.path.join(save_dir, "images")
        
        if not os.path.exists(images_dir):
            return
        
        # Get all referenced image filenames
        referenced = set()
        for page_data in notebook_data["pages"]:
            for image_data in page_data["images"]:
                if "image_path" in image_data:
                    filename = os.path.basename(image_data["image_path"])
                    referenced.add(filename)
        
        # Remove unreferenced files
        for filename in os.listdir(images_dir):
            if filename not in referenced:
                try:
                    os.remove(os.path.join(images_dir, filename))
                    print(f"Removed unused image: {filename}")
                except Exception as e:
                    print(f"Failed to remove {filename}: {e}")

    def restore_image_paths(self, notebook_data, load_path):
        """Convert relative paths back to absolute when loading"""
        load_dir = os.path.dirname(load_path)
        
        for page_data in notebook_data["pages"]:
            for image_data in page_data["images"]:
                if "image_path" in image_data:
                    rel_path = image_data["image_path"]
                    # Check if it's a relative path
                    if not os.path.isabs(rel_path):
                        abs_path = os.path.join(load_dir, rel_path)
                        if os.path.exists(abs_path):
                            image_data["image_path"] = abs_path
                        else:
                            print(f"Warning: Image not found: {abs_path}")
    
    def clear_all_pages(self):
        """Clear all pages and widgets"""
        for page in self.pages:
            page.clear()
            page.frame.destroy()
        self.pages = []
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = NotebookApp()
    app.run()