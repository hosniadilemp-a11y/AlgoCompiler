<div align="center">

# 🖥️ AlgoCompiler

**A Modern Web IDE for the Algorithmic Language**

*Write, compile, and debug algorithms in a beautiful browser-based environment — no setup needed beyond Python.*

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey?logo=flask)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-informational)](#-quick-start)

</div>

---

## 🌐 Live Demo

Try AlgoCompiler instantly in your browser:  
**[https://algocompiler.onrender.com](https://algocompiler.onrender.com)**

> [!NOTE]  
> The live version is hosted on Render. If it hasn't been visited recently, the server might be "sleeping." Please allow up to **60 seconds** for the first load.

---

## 📚 Table of Contents

- [What is AlgoCompiler?](#-what-is-algocompiler)
- [Features](#-features)
- [Screenshots](#-screenshots)
- [Quick Start](#-quick-start)
  - [Linux](#-linux)
  - [macOS](#-macos)
  - [Windows](#-windows)
- [Manual Setup (for experienced users)](#-manual-setup)
- [Project Structure](#-project-structure)
- [The Algorithmic Language Syntax Guide](#-the-algorithmic-language-syntax-guide)
- [Error Codes Reference](#-error-codes-reference)
- [Running the Tests](#-running-the-tests)
- [Reporting Bugs](#-reporting-bugs--issues)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🤔 What is AlgoCompiler?

**AlgoCompiler** is a full-stack web application that lets you write, compile, and execute algorithms written in the **French-flavoured pseudocode** language used in many Algerian and French Computer Science university courses.

Instead of worrying about Python, Java, or C syntax, you write **natural-language-style algorithms** directly in the browser:

```
Algorithme CalculerAge;
Var
    anneeNaissance : Entier;
    age            : Entier;
Debut
    Ecrire("Entrez votre année de naissance : ");
    Lire(anneeNaissance);
    age := 2024 - anneeNaissance;
    Ecrire("Vous avez aproximativement ", age, " ans.");
Fin.
```

AlgoCompiler **translates your algorithm to Python** and executes it instantly, displaying all output and variable states in real time.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎨 **Rich Code Editor** | Powered by [CodeMirror](https://codemirror.net/) with syntax highlighting, auto-complete, and code folding |
| ▶️ **Instant Execution** | Run your algorithm with a single click and see output in the live console |
| 🔍 **Variable Inspector** | Step-by-step debugger shows all variable names, values, types, and memory addresses |
| 📖 **Example Library** | Sliding panel with dozens of categorized example algorithms |
| 🛡️ **Runtime Protection** | Infinite loops, stack overflows, and memory exhaustion are safely caught |
| 📋 **Error Reference** | Clickable error codes link directly to a detailed documentation page |
| 💾 **File Management** | Open and save `.algo` files directly from/to your computer |
| 📦 **Pointer & Dynamic Memory** | Full support for `^Type` pointers, `allouer()`, `liberer()`, and `taille()` |
| 🔗 **Linked Lists & Records** | `Enregistrement` structures and linked list support |

---

## 📸 Screenshots

> Screenshots of the IDE in action can be found in the [`docs/screenshots/`](docs/) directory.

---

## 🚀 Quick Start

Choose your operating system below. **No programming experience required!**

---

### 🐧 Linux

**Step 1 — Open a Terminal**

Right-click on your desktop and choose **"Open Terminal"** (or search for "Terminal" in your apps menu).

**Step 2 — Install Python 3 (if not already installed)**

Most Linux distributions come with Python 3 pre-installed. Check by running:
```bash
python3 --version
```
If you see `Python 3.x.x`, you are ready. If not, install it:
- **Ubuntu / Debian:** `sudo apt install python3 python3-pip`
- **Fedora / CentOS:** `sudo dnf install python3 python3-pip`
- **Arch Linux:** `sudo pacman -S python`

**Step 3 — Download the project**

If you have `git` installed:
```bash
git clone https://github.com/hosniadilemp-a11y/Algorithemic_language_compiler.git
cd AlgoCompiler
```
Or download the ZIP from GitHub, extract it, and open a terminal inside the extracted folder.

**Step 4 — Run the setup script (one time only)**

```bash
chmod +x scripts/setup_linux.sh
./scripts/setup_linux.sh
```

**Step 5 — Launch the application**

```bash
./run_app.sh
```

**Step 6 — Open your browser**

Navigate to: **[http://localhost:5000](http://localhost:5000)**

That's it! 🎉

---

### 🍎 macOS

**Step 1 — Open Terminal**

Press `Command (⌘) + Space`, type **"Terminal"**, and press Enter.

**Step 2 — Install Python 3**

macOS does not include Python 3 by default. The easiest way is via [Homebrew](https://brew.sh):

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3
brew install python3
```

Alternatively, download the official Python installer from [python.org](https://www.python.org/downloads/).

**Step 3 — Download the project**

```bash
git clone https://github.com/hosniadilemp-a11y/Algorithemic_language_compiler.git
cd AlgoCompiler
```

**Step 4 — Run the setup script (one time only)**

```bash
chmod +x scripts/setup_mac.sh
./scripts/setup_mac.sh
```

**Step 5 — Launch the application**

```bash
./run_app.sh
```

**Step 6 — Open your browser**

Navigate to: **[http://localhost:5000](http://localhost:5000)**

---

### 🪟 Windows

**Step 1 — Install Python 3**

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Click the big yellow **"Download Python 3.x.x"** button
3. Run the installer
4. ⚠️ **IMPORTANT:** On the first screen of the installer, check the box that says **"Add Python to PATH"** before clicking Install

**Step 2 — Download the project**

- If you have Git for Windows: open **Git Bash** and run:
  ```bash
  git clone https://github.com/hosniadilemp-a11y/Algorithemic_language_compiler.git
  ```
- Or download the ZIP from GitHub and extract it anywhere (e.g., `C:\Users\YourName\AlgoCompiler`)

**Step 3 — Run the setup script (one time only)**

Double-click the file **`scripts\setup_windows.bat`**

A window will open, install all dependencies, and close when done.

**Step 4 — Launch the application**

Double-click the file **`run_app.bat`**

A window will open showing the server is starting.

**Step 5 — Open your browser**

Navigate to: **[http://localhost:5000](http://localhost:5000)**

> **Note:** Keep the terminal / command window open while using AlgoCompiler. Closing it stops the server.

---

## 🔧 Manual Setup

If you prefer to set things up manually (for experienced users):

```bash
# 1. Clone the repository
git clone https://github.com/hosniadilemp-a11y/Algorithemic_language_compiler.git
cd AlgoCompiler

# 2. (Recommended) Create a Python virtual environment
python3 -m venv venv
source venv/bin/activate   # Linux / macOS
# OR:
venv\Scripts\activate      # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the web server
python3 src/web/app.py
```

Then open **http://localhost:5000** in your browser.

---

## 📁 Project Structure

```
AlgoCompiler/
├── src/
│   ├── compiler/
│   │   ├── lexer.py          # Lexical Analyser — tokenizes raw Algo text
│   │   ├── parser.py         # Parser — validates grammar and generates Python
│   │   └── semantic.py       # Semantic Analyser — type checks and validations
│   └── web/
│       ├── app.py            # Flask web server — main entry point
│       ├── debugger.py       # TraceRunner — step-by-step execution engine
│       ├── static/
│       │   ├── style.css     # Main application styles (Dracula theme)
│       │   ├── script.js     # Frontend interaction logic
│       │   └── algo-mode.js  # CodeMirror custom syntax highlighting
│       └── templates/
│           ├── index.html    # Main IDE interface
│           └── errors.html   # Error code documentation
├── examples/                 # Ready-to-use .algo example programs
│   ├── Basics/               # Introduction examples
│   ├── Arrays/               # Tableau (array) examples
│   ├── Strings/              # Chaîne de caractères examples
│   ├── Functions/            # Functions and Procedures examples
│   ├── Pointers/             # Pointer examples
│   └── Dynamic Allocation/   # Linked lists and dynamic memory
├── tests/                    # Automated unit and integration tests
├── scripts/                  # Setup scripts for each platform
│   ├── setup_linux.sh
│   ├── setup_mac.sh
│   └── setup_windows.bat
├── run_app.sh                # Quick launch script (Linux / macOS)
├── run_app.bat               # Quick launch script (Windows)
└── requirements.txt          # Python dependency list
```

---

## 📝 The Algorithmic Language Syntax Guide

Below is a complete reference for beginners.

### Basic Structure

Every algorithm must follow this skeleton:

```
Algorithme NomDuProgramme;
Var
    <variable declarations>
Debut
    <instructions>
Fin.
```

### Variable Declaration

```
Var
    age          : Entier;       // Integer number
    prix         : Reel;         // Floating-point number
    nom[50]      : Chaine;       // String (max 50 characters)
    lettre       : Caractere;    // A single character
    estValide    : Booleen;      // True or False
    T[10]        : Tableau Entier; // Array of 10 integers
```

### Input / Output

```
Ecrire("Entrez votre nom : ");   // Print text to console
Lire(nom);                       // Read user input into variable
```

### Conditions

```
Si age >= 18 Alors
    Ecrire("Majeur");
Sinon
    Ecrire("Mineur");
Fin Si;
```

### Loops

```
// Counted loop (Pour)
Pour i <- 1 a 10 Faire
    Ecrire(i);
Fin Pour;

// Conditional loop (TantQue)
TantQue reponse <> "oui" Faire
    Lire(reponse);
FinTantQue;

// Do-while style (Repeter)
Repeter
    Lire(x);
Jusqu'a x > 0;
```

### Functions and Procedures

```
// Function (returns a value)
Fonction Carre(n : Entier) : Entier
Debut
    Retourner n * n;
Fin;

// Procedure (does not return a value)
Procedure AfficherSeparateur()
Debut
    Ecrire("================");
Fin;
```

### Records (Enregistrement)

```
Type
    Personne = Enregistrement
        nom[50] : Chaine;
        age     : Entier;
    Fin;
Var
    p : Personne;
Debut
    p.nom <- "Alice";
    p.age <- 30;
    Ecrire(p.nom, " a ", p.age, " ans.");
Fin.
```

### Operators

| Category | Operators |
|---|---|
| Arithmetic | `+`, `-`, `*`, `/`, `div` (integer division), `mod` (remainder) |
| Comparison | `=`, `<>` (not equal), `<`, `<=`, `>`, `>=` |
| Logical | `ET` (AND), `OU` (OR), `NON` (NOT) |
| Assignment | `<-` or `:=` |

---

## 🔴 Error Codes Reference

AlgoCompiler provides detailed, clickable error codes. You can find the full reference page at **http://localhost:5000/doc/errors** when the server is running.

| Code | Category | Short Description |
|---|---|---|
| `E1.1` | Lexical | Unknown or illegal character |
| `E2.1` | Syntax | Grammatical error (unexpected token) |
| `E2.2` | Syntax | Unexpected end of file |
| `E2.3` | Syntax | Missing `a` keyword in `Pour` loop |
| `E2.4` | Syntax | Incomplete variable declaration |
| `E3.1` | Semantic | Variable used before it was declared |
| `E3.2` | Semantic | Memory allocation type mismatch |
| `E3.3` | Semantic | Invalid string character assignment |
| `E3.4` | Semantic | Variable declared more than once |
| `E4.1` | Runtime | Infinite loop detected (exceeded 1M instructions) |
| `E4.2` | Runtime | Infinite recursion (stack overflow) |
| `E4.3` | Runtime | Out of memory |
| `E4.4` | Runtime | Array index out of bounds |
| `E4.5` | Runtime | Division by zero |
| `E5.1` | Flow | `Retourner` used outside a function |

---

## 🧪 Running the Tests

AlgoCompiler has a full suite of automated tests. To run all tests:

```bash
# Linux / macOS
python3 -m unittest discover tests

# Windows
python -m unittest discover tests
```

You should see output ending in `OK` with all tests passing.

---

## 🐛 Reporting Bugs & Issues

Found a bug? That's great — it helps us improve! Here's how to report it properly on GitHub:

### Step 1 — Check for Existing Issues

Before filing a new report, search the [Issues page](https://github.com/hosniadilemp-a11y/Algorithemic_language_compiler/issues) to see if someone already reported the same problem.

### Step 2 — Open a New Issue

Click the green **"New Issue"** button and fill in the following template:

```
**Summary:**
A one-sentence description of what went wrong.

**Steps to reproduce:**
1. Open AlgoCompiler at http://localhost:5000
2. Type the following code into the editor:
   [paste your .algo code here]
3. Click "Exécuter"
4. Observe the output / error

**Expected behaviour:**
What you expected to happen.

**Actual behaviour:**
What actually happened (include error messages, error codes like [E3.1], etc.)

**Environment:**
- Operating System: [e.g., Ubuntu 22.04 / Windows 11 / macOS 14]
- Python version: [run `python3 --version`]
- Browser: [e.g., Chrome 120, Firefox 121]

**Screenshots:**
[If applicable, paste screenshots here — you can drag and drop images directly into GitHub]
```

### Step 3 — Add Labels

If you have permission, add one of these labels to help us triage:
- `bug` — something is broken
- `enhancement` — a new feature request
- `documentation` — missing or wrong documentation
- `question` — you need help understanding something

### Tips for a Good Bug Report

- ✅ Include the **exact algorithm code** that triggered the error
- ✅ Copy-paste the **full error message** from the console
- ✅ Mention the **error code** (e.g., `[E4.1]`) if shown
- ✅ Describe **what you expected** vs **what actually happened**
- ❌ Don't say "it doesn't work" without details

---

## 🤝 Contributing

Contributions are welcome! Whether it's fixing a typo in the docs, adding a new example, or implementing a new language feature — all help is appreciated.

1. **Fork** this repository
2. Create a new branch: `git checkout -b feature/my-improvement`
3. Make your changes
4. Run the test suite: `python3 -m unittest discover tests`
5. **Commit** with a descriptive message: `git commit -m "Add support for XYZ feature"`
6. **Push** your branch: `git push origin feature/my-improvement`
7. Open a **Pull Request** on GitHub

Please ensure your code passes all existing tests before submitting a pull request.

---

## 📄 License

This project is released under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ for Computer Science students learning Algorithmics.

</div>
