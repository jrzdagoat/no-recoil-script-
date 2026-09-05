# JRZ Mouse Mover

A small desktop app with a UI: a slider to set the "strength" (how many
pixels the mouse moves down), a button to trigger the move, and saved
presets you can reload any time.

## Run it directly with Python
```
pip install pyautogui
python jrz_mouse_mover.py
```

## Build a Windows .exe using GitHub (no Windows machine needed)

This project includes a GitHub Actions workflow that builds `JRZMouseMover.exe`
for you on a free Windows cloud runner every time you push to `main`.

### 1. Create a GitHub repo
- Go to github.com → **New repository** → name it (e.g. `jrz-mouse-mover`) → **Create repository**.

### 2. Upload these files
Keep the folder structure exactly as it is in the zip:
```
jrz_mouse_mover.py
requirements.txt
.github/workflows/build-exe.yml
```
Easiest way: on the repo page, click **Add file → Upload files** and drag in
`jrz_mouse_mover.py` and `requirements.txt`. Then for the workflow file, if
dragging doesn't preserve the folder, click **Add file → Create new file**,
type the full path `.github/workflows/build-exe.yml` as the filename, and
paste in that file's contents.

Or, with git installed locally:
```bash
git init
git add jrz_mouse_mover.py requirements.txt .github/workflows/build-exe.yml README.md
git commit -m "Add JRZ Mouse Mover + build workflow"
git branch -M main
git remote add origin https://github.com/<your-username>/jrz-mouse-mover.git
git push -u origin main
```

### 3. Let GitHub build it
- Go to the **Actions** tab in your repo. A run called "Build Windows EXE"
  starts automatically after your push (or click **Run workflow** to trigger it manually).
- Wait for the green checkmark — usually 1-2 minutes.

### 4. Download the .exe
- Click into the finished workflow run.
- Scroll to **Artifacts** → download `JRZMouseMover-windows`.
- Unzip it — inside is `JRZMouseMover.exe`. Double-click to run it, no Python needed.

### Updating later
Edit `jrz_mouse_mover.py`, push to `main`, and GitHub rebuilds the exe
automatically — grab the new one from Actions → Artifacts.
