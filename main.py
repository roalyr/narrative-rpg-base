import curses
import curses.panel
import shutil

########################################

# CONSTANTS
anim_delay = 500

########################################

# WINDOW LAYOUT
# Main window.
height_main = 24
width_main = 40

# Tab switcher.
height_tab_switcher = 3
width_tab_switcher = width_main - 4
offset_vert_tab_switcher = 1
offset_horiz_tab_switcher = 2

# Tab buttons.
height_button_tab_switcher = 3
width_button_tab_switcher = 7
offset_vert_button_tab_switcher = 0
offset_horiz_button_tab_switcher = 0 # between buttons

# Text editor tab (window).
height_text_main = 20
width_text_main = 36
offset_vert_text_main = 3
offset_horiz_text_main = 2

# Text page character limit as defined by window size to avoid scrolling.
buffer_limit = (height_text_main - 2) * (width_text_main - 2) - 1

########################################

# CONTENT LOADING
strings = {
	"test_string" : "Simple Тест",
	"btn_text_main" : "Text",
}

########################################

# DATA STRYCTURES AND VARS
windows = {}
buttons = {}
panels = {}
buffer = []

########################################

# TESTING
test_text_ = "There are many variations of passages of Lorem Ipsum available, but the majority have suffered alteration in some form, by injected humour, or randomised words which don't look even slightly believable. If you are going to use a passage of Lorem Ipsum, you need to be sure there isn't anything embarrassing hidden in the middle of text. All the Lorem Ipsum generators on the Internet tend to repeat predefined chunks as necessary, making this the first true generator on the Internet."
test_text = "There are many variations of passages of Lorem Ipsum available"

# Split current page string into characters.
for c in test_text_:
	buffer.append(c)

########################################

# WINDOW FUNCTIONS
def update_win_main(stdscr, win_main):
	win_main.resize(height_main, width_main)
	win_main.clear()
	win_main.attron(curses.color_pair(1))
	win_main.border()
	win_main.addstr(0, width_main // 2 - len(strings["test_string"]) // 2, strings["test_string"])
	win_main.noutrefresh()
	
def update_win_tab_switcher(stdscr, win_tab_switcher):
	win_tab_switcher.resize(height_tab_switcher, width_tab_switcher)
	win_tab_switcher.clear()
	win_tab_switcher.attron(curses.color_pair(2))
	win_tab_switcher.border()
	win_tab_switcher.noutrefresh()
	
def update_win_text_main(stdscr, win_text_main):
	win_text_main.resize(height_text_main, width_text_main)
	win_text_main.clear()
	win_text_main.attron(curses.color_pair(2))
	win_text_main.border()
	win_text_main.noutrefresh()
	
# BUTTONS # TODO: make unified.
def update_button_tab_main_text(stdscr, button_tab_main_text):
	button_tab_main_text.resize(height_button_tab_switcher, width_button_tab_switcher)
	button_tab_main_text.clear()
	button_tab_main_text.attron(curses.color_pair(2))
	if not panels["panel_text_main"].hidden():
		button_tab_main_text.border(0, 0, 0, ' ', 0, 0, curses.ACS_VLINE, curses.ACS_LLCORNER)
	else:
		button_tab_main_text.border()
	button_title = strings["btn_text_main"]
	button_title_offset = width_button_tab_switcher // 2 - len(button_title) // 2
	button_tab_main_text.attron(curses.A_BOLD | curses.color_pair(1))
	button_tab_main_text.addstr(1, button_title_offset, button_title)
	button_tab_main_text.attroff(curses.A_BOLD | curses.color_pair(1))
	button_tab_main_text.noutrefresh()

# UPDATE MAIN
def update_all(stdscr):
	# Update windows contents and size (queue).
	stdscr.clear()
	update_win_main(stdscr, windows["win_main"])
	update_win_tab_switcher(stdscr, windows["win_tab_switcher"])
	update_win_text_main(stdscr, windows["win_text_main"])
	
	update_button_tab_main_text(stdscr, buttons["button_tab_main_text"])
	
	# Update all at once.
	curses.panel.update_panels()
	curses.doupdate()

########################################

# UI FUNCTIONS
def move_cursor(win_text, x, y, init_x, init_y, max_x, max_y):
	# Contain cursor.
	if y > max_y:
		if x < max_x:
			y = init_y
			x += 1
		else:
			y = max_y
	if y < init_y:
		if x > init_x:
			y = max_y
			x -= 1
		else:
			y = init_y
	if x >= max_x:
		x = max_x
	if x < init_x:
		x = init_x
	# Move cursor.
	try:
		win_text.move(y,x)
	except:
		pass
	#win_text.chgat(x, y, 1, curses.A_BLINK | curses.A_UNDERLINE)
	#win_text.refresh()
	return x, y

def is_mouse_click_in_button(mouse_x, mouse_y, btn_start_x, btn_start_y, btn_end_x, btn_end_y, btn_visible):
	return btn_visible and (btn_start_y <= mouse_y < btn_start_y + btn_end_y) and (btn_start_x <= mouse_x < btn_start_x + btn_end_x)

def handle_buttons(x, y, stdscr):
	# Tab switcher text button.
	if is_mouse_click_in_button(x, y, 
		buttons["button_tab_main_text"].getbegyx()[1] - 0, 
		buttons["button_tab_main_text"].getbegyx()[0] - 0, 
		buttons["button_tab_main_text"].getmaxyx()[1] + 0,  
		buttons["button_tab_main_text"].getmaxyx()[0] + 0, 
		not panels["panel_button_tab_main_text"].hidden()):
		
		if panels["panel_text_main"].hidden():
			panels["panel_text_main"].show()
			# Modify tab switcher button visibility when raised.
			panels["panel_button_tab_main_text"].show()
			update_all(stdscr)
			write_text(stdscr, windows["win_text_main"])
			panels["panel_text_main"].hide()
			return "start_text_edit"
		else:
			panels["panel_text_main"].hide()
			curses.curs_set(False)
			curses.panel.update_panels()
			windows["win_text_main"].refresh()
			return "stop_text_edit"
					

def render_buffer(win_text, init_x, init_y, max_x, max_y, x, y):
	# Fit buffer onto the window within limitations.
	for index, c in enumerate(buffer):
		ix = index % max_x + init_y
		iy = index // max_x + init_x
		if ix < max_x+1 and iy < max_y+1:
			# If the window is smaller - prevent crashing.
			try: win_text.addstr(iy, ix, c)
			except: pass
			# Reset cursor back to initial position.
			x, y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
	
def write_text(stdscr, win_text):
	# Start cursor.
	stdscr.timeout(-1)
	curses.curs_set(True)
	max_x = width_text_main
	max_y = height_text_main
	max_x -= 2
	max_y -= 2
	init_x = 1
	init_y = 1
	x = init_x
	y = init_y
	win_text.move(init_x, init_y)
	
	# Render text initially (from loaded byffer page).
	render_buffer(win_text, init_x, init_y, max_x, max_y, x, y)
	
	# Refresh window after input.
	curses.panel.update_panels() # Must be called here.
	win_text.refresh()
	
	# Start editing text..
	while True:
		
		key = stdscr.get_wch()
		
		# Handle navigation with screen button clicks.
		if key == curses.KEY_MOUSE:
			_, mx, my, _, bstate = curses.getmouse()

			# Left mouse click on text field, when cursor is shown.
			if bstate & curses.BUTTON1_CLICKED:
				lx = mx - offset_vert_text_main + 1
				ly = my - offset_horiz_text_main - 1
				x, y = move_cursor(win_text, lx, ly, init_x, init_y, max_x, max_y)
				
				# Button handling while text typing.
				gx = mx
				gy = my
				result = handle_buttons(gx, gy, stdscr)
				
				if result == "stop_text_edit":
					break 
		
		if key == curses.KEY_RIGHT:
			x += 1
			x,y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
		elif key == curses.KEY_LEFT:
			x -= 1
			x,y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
		elif key == curses.KEY_UP:
			y -= 1
			x,y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
		elif key == curses.KEY_DOWN:
			y += 1
			x,y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
			
		elif key in (curses.KEY_ENTER, chr(10), chr(13)):
			x += 1
			y = init_y
			x,y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
			
			
		elif key in (curses.KEY_BACKSPACE, chr(127)):
			index = max_y * (x-1) + (y-1)
			if (index - 1 >= 0) and (index - 1 <= len(buffer)):
				buffer.pop(index - 1)
			# Update cursor position manually.
			y -= 1
			x, y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
			# Clear the characters in the window after the buffer to prevent trailing.
			index_last = len(buffer)
			ix = index_last // max_y + init_x
			iy = index_last % max_y + init_y
			# Fill up with space. Restore border in right side.
			try: win_text.addstr(ix, iy, ' '); win_text.border()
			except: pass

		# Character insertion within limit.
		else:
			# Consume a space in the very end of buffer if it exists
			# to prevent clogging.
			if buffer[-1] == ' ':
				buffer.pop(-1)
				
			if (type(key) is str) and (len(buffer) <= buffer_limit):
				index = max_y * (x-1) + (y-1)
				# Insert character within existing text.
				if index <= len(buffer):
					buffer.insert(index, key)
				# Otherwise add spaces after the last character first.
				# This is needed to fill up space in buffer list.
				else:
					d = index - len(buffer)
					for i in range(d):
						buffer.append(' ')
					buffer.insert(index, key)
				# Update cursor position manually.
				y += 1
				x, y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
			# TODO: add notif. when buffer limit reached.
		
		# Render text within the loop as it is edited.
		render_buffer(win_text, init_x, init_y, max_x, max_y, x, y)
		
		# Refresh window after input.
		curses.panel.update_panels() # Must be called here.
		win_text.refresh()

########################################

# MAIN FUNCTIONS
def main(stdscr):
	# Init the screen and curses.
	stdscr.clear()
	curses.mousemask(curses.ALL_MOUSE_EVENTS)
	curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
	curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
	curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
	curses.curs_set(False)
	
	# Windows and panels.
	win_main = curses.newwin(height_main, width_main, 0, 0)
	win_text_main = curses.newwin(
		height_text_main, width_text_main, 
		offset_vert_text_main, offset_horiz_text_main)
		
	win_tab_switcher = curses.newwin(
		height_tab_switcher, width_tab_switcher, 
		offset_vert_tab_switcher, offset_horiz_tab_switcher)
	
	# Buttons.
	# Increment each horiz. offset by button width + offset.
	button_tab_main_text = win_tab_switcher.derwin(
		height_button_tab_switcher, width_button_tab_switcher, 
		offset_vert_button_tab_switcher, offset_horiz_button_tab_switcher)
	
	# Winfows and tabs.
	panel_main = curses.panel.new_panel(win_main)
	panel_text_main = curses.panel.new_panel(win_text_main)
	panel_tab_switcher = curses.panel.new_panel(win_tab_switcher)
	# Buttons.
	panel_button_tab_main_text = curses.panel.new_panel(button_tab_main_text)
	
	# Store references to windows, panels, buttons in dicts.
	# Windows and tabs.
	windows["win_main"] = win_main
	windows["win_text_main"] = win_text_main
	windows["win_tab_switcher"] = win_tab_switcher
	# Button sub-windows.
	buttons["button_tab_main_text"] = button_tab_main_text
	
	# Panels windows.
	panels["panel_main"] = panel_main
	panels["panel_text_main"] = panel_text_main
	panels["panel_tab_switcher"] = panel_tab_switcher
	# Panels buttons.
	panels["panel_button_tab_main_text"] = panel_button_tab_main_text
	
	# Init all once.
	# Windows.
	panels["panel_main"].show()
	panels["panel_tab_switcher"].show()
	panels["panel_text_main"].hide()
	# Buttons.
	panels["panel_button_tab_main_text"].show()
	
	# Update all windows and buttons.
	update_all(stdscr)
	
	while True:
		
		# Read user input. Input is made non-blocking for future
		# animation implementations.
		stdscr.timeout(anim_delay)
		key = stdscr.getch()
		
		# Process input.
		# Mouse clicks.
		if key == curses.KEY_MOUSE:
			_, mx, my, _, bstate = curses.getmouse()
		
			# Button handling.
			result = handle_buttons(mx, my, stdscr)
					
		# Quit.
		if key == ord('q'):
			quit()
		
		
		# Update after input.
		update_all(stdscr)

########################################

# Start
curses.wrapper(main)
