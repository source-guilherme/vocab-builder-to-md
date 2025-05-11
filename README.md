# Vocabulary Builder Exporter

A GUI tool to export vocabulary from a SQLite database to Markdown files, with filtering and preview options.

## Features

- Export vocabulary by book and/or date
- Markdown preview before export
- Dark mode support
- Custom output folder
- Standalone executable support (via PyInstaller)

## Installation

### Run from Source

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/vocab-builder-to-md.git
   cd vocab-builder-to-md
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python main.py
   ```

### Run as Executable

If you have a prebuilt executable, just double-click it to run.

Or build your own (see Packaging below).

## Usage

1. Click "Browse Vocab Builder File" to select your SQLite database.
2. Click "Select Output Folder" to choose where to save Markdown files.
3. (Optional) Use filter options to export by book or date.
4. Click "Preview Export" to see the Markdown output.
5. Click "Export!" to save the files.

## Packaging as Executable

To create a standalone executable (Windows):

1. Install PyInstaller:
   ```
   pip install pyinstaller
   ```
2. Build the executable:
   ```
   pyinstaller --onefile --windowed --icon=src/icon.ico --add-data "src/icon.ico;src" --name vocab-builder-to-md main.py
   ```
3. The executable will be in the `dist/` folder.

## Configuration

- The theme preference is saved in `config.json` in the project root.

## License

MIT License
