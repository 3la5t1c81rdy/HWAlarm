# HWAlarm - v1.0
A simple Homework Alarm program I made in Python. Does everything (well, most things) you'd expect of a task list. **It probably won't work in any OS other than Windows but always welcome to try**

**This is still in development with minimal features. As of now, you need to manually remove tasks once you want to clear them.**
## Dependencies
  - Pygame
  - PyWin32 (with all its modules correctly installed)
  - Time (Standard Library)
  - ctypes (Standard Library)
  - os (Standard Library)
  - sys (Standard Library)

## How to use
  1. Running the HWAlarm.py will open a new window.
      - *Left-click* to add homework/task
      - *Right-click* to remove homework/task
      - Scroll using mouse wheels
  2. Once there is an upcoming task (i.e. due in less than 12 hours), the window will start flashing in the taskbar.
  3. Now "how-to" information screen is available by pressing escape key on main view.
  4. Fonts can be changed, by pressing "f" key on the main window.
  5. Save/Load is possible - User is prompted to save/not save on exit, or can save/change save location manually by pressing "s" or "c", respectively. To load/open a save file, press "o."
