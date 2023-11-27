import win32gui
import win32con
import time as t
import pygame
import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('HWA v1.0')

def convert_weekday(wday):
    if (wday < 0) or (wday > 6):
        return None
    return ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][wday]
class Task:
    def __init__(self, name: str, tasktime: t.struct_time, course = None):
        self.name = name
        self.tasktime = tasktime
        self.course = course
    
    def __str__(self):
        return f"*{self.name}*\n for {self.course}, due {convert_weekday(self.tasktime[6])}, {self.tasktime[0]}/{self.tasktime[1]}/{self.tasktime[2]} {self.tasktime[3]}'o clock"
    

class Alert:
    def __init__(self, alarm):
        self.upcoming = []#(task,*-1,0,1,2,3*)] <- -1: !!!OVERDUE!!!, 0: due in less than 1hr, 1: due in 3 hours, 2: due in 12 hours, 3: due in 1 day, 4: due in 3 days
        self.upcoming_raw = []#only stores task
        self.alarm = alarm
        self.dnd = False
    def update_alert(self):
        print("update in progress..")
        currt = t.time()
        for i in self.alarm.task_list:
            if i in self.upcoming_raw:
                continue
            if t.mktime(i.tasktime) < currt:
                self.upcoming.insert(0,(i,-1,True))
                self.upcoming_raw.append(i)
            elif t.mktime(i.tasktime) - currt <= 3600:
                self.upcoming.insert(0,(i,0,True))
                self.upcoming_raw.append(i)
            elif t.mktime(i.tasktime) - currt <= 10800:
                self.upcoming.insert(0,(i,1,True))
                self.upcoming_raw.append(i)
            elif t.mktime(i.tasktime) - currt <= 43200:
                self.upcoming.append((i,2,True))
                self.upcoming_raw.append(i)
            elif t.mktime(i.tasktime) - currt <= 86400:
                self.upcoming.append((i,3,True))
                self.upcoming_raw.append(i)
            elif t.mktime(i.tasktime) - currt <= 259200:
                self.upcoming.append((i,4,True))
                self.upcoming_raw.append(i)
        for _,alertType,unchecked in self.upcoming:
            if unchecked and alertType < 3:
                flash(self.alarm.hwnd)
                break
        print("updated")
        #print(self.alarm.task_list,self.upcoming)
class Alarm_window:
    def __init__(self, setupTuple: tuple):
        self.disp = setupTuple[0]
        self.hwnd = setupTuple[1]
        self.screen_top_y = 0 #stores the vertical scroll
        self.max_y = 0
        self.task_list = []
        self.font = pygame.font.Font("HWA_resources/Roboto-Medium.ttf", 20)
        self.lineht = self.font.size("g")[1]
    def __str__(self):
        return_str = "{\n"
        ind = 0
        for task in self.task_list:
            return_str += str(task) + "\n ^ at index "+str(ind)+"\n,\n"
            ind += 1
        return return_str[:-2]+"\n}"
    def add_task(self):
        #WIP: you should add task according to the time order.
        try:
            a, b, c = input("Enter the name of the new task: "),t.strptime(input("Enter the due date in this form - YYYY/MM/DD hh (24-hr-format): "), "%Y/%m/%d %H"), input("Enter the class name: ")
            ind = 0
            for i in range(len(self.task_list)):
                if self.task_list[i].tasktime > b:
                    break
                ind += 1
            self.task_list.insert(ind,Task(a,b,c))
        except:
            print("Something went wrong.")
            if input("Press enter to try again. Type anything to stop.") == "":
                self.add_task()
    def remove_task(self):
        print(self)
        if len(self.task_list) > 0:
            try:
                tsk_index = int(input(f"Select the index of the task to remove (0 to {len(self.task_list) - 1}): "))
                if input(f"Are you sure you want to clear:\n\"{self.task_list[tsk_index]}\"\n? If so, type enter. If not, type anything else then press enter.") == "":
                    self.task_list.pop(tsk_index)
            except:
                print("Something went wrong.")
                if input("Press enter to try again. Type anything to stop.") == "":
                    self.remove_task()
        else:
            print("Homework list is already cleared!")
    def update_alarm(self):
        #draw all current alarm 
        curr_y = 0
        max_x, max_y = pygame.display.get_window_size()
        max_y += self.screen_top_y
        l_count = 0
        
        for i in self.task_list:
            """
            if curr_y < self.screen_top_y:
                curr_y += self.lineht*len(add_linebreak(self.font, str(i), max_x).split("\n"))
                continue
            """
            if curr_y >= max_y:
                break
            split_i = str(i).split("\n")
            line_broken_i = add_linebreak(self.font, split_i[1], max_x).split('\n')
            line_broken_taskname = add_linebreak(self.font, split_i[0], max_x).split('\n')
            #blit
            
            for line in range(len(line_broken_taskname)):
                self.disp.blit(self.font.render(line_broken_taskname[line], True, (150,0,0)), (0,curr_y - self.screen_top_y))
                curr_y += self.lineht
                l_count += 1
            for line in range(len(line_broken_i)):
                self.disp.blit(self.font.render(line_broken_i[line], True, (0,0,0)), (0,curr_y - self.screen_top_y))
                curr_y += self.lineht
                l_count += 1
            curr_y += self.lineht
        
        self.max_y = l_count*self.lineht
    def scroll_line(self,up_or_down: bool):
        if up_or_down:
            #up
            self.screen_top_y = max(0,self.screen_top_y - self.lineht)
        else:
            #down
            self.screen_top_y = max(0, min(self.max_y - pygame.display.get_window_size()[1],self.screen_top_y + self.lineht))
        print(self.screen_top_y, self.max_y)
def setup():
    pygame.init()
    pygame.display.set_icon(pygame.image.load("HWA_resources/HWA_icon.png"))
    pygame.display.set_caption("HWAlarm v1.0")
    w = pygame.display.set_mode((500,500), pygame.RESIZABLE)
    hwnd = pygame.display.get_wm_info()['window']
    return (w, hwnd)

def add_linebreak(font: pygame.font.Font, text, disp_width) -> str:
    size = font.size(text)
    if len(text) == 1 or size[0] <= disp_width:
        return text
    else:
        #find the *split-point* -##CAN BE OPTIMIZED TO O(n) = log(n) but seems unnecessary at this small scale
        curr_size = 0
        for i in range(len(text)):
            curr_size += font.size(text[i])[0]
            if curr_size > disp_width:
                #split at i; [0:i] and [i:]
                return text[:i] + "\n" + add_linebreak(font, text[i:], disp_width)
def flash(hwnd):
    win32gui.FlashWindowEx(hwnd, win32con.FLASHW_ALL | win32con.FLASHW_TIMERNOFG, 1, 0)