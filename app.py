import tkinter as tk
from tkinter import messagebox
import subprocess
import os
from pathlib import Path

BLOCKLIST_PATH = "/etc/hosts"
REDIRECT_IP = "127.0.0.1"
BLOCKER_TAG = "# [WebBlocker]"

# Local record to track blocked sites
BLOCKED_DB = Path.home() / ".webblocker"
BLOCKED_FILE = BLOCKED_DB / "blocked.txt"

class WebsiteBlockerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WebBlocker")
        self.root.geometry("400x500")
        self.dark_mode = True
        self._init_dirs()

        self.blocked_sites = self.load_blocked_sites()

        self.set_theme()
        self.build_ui()

    def _init_dirs(self):
        BLOCKED_DB.mkdir(exist_ok=True)
        BLOCKED_FILE.touch(exist_ok=True)

    def set_theme(self):
        if self.dark_mode:
            self.bg_color = "#121212"
            self.fg_color = "white"
            self.entry_bg = "#1e1e1e"
        else:
            self.bg_color = "#ffffff"
            self.fg_color = "#000000"
            self.entry_bg = "#f0f0f0"
        self.root.configure(bg=self.bg_color)

    def build_ui(self):
        self.title_label = tk.Label(self.root, text="WebBlocker", font=("Helvetica", 20), bg=self.bg_color, fg=self.fg_color)
        self.title_label.pack(pady=10)

        self.listbox = tk.Listbox(self.root, font=("Helvetica", 14), bg=self.entry_bg, fg=self.fg_color, height=10, selectbackground="#444")
        self.listbox.pack(fill="both", expand=True, padx=20, pady=10)

        self.entry = tk.Entry(self.root, font=("Helvetica", 14), bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color)
        self.entry.pack(pady=10, padx=20, fill="x")

        self.add_button = tk.Button(self.root, text="Block Website", command=self.block_website, bg="#2196F3", fg="white")
        self.add_button.pack(pady=5)

        self.remove_button = tk.Button(self.root, text="Unblock Selected", command=self.unblock_selected, bg="#f44336", fg="white")
        self.remove_button.pack(pady=5)

        self.toggle_button = tk.Button(self.root, text="Toggle Light/Dark Mode", command=self.toggle_mode, bg="#607D8B", fg="white")
        self.toggle_button.pack(pady=10)

        self.update_listbox()

    def load_blocked_sites(self):
        if BLOCKED_FILE.exists():
            with open(BLOCKED_FILE, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        return []

    def save_blocked_sites(self):
        with open(BLOCKED_FILE, 'w') as f:
            for site in self.blocked_sites:
                f.write(f"{site}\n")

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for site in self.blocked_sites:
            self.listbox.insert(tk.END, site)

    def block_website(self):
        url = self.entry.get().strip().lower()
        if not url:
            return
        if url in self.blocked_sites:
            messagebox.showinfo("Info", "Website is already blocked.")
            return

        # Append to hosts using sudo
        try:
            cmd = f'echo "{REDIRECT_IP} {url} {BLOCKER_TAG}" | sudo tee -a {BLOCKLIST_PATH}'
            subprocess.run(cmd, shell=True, check=True)
            subprocess.run(["sudo", "dscacheutil", "-flushcache"])
            self.blocked_sites.append(url)
            self.save_blocked_sites()
            self.update_listbox()
            self.entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Could not block site:\n{e}")

    def unblock_selected(self):
        selected = self.listbox.curselection()
        if not selected:
            return
        site = self.listbox.get(selected[0])

        # Remove from hosts file (still needs sudo)
        try:
            with open(BLOCKLIST_PATH, 'r') as f:
                lines = f.readlines()
            new_lines = [line for line in lines if site not in line or BLOCKER_TAG not in line]

            temp_file = Path("/tmp/hosts_temp")
            with open(temp_file, 'w') as f:
                f.writelines(new_lines)

            subprocess.run(["sudo", "cp", str(temp_file), BLOCKLIST_PATH], check=True)
            subprocess.run(["sudo", "dscacheutil", "-flushcache"])

            self.blocked_sites.remove(site)
            self.save_blocked_sites()
            self.update_listbox()
        except Exception as e:
            messagebox.showerror("Error", f"Could not unblock site:\n{e}")

    def toggle_mode(self):
        self.dark_mode = not self.dark_mode
        self.set_theme()
        self.title_label.config(bg=self.bg_color, fg=self.fg_color)
        self.listbox.config(bg=self.entry_bg, fg=self.fg_color)
        self.entry.config(bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color)
        self.root.configure(bg=self.bg_color)

# Entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = WebsiteBlockerApp(root)
    root.mainloop()