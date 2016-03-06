import pygame
import os
from pygame.locals import *

displaySize = 'small'

class Display:
    screen = None

    def __init__(self):
        """Initialize a new pygame screen using the frame buffer"""

        # Test if we are running X display
        display_no = os.getenv('DISPLAY')
        if display_no:
            print("X Display = {0}".format(display_no))

        # Check which frame buffer drivers are available Start with fbcon since
        # directfb hangs with composite output
        drivers = ['fbcon', 'directfb', 'svgalib']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                print('Driver: {0} failed.'.format(driver))
                continue
            found = True
            break

        if not found:
            raise Exception('No suitable video driver found!')

        # Determine display resolution.
        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        print "Frame Buffer Size: %d x %d" % (size[0], size[1])
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)

        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.mouse.set_visible(0)
        pygame.display.update()

        if displaySize == 'large':
            # Larger Display
            self.xmax = 800 - 35
            self.ymax = 480 - 5
            self.scaleIcon = True  # Weather icons need scaling.
            self.iconScale = 1.5  # Icon scale amount.
            self.subwinTh = 0.05  # Sub window text height
            self.tmdateTh = 0.100  # Time & Date Text Height
            self.tmdateSmTh = 0.06
            self.tmdateYPos = 10  # Time & Date Y Position
            self.tmdateYPosSm = 18  # Time & Date Y Position Small
        else:
            # Small Display
            self.xmax = 320 - 35
            self.ymax = 240 - 5
            self.scaleIcon = False		# No icon scaling needed.
            self.iconScale = 1.0
            self.subwinTh = 0.065		# Sub window text height
            self.tmdateTh = 0.125		# Time & Date Text Height
            self.tmdateSmTh = 0.075
            self.tmdateYPos = 1		# Time & Date Y Position
            self.tmdateYPosSm = 8		# Time & Date Y Position Small

    def __del__(self):
        """Destructor to make sure pygame shuts down, etc."""

pygame.init()

black = (0, 0, 0)
red = (255, 0, 0)
white = (255, 255, 255)

lcd = pygame.display.set_mode((320, 240))

myFont = pygame.font.SysFont("Times New Roman", 18)

insideTemp = myFont.render
