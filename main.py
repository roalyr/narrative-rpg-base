import curses
import curses.panel
import shutil



# Main window serves as a background, doesn't hold
# any text aside, maybe, from header and footer.
def update_win_main(stdscr, term_size, win_main, strings):
	height = term_size[1]
	width = term_size[0]
	win_main.resize(height, width)
	win_main.clear()
	win_main.attron(curses.color_pair(1))
	win_main.border()
	win_main.addstr(0, width // 2 - len(strings["test_string"]) // 2, strings["test_string"])
	# String insertion placeholder.
	win_main.noutrefresh()
	
def update_win_text_main(stdscr, term_size, win_text_main, strings):
	height = term_size[1] - 4
	width = term_size[0] - 4
	win_text_main.resize(height, width)
	win_text_main.clear()
	win_text_main.attron(curses.color_pair(2))
	win_text_main.border()
	win_text_main.addstr(0, width // 2 - len(strings["test_string"]) // 2, strings["test_string"])
	# String insertion placeholder.
	win_text_main.noutrefresh()

def update_all(stdscr, term_size, windows, panels, strings):
	# Update windows contents and size (queue).
	stdscr.clear()
	update_win_main(stdscr, term_size, windows["win_main"], strings)
	update_win_text_main(stdscr, term_size, windows["win_text_main"], strings)
	
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
	return x, y
	
def write_text(stdscr, win_text):
	
	test_text = "There are many variations of passages of Lorem Ipsum available, but the majority have suffered alteration in some form, by injected humour, or randomised words which don't look even slightly believable. If you are going to use a passage of Lorem Ipsum, you need to be sure there isn't anything embarrassing hidden in the middle of text. All the Lorem Ipsum generators on the Internet tend to repeat predefined chunks as necessary, making this the first true generator on the Internet. It uses a dictionary of over 200 Latin words, combined with a handful of model sentence structures, to generate Lorem Ipsum which looks reasonable. The generated Lorem Ipsum is therefore always free from repetition, injected humour, or non-characteristic words etc."
	test_text_ = "There are many variations of passages of Lorem Ipsum available"
	
	buffer = []
	
	# Split string into characters.
	for c in test_text:
		buffer.append(c)
	
	
	
	# Start cursor.
	stdscr.timeout(-1)
	curses.curs_set(True)
	max_x, max_y = win_text.getmaxyx() # Make const?
	max_x -= 2
	max_y -= 2
	init_x = 1
	init_y = 1
	x = init_x
	y = init_y
	win_text.move(init_x, init_y)
	win_text.refresh()
	
	# Fit buffer onto the window within limitations.
	for index, c in enumerate(buffer):
		ix = index // max_y + init_x
		iy = index % max_y + init_y
		if ix < max_x+1 and iy < max_y+1:
			win_text.addstr(ix, iy, c)

	# Start editing here.
	while True:
		key = stdscr.get_wch()
		if key == curses.KEY_RIGHT:
			y += 1
			move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
		elif key == curses.KEY_LEFT:
			y -= 1
			move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
		elif key == curses.KEY_UP:
			x -= 1
			move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
		elif key == curses.KEY_DOWN:
			x += 1
			move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
		else:
			if type(key) is str:
				# Update cursor position manually.
				y += 1
				x, y = move_cursor(win_text, x, y, init_x, init_y, max_x, max_y)
				win_text.addstr(x, y, key)
			
		# Refresh window after input.
		win_text.refresh()
		
		

	curses.curs_set(False)
	
	# Clean the text.
	# text = text.strip()

def main(stdscr):
	# Constants.
	anim_delay = 500
	
	# Init the screen and curses.
	stdscr.clear()
	curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
	curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
	curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
	curses.curs_set(False)
	height, width = stdscr.getmaxyx()
	
	# Strings loading.
	strings = {
		"test_string" : "Simple Тест",
	}
	
	# Create the windows and panels.
	win_main = curses.newwin(height, width, 0, 0)
	win_text_main = curses.newwin(height - 4, width - 4, 2, 2)
	panel_main = curses.panel.new_panel(win_main)
	panel_text_main = curses.panel.new_panel(win_text_main)
	
	# Store references to windows, panels, boxes in dicts.
	windows = {
		"win_main" : win_main,
		"win_text_main" : win_text_main,
	}
	
	panels = {
		"panel_main" : panel_main,
		"panel_text_main" : panel_text_main,
	}
	
	
	# Clear the screen and print the text
	#win_main.addstr(1, 1, text)
	#win_main.refresh()
	
	# Init all onve.
	term_size_prev = shutil.get_terminal_size()
	panels["panel_main"].show()
	update_all(stdscr, term_size_prev, windows, panels, strings)
	
	
	while True:
		#If resize terminal - do update all windows.
		term_size = shutil.get_terminal_size()
		if term_size != term_size_prev:
			update_all(stdscr, term_size, windows, panels, strings)
			term_size_prev = term_size
		
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
			update_all(stdscr, term_size, windows, panels, strings)
			write_text(stdscr, windows["win_text_main"])
			panels["panel_text_main"].hide()
			
		# Update after input.
		update_all(stdscr, term_size, windows, panels, strings)
		
		
		

# Start the curses application
curses.wrapper(main)
