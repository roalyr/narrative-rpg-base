import curses
import curses.panel
import shutil

import oracles

########################################

# CONSTANTS
anim_delay = -1

########################################

# WINDOW LAYOUT
# Main window.
height_main = 25
width_main = 95

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
height_tabbed_window = height_main - 4
width_tabbed_window = width_button_tab_switcher * 5
offset_vert_tabbed_window = 3
offset_horiz_tabbed_window = 2

# Auxilary window (right).
height_aux = height_tabbed_window + 2
width_aux = width_main - width_tabbed_window - 5
offset_vert_aux = 1
offset_horiz_aux = width_tabbed_window + 3


# Text page character limit as defined by window size to avoid scrolling.
buffer_limit = (height_tabbed_window - 2) * (width_tabbed_window - 2) - 1

########################################

# CONTENT LOADING
strings = {
	"main_title" : " Narrative game framework ",
	"button_text_main" : "Logs",
	"button_char" : "Char",
	"button_assets" : "Asst",
	"button_oracle" : "Orcl",
	"button_info" : "Info",
}

########################################

# DATA STRYCTURES AND VARS
windows = {}
buttons = {}
panels = {}
panels_buttons = {}
buffer = []

########################################

# TESTING
test_text = "There are many variations of passages of Lorem Ipsum available, but the majority have suffered alteration in some form, by injected humour, or randomised words which don't look even slightly believable. If you are going to use a passage of Lorem Ipsum, you need to be sure there isn't anything embarrassing hidden in the middle of text. All the Lorem Ipsum generators on the Internet tend to repeat predefined chunks as necessary, making this the first true generator on the Internet."
test_text_ = "There are many variations of passages of Lorem Ipsum available"

# Split current page string into characters.
for c in test_text_:
	buffer.append(c)

########################################

# BASIC FUNCTIONS.
def update_win(stdscr, win, h, w, col, title):
	win.resize(h, w)
	win.clear()
	win.attron(curses.color_pair(col))
	win.border()
	if title:
		win.addstr(0, w // 2 - len(title) // 2, title)
	win.noutrefresh()
	
def update_button_tab(stdscr, button, tab, h, w, col, col2, title, lr_corner, ll_corner):
	button.resize(h, w)
	button.clear()
	# Active
	if not tab.hidden():
		button.attron(curses.color_pair(col2))
		button.addstr(1, w // 2 - len(title) // 2, title + ':')
		button.border(0, 0, 0, ' ', 0, 0, lr_corner, ll_corner)
		button.attroff(curses.color_pair(col2))
	# Inactive
	else:
		button.attron(curses.color_pair(col))
		button.addstr(1, w // 2 - len(title) // 2, title)
		button.border()
		button.attroff(curses.color_pair(col))
	button.noutrefresh()

def handle_tab_buttons(x, y, stdscr, b, pb, p, result_start, result_stop, custom_function, *args):
	if is_mouse_click_in_button(x, y, 
		b.getbegyx()[1] - 0, 
		b.getbegyx()[0] - 0, 
		b.getmaxyx()[1] + 0,  
		b.getmaxyx()[0] + 0, 
		not pb.hidden()
	):					
		# When tab is inactive - activate it.
		if p.hidden():
			close_all_tabs(stdscr)
			# Modify tab switcher button visibility when tab raised.
			p.show()
			pb.show()
			update_all(stdscr)
			# Run a function with its own loop.
			custom_function(*args)
			# Finish when returning.
			close_all_tabs(stdscr)
			# Return result
			return result_start
		# When tab is active - close it.
		else:
			# close_all_tabs(stdscr)
			# Return result
			return result_stop
	# If no button pressed - return no result.
	return ''

def move_cursor(win_text, x, y, init_x, init_y, max_x, max_y):
	# Contain cursor.
	if x > max_x:
		if y < max_y:
			x = init_x
			y += 1
		else:
			x = max_x
	if x < init_x:
		if y > init_y:
			x = max_x
			y -= 1
		else:
			x = init_x
	if y >= max_y:
		y = max_y
	if y < init_y:
		y = init_y
	# Move cursor.
	try:
		win_text.move(y,x)
	except:
		pass
	return x, y

def is_mouse_click_in_button(mouse_x, mouse_y, btn_start_x, btn_start_y, btn_end_x, btn_end_y, btn_visible):
	return btn_visible and (btn_start_y <= mouse_y < btn_start_y + btn_end_y) and (btn_start_x <= mouse_x < btn_start_x + btn_end_x)

def render_buffer(text, win_text, init_x, init_y, max_x, max_y, x, y):
	# Fit buffer onto the window within limitations.
	for index, c in enumerate(text):
		ix = index % max_x + init_y
		iy = index // max_x + init_x
		if ix < max_x+1 and iy < max_y+1:
			# If the window is smaller - prevent crashing.
			try: win_text.addstr(iy, ix, c)
			except: pass
			# Reset cursor back to initial position.
			x, y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)

########################################

# TAB. INFO.
def display_info(stdscr,):
	stdscr.timeout(anim_delay)
	while True:
		try: key = stdscr.get_wch()
		except: key = -1
		
		# Handle navigation with screen button clicks.
		if key == curses.KEY_MOUSE:
			_, mx, my, _, bstate = curses.getmouse()

			# Left mouse click on text field, when cursor is shown.
			if bstate & curses.BUTTON1_CLICKED:
			
				# Button handling while text typing.
				result = handle_buttons(mx, my, stdscr)
				
				# Stop editor when closing the tab or switching to other tab.
				if result in ("start_text_edit", "start_char", "start_assets", "start_oracle", "stop_info"):
					break 
					
		curses.panel.update_panels() # Must be called here.
		windows["win_info"].refresh()
					

# TAB. ORACLE.
def display_oracle(stdscr,):
	
	# Start cursor.
	stdscr.timeout(anim_delay)
	curses.curs_set(False)
	max_x = width_tabbed_window
	max_y = height_tabbed_window
	max_x -= 2
	max_y -= 2
	init_x = 1
	init_y = 1
	x = init_x
	y = init_y
	windows["win_oracle"].move(init_x, init_y)
	
	rb = oracles.actions[1]
	
	# Render text initially (from loaded byffer page).
	render_buffer(rb, windows["win_oracle"], init_x, init_y, max_x, max_y, x, y)
	
	# Refresh window after input.
	curses.panel.update_panels() # Must be called here.
	windows["win_oracle"].refresh()
	
	while True:
		try: key = stdscr.get_wch()
		except: key = -1
		
		# Handle navigation with screen button clicks.
		if key == curses.KEY_MOUSE:
			_, mx, my, _, bstate = curses.getmouse()

			# Left mouse click on text field, when cursor is shown.
			if bstate & curses.BUTTON1_CLICKED:
			
				# Button handling while text typing.
				result = handle_buttons(mx, my, stdscr)
				
				# Stop editor when closing the tab or switching to other tab.
				if result in ("start_text_edit", "start_char", "start_assets", "stop_oracle", "start_info"):
					break
		
		elif key == 'q':
			break
					
		# Render text within the loop as it is edited.
		render_buffer(rb, windows["win_oracle"], init_x, init_y, max_x, max_y, x, y)
		
		# Refresh window after input.
		curses.panel.update_panels() # Must be called here.
		windows["win_oracle"].refresh()
					

# TAB. ASSETS.
def display_assets(stdscr,):
	stdscr.timeout(anim_delay)
	while True:
		try: key = stdscr.get_wch()
		except: key = -1
		
		# Handle navigation with screen button clicks.
		if key == curses.KEY_MOUSE:
			_, mx, my, _, bstate = curses.getmouse()

			# Left mouse click on text field, when cursor is shown.
			if bstate & curses.BUTTON1_CLICKED:
			
				# Button handling while text typing.
				result = handle_buttons(mx, my, stdscr)
				
				# Stop editor when closing the tab or switching to other tab.
				if result in ("start_text_edit", "start_char", "stop_assets", "start_oracle", "start_info"):
					break 
					
		curses.panel.update_panels() # Must be called here.
		windows["win_assets"].refresh()
					

# TAB. CHAR.
def display_char(stdscr,):
	stdscr.timeout(anim_delay)
	while True:
		try: key = stdscr.get_wch()
		except: key = -1
		
		# Handle navigation with screen button clicks.
		if key == curses.KEY_MOUSE:
			_, mx, my, _, bstate = curses.getmouse()

			# Left mouse click on text field, when cursor is shown.
			if bstate & curses.BUTTON1_CLICKED:
			
				# Button handling while text typing.
				result = handle_buttons(mx, my, stdscr)
				
				# Stop editor when closing the tab or switching to other tab.
				if result in ("start_text_edit", "stop_char", "start_assets", "start_oracle", "start_info"):
					break
	
		curses.panel.update_panels() # Must be called here.
		windows["win_char"].refresh()
					

# TAB. TEXT PROCESSING.
def write_text(stdscr):
	# Start cursor.
	stdscr.timeout(anim_delay)
	curses.curs_set(True)
	max_x = width_tabbed_window
	max_y = height_tabbed_window
	max_x -= 2
	max_y -= 2
	init_x = 1
	init_y = 1
	x = init_x
	y = init_y
	windows["win_text_main"].move(init_x, init_y)
	
	# Render text initially (from loaded byffer page).
	render_buffer(buffer, windows["win_text_main"], init_x, init_y, max_x, max_y, x, y)
	
	# Refresh window after input.
	curses.panel.update_panels() # Must be called here.
	windows["win_text_main"].refresh()
	
	# Start editing text..
	while True:
		
		try: key = stdscr.get_wch()
		except: key = -1
		
		# Handle navigation with screen button clicks.
		if key == curses.KEY_MOUSE:
			_, mx, my, _, bstate = curses.getmouse()

			# Left mouse click on text field, when cursor is shown.
			if bstate & curses.BUTTON1_CLICKED:
				lx = mx - offset_vert_tabbed_window + 1
				ly = my - offset_horiz_tabbed_window - 1
				x, y = move_cursor(windows["win_text_main"], lx, ly, init_x, init_y, max_x, max_y)
				
				# Button handling while text typing.
				result = handle_buttons(mx, my, stdscr)
				
				# Stop editor when closing the tab or switching to other tab.
				if result in ("stop_text_edit", "start_char", "start_assets", "start_oracle", "start_info"):
					break 
		####################
		
		if key == curses.KEY_RIGHT:
			x += 1
			x,y = move_cursor(windows["win_text_main"], x, y, init_x, init_y, max_x, max_y)
		elif key == curses.KEY_LEFT:
			x -= 1
			x,y = move_cursor(windows["win_text_main"], x, y, init_x, init_y, max_x, max_y)
		elif key == curses.KEY_UP:
			y -= 1
			x,y = move_cursor(windows["win_text_main"], x, y, init_x, init_y, max_x, max_y)
		elif key == curses.KEY_DOWN:
			y += 1
			x,y = move_cursor(windows["win_text_main"], x, y, init_x, init_y, max_x, max_y)
		####################
		
		elif key in (curses.KEY_ENTER, chr(10), chr(13)):
			y += 1
			x = init_x
			x,y = move_cursor(windows["win_text_main"], x, y, init_x, init_y, max_x, max_y)
		####################
			
		elif key in (curses.KEY_BACKSPACE, chr(127)):
			index = max_x * (y-1) + (x-1)
			if (index - 1 >= 0) and (index - 1 <= len(buffer)):
				try: buffer.pop(index - 1)
				except: pass
			# Update cursor position manually.
			x -= 1
			x, y = move_cursor(windows["win_text_main"], x, y, init_x, init_y, max_x, max_y)
			# Clear the characters in the window after the buffer to prevent trailing.
			index_last = len(buffer)
			
			ix = index_last % max_x + init_y
			iy = index_last // max_x+ init_x
			# Fill up with space. Restore border in right side.
			try: windows["win_text_main"].addstr(iy, ix, ' '); windows["win_text_main"].border()
			except: pass
		####################
		
		# Character insertion within limit.
		else:
			# Consume a space in the very end of buffer if it exists
			# to prevent clogging.
			if (len(buffer) > 0):
				if (buffer[-1] == ' '):
					buffer.pop(-1)
				
			if (type(key) is str) and (len(buffer) <= buffer_limit):
				index = max_x * (y-1) + (x-1)
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
				x += 1
				x, y = move_cursor(windows["win_text_main"], x, y, init_x, init_y, max_x, max_y)
			# TODO: add notif. when buffer limit reached.
		####################
		
		# Render text within the loop as it is edited.
		render_buffer(buffer, windows["win_text_main"], init_x, init_y, max_x, max_y, x, y)
		
		# Refresh window after input.
		curses.panel.update_panels() # Must be called here.
		windows["win_text_main"].refresh()

########################################

# DEFINITIONS: BUTTONS
def handle_buttons(x, y, stdscr):
	
	# Tab switcher text button.
	result = handle_tab_buttons(x, y, stdscr, 
		buttons["button_tab_main_text"],
		panels_buttons["panel_button_tab_main_text"],
		panels["panel_text_main"],
		"start_text_edit", "stop_text_edit",
		# Custom function.
		write_text, stdscr
	)
	if result: return result
	####################
	
	# Tab switcher char button.
	result = handle_tab_buttons(x, y, stdscr, 
		buttons["button_tab_char"],
		panels_buttons["panel_button_tab_char"],
		panels["panel_char"],
		"start_char", "stop_char",
		# Custom function.
		display_char, stdscr
	)
	if result: return result
	####################
	
	# Tab switcher assets button.
	result = handle_tab_buttons(x, y, stdscr, 
		buttons["button_tab_assets"],
		panels_buttons["panel_button_tab_assets"],
		panels["panel_assets"],
		"start_assets", "stop_assets",
		# Custom function.
		display_assets, stdscr
	)
	if result: return result
	####################
	
	# Tab switcher oracle button.
	result = handle_tab_buttons(x, y, stdscr, 
		buttons["button_tab_oracle"],
		panels_buttons["panel_button_tab_oracle"],
		panels["panel_oracle"],
		"start_oracle", "stop_oracle",
		# Custom function.
		display_oracle, stdscr
	)
	if result: return result
	####################
	
	# Tab switcher info button.
	result = handle_tab_buttons(x, y, stdscr, 
		buttons["button_tab_info"],
		panels_buttons["panel_button_tab_info"],
		panels["panel_info"],
		"start_info", "stop_info",
		# Custom function.
		display_info, stdscr
	)
	if result: return result
	####################
	
	# If no button pressed - return no result.
	return ''


# DEFINITIONS: UPDATES
def update_all(stdscr):
	# Update windows contents and size (queue).
	stdscr.clear()
	
	# Windows - add here.
	update_win(stdscr, windows["win_main"], height_main, width_main, 1, '')
	update_win(stdscr, windows["win_aux"], height_aux, width_aux, 3, strings["main_title"])
	update_win(stdscr, windows["win_tab_switcher"], height_tab_switcher, width_tab_switcher, 1, '')
	update_win(stdscr, windows["win_text_main"], height_tabbed_window, width_tabbed_window, 2, '')
	update_win(stdscr, windows["win_char"], height_tabbed_window, width_tabbed_window, 2, '')
	update_win(stdscr, windows["win_assets"], height_tabbed_window, width_tabbed_window, 2, '')
	update_win(stdscr, windows["win_oracle"], height_tabbed_window, width_tabbed_window, 2, '')
	update_win(stdscr, windows["win_info"], height_tabbed_window, width_tabbed_window, 2, '')
	####################
	
	# Buttons - add here.
	update_button_tab(stdscr, buttons["button_tab_main_text"], 
		panels["panel_text_main"], height_button_tab_switcher, 
		width_button_tab_switcher, 1, 2, strings["button_text_main"],
		curses.ACS_VLINE, curses.ACS_LLCORNER
	)
	update_button_tab(stdscr, buttons["button_tab_char"], 
		panels["panel_char"], height_button_tab_switcher, 
		width_button_tab_switcher, 1, 2, strings["button_char"],
		curses.ACS_LRCORNER, curses.ACS_LLCORNER
	)
	update_button_tab(stdscr, buttons["button_tab_assets"], 
		panels["panel_assets"], height_button_tab_switcher, 
		width_button_tab_switcher, 1, 2, strings["button_assets"],
		curses.ACS_LRCORNER, curses.ACS_LLCORNER
	)
	update_button_tab(stdscr, buttons["button_tab_oracle"], 
		panels["panel_oracle"], height_button_tab_switcher, 
		width_button_tab_switcher, 1, 2, strings["button_oracle"],
		curses.ACS_LRCORNER, curses.ACS_LLCORNER
	)
	update_button_tab(stdscr, buttons["button_tab_info"], 
		panels["panel_info"], height_button_tab_switcher, 
		width_button_tab_switcher, 1, 2, strings["button_info"],
		curses.ACS_LRCORNER, curses.ACS_VLINE
	)
	####################
	
	curses.panel.update_panels()
	curses.doupdate()


# DEFINITIONS: TAB CLOSING
def close_all_tabs(stdscr):
	
	# Add all tabs here.
	panels["panel_text_main"].hide()
	panels["panel_char"].hide()
	panels["panel_assets"].hide()
	panels["panel_oracle"].hide()
	panels["panel_info"].hide()
	####################
	
	curses.panel.update_panels()
	curses.curs_set(False)
	stdscr.timeout(anim_delay)
	return True


# DEFINITIONS: INIT
def main(stdscr):
	# Init curses.
	stdscr.clear()
	curses.mousemask(curses.ALL_MOUSE_EVENTS)
	curses.curs_set(False)
	####################
	
	# Color pairs.
	curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
	curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
	curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
	####################
	
	# Windows and panels.
	windows["win_main"] = curses.newwin(height_main, width_main, 0, 0)
	
	windows["win_aux"] = curses.newwin(height_aux, width_aux, offset_vert_aux, offset_horiz_aux)
	
	# Invisible. Do not update.
	windows["win_tab_switcher"] = curses.newwin(
		height_tab_switcher, width_tab_switcher, 
		offset_vert_tab_switcher, offset_horiz_tab_switcher)
	
	windows["win_text_main"] = curses.newwin(
		height_tabbed_window, width_tabbed_window, 
		offset_vert_tabbed_window, offset_horiz_tabbed_window)
		
	windows["win_char"] = curses.newwin(
		height_tabbed_window, width_tabbed_window, 
		offset_vert_tabbed_window, offset_horiz_tabbed_window)
		
	windows["win_assets"] = curses.newwin(
		height_tabbed_window, width_tabbed_window, 
		offset_vert_tabbed_window, offset_horiz_tabbed_window)
		
	windows["win_oracle"] = curses.newwin(
		height_tabbed_window, width_tabbed_window, 
		offset_vert_tabbed_window, offset_horiz_tabbed_window)
		
	windows["win_info"] = curses.newwin(
		height_tabbed_window, width_tabbed_window, 
		offset_vert_tabbed_window, offset_horiz_tabbed_window)
	####################
	
	# Buttons. Tabs.
	# Increment each horiz. offset by button width + offset.
	buttons["button_tab_main_text"] = windows["win_tab_switcher"].derwin(
		height_button_tab_switcher, width_button_tab_switcher, 
		offset_vert_button_tab_switcher, offset_horiz_button_tab_switcher)
	
	buttons["button_tab_char"] = windows["win_tab_switcher"].derwin(
		height_button_tab_switcher, width_button_tab_switcher, 
		offset_vert_button_tab_switcher, 
		offset_horiz_button_tab_switcher + width_button_tab_switcher * 1)
		
	buttons["button_tab_assets"] = windows["win_tab_switcher"].derwin(
		height_button_tab_switcher, width_button_tab_switcher, 
		offset_vert_button_tab_switcher, 
		offset_horiz_button_tab_switcher + width_button_tab_switcher * 2)
		
	buttons["button_tab_oracle"] = windows["win_tab_switcher"].derwin(
		height_button_tab_switcher, width_button_tab_switcher, 
		offset_vert_button_tab_switcher, 
		offset_horiz_button_tab_switcher + width_button_tab_switcher * 3)
		
	buttons["button_tab_info"] = windows["win_tab_switcher"].derwin(
		height_button_tab_switcher, width_button_tab_switcher, 
		offset_vert_button_tab_switcher, 
		offset_horiz_button_tab_switcher + width_button_tab_switcher * 4)
	####################
	
	# Winfows and tabs panels.
	panels["panel_main"] = curses.panel.new_panel(windows["win_main"])
	panels["panel_aux"] = curses.panel.new_panel(windows["win_aux"])
	panels["panel_tab_switcher"] = curses.panel.new_panel(windows["win_tab_switcher"])
	panels["panel_text_main"] = curses.panel.new_panel(windows["win_text_main"])
	panels["panel_char"] = curses.panel.new_panel(windows["win_char"])
	panels["panel_assets"] = curses.panel.new_panel(windows["win_assets"])
	panels["panel_oracle"] = curses.panel.new_panel(windows["win_oracle"])
	panels["panel_info"] = curses.panel.new_panel(windows["win_info"])
	####################
	
	# Buttons panels.
	panels_buttons["panel_button_tab_main_text"] = curses.panel.new_panel(buttons["button_tab_main_text"])
	panels_buttons["panel_button_tab_char"] = curses.panel.new_panel(buttons["button_tab_char"])
	panels_buttons["panel_button_tab_assets"] = curses.panel.new_panel(buttons["button_tab_assets"])
	panels_buttons["panel_button_tab_oracle"] = curses.panel.new_panel(buttons["button_tab_oracle"])
	panels_buttons["panel_button_tab_info"] = curses.panel.new_panel(buttons["button_tab_info"])
	####################
	
	# Init Windows panels.
	panels["panel_main"].show()
	panels["panel_aux"].show()
	panels["panel_tab_switcher"].hide() # This window should be hidden.
	panels["panel_text_main"].hide()
	panels["panel_char"].hide()
	panels["panel_assets"].hide()
	panels["panel_oracle"].hide()
	panels["panel_info"].hide()
	####################
	
	# Init Buttons.
	panels_buttons["panel_button_tab_main_text"].show()
	panels_buttons["panel_button_tab_char"].show()
	panels_buttons["panel_button_tab_assets"].show()
	panels_buttons["panel_button_tab_oracle"].show()
	panels_buttons["panel_button_tab_info"].show()
	####################
	
	# Open info at start.
	panels["panel_info"].show()
	panels_buttons["panel_button_tab_info"].show()
	
	# Update all windows and buttons.
	update_all(stdscr)
	
	while True:
		# Read user input. Input is made non-blocking for future
		# animation implementations.
		stdscr.timeout(anim_delay)
		key = stdscr.get_wch()
		
		# Process input.
		# Mouse clicks.
		if key == curses.KEY_MOUSE:
			_, mx, my, _, bstate = curses.getmouse()
		
			# Button handling.
			result = handle_buttons(mx, my, stdscr)
		####################
					
		# Process keys.
		if key == 'q':
			quit()
		####################
		
		# Update after input.
		update_all(stdscr)

########################################

# Start
curses.wrapper(main)
