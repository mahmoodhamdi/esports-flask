import os
import json
import time
import logging
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from urllib.parse import urlparse, unquote
from datetime import datetime
from app.crud.player_information_crud import save_player_info
from app.player_information import get_player_info as get_player_info_api

class PlayerFetcherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Player Data Fetcher")
        self.root.geometry("800x600")
        
        # Variables
        self.is_running = False
        self.current_thread = None
        self.delay_var = tk.IntVar(value=180)
        self.progress_var = tk.DoubleVar()
        
        # Paths
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.log_file_path = os.path.join(self.BASE_DIR, 'log.txt')
        self.processed_file_path = os.path.join(self.BASE_DIR, 'processed_players.txt')
        self.player_links_path = os.path.join(self.BASE_DIR, 'player_links.json')
        
        self.setup_gui()
        self.setup_logging()
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Player Data Fetcher", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection
        ttk.Label(main_frame, text="Player Links File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.file_var = tk.StringVar(value=self.player_links_path)
        file_entry = ttk.Entry(main_frame, textvariable=self.file_var, width=50)
        file_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Browse", 
                  command=self.browse_file).grid(row=1, column=2, padx=(5, 0), pady=5)
        
        # Delay setting
        ttk.Label(main_frame, text="Delay (seconds):").grid(row=2, column=0, sticky=tk.W, pady=5)
        delay_spinbox = ttk.Spinbox(main_frame, from_=1, to=3600, width=10, 
                                   textvariable=self.delay_var)
        delay_spinbox.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        
        # Progress bar
        ttk.Label(main_frame, text="Progress:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100, length=300)
        self.progress_bar.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        self.progress_label = ttk.Label(main_frame, text="0%")
        self.progress_label.grid(row=3, column=2, padx=(5, 0), pady=5)
        
        # Log display
        ttk.Label(main_frame, text="Log Output:").grid(row=4, column=0, sticky=(tk.W, tk.N), pady=(5, 0))
        self.log_display = scrolledtext.ScrolledText(main_frame, width=80, height=20)
        self.log_display.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), 
                             padx=(5, 0), pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=(10, 0), sticky=(tk.W, tk.E))
        
        self.start_button = ttk.Button(button_frame, text="Start Processing", 
                                      command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop Processing", 
                                     command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Clear Log", 
                  command=self.clear_log).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="View Status", 
                  command=self.show_status).pack(side=tk.LEFT, padx=(0, 10))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def setup_logging(self):
        # Create custom logging handler for GUI
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget, status_var):
                super().__init__()
                self.text_widget = text_widget
                self.status_var = status_var
                
            def emit(self, record):
                msg = self.format(record)
                # Schedule GUI update in main thread
                self.text_widget.after(0, self._append_log, msg)
                self.status_var.set(msg)
                
            def _append_log(self, msg):
                self.text_widget.insert(tk.END, msg + '\n')
                self.text_widget.see(tk.END)
        
        # Setup logging
        self.logger = logging.getLogger('PlayerFetcher')
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Add file handler
        file_handler = logging.FileHandler(self.log_file_path, mode='a', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(file_handler)
        
        # Add GUI handler
        gui_handler = GUILogHandler(self.log_display, self.status_var)
        gui_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(gui_handler)
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Player Links JSON File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=self.BASE_DIR
        )
        if filename:
            self.file_var.set(filename)
            self.player_links_path = filename
            
    def load_processed_links(self):
        if os.path.exists(self.processed_file_path):
            with open(self.processed_file_path, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f.readlines())
        return set()
        
    def save_processed_link(self, url):
        with open(self.processed_file_path, 'a', encoding='utf-8') as f:
            f.write(url + '\n')
            
    def update_progress(self, current, total):
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
            self.progress_label.config(text=f"{progress:.1f}% ({current}/{total})")
        else:
            self.progress_var.set(0)
            self.progress_label.config(text="0%")
            
    def fetch_players_worker(self):
        try:
            # Load URLs
            with open(self.player_links_path, 'r', encoding='utf-8') as f:
                urls = json.load(f)
            if not isinstance(urls, list):
                self.logger.error("player_links.json must contain a JSON array of URLs")
                return
        except Exception as e:
            self.logger.exception(f"Failed to load player_links.json: {e}")
            return
            
        processed_links = self.load_processed_links()
        remaining = [url for url in urls if url not in processed_links]
        
        if not remaining:
            self.logger.info("✅ All players have already been processed.")
            return
            
        total_remaining = len(remaining)
        delay_seconds = self.delay_var.get()
        start_all = time.time()
        
        for index, url in enumerate(remaining):
            if not self.is_running:  # Check if stopped
                self.logger.info("❌ Processing stopped by user")
                break
                
            try:
                start_time = time.time()
                parsed_url = urlparse(url)
                path_parts = parsed_url.path.strip("/").split("/")
                if len(path_parts) != 2:
                    self.logger.warning(f"[{index+1}/{total_remaining}] Invalid URL format: {url}")
                    continue
                    
                game = path_parts[0].lower()
                player = unquote(path_parts[1])
                
                # Update progress
                self.root.after(0, self.update_progress, index + 1, total_remaining)
                
                self.logger.info(f"[{index+1}/{total_remaining}] Fetching info for: {player} ({game})")
                
                data, _ = get_player_info_api(game, player)
                if not data:
                    self.logger.warning(f"⚠️ API fetch failed for {player} ({game})")
                    continue
                    
                if not save_player_info(game, player, data):
                    self.logger.error(f"❌ DB save failed for {player} ({game})")
                    continue
                    
                elapsed = time.time() - start_time
                self.logger.info(f"✅ Success for {player} ({game}) [Took {elapsed:.2f} sec]")
                
                self.save_processed_link(url)
                
            except Exception as e:
                self.logger.exception(f"[{index+1}/{total_remaining}] Exception while processing {url}: {e}")
                
            if self.is_running and index < total_remaining - 1:  # Don't wait after last item
                self.logger.info(f"⏳ Waiting {delay_seconds} seconds before next player...")
                for i in range(delay_seconds):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
        total_time = time.time() - start_all
        self.logger.info(f"🎉 Done! Processed {len(remaining)} players in {total_time:.2f} seconds.")
        
        # Reset UI state
        self.root.after(0, self.processing_finished)
        
    def start_processing(self):
        if not os.path.exists(self.file_var.get()):
            messagebox.showerror("Error", "Player links file not found!")
            return
            
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("Processing...")
        
        # Start processing in separate thread
        self.current_thread = threading.Thread(target=self.fetch_players_worker)
        self.current_thread.daemon = True
        self.current_thread.start()
        
    def stop_processing(self):
        self.is_running = False
        self.status_var.set("Stopping...")
        self.logger.info("🛑 Stop requested by user...")
        
    def processing_finished(self):
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Finished")
        
    def clear_log(self):
        self.log_display.delete(1.0, tk.END)
        
    def show_status(self):
        try:
            with open(self.file_var.get(), 'r', encoding='utf-8') as f:
                urls = json.load(f)
            total_urls = len(urls) if isinstance(urls, list) else 0
            
            processed_links = self.load_processed_links()
            processed_count = len(processed_links)
            remaining_count = total_urls - processed_count
            
            status_msg = f"""Status Summary:
            
Total URLs: {total_urls}
Processed: {processed_count}
Remaining: {remaining_count}
Progress: {(processed_count/total_urls*100):.1f}% complete

Files:
- Links file: {self.file_var.get()}
- Processed file: {self.processed_file_path}
- Log file: {self.log_file_path}"""
            
            messagebox.showinfo("Status", status_msg)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not load status: {e}")

def main():
    root = tk.Tk()
    app = PlayerFetcherGUI(root)
    
    # Handle window closing
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("Quit", "Processing is running. Stop and quit?"):
                app.stop_processing()
                root.after(1000, root.destroy)  # Give time to stop
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()