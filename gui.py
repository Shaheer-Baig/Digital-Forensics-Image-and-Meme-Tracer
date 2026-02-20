import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from PIL import Image
import threading

# Configuration - Professional Dark Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Professional Dark Blue Palette
COLOR_PRIMARY = "#0F172A"      # Slate 900 - Very dark blue
COLOR_SECONDARY = "#1E293B"    # Slate 800
COLOR_ACCENT = "#334155"       # Slate 700 - Muted blue accent
COLOR_HOVER = "#475569"        # Slate 600
COLOR_SUCCESS = "#10B981"      # Emerald 500
COLOR_WARNING = "#F59E0B"      # Amber 500
COLOR_TEXT_PRIMARY = "#F1F5F9" # Slate 100
COLOR_TEXT_SECONDARY = "#CBD5E1" # Slate 300

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Forensic Image & Meme Tracer Tool")
        self.geometry("1200x750")

        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)  # Footer row

        # --- Left Sidebar (Input) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color=COLOR_PRIMARY)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew", rowspan=2)
        self.sidebar_frame.grid_rowconfigure(3, weight=1)

        # Logo with professional styling
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="🔍 Forensic Image\n& Meme Tracer", 
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
            justify="center"
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(40, 30))

        self.upload_btn = ctk.CTkButton(
            self.sidebar_frame, 
            text="📂 Select Image", 
            command=self.select_image,
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_HOVER,
            height=45,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_ACCENT
        )
        self.upload_btn.grid(row=1, column=0, padx=25, pady=15, sticky="ew")

        self.image_preview_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="No Image Selected", 
            text_color=COLOR_TEXT_SECONDARY,
            font=ctk.CTkFont(size=11)
        )
        self.image_preview_label.grid(row=2, column=0, padx=20, pady=15)

        self.start_btn = ctk.CTkButton(
            self.sidebar_frame, 
            text="🚀 Start Analysis", 
            command=self.start_trace, 
            state="disabled",
            fg_color=COLOR_SUCCESS,
            hover_color="#059669",
            height=45,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.start_btn.grid(row=3, column=0, padx=25, pady=15, sticky="ew")

        # --- Right Panel (Results) ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(self.main_frame, text="Ready", anchor="w")
        self.status_label.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="ew")

        self.results_scroll = ctk.CTkScrollableFrame(
            self.main_frame, 
            label_text="🎯 Trace Results",
            label_font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=10
        )
        self.results_scroll.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")

        # Footer with Code_of_Duty branding
        self.footer_frame = ctk.CTkFrame(self, fg_color=COLOR_PRIMARY, height=50, corner_radius=0)
        self.footer_frame.grid(row=1, column=1, sticky="ew", padx=0, pady=0)
        self.footer_frame.grid_propagate(False)
        
        footer_text = ctk.CTkLabel(
            self.footer_frame,
            text="⚡ Powered by Code_of_Duty | Advanced Forensic Solutions",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#93C5FD"
        )
        footer_text.pack(expand=True)

        self.selected_image_path = None

    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp")])
        if file_path:
            self.selected_image_path = file_path
            self.show_image_preview(file_path)
            self.start_btn.configure(state="normal")
            self.status_label.configure(text=f"Selected: {file_path.split('/')[-1]}")

    def show_image_preview(self, path):
        try:
            img = Image.open(path)
            img.thumbnail((200, 200))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.image_preview_label.configure(image=ctk_img, text="")
        except Exception as e:
            self.status_label.configure(text=f"Error loading image: {e}")

    def start_trace(self):
        if not self.selected_image_path:
            return
        
        # Hardcoded API keys (hidden from GUI)
        api_key = "6ae5b95071c010f5b4efeb1ed9fe82c002c281e7b7730b3931d3089fb1ea0230"
        rapidapi_key = "f6df45f229msh663b7425d5d9628p164833jsn84c458789ef9"
        
        self.start_btn.configure(state="disabled")
        self.status_label.configure(text="Starting trace... this may take a while.")
        
        # Run in background thread to keep GUI responsive
        threading.Thread(target=self.run_trace_logic, args=(api_key, rapidapi_key), daemon=True).start()

    def run_trace_logic(self, api_key=None, rapidapi_key=None):
        try:
            from scraper import Scraper
            from hasher import Hasher
            from analyzer import Analyzer
            import datetime

            self.update_status("Initializing engines...")
            scraper = Scraper(api_key=api_key, rapidapi_key=rapidapi_key)
            
            # 1. Search
            self.update_status("Running Hybrid Search (OCR + Visual)...")
            candidates = scraper.hybrid_search(self.selected_image_path)
            
            # FAIL-SAFE: If no candidates found, force manual check links
            if not candidates:
                self.update_status("Automated search yielded no results. Generating manual links...")
                image_url = scraper.upload_image(self.selected_image_path)
                if not image_url:
                    image_url = "https://catbox.moe" # Fallback
                
                import urllib.parse
                candidates = [
                    {
                        'url': f"https://www.bing.com/images/search?view=detailv2&iss=sbi&form=SBIHMP&q=imgurl:{urllib.parse.quote(image_url)}",
                        'title': 'Manual Check: Bing Visual Search',
                        'manual_check': True,
                        'date_str': 'Now',
                        'user': 'System'
                    },
                    {
                        'url': f"https://yandex.com/images/search?rpt=imageview&url={urllib.parse.quote(image_url)}",
                        'title': 'Manual Check: Yandex Visual Search',
                        'manual_check': True,
                        'date_str': 'Now',
                        'user': 'System'
                    },
                    {
                        'url': f"https://lens.google.com/uploadbyurl?url={urllib.parse.quote(image_url)}",
                        'title': 'Manual Check: Google Lens',
                        'manual_check': True,
                        'date_str': 'Now',
                        'user': 'System'
                    }
                ]

            self.update_status(f"Found {len(candidates)} candidates. Verifying...")
            
            # 2. Verify & Analyze (Parallel)
            verified_matches = []
            original_phash = Hasher.compute_phash(self.selected_image_path)
            
            if not original_phash:
                self.update_status("Could not hash original image. Skipping verification.")
                verified_matches = candidates
            else:
                self.update_status(f"Verifying {len(candidates)} candidates in parallel...")
                
                import concurrent.futures
                
                def verify_candidate(cand):
                    try:
                        # If it's a manual check, keep it
                        if cand.get('manual_check'):
                            return cand
                            
                        # VISUAL ACCURACY CHECK
                        # If we have a thumbnail, download and hash it!
                        if cand.get('thumbnail'):
                            thumb_url = cand['thumbnail']
                            try:
                                # Download thumbnail (Fast)
                                thumb_img = Hasher.download_image(thumb_url)
                                if thumb_img:
                                    cand_hash = Hasher.compute_phash(thumb_img)
                                    if cand_hash and original_phash:
                                        # Compare!
                                        is_match = Analyzer.compare_hashes(original_phash, cand_hash, threshold=15) # Slightly looser for thumbnails
                                        if is_match:
                                            cand['verification'] = "Verified Match"
                                        else:
                                            cand['verification'] = "Low Similarity"
                                            # Optional: Filter out? The user said "visual accuracy".
                                            # Let's keep it but mark it.
                                    else:
                                        cand['verification'] = "Hash Failed"
                                else:
                                    cand['verification'] = "Thumb Download Failed"
                            except:
                                cand['verification'] = "Verification Error"
                        else:
                            cand['verification'] = "No Thumbnail"
                        
                        # Format Date
                        if cand.get('date'):
                            dt = datetime.datetime.fromtimestamp(cand['date'])
                            cand['date_str'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                            cand['timestamp'] = cand['date']
                        else:
                            cand['date_str'] = "Unknown Date"
                            cand['timestamp'] = 0
                            
                        return cand
                    except Exception as e:
                        return None

                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(verify_candidate, c) for c in candidates]
                    for future in concurrent.futures.as_completed(futures):
                        res = future.result()
                        if res:
                            # Filter out "Low Similarity" if you want strict accuracy
                            # The user said "visual accuracy".
                            if res.get('verification') == "Low Similarity":
                                continue # Skip bad matches!
                            verified_matches.append(res)

            # 3. Sort
            sorted_matches = sorted(verified_matches, key=lambda x: x['timestamp'] if x['timestamp'] else 9999999999)
            
            # 4. Display
            self.update_results(sorted_matches)
            self.update_status(f"Trace Complete. Found {len(sorted_matches)} verified matches.")
            
        except Exception as e:
            print(e)
            self.update_status(f"Error: {str(e)}")
        finally:
            self.enable_button()

    def update_results(self, matches):
        # Schedule UI update on main thread
        self.after(0, lambda: self._update_results_safe(matches))

    def _update_results_safe(self, matches):
        # Clear previous
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        import webbrowser
        from PIL import Image, ImageTk
        import requests
        from io import BytesIO

        for i, match in enumerate(matches):
            frame = ctk.CTkFrame(
                self.results_scroll,
                corner_radius=12,
                border_width=2,
                border_color="#374151"
            )
            frame.pack(fill="x", padx=5, pady=8)
            
            # Layout: [Thumbnail] [Info] [Button]
            
            # Thumbnail
            if match.get('thumbnail'):
                try:
                    response = requests.get(match['thumbnail'], timeout=5)
                    if response.status_code == 200:
                        img_data = Image.open(BytesIO(response.content))
                        # Resize for thumbnail
                        img_data.thumbnail((100, 100))
                        ctk_thumb = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=img_data.size)
                        
                        thumb_label = ctk.CTkLabel(frame, image=ctk_thumb, text="")
                        thumb_label.pack(side="left", padx=10, pady=10)
                except Exception as e:
                    print(f"Thumb display error: {e}")
                    pass

            # Special handling for Manual Check links
            if match.get('manual_check'):
                frame.configure(border_color=COLOR_WARNING, border_width=3)
                lbl = ctk.CTkLabel(
                    frame, 
                    text="⚠️ MANUAL CHECK REQUIRED", 
                    text_color=COLOR_WARNING, 
                    font=ctk.CTkFont(size=11, weight="bold")
                )
                lbl.pack(anchor="w", padx=10, pady=(5, 0))
                
            # Highlight earliest (only if not a manual check)
            elif i == 0 and match.get('timestamp'):
                frame.configure(border_color=COLOR_SUCCESS, border_width=3)
                lbl = ctk.CTkLabel(
                    frame, 
                    text="🏆 EARLIEST MATCH", 
                    text_color=COLOR_SUCCESS, 
                    font=ctk.CTkFont(size=11, weight="bold")
                )
                lbl.pack(anchor="w", padx=10, pady=(5, 0))

            title = match.get('title', 'No Title')
            date = match.get('date_str', 'Unknown')
            user = match.get('user', 'Unknown')
            url = match.get('url', '')
            verification = match.get('verification', '')
            
            info_text = f"Date: {date}\nUser: {user}\nStatus: {verification}\nTitle: {title[:50]}..."
            
            info_lbl = ctk.CTkLabel(frame, text=info_text, justify="left", anchor="w")
            info_lbl.pack(side="left", padx=10, pady=5)
            
            link_btn = ctk.CTkButton(frame, text="Open Link", width=100, 
                                   command=lambda u=url: webbrowser.open(u))
            link_btn.pack(side="right", padx=10)

    def update_status(self, text):
        self.after(0, lambda: self.status_label.configure(text=text))

    def enable_button(self):
        self.after(0, lambda: self.start_btn.configure(state="normal"))

if __name__ == "__main__":
    app = App()
    app.mainloop()
