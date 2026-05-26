import io
import os
import platform
import re
import sys

from PIL import Image

# Import Textual TUI widgets
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Button, DataTable, Footer, Header, Input, Log, Static

# ==========================================
# 1. CROSS-PLATFORM OCR & RENAMING UTILITIES
# ==========================================


def crop_document_target(image_path):
    """Crops the input image to the Delivery Note No. cell only, excluding the Dated column."""
    img = Image.open(image_path)
    width, height = img.size
    left = int(width * 0.45)
    top = int(height * 0.05)
    right = int(width * 0.62)  # stopped before the Dated column to avoid capturing the date
    bottom = int(height * 0.12)
    return img.crop((left, top, right, bottom))


def parse_cleaned_string(combined_string):
    """Extracts the exact delivery note identity from OCR text."""
    match = re.search(r"(DN-[A-Z0-9]+-\d{4}-\d+)", combined_string, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None


def run_mac_ocr(cropped_img):
    import Cocoa
    import Vision

    img_byte_arr = io.BytesIO()
    cropped_img.save(img_byte_arr, format="JPEG")
    img_data = Cocoa.NSData.dataWithBytes_length_(
        img_byte_arr.getvalue(), len(img_byte_arr.getvalue())
    )

    text_strings = []

    def completion_handler(request, error):
        if not error:
            for observation in request.results():
                text_strings.append(observation.text())

    request = Vision.VNRecognizeTextRequest.alloc().initWithCompletionHandler_(
        completion_handler
    )
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)

    handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(img_data, None)
    success, _ = handler.performRequests_error_([request], None)
    return "".join(text_strings).replace(" ", "") if success else ""


def run_windows_ocr(cropped_img):
    import asyncio

    import winrt.windows.graphics.imaging as imaging
    import winrt.windows.media.ocr as ocr
    import winrt.windows.storage.streams as streams

    async def _async_win_ocr():
        img_byte_arr = io.BytesIO()
        cropped_img.save(img_byte_arr, format="JPEG")
        data_writer = streams.DataWriter()
        data_writer.write_bytes(list(img_byte_arr.getvalue()))
        stream = streams.InMemoryRandomAccessStream()
        await stream.write_async(data_writer.detach_buffer())
        stream.seek(0)

        decoder = await imaging.ImageDecoder.create_async(stream)
        software_bitmap = await decoder.get_software_bitmap_async()
        engine = ocr.OcrEngine.try_create_from_user_profile_languages()
        ocr_result = await engine.recognize_async(software_bitmap)
        return "".join([line.text for line in ocr_result.lines]).replace(" ", "")

    return asyncio.run(_async_win_ocr())


def extract_delivery_note(image_path):
    """Processes a single file and extracts its note number."""
    current_os = platform.system()
    if not os.path.exists(image_path):
        return "File Not Found"

    try:
        cropped_img = crop_document_target(image_path)
        if current_os == "Darwin":
            raw_text = run_mac_ocr(cropped_img)
        elif current_os == "Windows":
            raw_text = run_windows_ocr(cropped_img)
        else:
            return "Unsupported OS"

        parsed_result = parse_cleaned_string(raw_text)
        return parsed_result if parsed_result else "Parsing Match Failed"
    except Exception:
        return "Processing Error"


PATTERN = r"DN-[A-Z]+-\d{4}-\d+"


def extract_number_from_text_using_regex(text, logger):
    logger.write_line(f"Text: {text}")
    match = re.search(PATTERN, text)
    if match:
        return match.group(0)
    return None


def extract_number_from_text(text, logger):
    logger.write_line(f"Text: {text}")

    parts = text.split("-")
    return parts[3] if len(parts) > 3 else None


# ==========================================
# 2. BATCH TUI LAYOUT APPLICATION WITH RENAMER
# ==========================================


class BatchOCRScannerApp(App):
    """A terminal dashboard optimized for scanning and renaming directories of delivery notes."""

    CSS = """
    Screen {
        background: #1e1e2e;
    }
    #main-container {
        padding: 1 2;
    }
    .panel-title {
        text-style: bold;
        color: #cdd6f4;
        margin-top: 1;
        margin-bottom: 1;
    }
    Input {
        background: #313244;
        color: #cdd6f4;
        border: tall #cba6f7;
    }
    Button {
        background: #a6e3a1;
        color: #11111b;
        text-style: bold;
        border: none;
        margin-top: 1;
        width: 100%;
    }
    Button:hover {
        background: #94e2d5;
    }
    DataTable {
        background: #11111b;
        border: solid #45475a;
        height: 14;
        margin-top: 1;
    }
    Log {
        background: #11111b;
        border: solid #45475a;
        height: 9;
        margin-top: 1;
    }
    """

    BINDINGS = [("q", "quit", "Quit Application")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            yield Static("📁 BATCH TARGET FOLDER", classes="panel-title")
            yield Input(
                placeholder="Enter absolute directory path (e.g., /Users/name/Documents/DeliveryNotes)",
                id="folder-input",
            )
            yield Button(
                "Begin Batch Scan & Auto-Rename Pipeline",
                id="batch-scan-btn",
                variant="success",
            )

            yield Static("📊 EXTRACTION & RENAMING PROGRESS", classes="panel-title")
            yield DataTable(id="results-table")

            yield Static("🖥️ SYSTEM EVENT CONSOLE LOG", classes="panel-title")
            yield Log(id="engine-log")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize columns inside the data viewport table."""
        table = self.query_one("#results-table", DataTable)
        table.add_columns(
            "Original File Name", "Extracted ID", "New File Name", "Status"
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "batch-scan-btn":
            folder_path = self.query_one("#folder-input", Input).value.strip()
            logger = self.query_one("#engine-log", Log)
            table = self.query_one("#results-table", DataTable)

            if not folder_path or not os.path.isdir(folder_path):
                logger.write_line(
                    "[ERROR] Invalid directory target. Please check the folder pathway."
                )
                return

            logger.clear()
            table.clear()

            supported_extensions = (".jpg", ".jpeg", ".png", ".tiff")
            all_files = os.listdir(folder_path)
            target_images = [
                f for f in all_files if f.lower().endswith(supported_extensions)
            ]

            if not target_images:
                logger.write_line(
                    f"[INFO] No compatible image assets discovered in folder target."
                )
                return

            logger.write_line(
                f"[START] Batch pipeline active. Processing {len(target_images)} files..."
            )

            for idx, filename in enumerate(target_images, 1):
                full_path = os.path.join(folder_path, filename)
                logger.write_line(f"Reading ({idx}/{len(target_images)}): {filename}")

                # 1. Run the native OCR Engine
                note_number = extract_delivery_note(full_path)
                logger.write_line(
                    f"-> {extract_number_from_text(note_number, logger)}: {filename}"
                )

                # 2. Handle Renaming Actions based on extraction success
                if "DN-" in note_number:
                    file_ext = os.path.splitext(filename)[
                        1
                    ]  # Keeps original format extension (.jpg, .png, etc)
                    new_filename = (
                        f"{extract_number_from_text(note_number, logger)}{file_ext}"
                    )
                    new_full_path = os.path.join(folder_path, new_filename)

                    if filename == new_filename:
                        status_style = "[yellow]ALREADY RENAMED[/yellow]"
                        logger.write_line(
                            f"Skipping: '{filename}' is already correctly named."
                        )
                    elif os.path.exists(new_full_path):
                        status_style = "[orange3]NAME CONFLICT[/orange3]"
                        logger.write_line(
                            f"[WARN] File '{new_filename}' already exists! Skipping to protect data."
                        )
                    else:
                        try:
                            os.rename(full_path, new_full_path)
                            status_style = "[green]RENAMED[/green]"
                            logger.write_line(
                                f"Successfully moved: '{filename}' ➡️ '{new_filename}'"
                            )
                        except Exception as e:
                            status_style = "[red]RENAME ERROR[/red]"
                            logger.write_line(
                                f"[ERROR] OS File system locked: {str(e)}"
                            )
                else:
                    new_filename = "N/A"
                    status_style = "[red]OCR FAILED[/red]"
                    logger.write_line(
                        f"[WARN] Could not safely identify index values for {filename}"
                    )

                # 3. Dynamically push a row straight to the live terminal grid
                table.add_row(filename, note_number, new_filename, status_style)
                self.refresh()

            logger.write_line(
                "[FINISH] Batch system execution pipeline completed smoothly."
            )


if __name__ == "__main__":
    BatchOCRScannerApp().run()
