import customtkinter as ctk
import tkinter.font as tkFont

class NotebookApp:
    def __init__(self):
        ctk.set_appearance_mode("light")
        
        self.root = ctk.CTk()
        self.root.title("Notebook App")
        
        self.setup_sidebar_close_binding()

        # Set max size to 1920x1080
        self.root.maxsize(1920, 1080)
        self.root.geometry("800x600")
        self.root.configure(fg_color="#c1a273")
        
        # Hidden top bar
        self.top_bar_visible = False
        self.top_bar = None
        self.sidebar_visible = False
        
        # Text box creation state
        self.creating_textbox = False
        self.selection_start = None
        self.selection_rect = None
        self.current_page = None
        self.textboxes = []  # Store created text boxes
        
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
        
        # Page data structure
        self.current_left_page = 0
        self.current_right_page = 1
        self.pages = []  # Will store page content later
        
        # Bind text box creation events
        self.setup_textbox_creation()
        
        # Sidebar for page selector
        self.sidebar = None
        
        # Bind mouse movement to show/hide bar
        self.root.bind("<Motion>", self.check_mouse_position)
        
        # Create hidden top bar initially
        self.create_top_bar()
        self.top_bar.place_forget()
        
        # Create sidebar
        self.create_sidebar()

    def setup_sidebar_close_binding(self):
        # Bind left-click anywhere on the root
        self.root.bind("<Button-1>", self.check_click_outside_sidebar)

    def check_click_outside_sidebar(self, event):
        if not self.sidebar_visible:
            return  # Sidebar already closed

        # Ignore clicks inside sidebar
        sx1 = self.sidebar.winfo_x()
        sy1 = self.sidebar.winfo_y()
        sx2 = sx1 + self.sidebar.winfo_width()
        sy2 = sy1 + self.sidebar.winfo_height()
        if sx1 <= event.x <= sx2 and sy1 <= event.y <= sy2:
            return

        # Ignore clicks inside top bar
        if self.top_bar is not None:
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
            # Get widget position relative to its parent
            widget_x = widget.winfo_x()
            widget_y = widget.winfo_y()
            widget_width = widget.winfo_width()
            widget_height = widget.winfo_height()
            
            # Check if event coordinates are within widget bounds
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
        for tb_data in self.textboxes:
            tb_data['formatting_frame'].place_forget()
        self.root.focus()  # Removes focus from any textbox

    def start_textbox_creation(self, event):
        """Start creating a text box on double-click"""
        self.creating_textbox = True
        self.selection_start = (event.x, event.y)

        # Determine which page the canvas belongs to
        if event.widget == self.left_canvas:
            self.current_page = self.left_page
            canvas = self.left_canvas
        else:
            self.current_page = self.right_page
            canvas = self.right_canvas

        # Clear any existing selection rectangle
        self.clear_selection_rect()

        # Create dashed selection rectangle
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

        if width < 50: width = 200
        if height < 30: height = 100

        parent = self.current_page
        canvas = self.left_canvas if parent == self.left_page else self.right_canvas

        self.clear_selection_rect()

        x = min(start_x, end_x)
        y = min(start_y, end_y)

        # Create the textbox
        textbox = ctk.CTkTextbox(
            parent,
            fg_color="transparent",
            text_color="#3d2c1e",
            font=("Arial", 11),
            border_width=0,
            corner_radius=3,
            wrap="word",
            width=width,
            height=height
        )
        textbox.place(x=x, y=y)
        textbox.insert("1.0", "Click to edit...")
        
        # Create formatting toolbar frame
        formatting_frame = ctk.CTkFrame(
            parent,
            fg_color="#f5e8c8",
            width=120,
            height=30,
            corner_radius=3,
            border_width=1,
            border_color="#a08c6e"
        )
        formatting_frame.pack_propagate(False)
        formatting_frame.place_forget()  # Hidden initially
        
        # Formatting buttons
        bold_btn = ctk.CTkButton(
            formatting_frame,
            text="B",
            width=30,
            height=24,
            fg_color="#e0d0b0",
            hover_color="#d0c0a0",
            text_color="#3d2c1e",
            font=("Arial", 11, "bold"),
            corner_radius=2,
            command=lambda: self.toggle_bold(textbox)
        )
        bold_btn.pack(side="left", padx=(5, 2), pady=3)
        
        italic_btn = ctk.CTkButton(
            formatting_frame,
            text="I",
            width=30,
            height=24,
            fg_color="#e0d0b0",
            hover_color="#d0c0a0",
            text_color="#3d2c1e",
            font=("Arial", 11, "italic"),
            corner_radius=2,
            command=lambda: self.toggle_italic(textbox)
        )
        italic_btn.pack(side="left", padx=2, pady=3)
        
        # Font size dropdown
        font_sizes = ["8", "10", "11", "12", "14", "16", "18", "20", "24"]
        font_size_var = ctk.StringVar(value="11")
        
        font_size_menu = ctk.CTkOptionMenu(
            formatting_frame,
            values=font_sizes,
            variable=font_size_var,
            width=50,
            height=24,
            fg_color="#e0d0b0",
            button_color="#d0c0a0",
            button_hover_color="#c0b090",
            text_color="#3d2c1e",
            font=("Arial", 10),
            corner_radius=2,
            command=lambda size: self.change_font_size(textbox, size)
        )
        font_size_menu.pack(side="left", padx=(2, 5), pady=3)
        
        # Store formatting state
        textbox.formatting_state = {
            'bold': False,
            'italic': False,
            'font_size': 11,
            'font_family': "Arial"
        }
        
        # Store tags for text formatting
        textbox.tag_configure("bold", font=("Arial", 11, "bold"))
        textbox.tag_configure("italic", font=("Arial", 11, "italic"))
        textbox.tag_configure("bolditalic", font=("Arial", 11, "bold italic"))
        
        textbox.lift()
        formatting_frame.lift()

        # Resize handle
        handle_size = 10
        resize_handle = ctk.CTkFrame(parent, fg_color="#a08c6e", width=handle_size, height=handle_size, corner_radius=2)
        resize_handle.place(x=x+width-handle_size, y=y+height-handle_size)

        # Placeholder text
        def clear_placeholder(e):
            if textbox.get("1.0", "end-1c") == "Click to edit...":
                textbox.delete("1.0", "end")

        # Focus in/out behavior
        def focus_in(e):
            textbox.configure(fg_color="#f5e8c8", border_width=1, border_color="#a08c6e")
            clear_placeholder(e)
            resize_handle.place(x=textbox.winfo_x()+textbox.winfo_width()-handle_size,
                                y=textbox.winfo_y()+textbox.winfo_height()-handle_size)
            # Show formatting toolbar above textbox
            formatting_frame.place(x=textbox.winfo_x(), 
                                  y=textbox.winfo_y()-35)

        def focus_out(e):
            textbox.configure(fg_color="transparent", border_width=0)
            resize_handle.place_forget()
            # Hide formatting toolbar
            formatting_frame.place_forget()

        textbox.bind("<FocusIn>", focus_in)
        textbox.bind("<FocusOut>", focus_out)
        
        # Also hide toolbar when clicking elsewhere
        def hide_toolbar(e):
            if not self.is_mouse_over_widget(textbox, e) and not self.is_mouse_over_widget(formatting_frame, e):
                formatting_frame.place_forget()
                
        parent.bind("<Button-1>", hide_toolbar, add="+")

        # Resize logic
        def start_resize(event):
            resize_handle.start_x = event.x
            resize_handle.start_y = event.y
            resize_handle.start_width = textbox.winfo_width()
            resize_handle.start_height = textbox.winfo_height()

        def do_resize(event):
            dx = event.x - resize_handle.start_x
            dy = event.y - resize_handle.start_y

            new_width = max(50, resize_handle.start_width + dx)
            new_height = max(30, resize_handle.start_height + dy)

            textbox.configure(width=new_width, height=new_height)
            resize_handle.place(x=textbox.winfo_x() + new_width - handle_size,
                                y=textbox.winfo_y() + new_height - handle_size)
            # Update toolbar position
            if formatting_frame.winfo_ismapped():
                formatting_frame.place(x=textbox.winfo_x(), 
                                      y=textbox.winfo_y()-35)
                
        textbox.lift()
        formatting_frame.lift()
        resize_handle.lift()
        textbox.update_idletasks()
        resize_handle.update_idletasks()
        formatting_frame.update_idletasks()
        
        resize_handle.bind("<Button-1>", start_resize)
        resize_handle.bind("<B1-Motion>", do_resize)

        # Drag logic
        def start_drag(event):
            textbox.drag_start_x = event.x
            textbox.drag_start_y = event.y

        def do_drag(event):
            dx = event.x - textbox.drag_start_x
            dy = event.y - textbox.drag_start_y

            new_x = textbox.winfo_x() + dx
            new_y = textbox.winfo_y() + dy

            page_width = parent.winfo_width()
            page_height = parent.winfo_height()

            new_x = max(0, min(new_x, page_width - textbox.winfo_width()))
            new_y = max(0, min(new_y, page_height - textbox.winfo_height()))

            textbox.place(x=new_x, y=new_y)
            resize_handle.place(x=new_x + textbox.winfo_width() - handle_size,
                                y=new_y + textbox.winfo_height() - handle_size)
            # Update toolbar position
            if formatting_frame.winfo_ismapped():
                formatting_frame.place(x=new_x, 
                                      y=new_y-35)
                
            textbox.lift()
            formatting_frame.lift()
            resize_handle.lift()
            parent.update_idletasks()

        textbox.bind("<Button-1>", start_drag)
        textbox.bind("<B1-Motion>", do_drag)

        # Add to stored textboxes
        self.textboxes.append({
            'widget': textbox,
            'page': parent,
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'handle': resize_handle,
            'formatting_frame': formatting_frame,
            'formatting_state': textbox.formatting_state
        })

        self.creating_textbox = False
        self.selection_start = None
        self.current_page = None

    def toggle_bold(self, textbox):
        """Toggle bold formatting for selected text"""
        try:
            # Get current selection
            sel_start = textbox.index("sel.first")
            sel_end = textbox.index("sel.last")
            
            # Check if selection already has bold tag
            tags = textbox.tag_names(sel_start)
            
            if "bold" in tags or "bolditalic" in tags:
                # Remove bold
                textbox.tag_remove("bold", sel_start, sel_end)
                textbox.tag_remove("bolditalic", sel_start, sel_end)
                
                # If it was bolditalic, keep italic
                if "bolditalic" in tags:
                    textbox.tag_add("italic", sel_start, sel_end)
            else:
                # Add bold
                if "italic" in tags:
                    textbox.tag_remove("italic", sel_start, sel_end)
                    textbox.tag_add("bolditalic", sel_start, sel_end)
                else:
                    textbox.tag_add("bold", sel_start, sel_end)
                    
        except tkinter.TclError:
            # No text selected, do nothing or apply to entire textbox
            pass

    def toggle_italic(self, textbox):
        """Toggle italic formatting for selected text"""
        try:
            # Get current selection
            sel_start = textbox.index("sel.first")
            sel_end = textbox.index("sel.last")
            
            # Check if selection already has italic tag
            tags = textbox.tag_names(sel_start)
            
            if "italic" in tags or "bolditalic" in tags:
                # Remove italic
                textbox.tag_remove("italic", sel_start, sel_end)
                textbox.tag_remove("bolditalic", sel_start, sel_end)
                
                # If it was bolditalic, keep bold
                if "bolditalic" in tags:
                    textbox.tag_add("bold", sel_start, sel_end)
            else:
                # Add italic
                if "bold" in tags:
                    textbox.tag_remove("bold", sel_start, sel_end)
                    textbox.tag_add("bolditalic", sel_start, sel_end)
                else:
                    textbox.tag_add("italic", sel_start, sel_end)
                    
        except tkinter.TclError:
            # No text selected, do nothing or apply to entire textbox
            pass

    def change_font_size(self, textbox, size):
        """Change font size for selected text or entire textbox"""
        try:
            size = int(size)
            # Get current selection
            sel_start = textbox.index("sel.first")
            sel_end = textbox.index("sel.last")
            
            # Get current tags to preserve bold/italic
            tags = textbox.tag_names(sel_start)
            
            # Create new tag with updated font size
            font_config = "Arial"
            if "bold" in tags:
                font_config += " bold"
            elif "italic" in tags:
                font_config += " italic"
            elif "bolditalic" in tags:
                font_config += " bold italic"
                
            # Create a unique tag name for this size combination
            tag_name = f"size{size}_{font_config.replace(' ', '_')}"
            
            # Configure the tag if it doesn't exist
            if tag_name not in textbox.tag_names():
                textbox.tag_configure(tag_name, font=(font_config, size))
            
            # Apply the tag to selection
            textbox.tag_add(tag_name, sel_start, sel_end)
            
        except tkinter.TclError:
            # No text selected, apply to entire textbox
            textbox.configure(font=("Arial", size))
            # Update formatting state
            textbox.formatting_state['font_size'] = size

    def clear_placeholder(self, textbox):
        if textbox.get("1.0", "end-1c") == "Click to edit...":
            textbox.delete("1.0", "end")

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
        
        # File button
        file_btn = ctk.CTkButton(
            self.top_bar,
            text="File",
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
        for tb_data in self.textboxes:
            formatting_frame = tb_data['formatting_frame']
            if formatting_frame.winfo_ismapped():
                if self.is_mouse_over_widget(formatting_frame, event):
                    return  # Don't hide top bar if over toolbar

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
    
    # New methods for page management
    def get_left_page(self):
        """Returns the left page frame"""
        return self.left_page
    
    def get_right_page(self):
        """Returns the right page frame"""
        return self.right_page
    
    def get_current_pages(self):
        """Returns current page numbers being displayed"""
        return (self.current_left_page, self.current_right_page)
    
    def turn_page_right(self):
        """Simulate turning page to right (for future implementation)"""
        pass
    
    def turn_page_left(self):
        """Simulate turning page to left (for future implementation)"""
        pass
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = NotebookApp()
    app.run()