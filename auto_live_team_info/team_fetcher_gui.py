import os
import json
import time
import logging
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from urllib.parse import urlparse, unquote
from app.team_information import get_team_info_by_url
from app.crud.team_information_crud import save_team_info

class TeamFetcherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Team Data Fetcher")
        self.root.geometry("900x700")
        
        self.is_running = False
        self.is_paused = False
        self.delay_var = tk.IntVar(value=180)
        self.progress_var = tk.DoubleVar()
        self.current_thread = None

        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.links_path = os.path.join(self.BASE_DIR, 'all_game_urls.json')
        self.processed_path = os.path.join(self.BASE_DIR, 'processed_teams.txt')
        self.log_file_path = os.path.join(self.BASE_DIR, 'team_fetch_log.txt')

        # Statistics
        self.stats = {
            'total': 0,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }

        self.setup_gui()
        self.setup_logging()
        self.validate_dependencies()

    def setup_gui(self):
        main = ttk.Frame(self.root, padding="10")
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # File selection section
        file_frame = ttk.LabelFrame(main, text="Configuration", padding="5")
        file_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        ttk.Label(file_frame, text="Team Links File:").grid(row=0, column=0, sticky="w")
        self.file_var = tk.StringVar(value=self.links_path)
        ttk.Entry(file_frame, textvariable=self.file_var, width=50).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(file_frame, text="Browse", command=self.browse_file).grid(row=0, column=2)

        ttk.Label(file_frame, text="Delay between requests (sec):").grid(row=1, column=0, sticky="w", pady=5)
        delay_frame = ttk.Frame(file_frame)
        delay_frame.grid(row=1, column=1, sticky="w", pady=5)
        ttk.Spinbox(delay_frame, from_=1, to=3600, textvariable=self.delay_var, width=10).pack(side="left")
        ttk.Label(delay_frame, text="(Recommended: 60-300 seconds)").pack(side="left", padx=(10, 0))

        # Statistics section
        stats_frame = ttk.LabelFrame(main, text="Statistics", padding="5")
        stats_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        
        self.stats_labels = {}
        for i, (key, label) in enumerate([
            ('total', 'Total URLs:'),
            ('processed', 'Processed:'),
            ('successful', 'Successful:'),
            ('failed', 'Failed:'),
            ('skipped', 'Skipped:')
        ]):
            ttk.Label(stats_frame, text=label).grid(row=0, column=i*2, sticky="w", padx=(0, 5))
            self.stats_labels[key] = ttk.Label(stats_frame, text="0", foreground="blue")
            self.stats_labels[key].grid(row=0, column=i*2+1, sticky="w", padx=(0, 15))

        # Progress section
        progress_frame = ttk.LabelFrame(main, text="Progress", padding="5")
        progress_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.grid(row=0, column=1)

        self.status_label = ttk.Label(progress_frame, text="Ready", foreground="green")
        self.status_label.grid(row=1, column=0, columnspan=2, pady=(5, 0))

        # Log section
        log_frame = ttk.LabelFrame(main, text="Log", padding="5")
        log_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # Control buttons
        button_frame = ttk.Frame(main)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)

        self.start_btn = ttk.Button(button_frame, text="Start", command=self.start)
        self.start_btn.pack(side="left", padx=5)
        
        self.pause_btn = ttk.Button(button_frame, text="Pause", command=self.pause, state="disabled")
        self.pause_btn.pack(side="left", padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="Clear Log", command=self.clear_log).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Open Log File", command=self.open_log_file).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Reset Progress", command=self.reset_progress).pack(side="left", padx=5)

        # Configure grid weights
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)

    def setup_logging(self):
        class TextHandler(logging.Handler):
            def __init__(self, widget):
                super().__init__()
                self.widget = widget

            def emit(self, record):
                msg = self.format(record)
                def append_text():
                    self.widget.insert(tk.END, msg + "\n")
                    self.widget.see(tk.END)
                    # Keep log size manageable
                    if int(self.widget.index('end-1c').split('.')[0]) > 1000:
                        self.widget.delete('1.0', '500.0')
                
                self.widget.after(0, append_text)

        self.logger = logging.getLogger("TeamFetcher")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()

        # File handler
        file_handler = logging.FileHandler(self.log_file_path, mode='a', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(file_handler)

        # GUI handler
        gui_handler = TextHandler(self.log_text)
        gui_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        self.logger.addHandler(gui_handler)

    def validate_dependencies(self):
        """Check if required modules are available"""
        try:
            # Test if the required modules can be imported
            from app.team_information import get_team_info_by_url
            from app.crud.team_information_crud import save_team_info
            self.logger.info("✅ Dependencies validated successfully")
        except ImportError as e:
            self.logger.error(f"❌ Missing dependency: {e}")
            messagebox.showerror("Dependency Error", f"Required module not found: {e}")

    def browse_file(self):
        path = filedialog.askopenfilename(
            title="Select JSON file containing team URLs", 
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            self.file_var.set(path)
            self.links_path = path
            self.validate_json_file()

    def validate_json_file(self):
        """Validate the selected JSON file"""
        try:
            with open(self.links_path, 'r', encoding='utf-8') as f:
                urls = json.load(f)
                if isinstance(urls, list):
                    self.logger.info(f"✅ Loaded {len(urls)} URLs from file")
                    self.stats['total'] = len(urls)
                    self.update_stats()
                else:
                    self.logger.error("❌ JSON file must contain an array of URLs")
        except Exception as e:
            self.logger.error(f"❌ Invalid JSON file: {e}")

    def load_processed(self):
        if os.path.exists(self.processed_path):
            with open(self.processed_path, 'r', encoding='utf-8') as f:
                processed_set = set(line.strip() for line in f if line.strip())
                self.logger.info(f"📁 Loaded {len(processed_set)} previously processed URLs")
                return processed_set
        return set()

    def save_processed(self, url):
        with open(self.processed_path, 'a', encoding='utf-8') as f:
            f.write(url + "\n")

    def update_progress(self, current, total):
        percent = (current / total) * 100 if total else 0
        self.progress_var.set(percent)
        self.progress_label.config(text=f"{percent:.1f}% ({current}/{total})")

    def update_stats(self):
        for key, label in self.stats_labels.items():
            label.config(text=str(self.stats[key]))

    def update_status(self, message, color="black"):
        self.status_label.config(text=message, foreground=color)

    def fetch_worker(self):
        try:
            with open(self.links_path, 'r', encoding='utf-8') as f:
                urls = json.load(f)
        except Exception as e:
            self.logger.error(f"❌ Failed to load JSON: {e}")
            self.root.after(0, self.finish)
            return

        processed = self.load_processed()
        new_urls = [url for url in urls if url not in processed]
        
        self.stats['total'] = len(urls)
        self.stats['skipped'] = len(processed)
        total_new = len(new_urls)

        self.root.after(0, self.update_stats)

        if total_new == 0:
            self.logger.info("✅ No new teams to process.")
            self.root.after(0, self.finish)
            return

        delay = self.delay_var.get()
        self.root.after(0, self.update_status, f"Processing {total_new} URLs...", "blue")

        for index, url in enumerate(new_urls, 1):
            if not self.is_running:
                self.logger.info("🛑 Stopped by user.")
                break

            # Handle pause
            while self.is_paused and self.is_running:
                time.sleep(0.5)

            if not self.is_running:
                break

            self.logger.info(f"[{index}/{total_new}] Fetching: {url}")
            
            try:
                game, team = self.parse_url(url)
                if not game or not team:
                    self.logger.warning(f"⚠️ Invalid URL format: {url}")
                    self.stats['failed'] += 1
                    continue

                self.root.after(0, self.update_status, f"Fetching: {team}", "blue")
                
                data, _ = get_team_info_by_url(url)
                if not data:
                    self.logger.warning(f"❌ Failed to fetch info for: {team}")
                    self.stats['failed'] += 1
                    continue

                if save_team_info(game, team, data):
                    self.logger.info(f"✅ Saved info for: {team}")
                    self.save_processed(url)
                    self.stats['successful'] += 1
                else:
                    self.logger.warning(f"❌ Failed to save data for: {team}")
                    self.stats['failed'] += 1

            except Exception as e:
                self.logger.error(f"❌ Exception while processing {url}: {e}")
                self.stats['failed'] += 1

            self.stats['processed'] += 1
            self.root.after(0, self.update_progress, index, total_new)
            self.root.after(0, self.update_stats)

            # Delay between requests
            if index < total_new:
                self.logger.info(f"⏳ Waiting {delay} seconds...")
                self.root.after(0, self.update_status, f"Waiting {delay}s... ({index}/{total_new})", "orange")
                
                for sec in range(delay):
                    if not self.is_running:
                        break
                    # Handle pause during delay
                    while self.is_paused and self.is_running:
                        time.sleep(0.5)
                    if not self.is_running:
                        break
                    time.sleep(1)

        self.root.after(0, self.finish)

    def parse_url(self, url):
        """Parse Liquipedia URL to extract game and team name"""
        try:
            parsed = urlparse(url)
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2:
                game = parts[0].lower()
                team = unquote(parts[1])
                return game, team
        except Exception as e:
            self.logger.error(f"Error parsing URL {url}: {e}")
            return None, None
        return None, None

    def start(self):
        if not os.path.exists(self.file_var.get()):
            messagebox.showerror("File not found", "Please select a valid JSON file.")
            return
        
        self.is_running = True
        self.is_paused = False
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.stop_btn.config(state="normal")
        
        self.current_thread = threading.Thread(target=self.fetch_worker, daemon=True)
        self.current_thread.start()
        self.logger.info("🚀 Started team data fetching process")

    def pause(self):
        if self.is_paused:
            self.is_paused = False
            self.pause_btn.config(text="Pause")
            self.update_status("Resumed", "blue")
            self.logger.info("▶️ Resumed processing")
        else:
            self.is_paused = True
            self.pause_btn.config(text="Resume")
            self.update_status("Paused", "orange")
            self.logger.info("⏸️ Paused processing")

    def stop(self):
        self.is_running = False
        self.is_paused = False
        self.logger.info("🛑 Stop requested")

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def open_log_file(self):
        """Open log file in default text editor"""
        try:
            if os.path.exists(self.log_file_path):
                if os.name == 'nt':  # Windows
                    os.startfile(self.log_file_path)
                else:  # Unix/Linux/Mac
                    os.system(f'open "{self.log_file_path}"')
        except Exception as e:
            self.logger.error(f"Failed to open log file: {e}")

    def reset_progress(self):
        """Reset processed teams file"""
        if messagebox.askyesno("Reset Progress", "This will clear all processed team records. Are you sure?"):
            try:
                if os.path.exists(self.processed_path):
                    os.remove(self.processed_path)
                self.stats = {key: 0 for key in self.stats}
                self.update_stats()
                self.progress_var.set(0)
                self.progress_label.config(text="0%")
                self.update_status("Progress reset", "green")
                self.logger.info("🔄 Progress reset successfully")
            except Exception as e:
                self.logger.error(f"Failed to reset progress: {e}")

    def finish(self):
        self.is_running = False
        self.is_paused = False
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled", text="Pause")
        self.stop_btn.config(state="disabled")
        
        success_rate = (self.stats['successful'] / max(self.stats['processed'], 1)) * 100
        self.update_status(f"Completed! Success rate: {success_rate:.1f}%", "green")
        self.logger.info(f"🎉 Process completed! Success: {self.stats['successful']}, Failed: {self.stats['failed']}")

def main():
    root = tk.Tk()
    app = TeamFetcherGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()