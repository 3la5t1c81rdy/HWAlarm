from HWAHelper import *
if __name__ == '__main__':
    HWAlarm = Alarm_window(setup())
    HWAlert = Alert(HWAlarm)
    tstamp = 0
    c = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    HWAlarm.add_task()
                elif event.button == 3:
                    HWAlarm.remove_task()
                elif event.button == 4:
                    #up
                    HWAlarm.scroll_line(True)
                elif event.button == 5:
                    #down
                    HWAlarm.scroll_line(False)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    HWAlarm.text_info("Left click to add task.\nRight click to remove task.\nYou can use mouse scroll to maneuver between task list.\nPress \"f\" key to change display font.")
                if event.key == pygame.K_f:
                    HWAlarm.change_font()
        
        HWAlarm.clear()
        
        
        if t.time() - tstamp > 5:
            tstamp = t.time()
            HWAlert.update_alert()
        HWAlarm.update_alarm()
        if HWAlarm.get_num_tasks() == 0:
            HWAlarm.splash_nullscreen()
        pygame.display.flip()
        c.tick(20)
    quit(0)