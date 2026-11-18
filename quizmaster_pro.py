"""
QUIZMASTER PRO — Advanced Python / C++ / Java Quiz Application
-------------------------------------------------------------
Requirements:
    pip install mysql-connector-python

MySQL setup:
    Create a .env-style environment configuration before running:
        Windows PowerShell:
            $env:QUIZ_DB_HOST="localhost"
            $env:QUIZ_DB_USER="root"
            $env:QUIZ_DB_PASSWORD="your_mysql_password"
        Then:
            python quizmaster_pro.py

The app creates the quiz_app database and its tables automatically.
If MySQL is unavailable, the application displays a clear error and
continues without saving results (the quiz itself remains usable).
"""

import csv
import os
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

import mysql.connector
from mysql.connector import Error

# ----------------------------- CONFIGURATION -----------------------------

APP_BG = "#101522"
PANEL = "#192235"
PANEL_LIGHT = "#222e45"
ACCENT = "#6C8CFF"
ACCENT_HOVER = "#829DFF"
TEXT = "#F3F6FC"
MUTED = "#A7B2C7"
GREEN = "#35C995"
RED = "#FF657A"
YELLOW = "#F5C76B"

QUIZ_SECONDS = 15
LANGUAGES = ("Python", "C++", "Java")

QUESTION_BANK = {
    "Python": [
        ("What is a function in Python?", ["Keyword", "Type of variable", "Imported library", "A block of code that performs a specific task"], "A block of code that performs a specific task"),
        ("Which keyword defines a function?", ["func", "def", "class", "void"], "def"),
        ("Which statement about Python lists is correct?", ["They are immutable", "They can contain different data types", "They only store strings", "They cannot be resized"], "They can contain different data types"),
        ("Which function accepts keyboard input?", ["input()", "get_input()", "user_input()", "read_input()"], "input()"),
        ("Which of these is a Python web framework?", ["Django", "TensorFlow", "NumPy", "Matplotlib"], "Django"),
        ("Python variable names are:", ["Not case-sensitive", "Always uppercase", "Case-sensitive", "Required to start with a number"], "Case-sensitive"),
        ("Which data structure stores key-value pairs?", ["List", "Tuple", "Dictionary", "Set only"], "Dictionary"),
        ("What is the conventional alias for NumPy?", ["np", "nUmpy", "numPY", "numpy only"], "np"),
        ("Which keyword handles exceptions?", ["catch", "error", "except", "final"], "except"),
        ("What does len([2, 4, 6]) return?", ["2", "3", "4", "6"], "3"),
        ("Which symbol is used for exponentiation?", ["^", "**", "//", "%%"], "**"),
        ("What is the result of 10 // 3?", ["3.33", "1", "3", "4"], "3"),
        ("Which collection does not allow duplicate elements?", ["List", "Tuple", "Set", "Dictionary values"], "Set"),
        ("Which keyword is used to create a class?", ["object", "struct", "class", "define"], "class"),
        ("What does append() do to a list?", ["Removes the last item", "Adds an item to the end", "Sorts the list", "Copies the list"], "Adds an item to the end"),
    ],
    "C++": [
        ("What type of language is C++?", ["Markup language", "Compiled general-purpose language", "Database language", "Stylesheet language"], "Compiled general-purpose language"),
        ("Which header is commonly used for input and output streams?", ["<iostream>", "<stdio.h>", "<math.h>", "<fstream.h>"], "<iostream>"),
        ("Which object is used for standard output?", ["cin", "cout", "print", "echo"], "cout"),
        ("Which object is used for standard input?", ["cin", "cout", "scan", "read"], "cin"),
        ("Does C++ support object-oriented programming?", ["Yes", "No", "Only through libraries", "Only in C++20"], "Yes"),
        ("Which keyword starts a traditional for loop?", ["loop", "for", "repeat", "iterate"], "for"),
        ("Which symbol begins a single-line comment?", ["#", "//", "<!--", "--"], "//"),
        ("Which of these is a built-in integer type?", ["integer", "number", "int", "num"], "int"),
        ("What is the conventional entry-point function?", ["start()", "run()", "main()", "init()"], "main()"),
        ("Which operator dereferences a pointer?", ["&", "*", "#", "@"], "*"),
        ("Which operator accesses a class member through an object?", ["->", ".", "::", "&"], "."),
        ("Which keyword dynamically allocates memory?", ["create", "malloc only", "new", "alloc"], "new"),
        ("Which access specifier makes members accessible from anywhere permitted by the object?", ["private", "protected", "public", "static"], "public"),
        ("Which container is provided by the C++ Standard Library for a dynamic sequence?", ["vector", "record", "arraylist", "sequence"], "vector"),
        ("What does the == operator test?", ["Assignment", "Equality", "Address", "Scope"], "Equality"),
    ],
    "Java": [
        ("Java is commonly described as:", ["Compiled only to native code", "Interpreted only", "Compiled to bytecode and executed by the JVM", "A markup language"], "Compiled to bytecode and executed by the JVM"),
        ("What does JVM stand for?", ["Java Virtual Machine", "Java Variable Manager", "Joint Virtual Method", "Java Verified Module"], "Java Virtual Machine"),
        ("Which is a standard Java output statement?", ["System.out.println()", "console.log()", "echo()", "printline()"], "System.out.println()"),
        ("Does Java support object-oriented programming?", ["Yes", "No", "Only through external libraries", "Only for interfaces"], "Yes"),
        ("Which keyword starts a traditional for loop?", ["loop", "for", "repeat", "iterate"], "for"),
        ("Which symbol begins a single-line comment?", ["#", "//", "--", "<!--"], "//"),
        ("Which is a primitive Java data type?", ["integer", "number", "int", "numeric"], "int"),
        ("Which keyword declares a class?", ["define", "object", "class", "struct"], "class"),
        ("Which method is the conventional Java application entry point?", ["start()", "main()", "run()", "init()"], "main()"),
        ("Which package contains the AWT GUI toolkit?", ["java.awt", "java.io", "java.util", "java.net"], "java.awt"),
        ("Which keyword creates an object?", ["alloc", "new", "make", "object"], "new"),
        ("Which keyword is used for inheritance between classes?", ["implements", "inherits", "extends", "superclass"], "extends"),
        ("Which collection interface does ArrayList implement?", ["Map", "List", "Set", "Queue only"], "List"),
        ("Which keyword prevents a class from being subclassed?", ["static", "private", "final", "const"], "final"),
        ("Which exception category must generally be caught or declared?", ["Checked exception", "Syntax warning", "Runtime error only", "Logical exception"], "Checked exception"),
    ],
}


# ------------------------------- DATABASE --------------------------------

class Database:
    def __init__(self):
        self.enabled = False
        self.error = "MySQL connection was not initialized."
        self.connection_config = {
            "host": os.getenv("QUIZ_DB_HOST", "localhost"),
            "user": os.getenv("QUIZ_DB_USER", "root"),
            "password": os.getenv("QUIZ_DB_PASSWORD", ""),
            "database": "quiz_app",
            "autocommit": False,
        }
        self.initialize()

    def connect(self, include_database=True):
        config = dict(self.connection_config)
        if not include_database:
            config.pop("database", None)
        return mysql.connector.connect(**config)

    def initialize(self):
        try:
            conn = self.connect(include_database=False)
            cur = conn.cursor()
            cur.execute("CREATE DATABASE IF NOT EXISTS quiz_app")
            cur.close()
            conn.close()

            conn = self.connect()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    player_name VARCHAR(80) NOT NULL,
                    language VARCHAR(20) NOT NULL,
                    difficulty VARCHAR(20) NOT NULL,
                    score INT NOT NULL,
                    total INT NOT NULL,
                    percentage DECIMAL(5,2) NOT NULL,
                    correct_count INT NOT NULL DEFAULT 0,
                    wrong_count INT NOT NULL DEFAULT 0,
                    skipped_count INT NOT NULL DEFAULT 0,
                    time_taken INT NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Migrate older versions of the original results table.
            cur.execute("SHOW COLUMNS FROM results")
            existing = {row[0] for row in cur.fetchall()}
            migrations = {
                "player_name": "ALTER TABLE results ADD COLUMN player_name VARCHAR(80) NULL",
                "difficulty": "ALTER TABLE results ADD COLUMN difficulty VARCHAR(20) NOT NULL DEFAULT 'Mixed'",
                "total": "ALTER TABLE results ADD COLUMN total INT NOT NULL DEFAULT 0",
                "percentage": "ALTER TABLE results ADD COLUMN percentage DECIMAL(5,2) NOT NULL DEFAULT 0",
                "correct_count": "ALTER TABLE results ADD COLUMN correct_count INT NOT NULL DEFAULT 0",
                "wrong_count": "ALTER TABLE results ADD COLUMN wrong_count INT NOT NULL DEFAULT 0",
                "skipped_count": "ALTER TABLE results ADD COLUMN skipped_count INT NOT NULL DEFAULT 0",
                "time_taken": "ALTER TABLE results ADD COLUMN time_taken INT NOT NULL DEFAULT 0",
                "created_at": "ALTER TABLE results ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            }
            for column, sql in migrations.items():
                if column not in existing:
                    cur.execute(sql)
            # Keep compatibility with the original table's name column.
            cur.execute("SHOW COLUMNS FROM results LIKE 'name'")
            has_old_name = cur.fetchone() is not None
            if has_old_name:
                cur.execute("UPDATE results SET player_name = name WHERE player_name IS NULL")
            conn.commit()
            cur.close()
            conn.close()
            self.enabled = True
        except Exception as exc:
            self.enabled = False
            self.error = str(exc)

    def save_result(self, result):
        if not self.enabled:
            return False
        try:
            conn = self.connect()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO results
                (player_name, language, difficulty, score, total, percentage,
                 correct_count, wrong_count, skipped_count, time_taken)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                result["name"], result["language"], result["difficulty"],
                result["score"], result["total"], result["percentage"],
                result["correct"], result["wrong"], result["skipped"],
                result["time_taken"]
            ))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as exc:
            messagebox.showerror("Database error", f"Could not save result:\n{exc}")
            return False

    def fetch_results(self, search="", language="All"):
        if not self.enabled:
            return []
        conn = self.connect()
        cur = conn.cursor()
        sql = """SELECT id, player_name, language, difficulty, score, total,
                 percentage, created_at FROM results WHERE player_name LIKE %s"""
        params = [f"%{search}%"]
        if language != "All":
            sql += " AND language = %s"
            params.append(language)
        sql += " ORDER BY percentage DESC, created_at DESC"
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def delete_result(self, result_id):
        if not self.enabled:
            return
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM results WHERE id = %s", (result_id,))
        conn.commit()
        cur.close()
        conn.close()

    def clear_results(self):
        if not self.enabled:
            return
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM results")
        conn.commit()
        cur.close()
        conn.close()


# ------------------------------- UI HELPERS -------------------------------

def make_button(parent, text, command, color=ACCENT, width=None):
    return tk.Button(
        parent, text=text, command=command, bg=color, fg="white",
        activebackground=ACCENT_HOVER, activeforeground="white",
        relief="flat", bd=0, padx=18, pady=10,
        font=("Segoe UI", 10, "bold"), cursor="hand2", width=width
    )


def heading(parent, text, size=20):
    return tk.Label(parent, text=text, bg=APP_BG, fg=TEXT,
                    font=("Segoe UI", size, "bold"))


# --------------------------------- APP -------------------------------------

class QuizMasterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QuizMaster Pro")
        self.root.geometry("1080x720")
        self.root.minsize(850, 620)
        self.root.configure(bg=APP_BG)
        self.db = Database()

        self.player_name = ""
        self.language = "Python"
        self.difficulty = "Mixed"
        self.question_count = 10
        self.quiz_questions = []
        self.answers = []
        self.index = 0
        self.score = 0
        self.time_left = QUIZ_SECONDS
        self.timer_job = None
        self.started_at = None
        self.finished = False
        self.last_result = None
        self.last_saved = False

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(
            "TProgressbar", troughcolor=PANEL_LIGHT,
            background=ACCENT, bordercolor=PANEL_LIGHT,
            lightcolor=ACCENT, darkcolor=ACCENT
        )
        self.show_home()

    def clear(self):
        self.cancel_timer()
        for widget in self.root.winfo_children():
            widget.destroy()

    def base_page(self):
        self.clear()
        outer = tk.Frame(self.root, bg=APP_BG)
        outer.pack(fill="both", expand=True, padx=34, pady=25)
        top = tk.Frame(outer, bg=APP_BG)
        top.pack(fill="x", pady=(0, 22))
        tk.Label(top, text="QUIZMASTER", bg=APP_BG, fg=TEXT,
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        tk.Label(top, text="PRO", bg=APP_BG, fg=ACCENT,
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=5)
        tk.Label(top, text="PYTHON  •  C++  •  JAVA", bg=APP_BG, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(side="right")
        return outer

    def show_home(self):
        page = self.base_page()
        content = tk.Frame(page, bg=APP_BG)
        content.pack(expand=True, fill="both")

        tk.Label(content, text="Test your skills.\nTrack your progress.",
                 bg=APP_BG, fg=TEXT, justify="center",
                 font=("Segoe UI", 30, "bold")).pack(pady=(10, 8))
        tk.Label(content, text="A focused coding quiz experience with timed challenges and performance analytics.",
                 bg=APP_BG, fg=MUTED, font=("Segoe UI", 10)).pack(pady=(0, 25))

        card = tk.Frame(content, bg=PANEL, padx=32, pady=25)
        card.pack()
        tk.Label(card, text="SET UP YOUR QUIZ", bg=PANEL, fg=ACCENT,
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 18))

        tk.Label(card, text="Your name", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=8)
        self.name_var = tk.StringVar()
        name_entry = tk.Entry(card, textvariable=self.name_var, width=28,
                              bg=PANEL_LIGHT, fg=TEXT, insertbackground=TEXT,
                              relief="flat", font=("Segoe UI", 11))
        name_entry.grid(row=1, column=1, padx=(22, 0), ipady=8)

        tk.Label(card, text="Programming language", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", pady=8)
        self.lang_var = tk.StringVar(value="Python")
        ttk.Combobox(card, textvariable=self.lang_var, values=LANGUAGES,
                     state="readonly", width=25).grid(row=2, column=1, padx=(22, 0), ipady=4)

        tk.Label(card, text="Difficulty", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 10)).grid(row=3, column=0, sticky="w", pady=8)
        self.diff_var = tk.StringVar(value="Mixed")
        ttk.Combobox(card, textvariable=self.diff_var,
                     values=("Easy", "Medium", "Hard", "Mixed"),
                     state="readonly", width=25).grid(row=3, column=1, padx=(22, 0), ipady=4)

        tk.Label(card, text="Number of questions", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 10)).grid(row=4, column=0, sticky="w", pady=8)
        self.count_var = tk.StringVar(value="10")
        ttk.Combobox(card, textvariable=self.count_var,
                     values=("5", "10", "15"), state="readonly",
                     width=25).grid(row=4, column=1, padx=(22, 0), ipady=4)

        tk.Label(card, text="Note: the current question bank is mixed-level; this selection is saved with your result.",
                 bg=PANEL, fg=MUTED, font=("Segoe UI", 8), wraplength=330,
                 justify="left").grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 0))
        make_button(card, "START QUIZ  →", self.start_quiz, GREEN, 22).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(23, 8))
        actions = tk.Frame(content, bg=APP_BG)
        actions.pack(pady=18)
        make_button(actions, "Results dashboard", self.show_dashboard, PANEL_LIGHT).pack(side="left", padx=6)
        make_button(actions, "How to use", self.show_help, PANEL_LIGHT).pack(side="left", padx=6)

        if self.db.enabled:
            status = "MySQL connected • Results will be saved"
            color = GREEN
        else:
            status = "MySQL unavailable • Quiz works, but results will not be saved"
            color = YELLOW
        tk.Label(content, text=status, bg=APP_BG, fg=color,
                 font=("Segoe UI", 9)).pack(pady=5)
        if not self.db.enabled:
            tk.Label(
                content,
                text=f"Connection error: {self.db.error}\n"
                     "Check that the MySQL server is running and that "
                     "QUIZ_DB_HOST, QUIZ_DB_USER, and QUIZ_DB_PASSWORD are correct.",
                bg=APP_BG, fg=MUTED, font=("Segoe UI", 9),
                wraplength=800, justify="center"
            ).pack(pady=(0, 5))

    def show_help(self):
        messagebox.showinfo(
            "How to use QuizMaster Pro",
            "1. Enter your name and choose a language.\n"
            "2. Select a difficulty and question count.\n"
            f"3. Each question has {QUIZ_SECONDS} seconds.\n"
            "4. Select an option and press Next.\n"
            "5. Review your score and explanations at the end.\n\n"
            "The current question bank contains introductory questions. "
            "The current question bank is mixed-level; the selected difficulty label is stored with the result."
        )

    def start_quiz(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Name required", "Please enter your name.")
            return
        self.player_name = name[:80]
        self.language = self.lang_var.get()
        self.difficulty = self.diff_var.get()
        self.question_count = int(self.count_var.get())
        bank = QUESTION_BANK[self.language][:]
        random.shuffle(bank)
        chosen = bank[:min(self.question_count, len(bank))]
        self.quiz_questions = []
        for question, options, answer in chosen:
            shuffled = options[:]
            random.shuffle(shuffled)
            self.quiz_questions.append({
                "question": question,
                "options": shuffled,
                "answer": answer
            })
        self.answers = [None] * len(self.quiz_questions)
        self.index = 0
        self.score = 0
        self.finished = False
        self.started_at = datetime.now()
        self.show_question()

    def show_question(self):
        self.cancel_timer()
        if self.index >= len(self.quiz_questions):
            self.finish_quiz()
            return

        page = self.base_page()
        top_info = tk.Frame(page, bg=APP_BG)
        top_info.pack(fill="x")
        tk.Label(top_info, text=f"{self.language}  /  {self.difficulty}",
                 bg=APP_BG, fg=MUTED, font=("Segoe UI", 10, "bold")).pack(side="left")
        self.timer_label = tk.Label(top_info, text="", bg=APP_BG, fg=YELLOW,
                                    font=("Segoe UI", 12, "bold"))
        self.timer_label.pack(side="right")

        self.progress_label = tk.Label(page, text="", bg=APP_BG, fg=MUTED,
                                       font=("Segoe UI", 10))
        self.progress_label.pack(anchor="w", pady=(28, 8))
        self.progress = ttk.Progressbar(page, maximum=len(self.quiz_questions),
                                        value=self.index, mode="determinate")
        self.progress.pack(fill="x", pady=(0, 28))

        card = tk.Frame(page, bg=PANEL, padx=34, pady=30)
        card.pack(fill="both", expand=True)
        q = self.quiz_questions[self.index]
        tk.Label(card, text=f"QUESTION {self.index + 1:02d}",
                 bg=PANEL, fg=ACCENT, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(card, text=q["question"], bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 20, "bold"), wraplength=850,
                 justify="left").pack(anchor="w", pady=(15, 26))

        self.answer_var = tk.StringVar(value="")
        self.option_buttons = []
        for i, option in enumerate(q["options"]):
            rb = tk.Radiobutton(
                card, text=option, variable=self.answer_var, value=option,
                bg=PANEL_LIGHT, fg=TEXT, selectcolor=ACCENT,
                activebackground=PANEL_LIGHT, activeforeground=TEXT,
                font=("Segoe UI", 11), anchor="w", justify="left",
                padx=15, pady=12, wraplength=800, cursor="hand2",
                indicatoron=False, relief="flat", bd=0
            )
            rb.pack(fill="x", pady=5)
            self.option_buttons.append(rb)

        bottom = tk.Frame(page, bg=APP_BG)
        bottom.pack(fill="x", pady=18)
        make_button(bottom, "Exit quiz", self.confirm_exit, PANEL_LIGHT).pack(side="left")
        self.next_button = make_button(
            bottom, "Next question  →", self.submit_answer, GREEN)
        self.next_button.pack(side="right")

        self.update_progress_text()
        self.time_left = QUIZ_SECONDS
        self.update_timer()

    def update_progress_text(self):
        self.progress_label.config(
            text=f"Question {self.index + 1} of {len(self.quiz_questions)}"
        )

    def update_timer(self):
        self.timer_label.config(text=f"TIME LEFT  {self.time_left:02d}s")
        if self.time_left <= 0:
            self.submit_answer(timed_out=True)
            return
        self.time_left -= 1
        self.timer_job = self.root.after(1000, self.update_timer)

    def cancel_timer(self):
        if self.timer_job is not None:
            try:
                self.root.after_cancel(self.timer_job)
            except tk.TclError:
                pass
            self.timer_job = None

    def submit_answer(self, timed_out=False):
        if self.finished:
            return
        self.cancel_timer()
        selected = self.answer_var.get().strip()
        q = self.quiz_questions[self.index]
        self.answers[self.index] = {
            "selected": selected or None,
            "correct": selected == q["answer"],
            "timed_out": timed_out,
            "question": q["question"],
            "answer": q["answer"],
        }
        self.index += 1
        if self.index >= len(self.quiz_questions):
            self.finish_quiz()
        else:
            self.show_question()

    def confirm_exit(self):
        if messagebox.askyesno("Exit quiz", "End this quiz now? Your unanswered questions will be marked as skipped."):
            self.finish_quiz()

    def finish_quiz(self):
        if self.finished:
            return
        self.finished = True
        self.cancel_timer()
        total = len(self.quiz_questions)
        correct = sum(1 for a in self.answers if a and a["correct"])
        wrong = sum(1 for a in self.answers if a and a["selected"] and not a["correct"])
        skipped = total - correct - wrong
        elapsed = max(0, int((datetime.now() - self.started_at).total_seconds()))
        result = {
            "name": self.player_name, "language": self.language,
            "difficulty": self.difficulty, "score": correct, "total": total,
            "percentage": round(correct / total * 100, 2) if total else 0,
            "correct": correct, "wrong": wrong, "skipped": skipped,
            "time_taken": elapsed,
        }
        saved = self.db.save_result(result)
        self.last_result = result
        self.last_saved = saved
        self.show_result(result, saved)

    def show_result(self, result, saved):
        page = self.base_page()
        tk.Label(page, text="QUIZ COMPLETED", bg=APP_BG, fg=ACCENT,
                 font=("Segoe UI", 11, "bold")).pack(pady=(10, 5))
        tk.Label(page, text=f"Well done, {self.player_name}!",
                 bg=APP_BG, fg=TEXT, font=("Segoe UI", 27, "bold")).pack()
        tk.Label(page, text=f"{result['score']} / {result['total']} correct",
                 bg=APP_BG, fg=GREEN, font=("Segoe UI", 22, "bold")).pack(pady=8)

        card = tk.Frame(page, bg=PANEL, padx=28, pady=22)
        card.pack(fill="x", pady=18)
        stats = [
            ("ACCURACY", f"{result['percentage']:.1f}%"),
            ("CORRECT", str(result["correct"])),
            ("INCORRECT", str(result["wrong"])),
            ("SKIPPED", str(result["skipped"])),
            ("TIME", f"{result['time_taken']} sec"),
        ]
        for i, (label, value) in enumerate(stats):
            cell = tk.Frame(card, bg=PANEL)
            cell.grid(row=0, column=i, padx=18, sticky="nsew")
            tk.Label(cell, text=label, bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 8, "bold")).pack()
            tk.Label(cell, text=value, bg=PANEL, fg=TEXT,
                     font=("Segoe UI", 17, "bold")).pack(pady=5)
            card.grid_columnconfigure(i, weight=1)

        tk.Label(page, text=("Result saved to MySQL." if saved else
                             "Result not saved — check your MySQL connection."),
                 bg=APP_BG, fg=GREEN if saved else YELLOW,
                 font=("Segoe UI", 9)).pack()
        buttons = tk.Frame(page, bg=APP_BG)
        buttons.pack(pady=18)
        make_button(buttons, "Review answers", self.show_review, ACCENT).pack(side="left", padx=6)
        make_button(buttons, "Dashboard", self.show_dashboard, PANEL_LIGHT).pack(side="left", padx=6)
        make_button(buttons, "Home", self.show_home, GREEN).pack(side="left", padx=6)

    def show_review(self):
        page = self.base_page()
        heading(page, "Answer review", 22).pack(anchor="w", pady=(5, 15))
        canvas = tk.Canvas(page, bg=APP_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(page, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=APP_BG)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=990)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for i, item in enumerate(self.answers, 1):
            color = GREEN if item and item["correct"] else RED if item and item["selected"] else YELLOW
            card = tk.Frame(scroll_frame, bg=PANEL, padx=20, pady=15)
            card.pack(fill="x", pady=7, padx=5)
            tk.Label(card, text=f"{i}. {item['question']}", bg=PANEL, fg=TEXT,
                     font=("Segoe UI", 11, "bold"), wraplength=900,
                     justify="left").pack(anchor="w")
            chosen = item["selected"] if item and item["selected"] else "Not answered"
            tk.Label(card, text=f"Your answer: {chosen}", bg=PANEL, fg=color,
                     font=("Segoe UI", 10)).pack(anchor="w", pady=(8, 2))
            tk.Label(card, text=f"Correct answer: {item['answer']}", bg=PANEL, fg=GREEN,
                     font=("Segoe UI", 10)).pack(anchor="w")

        make_button(page, "Back to results", lambda: self.show_result(self.last_result, self.last_saved), PANEL_LIGHT).pack(pady=10)

    def show_dashboard(self):
        page = self.base_page()
        heading(page, "Results dashboard", 23).pack(anchor="w", pady=(0, 15))
        if not self.db.enabled:
            tk.Label(page, text="Connect to MySQL to view saved results.",
                     bg=APP_BG, fg=YELLOW, font=("Segoe UI", 11)).pack(anchor="w")
            make_button(page, "Back home", self.show_home, PANEL_LIGHT).pack(anchor="w", pady=20)
            return

        filters = tk.Frame(page, bg=APP_BG)
        filters.pack(fill="x", pady=(0, 12))
        search_var = tk.StringVar()
        language_var = tk.StringVar(value="All")
        tk.Entry(filters, textvariable=search_var, bg=PANEL_LIGHT, fg=TEXT,
                 insertbackground=TEXT, relief="flat", width=25,
                 font=("Segoe UI", 10)).pack(side="left", ipady=7, padx=(0, 8))
        ttk.Combobox(filters, textvariable=language_var,
                     values=("All",) + LANGUAGES, state="readonly",
                     width=12).pack(side="left", padx=5)
        tree_frame = tk.Frame(page, bg=PANEL)
        tree_frame.pack(fill="both", expand=True)
        columns = ("id", "name", "language", "difficulty", "score", "percentage", "date")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        labels = ("ID", "Player", "Language", "Difficulty", "Score", "Accuracy", "Date")
        widths = (55, 180, 100, 100, 80, 100, 170)
        for col, label, width in zip(columns, labels, widths):
            tree.heading(col, text=label)
            tree.column(col, width=width, anchor="center")
        tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        scroll.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scroll.set)

        def refresh():
            tree.delete(*tree.get_children())
            try:
                rows = self.db.fetch_results(search_var.get().strip(), language_var.get())
                for row in rows:
                    created = row[7].strftime("%d %b %Y %H:%M") if row[7] else ""
                    tree.insert("", "end", values=(
                        row[0], row[1], row[2], row[3],
                        f"{row[4]}/{row[5]}", f"{float(row[6]):.1f}%", created
                    ))
            except Exception as exc:
                messagebox.showerror("Dashboard error", str(exc))

        def delete_selected():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Select a result", "Choose a result row first.")
                return
            result_id = tree.item(selection[0], "values")[0]
            if messagebox.askyesno("Delete result", f"Delete result #{result_id}?"):
                try:
                    self.db.delete_result(result_id)
                    refresh()
                except Exception as exc:
                    messagebox.showerror("Database error", str(exc))

        def export_csv():
            rows = self.db.fetch_results(search_var.get().strip(), language_var.get())
            if not rows:
                messagebox.showinfo("Export", "There are no results to export.")
                return
            path = filedialog.asksaveasfilename(
                defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
                initialfile="quiz_results.csv"
            )
            if not path:
                return
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(labels)
                for row in rows:
                    writer.writerow(row)
            messagebox.showinfo("Export complete", f"Results exported to:\n{path}")

        controls = tk.Frame(page, bg=APP_BG)
        controls.pack(fill="x", pady=12)
        make_button(controls, "Search / filter", refresh, ACCENT).pack(side="left", padx=(0, 7))
        make_button(controls, "Delete selected", delete_selected, RED).pack(side="left", padx=7)
        make_button(controls, "Export CSV", export_csv, GREEN).pack(side="left", padx=7)
        make_button(controls, "Refresh", refresh, PANEL_LIGHT).pack(side="left", padx=7)
        make_button(controls, "Home", self.show_home, PANEL_LIGHT).pack(side="right")
        refresh()


def main():
    root = tk.Tk()
    app = QuizMasterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
