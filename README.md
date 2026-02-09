# Japanese Vertical PDF OCR Tool

このツールは、PyMuPDF と Tesseract OCR を使用して、日本語の縦書きPDF（小説など）からテキストを抽出するためのユーティリティです。
GUIを備えており、フォルダ単位での一括処理や進捗確認が容易に行えます。

## 必要要件

- Windows OS
- Python 3.x
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (v5推奨)
    - **インストール方法**:
        1. [UB-MannheimのGitHubページ](https://github.com/UB-Mannheim/tesseract/wiki) などから、Windows用のインストーラー（例: `tesseract-ocr-w64-setup-v5.x.x.exe`）をダウンロードします。
        2. インストーラーを実行します。
        3. インストール中の「Choose Components」画面で、**"Additional script data (download)"** -> **"Japanese script"** および **"Additional language data (download)"** -> **"Japanese (vertical)"** にチェックを入れてください。
           - これにより `jpn_vert` データがインストールされます。
        4. インストール先パスをメモしておいてください（デフォルト: `C:\Program Files\Tesseract-OCR`）。

## インストール

1. このリポジトリをクローンまたはダウンロードします。
2. 必要なPythonライブラリをインストールします。
   ```bash
   pip install -r requirements.txt
   ```
   (`requirements.txt` には `pymupdf`, `pytesseract`, `Pillow` などが含まれている必要があります)

## 使い方 (GUI)

1. `ocr_gui.py` を実行します。
   ```bash
   python ocr_gui.py
   ```
2. **Source Directory (PDFs)**:
   - 「Browse」ボタンを押して、OCR処理を行いたいPDFファイルが入っているフォルダを選択します。
3. **Output Directory (Txt Files)**:
   - 「Browse」ボタンを押して、抽出したテキストファイルを保存するフォルダを選択します。
   - デフォルトはスクリプト実行ディレクトリです。
4. **OCR Settings**:
   - **Zoom**: 画質設定（デフォルト: 3）。値を大きくすると画質が向上しますが、処理時間が長くなります。
   - **PSM**: ページ分割モード（デフォルト: 5）。縦書きの単一ブロックとして認識させます。
   - **Lang**: 言語設定（デフォルト: `jpn_vert`）。
   - **Tesseract Path**: Tesseractが標準以外の場所にインストールされている場合、ここで `tesseract.exe` を指定してください。
5. **START PROCESSING**:
   - ボタンを押すと処理が開始されます。
   - 画面左側にファイル単位のログ、右側にページ単位の進捗が表示されます。
   - 処理済みのファイルは履歴 (`processed_log.txt`) に記録され、次回実行時には自動的にスキップされます。
6. **STOP**:
   - 中断したい場合は「STOP」ボタンを押してください。
7. **Manual**:
   - 「Manual」ボタンを押すと、このドキュメントを別ウィンドウで閲覧できます。

## ファイル構成

- `ocr_gui.py`: メインのGUIアプリケーション。
- `ocr_script.py`: OCR処理のコアロジック。
- `processed_log.txt`: 処理完了したファイル名のリスト（自動生成）。
- `requirements.txt`: 依存ライブラリリスト。

## トラブルシューティング

- **Tesseractが見つからない場合**:
  - Tesseractがインストールされているか確認してください。
  - パスが異なる場合は、`ocr_script.py` 内の `tesseract_cmd` 設定を変更するか、環境変数 `PATH` にTesseractのディレクトリを追加してください。
- **ログの書き込みエラー**:
  - フォルダの書き込み権限を確認してください。

## ライセンス

[MIT License](LICENSE) (または任意のライセンス)
