import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import io
import datetime

# ==============================================================================
# BAZA WIEDZY I LOGIKA ANALITYCZNA
# ==============================================================================

def wczytaj_konfiguracje(plik_json='konfiguracja.json'):
    try:
        with open(plik_json, 'r', encoding='utf-8') as f:
            konfiguracja = json.load(f)
        return konfiguracja['profiles'], konfiguracja['weights']
    except Exception as e:
        print(f"BŁĄD KRYTYCZNY: Problem z plikiem konfiguracyjnym. {e}")
        return None, None

class MethodologySelector:
    def __init__(self, user_answers, profiles, weights):
        self.answers = user_answers
        self.profiles = profiles
        self.weights = weights
    def calculate_scores(self):
        scores = {}
        for methodology, profile in self.profiles.items():
            weighted_distance = 0
            for key, profile_value in profile.items():
                if key in self.answers:
                    user_value = self.answers.get(key, 3)
                    weight = self.weights.get(key, 1.0)
                    weighted_distance += (weight * (user_value - profile_value))**2
            if weighted_distance > 0:
                scores[methodology] = 1 / (1 + weighted_distance**0.5)
            else:
                scores[methodology] = 1.0 if any(k in self.answers for k in profile) else 0.0
        if 'autonomia_zespolu' in self.answers:
            team_size = self.answers.get('wielkosc_zespolu', 10)
            if 3 <= team_size <= 9:
                 scores['Zwinny (Agile)'] *= 1.2
                 scores['Szczupły (Lean)'] *= 1.1
            elif team_size > 9:
                 scores['Predyktywny'] *= 1.1
                 scores['Hybrydowy'] *= 1.1
        total_score = sum(scores.values())
        if total_score == 0: return {}
        return {k: (v / total_score) * 100 for k, v in scores.items()}

# ==============================================================================
# APLIKACJA GUI
# ==============================================================================

PYTANIA_FAZY = {
    "Plan (Zaplanuj)": {
        'stabilnosc_wymagan': "Na ile stabilne i znane są wymagania?",
        'zlozonosc_problemu': "Jak złożony jest problem do rozwiązania?",
        'zaangazowanie_klienta': "Jakie jest planowane zaangażowanie klienta w tej fazie?",
    },
    "Do (Wykonaj)": {
        'mozliwosc_podzialu': "Czy pracę można podzielić na małe, niezależne części?",
        'autonomia_zespolu': "Jaki jest poziom autonomii i doświadczenia zespołu wykonawczego?",
        'stabilnosc_technologii': "Na ile stabilna i dojrzała jest technologia?",
    },
    "Check (Sprawdź)": {
        'presja_czasu': "Jak istotne jest częste sprawdzanie postępów i wczesne dostarczanie wartości?",
        'wplyw_biznesowy': "Jak krytyczny dla biznesu jest weryfikowany rezultat?",
    },
    "Act (Działaj/Popraw)": {
        'kultura_organizacyjna': "Czy kultura organizacji wspiera adaptację i wprowadzanie zmian?",
        'zarzadzanie_przeplywem': "Czy proces musi być elastyczny i pozwalać na ciągłe modyfikacje?",
    }
}

class App(ttk.Window):
    def __init__(self, profiles, weights):
        super().__init__(themename="litera")
        self.profiles = profiles
        self.weights = weights
        self.title("System Ekspercki - Model PDCA v2.4")
        self.geometry("800x850")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._quit)

        self.odpowiedzi_vars = {}
        self.canvas_widget = None
        self.create_widgets()

    def _quit(self):
        self.quit()
        self.destroy()

    def create_widgets(self):
        # Główny kontener z mechanizmem przewijania
        container = ttk.Frame(self)
        container.pack(fill=BOTH, expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Interfejs zakładek
        notebook = ttk.Notebook(self.scrollable_frame)
        notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)

        for faza, pytania in PYTANIA_FAZY.items():
            phase_frame = ttk.Frame(notebook, padding="15")
            notebook.add(phase_frame, text=faza)
            for klucz, pytanie in pytania.items():
                frame = ttk.Frame(phase_frame, padding=(0, 10))
                frame.pack(fill=X, expand=True)
                label = ttk.Label(frame, text=pytanie)
                label.pack(anchor='w')
                slider_var = ttk.IntVar(value=3)
                self.odpowiedzi_vars[klucz] = slider_var
                slider = ttk.Scale(frame, from_=1, to=5, orient=HORIZONTAL, variable=slider_var, length=300)
                slider.pack(fill=X, expand=True)

        do_phase_frame = notebook.nametowidget(notebook.tabs()[1])
        team_size_frame = ttk.Frame(do_phase_frame, padding=(0, 10))
        team_size_frame.pack(fill=X, expand=True)
        team_label = ttk.Label(team_size_frame, text="Planowana wielkość zespołu wykonawczego:")
        team_label.pack(side=LEFT, padx=(0, 10))
        self.team_size_var = ttk.StringVar(value="7")
        team_size_entry = ttk.Entry(team_size_frame, textvariable=self.team_size_var, width=5)
        team_size_entry.pack(side=LEFT)

        analyze_button = ttk.Button(self.scrollable_frame, text="Analizuj Proces PDCA", command=self.uruchom_analize, bootstyle=SUCCESS)
        analyze_button.pack(pady=20, ipadx=10, ipady=5)
        
        self.results_frame = ttk.LabelFrame(self.scrollable_frame, text="Wyniki Analizy", padding="15")
        self.results_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

    def uruchom_analize(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        dane_projektu = {klucz: var.get() for klucz, var in self.odpowiedzi_vars.items()}
        try:
            dane_projektu['wielkosc_zespolu'] = int(self.team_size_var.get())
        except (ValueError, ttk.TclError):
            ttk.Label(self.results_frame, text="Błąd: Podaj poprawną wielkość zespołu.", bootstyle=DANGER).pack()
            return

        rekomendacja_hybrydowa = {}
        for faza, pytania in PYTANIA_FAZY.items():
            odpowiedzi_dla_fazy = {k: v for k, v in dane_projektu.items() if k in pytania}
            if faza == "Do (Wykonaj)":
                 odpowiedzi_dla_fazy['wielkosc_zespolu'] = dane_projektu['wielkosc_zespolu']
            selector = MethodologySelector(odpowiedzi_dla_fazy, self.profiles, self.weights)
            wyniki = selector.calculate_scores()
            if wyniki:
                top_rekomendacja = sorted(wyniki.items(), key=lambda item: item[1], reverse=True)[0][0]
                rekomendacja_hybrydowa[faza] = top_rekomendacja

        ttk.Label(self.results_frame, text="🥇 Rekomendowane Podejścia dla Faz PDCA:", font=("Helvetica", 12, "bold")).pack(anchor='w', pady=5)
        for faza, rekomendacja in rekomendacja_hybrydowa.items():
            ttk.Label(self.results_frame, text=f"  • {faza}: {rekomendacja}", font=("Helvetica", 10)).pack(anchor='w')

        # Wywołanie funkcji tworzącej wykres w GUI
        self.stworz_wykres_radarowy_w_gui(dane_projektu, rekomendacja_hybrydowa)

    def stworz_wykres_radarowy_w_gui(self, dane_projektu, rekomendacja_hybrydowa):
        # Usunięcie poprzedniego wykresu, jeśli istnieje
        if self.canvas_widget:
            self.canvas_widget.destroy()

        plt.style.use('ggplot')
        labels = list(self.odpowiedzi_vars.keys())
        num_vars = len(labels)

        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1] # Zamknięcie wielokąta

        fig = Figure(figsize=(5, 5))
        ax = fig.add_subplot(111, polar=True)

        # Rysowanie danych użytkownika
        user_values = [dane_projektu.get(l, 3) for l in labels]
        user_values += user_values[:1]
        ax.plot(angles, user_values, color='#e6194B', linewidth=2, linestyle='solid', label='Profil Projektu (ogólny)')
        ax.fill(angles, user_values, color='#e6194B', alpha=0.25)

        # Rysowanie danych dla rekomendacji z fazy "Do"
        faza_kluczowa = "Do (Wykonaj)"
        rekomendacja_nazwa = rekomendacja_hybrydowa.get(faza_kluczowa, "")
        if rekomendacja_nazwa in self.profiles:
            rekomendacja_profil = self.profiles[rekomendacja_nazwa]
            profile_values = [rekomendacja_profil.get(l, 3) for l in labels]
            profile_values += profile_values[:1]
            ax.plot(angles, profile_values, color='#4363d8', linewidth=1.5, linestyle='dashed', label=f'Profil "{rekomendacja_nazwa}"')
            ax.fill(angles, profile_values, color='#4363d8', alpha=0.25)
        
        ax.set_yticklabels([])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, size=8)
        ax.legend(loc='upper right', bbox_to_anchor=(1.4, 1.1))

        # Osadzenie wykresu w oknie Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.results_frame)
        canvas.draw()
        self.canvas_widget = canvas.get_tk_widget()
        self.canvas_widget.pack(fill=BOTH, expand=True, pady=10)

if __name__ == "__main__":
    PROFILES, WEIGHTS = wczytaj_konfiguracje()
    if PROFILES:
        app = App(PROFILES, WEIGHTS)
        app.mainloop()