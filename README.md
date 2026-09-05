# Mouse Mover

A small macro that moves your mouse cursor down by an adjustable amount,
with named presets you can save and reload.

## Build a Windows .exe using GitHub (no Windows machine needed)

This repo includes a GitHub Actions workflow that builds the `.exe` for
you on a free Windows cloud runner every time you push to `main`.

### 1. Create a GitHub repo
- Go to github.com → **New repository** → name it (e.g. `mouse-mover`) → **Create repository**.

### 2. Upload these files
Upload all of them, keeping the folder structure exactly as-is:
```
mouse_mover.py
requirements.txt
.github/workflows/build-exe.yml
```
Easiest way: on the repo page, click **Add file → Upload files**, drag in
`mouse_mover.py` and `requirements.txt`, then repeat for the `.github/workflows/build-exe.yml`
file (GitHub will recreate the folders automatically based on the path you drop it at —
if the web uploader flattens it, instead use the "Create new file" button and type the
full path `.github/workflows/build-exe.yml` as the filename).

Or, if you have git installed locally:
```bash
git init
git add mouse_mover.py requirements.txt .github/workflows/build-exe.yml
git commit -m "Add mouse mover + build workflow"
git branch -M main
git remote add origin https://github.com/<your-username>/mouse-mover.git
git push -u origin main
```

### 3. Let GitHub build it
- Go to the **Actions** tab in your repo. A workflow run called "Build Windows EXE"
  should start automatically after your push (or click **Run workflow** to trigger it manually).
- Wait for it to finish (green checkmark, usually ~1-2 minutes).

### 4. Download the .exe
- Click into the finished workflow run.
- Scroll to **Artifacts** at the bottom → download `mouse_mover-windows`.
- Unzip it — inside is `mouse_mover.exe`, ready to run on any Windows machine
  (no Python install required on the machine that runs it).

### Updating later
Any time you edit `mouse_mover.py` and push the change to `main`, GitHub will
automatically rebuild the `.exe` for you — just grab the new one from Actions → Artifacts.

## Running it directly with Python instead
If you'd rather not deal with GitHub at all:
```
pip install pyautogui
python mouse_mover.py
```
