# Guidelines: Customizing Extraction & Filters via `filter_config.json`

The extraction tool uses a dynamic configuration file named `filter_config.json` located in the root of the workspace. This file allows you to customize keyword searches, add or remove false-positive filters, adjust subsystem categories, and control bypass parameters without modifying the code.

---

## 🛠️ Configuration Settings

The JSON file contains the following fields:

### 1. `bypass_filtering` (Boolean)
*   **Purpose**: Toggles false-positive filtering globally.
*   **Values**:
    *   `false` (Default): Evaluates paragraphs against the `false_positive_patterns` and excludes matches.
    *   `true`: Bypasses all false-positive filtering (retains everything that matches keywords).

### 2. `no_filter` (Boolean)
*   **Purpose**: Toggles all filtering checks (both keyword matching and false-positive heuristics).
*   **Values**:
    *   `false` (Default): Standard operation utilizing keywords and false-positive checks.
    *   `true`: Extracts ALL paragraphs (greater than 15 characters) regardless of content, bypassing all filters.

### 2. `keywords` (Array of Strings)
*   **Purpose**: Regular expression (regex) patterns to match and extract relevant paragraphs.
*   **How to Edit**: 
    *   Add any new regex terms or raw words you want to search for.
    *   Example: To extract all electrical UPS or transformer specifications, you could add:
        ```json
        "\\bups\\b",
        "\\btransformer[s]?\\b"
        ```
    *   *Note*: Remember to double-escape backslashes in JSON (e.g. use `\\b` for word boundaries instead of `\b`).

### 3. `false_positive_patterns` (Array of Strings)
*   **Purpose**: Regex patterns used to weed out paragraphs that matched the keywords but are not actually relevant (e.g. piping, temporary facilities, BARC guidelines).
*   **How to Edit**:
    *   Add new phrases or terms that tend to appear in false positive rows.
    *   Example: If the word "switch" is matching civil building light switches, you can add:
        ```json
        "\\blight\\s+switch\\b"
        ```

### 4. `category_order` (Object/Dictionary)
*   **Purpose**: Sets the sorting order for subsystems inside the compiled Excel output.
*   **How to Edit**:
    *   The keys represent subsystem names, and values represent sorting ranks (lower numbers appear first).
    *   If you introduce new subsystem labels, add them here to control their placement in the spreadsheet.

---

## 🔄 Dynamic Reloading

*   **Offline CLI Runs**: The tool reads `filter_config.json` from disk every time `python extract_to_excel.py` is run.
*   **Web Dashboard App**: The Flask backend reads the configuration file dynamically on every new extraction request. There is no need to restart the Flask server after saving edits to `filter_config.json`.
*   **Bypassing via UI/CLI**:
    *   **UI**: Toggle "Bypass False-Positive Filter" or "No Filter" in the settings panel.
    *   **CLI**: Use `--bypass-filtering` or `--no-filter` flags:
        ```bash
        python extract_to_excel.py --force-extract --bypass-filtering
        python extract_to_excel.py --force-extract --no-filter
        ```
*   **Fallback Safety**: If `filter_config.json` is missing or contains invalid JSON syntax, the tool will display a warning and fall back to the built-in telecom/security defaults.
