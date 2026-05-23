# 📄 Cross-Platform Delivery Note OCR Scanner & Renamer

A blazing-fast, lightweight **Text User Interface (TUI)** utility built in Python that automatically scans directories of scanned invoices or delivery notes, extracts their unique tracking identifiers using **native operating system hardware engines**, and cleanly renames the files in bulk.

No heavy machine learning models to download, no expensive cloud API subscriptions, and no processing lag.

---

## 🚀 Key Features

* **⚡ Native OS Acceleration:** Dynamically detects your platform environment to route computations to the fastest local binary libraries available:
    * **macOS:** Leverages Apple's native **Vision Framework** (The core engine powering Live Text).
    * **Windows:** Leverages Microsoft's native **Windows Media OCR API**.
* **📟 Elegant Terminal User Interface:** Built using the modern asynchronous **Textual** framework, featuring scrollable data grids, live system event logging counters, and smooth keyboard navigation bindings.
* **🧠 Intelligently Handled Character Merging:** Automatically resolves common OCR optical illusions where a trailing tracking number merges seamlessly with a adjacent numerical date (e.g., parsing `DN-IKD-0526-1` correctly even when right next to `1-May-26`).
* **🛡️ Data Integrity Guards:** Built-in safeguards that check for name collisions and prevent accidental file overwrites or double-scanning.
* **🤖 Full CI/CD Automation:** Includes a GitHub Actions pipeline matrix to automatically build single-file distributable binaries for both platforms on every tag push.

---

## 🛠️ Installation & Local Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME
```

### 2. Configure Your Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

```

### 3. Install Requirements

The configuration maps specific environmental markers to install *only* the dependencies required for your current operating system framework:

```bash
pip install -r requirements.txt

```

---

## 🖥️ Usage

Launch the terminal application directly from your workspace:

```bash
python __init__.py

```

### 🕹️ Interface Controls:

1. **Target Selection:** Type or paste the absolute folder path containing your delivery note images into the **Batch Target Folder** input line.
2. **Execution:** Click the green button or navigate to it using your keyboard to initialize processing.
3. **Real-Time Tracking:** Watch the `Data Table` display original filenames, extracted tracking IDs, new targets, and immediate pipeline status streams.
4. **Graceful Exit:** Press `Q` at any time to kill the interface wrapper and drop cleanly back to your terminal shell prompt.

---

## 📦 Creating Standalone Binaries Locally

If you want to compile a single executable file that can run on other machines *without* needing Python or dependency environments installed, use PyInstaller.

> **Note:** Executable compilation is host-dependent. You must compile on a Mac to get a Mac binary, and compile on Windows to get a Windows `.exe`.

**On macOS:**

```bash
pip install pyinstaller
pyinstaller --onefile --name="DeliveryNoteScanner" --hidden-import="Cocoa" --hidden-import="Vision" --hidden-import="Foundation" __init__.py

```

**On Windows:**

```bash
pip install pyinstaller
pyinstaller --onefile --name="DeliveryNoteScanner" --hidden-import="winrt.windows.media.ocr" --hidden-import="winrt.windows.graphics.imaging" --hidden-import="winrt.windows.storage.streams" __init__.py

```

Your compiled standalone application will be waiting inside the local `dist/` directory!

---

## 🤖 Automated CI/CD Deployment (GitHub Actions)

This repository includes a completely automated deployment system. You do not need to compile things manually to hand them to non-technical users.

Whenever you push a version tag to your repository, a GitHub runner matrix spins up parallel virtual machine instances, processes the compilation configurations, creates a brand new **GitHub Release**, and builds/uploads the assets cleanly.

To fire the automated pipeline release engine:

```bash
git tag -a v1.0.0 -m "Release initial production-ready application"
git push origin v1.0.0

```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more details.