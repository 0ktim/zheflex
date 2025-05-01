import sys
import csv
import serial
import serial.tools.list_ports
import customtkinter as ctk
from customtkinter import CTkFont
from tkinter import ttk, messagebox, filedialog

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class ReactionTesterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        icon_path = os.path.join(base_path, "zheflex.ico")

        self.iconbitmap(default=icon_path)
        
        self.title("Zheflex")
        self.geometry("1100x800")
        self.resizable(True, True)
        self.minsize(1000, 800)

        self.default_font = CTkFont(family="Segoe UI", size=24, weight="bold")
        self.test_running = False

        top_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#ECECEC")
        top_frame.pack(fill="x", padx=20, pady=(20,10))
        top_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top_frame,
            text="Име на участника:",
            font=self.default_font,
            text_color="#333333",
            bg_color=top_frame.cget("fg_color")
        ).grid(row=0, column=0, padx=(10,5), pady=10, sticky="w")

        self.entry_name = ctk.CTkEntry(
            top_frame,
            placeholder_text="Въведете име...",
            font=self.default_font,
            fg_color="white",
            border_color="#CCCCCC",
            corner_radius=8
        )
        self.entry_name.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        ctk.CTkLabel(
            top_frame,
            text="COM порт:",
            font=self.default_font,
            text_color="#333333",
            bg_color=top_frame.cget("fg_color")
        ).grid(row=0, column=2, padx=(20,5), pady=10, sticky="w")

        self.update_idletasks()
        entry_h = self.entry_name.winfo_height()

        ports = self.get_com_ports()
        if not ports:
            ports = ["Няма портове"]

        self.combo = ctk.CTkOptionMenu(
            top_frame,
            values=ports,
            font=self.default_font,
            fg_color="white",
            button_color="white",
            dropdown_fg_color="white",
            button_hover_color="white",
            corner_radius=8,
            height=entry_h,
            text_color="#333333",
            dropdown_text_color="#333333"
        )
        self.combo.grid(row=0, column=3, padx=5, pady=10, sticky="w")
        self.combo.set(ports[0])
        
        self.after(2000, self.poll_ports)

        ctk.CTkButton(
            top_frame,
            text="Свържи",
            font=self.default_font,
            fg_color="#1F6AA5",
            hover_color="#3B82F6",
            text_color="white",
            corner_radius=8,
            width=150,
            command=self.connect_serial
        ).grid(row=0, column=4, padx=(10,20), pady=10, sticky="w")


        middle_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#FAFAFA")
        middle_frame.pack(fill="both", expand=True, padx=20, pady=10)

        style = ttk.Style(middle_frame)
        style.theme_use("clam")
        style.configure("Treeview",
                        background="white",
                        fieldbackground="white",
                        font=('Segoe UI', 16),
                        rowheight=30)
        style.configure("Treeview.Heading",
                        background="#E1E1E1",
                        font=('Segoe UI', 16, 'bold'))
        style.map("Treeview.Heading",
                  background=[("active", "#D0D0D0")])

        self.tree = ttk.Treeview(
            middle_frame,
            columns=("Name", "Gas", "Brake"),
            show="headings",
            selectmode="browse"
        )
        for col, text, w in [("Name","Име",200),
                             ("Gas","Газ (ms)",200),
                             ("Brake","Спирачка (ms)",200)]:
            self.tree.heading(col, text=text)
            self.tree.column(col, anchor="center", width=w)
        self.tree.pack(fill="both", expand=True, side="left", padx=(5,0), pady=5)

        scrollbar = ttk.Scrollbar(middle_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y", padx=(0,5), pady=5)
        self.tree.configure(yscrollcommand=scrollbar.set)


        button_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#F0F0F0")
        button_frame.pack(fill="x", padx=20, pady=(0,10))
        button_frame.grid_columnconfigure(0, weight=1)

        self.test_button = ctk.CTkButton(
            button_frame,
            text="СТАРТ",
            font=self.default_font,
            corner_radius=8,
            hover=True,
            text_color="white",
            fg_color="#1F7335",
            hover_color="#248c40",
            command=self.toggle_test,
            state="disabled"
        )
        self.test_button.grid(row=0, column=0, pady=10, sticky="ew")


        bottom_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#F0F0F0")
        bottom_frame.pack(fill="x", padx=20, pady=(0,20))
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)
        bottom_frame.grid_columnconfigure(2, weight=0)
        bottom_frame.grid_columnconfigure(3, weight=0)

        self.gas_stat_label = ctk.CTkLabel(
            bottom_frame,
            text="Газ: –",
            font=self.default_font,
            text_color="#333333"
        )
        self.gas_stat_label.grid(row=0, column=0, columnspan=2,
                                 padx=5, pady=(10,2), sticky="w")

        self.brake_stat_label = ctk.CTkLabel(
            bottom_frame,
            text="Спирачка: –",
            font=self.default_font,
            text_color="#333333"
        )
        self.brake_stat_label.grid(row=1, column=0, columnspan=2,
                                   padx=5, pady=(2,10), sticky="w")

        export_btn = ctk.CTkButton(
            bottom_frame,
            text="Експорт CSV...",
            font=self.default_font,
            fg_color="#1F6AA5",
            hover_color="#3B82F6",
            text_color="white",
            corner_radius=8,
            width=220,
            command=self.export_csv
        )
        export_btn.grid(row=0, column=2, rowspan=2, padx=5, pady=10, sticky="ne")

        clear_btn = ctk.CTkButton(
            bottom_frame,
            text="Изчисти",
            font=self.default_font,
            fg_color="#c23030",
            hover_color="#e03030",
            text_color="white",
            corner_radius=8,
            width=150,
            command=self.clear_data
        )
        clear_btn.grid(row=0, column=3, rowspan=2, padx=5, pady=10, sticky="ne")

        watermark = ctk.CTkLabel(
            self,
            text="Author: 0ktim",                  # смени на своето име
            font=CTkFont(family="Segoe UI", size=14),   # по-малък шрифт
            fg_color="#F0F0F0",
            text_color="#cacaca"                        # бледо сиво
        )
        watermark.place(relx=0.98, rely=0.97, anchor="se")

        self.ser = None
        self.results = []
        self.after(200, self.read_serial)


    def get_com_ports(self):
        return [p.device for p in serial.tools.list_ports.comports()]

    def poll_ports(self):
        ports = self.get_com_ports()
        new_vals = ports if ports else ["Няма портове"]
        if set(new_vals) != set(self.combo.cget("values")):
            self.combo.configure(values=new_vals)
            self.combo.set(new_vals[0])
        self.after(2000, self.poll_ports)

    def connect_serial(self):
        port = self.combo.get()
        if not port:
            messagebox.showwarning("Внимание", "Моля, изберете COM порт!")
            return
        try:
            self.ser = serial.Serial(port, 9600, timeout=1)
            messagebox.showinfo("Успех", f"Свързано към {port}")
            self.test_button.configure(state="normal")
        except Exception as e:
            messagebox.showerror("Грешка при свързване", str(e))


    def toggle_test(self):
        if not self.ser:
            messagebox.showwarning("Няма връзка", "Свържете се с порта първо!")
            return
        if not self.test_running:
            self.ser.write(b'S')
            self.test_running = True
            self.test_button.configure(
                text="СТОП", fg_color="#A51F1F", hover_color="#bd2424"
            )
        else:
            self.ser.write(b'T')
            self.test_running = False
            self.test_button.configure(
                text="СТАРТ", fg_color="#1F7335", hover_color="#248c40"
            )


    def read_serial(self):
        if self.test_running and self.ser and self.ser.in_waiting:
            line = self.ser.readline().decode('utf-8', errors='replace').strip()
            parts = line.split(',')
            if len(parts) == 2:
                name = self.entry_name.get().strip() or "-"
                try:
                    gas, brake = map(int, parts)
                except ValueError:
                    return self.after(200, self.read_serial)

                self.tree.insert("", "end", values=(name, gas, brake))
                self.results.append((name, gas, brake))
                with open('results.csv','a',newline='',encoding='utf-8-sig') as f:
                    csv.writer(f).writerow([name, gas, brake])
                self.update_stats()

                self.ser.write(b'T')
                self.test_running = False
                self.test_button.configure(
                    text="Start Test", fg_color="#1F7335", hover_color="#248c40"
                )

        self.after(200, self.read_serial)


    def update_stats(self):
        if not self.results:
            self.gas_stat_label.configure(text="Газ: –")
            self.brake_stat_label.configure(text="Спирачка: –")
            return

        gases  = [g for _, g, _ in self.results]
        brakes = [b for _, _, b in self.results]

        avg_g = round(sum(gases) / len(gases))
        best_g = min(gases)
        worst_g = max(gases)

        avg_b = round(sum(brakes) / len(brakes))
        best_b = min(brakes)
        worst_b = max(brakes)

        self.gas_stat_label.configure(
            text=f" Газ             – средно: {avg_g} ms    най-добро: {best_g} ms    най-лошо: {worst_g} ms"
        )
        self.brake_stat_label.configure(
            text=f" Спирачка – средно: {avg_b} ms    най-добро: {best_b} ms    най-лошо: {worst_b} ms"
        )


    def export_csv(self):
        if not self.results:
            messagebox.showinfo("Няма данни", "Все още няма резултати за експорт.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файлове","*.csv")],
            title="Запиши CSV файл като..."
        )
        if path:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["Име", "Газ (ms)", "Спирачка (ms)"])
                writer.writerows(self.results)
            messagebox.showinfo("Готово", f"Файлът е записан:\n{path}")

    def clear_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results.clear()
        self.gas_stat_label.configure(text="Газ: –")
        self.brake_stat_label.configure(text="Спирачка: –")


if __name__ == "__main__":
    app = ReactionTesterApp()
    app.mainloop()
