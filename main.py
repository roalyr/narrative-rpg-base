import curses
import curses.panel
import shutil

anim_delay = 500

height_main = 24
width_main = 40

height_text_main = 20
width_text_main = 36

# Text page character limit as defined by window size to avoid scrolling.
buffer_limit = (height_text_main - 2) * (width_text_main - 2) - 1

# Strings loading.
strings = {
	"test_string" : "Simple Тест",
}

windows = {}
panels = {}
buffer = []

# TEST
test_text_ = "There are many variations of passages of Lorem Ipsum available, but the majority have suffered alteration in some form, by injected humour, or randomised words which don't look even slightly believable. If you are going to use a passage of Lorem Ipsum, you need to be sure there isn't anything embarrassing hidden in the middle of text. All the Lorem Ipsum generators on the Internet tend to repeat predefined chunks as necessary, making this the first true generator on the Internet."
test_text = "There are many variations of passages of Lorem Ipsum available"

# Split current page string into characters.
for c in test_text_:
	buffer.append(c)

# Main window serves as a background, doesn't hold
# any text aside, maybe, from header and footer.
def update_win_main(stdscr, win_main):
	win_main.resize(height_main, width_main)
	win_main.clear()
	win_main.attron(curses.color_pair(1))
	win_main.border()
	win_main.addstr(0, width_main // 2 - len(strings["test_string"]) // 2, strings["test_string"])
	# String insertion placeholder.
	win_main.noutrefresh()
	
def update_win_text_main(stdscr, win_text_main):
	win_text_main.resize(height_text_main, width_text_main)
	win_text_main.clear()
	win_text_main.attron(curses.color_pair(2))
	win_text_main.border()
	# String insertion placeholder.
	win_text_main.noutrefresh()

def update_all(stdscr):
	# Update windows contents and size (queue).
	stdscr.clear()
	update_win_main(stdscr, windows["win_main"])
	update_win_text_main(stdscr, windows["win_text_main"])
	
	# Update all at once.
	curses.panel.update_panels()
	curses.doupdate()
	
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
	win_text.move(x,y)
	#win_text.chgat(x, y, 1, curses.A_BLINK | curses.A_UNDERLINE)
	#win_text.refresh()
	return x, y
	
def render_buffer(win_text, init_x, init_y, max_x, max_y, x, y):
	# Fit buffer onto the window within limitations.
	for index, c in enumerate(buffer):
		ix = index // max_y + init_x
		iy = index % max_y + init_y
		if ix < max_x+1 and iy < max_y+1:
			# If the window is smaller - prevent crashing.
			try: win_text.addstr(ix, iy, c)
			except: pass
			# Reset cursor back to initial position.
			x, y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
	
def write_text(stdscr, win_text):
	# Start cursor.
	stdscr.timeout(-1)
	curses.curs_set(True)
	curses.mousemask(curses.ALL_MOUSE_EVENTS)
	max_x = height_text_main
	max_y = width_text_main
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
			_, my, mx, _, bstate = curses.getmouse()
			mx -= init_x + 1
			my -= init_y + 1

			# Left mouse click on text field, when cursor is shown.
			if bstate & curses.BUTTON1_CLICKED:
				x,y = move_cursor(win_text, mx, my, init_x, init_y, max_x, max_y)
				
		
		if key == curses.KEY_RIGHT:
			y += 1
			x,y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
		elif key == curses.KEY_LEFT:
			y -= 1
			x,y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
		elif key == curses.KEY_UP:
			x -= 1
			x,y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
		elif key == curses.KEY_DOWN:
			x += 1
			x,y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
			
		elif key in (curses.KEY_ENTER, chr(10), chr(13)):
			x += 1
			y = init_y
			x,y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
			
		elif key == "q": # TODO
			# Refresh window after input.
			curses.curs_set(False)
			curses.panel.update_panels()
			win_text.refresh()
			break
			
		elif key in (curses.KEY_BACKSPACE, chr(127)):
			index = max_y * (x-1) + (y-1)
			if (index - 1 > 0) and (index - 1 < len(buffer)):
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

def main(stdscr):
	# Init the screen and curses.
	stdscr.clear()
	curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
	curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
	curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
	curses.curs_set(False)
	
	# Create the windows and panels.
	win_main = curses.newwin(height_main, width_main, 0, 0)
	win_text_main = curses.newwin(height_main - 4, width_main - 4, 2, 2)
	panel_main = curses.panel.new_panel(win_main)
	panel_text_main = curses.panel.new_panel(win_text_main)
	
	# Store references to windows, panels, boxes in dicts.
	windows["win_main"] = win_main
	windows["win_text_main"] = win_text_main
	
	panels["panel_main"] = panel_main
	panels["panel_text_main"] = panel_text_main
	
	# Init all once.
	panels["panel_main"].show()
	panels["panel_text_main"].hide()
	update_all(stdscr)
	
	
	while True:
		
		# Read user input. Input is made non-blocking for future
		# animation implementations.
		stdscr.timeout(anim_delay)
		key = stdscr.getch()
		
		# Process input.
		# Quit.
		if key == ord('q'):
			quit()
		# Start writing text.
		elif key == ord('t'):
			panels["panel_text_main"].show()
			update_all(stdscr)
			write_text(stdscr, windows["win_text_main"])
			panels["panel_text_main"].hide()
			
		# Update after input.
		update_all(stdscr)

# Start the curses application
curses.wrapper(main)
