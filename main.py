import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Frame, Canvas
import re
import struct
import os

class ColorSwatch:
    def __init__(self, parent, color, name):
        self.frame = Frame(parent, bd=1, relief=tk.SOLID, bg="#f0f0f0")
        self.color = color
        self.name = name
        
        # Create color preview
        self.canvas = Canvas(self.frame, width=30, height=30, bg="#%02x%02x%02x" % color, 
                            highlightthickness=0, bd=0)
        self.canvas.pack(padx=2, pady=2)
        self.canvas.create_rectangle(0, 0, 29, 29, outline="#333")
        
        # Truncate long names
        display_name = name if len(name) <= 15 else name[:12] + "..."
        name_label = tk.Label(self.frame, text=display_name, font=("Arial", 8), bg="#f0f0f0")
        name_label.pack(padx=2, pady=(0, 2))
        
        # Tooltip functionality
        self.tooltip = None
        self.canvas.bind("<Enter>", self.show_tooltip)
        self.canvas.bind("<Leave>", self.hide_tooltip)
        
    def show_tooltip(self, event=None):
        tooltip_text = f"{self.name}\nRGB: {self.color}"
        self.tooltip = tk.Toplevel(self.frame)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.geometry(f"+{event.x_root+10}+{event.y_root+10}")
        label = tk.Label(self.tooltip, text=tooltip_text, bg="#ffffe0", relief="solid", borderwidth=1)
        label.pack()
        
    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class GPLtoACOConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("GPL to ACO Converter")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        self.current_colors = []
        self.palette_name = ""
        self.columns = 0
        self.filepath = ""
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top section
        top_frame = ttk.LabelFrame(main_frame, text="Palette Conversion")
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # File selection
        file_frame = ttk.Frame(top_frame)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.file_label = ttk.Label(file_frame, text="No palette loaded", font=("Arial", 9))
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        btn_load = ttk.Button(file_frame, text="Load GPL", command=self.load_gpl)
        btn_load.pack(side=tk.RIGHT)
        
        # Info display
        info_frame = ttk.Frame(top_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.name_label = ttk.Label(info_frame, text="Name: -")
        self.name_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.colors_label = ttk.Label(info_frame, text="Colors: 0")
        self.colors_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.columns_label = ttk.Label(info_frame, text="Columns: 0")
        self.columns_label.pack(side=tk.LEFT)
        
        # Options
        self.nonull_var = tk.BooleanVar()
        nonull_check = ttk.Checkbutton(
            top_frame, 
            text="Exclude null terminator in color names",
            variable=self.nonull_var,
            onvalue=True,
            offvalue=False
        )
        nonull_check.pack(padx=5, pady=(0, 5))
        
        # Convert button
        btn_convert = ttk.Button(top_frame, text="Convert to ACO", command=self.convert_to_aco)
        btn_convert.pack(pady=(0, 5))
        
        # Preview area
        preview_frame = ttk.LabelFrame(main_frame, text="Palette Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create canvas with scrollbar
        self.canvas = Canvas(preview_frame, bg="white")
        scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to load GPL palette")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def load_gpl(self):
        filepath = filedialog.askopenfilename(
            title="Open GIMP Palette",
            filetypes=[("GIMP Palettes", "*.gpl"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
            
        try:
            name, columns, colors = self.load_and_parse_gpl(filepath)
            self.current_colors = colors
            self.palette_name = name
            self.columns = columns
            self.filepath = filepath
            
            # Update UI
            self.file_label.config(text=os.path.basename(filepath))
            self.name_label.config(text=f"Name: {name}")
            self.colors_label.config(text=f"Colors: {len(colors)}")
            self.columns_label.config(text=f"Columns: {columns}")
            self.status_var.set(f"Loaded {len(colors)} colors from {os.path.basename(filepath)}")
            
            # Display color preview
            self.display_color_preview(colors, columns)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load GPL file:\n{str(e)}")
    
    def display_color_preview(self, colors, columns):
        # Clear existing preview
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not colors:
            return
            
        # Determine grid dimensions
        max_cols = max(columns, 8) if columns > 0 else 8
        max_cols = min(max_cols, 12)  # Limit to 12 columns for display
        
        # Create color swatches
        for i, color in enumerate(colors):
            r, g, b, name = color
            rgb_color = (r, g, b)
            swatch = ColorSwatch(self.scrollable_frame, rgb_color, name)
            
            row = i // max_cols
            col = i % max_cols
            swatch.frame.grid(row=row, column=col, padx=5, pady=5)
    
    def load_and_parse_gpl(self, filepath):
        name = ""
        columns = 0
        colors = []

        # Handle UTF-8 BOM and mixed spaces/tabs
        pat1 = re.compile(r'^\s*(\d+)\s+(\d+)\s+(\d+)\s+(.+)$')
        pat2 = re.compile(r'^\s*(\d+)\s+(\d+)\s+(\d+)\s*$')

        # Handle UTF-8 BOM
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            lines = f.read().splitlines()

        linenum = 0
        for l in lines:
            linenum += 1
            if linenum == 1:
                if "GIMP Palette" in l:
                    continue
                else:
                    raise ValueError("This file is not a GIMP palette")

            # Skip empty lines and comments
            if not l.strip() or l.strip().startswith('#'):
                continue

            # Normalize tabs to spaces
            l = l.replace('\t', ' ')

            if l.startswith("Name:"):
                name = l[5:].strip()
            elif l.startswith("Columns:"):
                columns = int(l[8:].strip())
            else:
                # r g b colorname
                r = pat1.match(l)
                if r:
                    r, g, b, cname = r.groups()
                    colors.append([int(r), int(g), int(b), cname])
                else:
                    r = pat2.match(l)
                    if r:
                        r, g, b = r.groups()
                        colors.append([int(r), int(g), int(b), ""])
                    else:
                        # Try to parse with any whitespace
                        parts = l.split()
                        if len(parts) >= 3:
                            try:
                                r, g, b = map(int, parts[:3])
                                cname = " ".join(parts[3:]) if len(parts) > 3 else ""
                                colors.append([r, g, b, cname])
                            except ValueError:
                                raise ValueError(f"Syntax error in line {linenum}: {l}")
                        else:
                            raise ValueError(f"Syntax error in line {linenum}: {l}")

        return name, columns, colors

    def create_aco(self, vernum, nonull, colors):
        aco_ver = vernum  # 1 or 2
        col_len = len(colors)
        bindata = struct.pack(">2H", aco_ver, col_len)

        cspace = 0  # color ID 0 = RGB
        for c in colors:
            r, g, b, color_name = c

            w = int(65535 * r / 255)
            x = int(65535 * g / 255)
            y = int(65535 * b / 255)
            z = 0

            bindata += struct.pack(">5H", cspace, w, x, y, z)

            if vernum == 2:
                if not nonull:
                    name_len = len(color_name) + 1
                    bindata += struct.pack(">L", name_len)
                    for s in color_name:
                        n = ord(s)
                        bindata += struct.pack(">H", n)

                    # add NULL word
                    bindata += struct.pack(">H", 0)
                else:
                    name_len = len(color_name)
                    bindata += struct.pack(">L", name_len)
                    for s in color_name:
                        n = ord(s)
                        bindata += struct.pack(">H", n)

        return bindata

    def convert_to_aco(self):
        if not self.current_colors:
            messagebox.showwarning("No Palette", "Please load a GPL palette first")
            return
            
        # Suggest a filename based on palette name
        suggested_name = self.palette_name.replace(" ", "_") + ".aco"
        save_path = filedialog.asksaveasfilename(
            title="Save ACO File",
            filetypes=[("Photoshop Swatches", "*.aco"), ("All files", "*.*")],
            initialfile=suggested_name
        )
        
        if not save_path:
            return
            
        if not save_path.lower().endswith('.aco'):
            save_path += '.aco'
        
        try:
            nonull = self.nonull_var.get()
            # Create aco binary ver1 and ver2
            aco_bin = self.create_aco(1, nonull, self.current_colors)
            aco_bin += self.create_aco(2, nonull, self.current_colors)
            
            with open(save_path, 'wb') as f:
                f.write(aco_bin)
                
            self.status_var.set(f"Successfully saved {len(self.current_colors)} colors to {os.path.basename(save_path)}")
            messagebox.showinfo("Success", "ACO file created successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create ACO file:\n{str(e)}")

if __name__ == '__main__':
    root = tk.Tk()
    app = GPLtoACOConverter(root)
    root.mainloop()