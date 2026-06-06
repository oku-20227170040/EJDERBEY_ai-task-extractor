import os
import re
import zipfile
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

# Akademik NLP Kütüphanesi
import stanza

# --- 1. NLP VE GÖREV ÇIKARIMI (POS TAGGING & MORPHOLOGICAL ANALYSIS) ---
class NLPProcessor:
    def __init__(self):
        # Stanza'nın Türkçe modelini indir (Eğer yüklü değilse arka planda otomatik indirir)
        # Sadece tokenize (kelime ayırma), mwt (çoklu kelime), pos (sözcük türü) ve lemma (kök) işlemcilerini kullanıyoruz.
        stanza.download('tr', processors='tokenize,mwt,pos,lemma', verbose=False)
        self.nlp = stanza.Pipeline('tr', processors='tokenize,mwt,pos,lemma', use_gpu=False, verbose=False)
        
        # Günlük sohbet filtreleri (Görev kipi alsa bile geçmiş zamansa veya sohbetse ele)
        self.ignore_words = {"zaten", "dün", "önceki", "acaba", "keşke", "belki", "malesef", "maalesef"}
        
        # Sadece belirli emir kiplerini görev kabul etmek için (Örn: "bak", "dur" görev değildir, "hazırla" görevdir)
        self.action_verbs = {
            "yap", "et", "git", "al", "ver", "gönder", "ilet", "ara", "sor", 
            "hazırla", "çöz", "hallet", "planla", "ayarla", "buluş", "görüş", "yaz", "oku"
        }
        
        # Zaman bildiren ifadeler
        self.time_keywords = ["yarın", "akşam", "pazartesi", "salı", "çarşamba", "perşembe", 
                              "cuma", "cumartesi", "pazar", "haftaya", "bugün", "sabah", "öğle", "sonra"]

    def extract_time(self, text):
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        words = clean_text.split()
        for word in words:
            if word in self.time_keywords:
                return word.capitalize()
        return "Belirtilmedi"

    def is_task(self, text):
        # Ön filtreleme: Cümle çok kısa veya sohbet içeriyorsa NLP modelini yorma
        words = text.lower().split()
        if len(words) < 2 or len(words) > 50 or any(ignore in words for ignore in self.ignore_words):
            return False

        # --- AKADEMİK NLP ANALİZİ BAŞLIYOR ---
        doc = self.nlp(text)
        
        for sentence in doc.sentences:
            for word in sentence.words:
                
                # 1. KURAL: Kelime Kökü (Lemma) Analizi 
                # (Eğer cümlenin içinde kökü 'gerek', 'lazım', 'şart' olan bir sıfat/isim varsa)
                if word.lemma in ["gerek", "gerekmek", "lazım", "şart", "mecbur"]:
                    return True
                    
                # 2. KURAL: Sözcük Türü (UPOS) ve Morfolojik Özellikler (Feats)
                # Eğer kelime bir FİİL (VERB) ise, aldığı eklere (kiplere) bak!
                if word.upos == "VERB" and word.feats:
                    
                    # A) Gereklilik Kipi (-malı, -meli) -> Morphological Feature: Mood=Nec
                    if "Mood=Nec" in word.feats:
                        return True
                        
                    # B) İstek ve Öneri Kipi (-alım, -elim) -> Morphological Feature: Mood=Opt
                    if "Mood=Opt" in word.feats:
                        return True
                        
                    # C) Emir Kipi -> Morphological Feature: Mood=Imp
                    # Her emiri ("gel", "gül") değil, sadece iş/eylem belirtenleri al.
                    if "Mood=Imp" in word.feats and word.lemma in self.action_verbs:
                        return True

        return False

# --- 2. GÖREV VE DİNAMİK DOSYA YÖNETİMİ ---
class TaskManager:
    def __init__(self):
        self.tasks = []
        self.contacts = set()

    def add_task(self, date, sender, content, deadline):
        task_id = len(self.tasks) + 1
        self.tasks.append({
            "ID": task_id, 
            "Tarih": date, 
            "Kişi": sender, 
            "Görev": content, 
            "Zaman Etiketi": deadline
        })
        self.contacts.add(sender)

    def delete_task(self, task_id):
        self.tasks = [t for t in self.tasks if t["ID"] != task_id]

    def update_task(self, task_id, new_content):
        for t in self.tasks:
            if t["ID"] == task_id:
                t["Görev"] = new_content
                break

    def get_contacts(self):
        return sorted(list(self.contacts))

    def get_tasks_by_contact(self, contact_name):
        if contact_name == "Tüm Kişiler":
            return self.tasks
        return [t for t in self.tasks if t["Kişi"] == contact_name]

    def save_to_csv(self, project_name):
        if not self.tasks:
            return False, "Kaydedilecek görev bulunamadı."
        
        results_dir = os.path.join("RESULTS", project_name)
        os.makedirs(results_dir, exist_ok=True)
        file_path = os.path.join(results_dir, f"{project_name}_gorevler.csv")
        
        df = pd.DataFrame(self.tasks)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        return True, file_path

# --- 3. MODERN ARAYÜZ (GUI) ---
class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EJDERBEY - Akademik NLP Görev Asistanı")
        self.root.geometry("900x600")
        self.root.configure(bg="#f4f4f9")
        
        self.processor = None # İşlem başlayınca yüklenecek (Arayüz donmasın diye)
        self.task_manager = TaskManager()
        self.current_project = "Bilinmeyen_Proje"

        self.setup_ui()

    def setup_ui(self):
        top_frame = tk.Frame(self.root, bg="#2c3e50", pady=15)
        top_frame.pack(fill=tk.X)

        title_lbl = tk.Label(top_frame, text="WhatsApp Görev Çıkarıcı (POS Tagging)", font=("Segoe UI", 16, "bold"), bg="#2c3e50", fg="white")
        title_lbl.pack(side=tk.LEFT, padx=20)

        upload_btn = tk.Button(top_frame, text="📂 ZIP Yükle", font=("Segoe UI", 10, "bold"), bg="#27ae60", fg="white", cursor="hand2", command=self.process_zip, relief=tk.FLAT, padx=15, pady=5)
        upload_btn.pack(side=tk.RIGHT, padx=20)

        export_btn = tk.Button(top_frame, text="💾 Excel'e Kaydet", font=("Segoe UI", 10, "bold"), bg="#2980b9", fg="white", cursor="hand2", command=self.save_data, relief=tk.FLAT, padx=15, pady=5)
        export_btn.pack(side=tk.RIGHT, padx=10)

        middle_frame = tk.Frame(self.root, bg="#f4f4f9")
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        left_frame = tk.Frame(middle_frame, bg="#f4f4f9")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))

        lbl_contacts = tk.Label(left_frame, text="👥 Kişiler Listesi", font=("Segoe UI", 11, "bold"), bg="#f4f4f9")
        lbl_contacts.pack(anchor="w", pady=(0, 5))

        self.contact_listbox = tk.Listbox(left_frame, width=25, font=("Segoe UI", 10), selectbackground="#3498db", relief=tk.FLAT, borderwidth=1, highlightthickness=1)
        self.contact_listbox.pack(fill=tk.Y, expand=True)
        self.contact_listbox.bind('<<ListboxSelect>>', self.filter_by_contact)

        right_frame = tk.Frame(middle_frame, bg="#f4f4f9")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        lbl_tasks = tk.Label(right_frame, text="📋 Bulunan Görevler", font=("Segoe UI", 11, "bold"), bg="#f4f4f9")
        lbl_tasks.pack(anchor="w", pady=(0, 5))

        columns = ("ID", "Tarih", "Kişi", "Görev", "Zaman")
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("ID", text="ID")
        self.tree.column("ID", width=40, anchor="center")
        self.tree.heading("Tarih", text="Tarih")
        self.tree.column("Tarih", width=120, anchor="center")
        self.tree.heading("Kişi", text="Kişi")
        self.tree.column("Kişi", width=120, anchor="w")
        self.tree.heading("Görev", text="Görev İçeriği")
        self.tree.column("Görev", width=350, anchor="w")
        self.tree.heading("Zaman", text="Zaman Etiketi")
        self.tree.column("Zaman", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        bottom_frame = tk.Frame(self.root, bg="#f4f4f9")
        bottom_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        del_btn = tk.Button(bottom_frame, text="➖ Görevi Sil", font=("Segoe UI", 10, "bold"), bg="#e74c3c", fg="white", cursor="hand2", command=self.delete_selected_task, relief=tk.FLAT, padx=15)
        del_btn.pack(side=tk.RIGHT)

        edit_btn = tk.Button(bottom_frame, text="✏️ Görevi Düzenle", font=("Segoe UI", 10, "bold"), bg="#f39c12", fg="white", cursor="hand2", command=self.edit_selected_task, relief=tk.FLAT, padx=15)
        edit_btn.pack(side=tk.RIGHT, padx=10)

    def parse_whatsapp_line(self, line_str):
        line_str = line_str.replace('\ufeff', '').strip()
        pattern = r"^(?:\[)?(?P<date>\d{1,2}[./-]\d{1,2}[./-]\d{2,4}.*?)(?:\])?\s*(?:-)?\s*(?P<sender>[^:]+):\s*(?P<message>.*)"
        match = re.search(pattern, line_str)
        if match:
            return match.group('date').strip(), match.group('sender').strip(), match.group('message').strip()
        return None, None, None

    def process_zip(self):
        zip_path = filedialog.askopenfilename(title="WhatsApp ZIP Dosyasını Seçin", filetypes=[("ZIP Archive", "*.zip")])
        if not zip_path:
            return

        # NLP Modelini Lazy (Tembel) Yükleme: Arayüz ilk açılışta donmasın diye dosya seçildikten sonra yüklenir.
        if self.processor is None:
            messagebox.showinfo("NLP Modeli Yükleniyor", "Stanza NLP modeli hazırlanıyor.\n(İlk kullanımda internetten ~500MB dil paketi indirebilir, bu biraz zaman alabilir.)\n\nTamam'a basıp işlemin bitmesini bekleyiniz.")
            self.root.update()
            self.processor = NLPProcessor()

        self.current_project = os.path.splitext(os.path.basename(zip_path))[0]
        self.task_manager = TaskManager()
        
        toplam_okunan_satir = 0

        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                txt_filename = next((name for name in z.namelist() if name.endswith('.txt')), None)
                if not txt_filename:
                    messagebox.showerror("Hata", "ZIP içerisinde .txt formatında sohbet dosyası bulunamadı!")
                    return

                with z.open(txt_filename) as f:
                    for line in f:
                        line_str = line.decode('utf-8', errors='ignore')
                        date, sender, message = self.parse_whatsapp_line(line_str)
                        
                        if message:
                            toplam_okunan_satir += 1
                            if any(x in message for x in ["Görüntü dahil", "Medya dahil", "omitted", "araması", "mesajlar silindi"]):
                                continue

                            # NLP analizi (Stanza POS & Morphology)
                            if self.processor.is_task(message):
                                deadline = self.processor.extract_time(message)
                                self.task_manager.add_task(date, sender, message, deadline)

            self.refresh_ui()
            
            if len(self.task_manager.tasks) > 0:
                messagebox.showinfo("Başarılı", f"Sohbetten {toplam_okunan_satir} mesaj Morfolojik olarak incelendi.\nToplam {len(self.task_manager.tasks)} NLP onaylı görev yakalandı!")
            else:
                messagebox.showwarning("Uyarı", f"{toplam_okunan_satir} satır okundu ancak morfolojik olarak görev kipine uygun cümle bulunamadı.")

        except Exception as e:
            messagebox.showerror("Hata", f"Beklenmeyen bir hata oluştu:\n{str(e)}")

    def refresh_ui(self, contact_filter="Tüm Kişiler"):
        for row in self.tree.get_children():
            self.tree.delete(row)

        tasks = self.task_manager.get_tasks_by_contact(contact_filter)
        for t in tasks:
            self.tree.insert("", tk.END, values=(t["ID"], t["Tarih"], t["Kişi"], t["Görev"], t["Zaman Etiketi"]))

        if contact_filter == "Tüm Kişiler":
            self.contact_listbox.delete(0, tk.END)
            self.contact_listbox.insert(tk.END, "Tüm Kişiler")
            for contact in self.task_manager.get_contacts():
                self.contact_listbox.insert(tk.END, contact)
            self.contact_listbox.selection_set(0)

    def filter_by_contact(self, event):
        selection = self.contact_listbox.curselection()
        if selection:
            selected_contact = self.contact_listbox.get(selection[0])
            self.refresh_ui(selected_contact)

    def delete_selected_task(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Uyarı", "Lütfen silmek için tablodan bir görev seçin.")
            return

        confirm = messagebox.askyesno("Onay", "Seçili görevi silmek istediğinize emin misiniz?", icon='warning')
        if confirm:
            item_values = self.tree.item(selected_item[0], "values")
            task_id = int(item_values[0])
            self.task_manager.delete_task(task_id)
            
            selection = self.contact_listbox.curselection()
            active_filter = self.contact_listbox.get(selection[0]) if selection else "Tüm Kişiler"
            self.refresh_ui(active_filter)

    def edit_selected_task(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek için tablodan bir görev seçin.")
            return

        item_values = self.tree.item(selected_item[0], "values")
        task_id = int(item_values[0])
        current_task = item_values[3]

        new_task = simpledialog.askstring("Görevi Düzenle", "Yeni görev içeriğini girin:", initialvalue=current_task)
        
        if new_task and new_task.strip() != "":
            self.task_manager.update_task(task_id, new_task)
            
            selection = self.contact_listbox.curselection()
            active_filter = self.contact_listbox.get(selection[0]) if selection else "Tüm Kişiler"
            self.refresh_ui(active_filter)

    def save_data(self):
        success, msg = self.task_manager.save_to_csv(self.current_project)
        if success:
            messagebox.showinfo("Kayıt Başarılı", f"Görevler Excel (CSV) olarak başarıyla kaydedildi:\n\n{msg}")
        else:
            messagebox.showwarning("Uyarı", msg)

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = AppGUI(root)
    root.mainloop()