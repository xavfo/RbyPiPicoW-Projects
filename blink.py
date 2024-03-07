from machine import ADC, Timer
from utime import sleep
from micropython import const
import picoexplorer as pico
import random

# pico tennis - by Stewart Twynham

# first - some gameplay elements...
MAX_SCORE = const(15)
PADDLE_SIZE = const(30)
BALL_SPEED = const(7)

# get our screen dimensions
screen_width = pico.get_width()
screen_height = pico.get_height()

# these will be the constraints of our ball and our players on the screen
ball_xmin = 22
ball_xmax = screen_width - 22
ball_ymin = 72
ball_ymax = screen_height - 22
paddle_range = screen_height - PADDLE_SIZE - 74

# initialise display
# this is 2 bytes per pixel (RGB565)
display_buffer = bytearray(screen_width * screen_height * 2)
pico.init(display_buffer)

# initialise the timer - we use this for the sounds
tim = Timer()

# prepare the sound on GPIO0
pico.set_audio_pin(0)

# these are the scores on the doors
player1 = 0
player2 = 0

# we use classes for the moving features because it keeps the code nice and tidy

# our ball and its movements are defined in a class
class Ball:
    def __init__(self, x=0, y=0, dx=0, dy=0):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy

    # this is where we draw the ball from the x/y position
    def draw(self):
        pico.set_pen(224, 231, 34)
        pico.circle(self.x, self.y, 10)
    
    # this resets the ball to emerge from the net during the game
    def reset(self):
        self.x = int(screen_width / 2)
        self.y = int(screen_height / 2) + 30
        
        # we give some randomisation to the starting direction
        if (random.randint(0,1) == 0):
            self.dx = - BALL_SPEED
        else:
            self.dx = BALL_SPEED
        if (random.randint(0,1) == 0):
            self.dy = - BALL_SPEED
        else:
            self.dy = BALL_SPEED

    # this moves the ball around the screen as the game progresses
    def move(self):
        self.x += self.dx
        self.y += self.dy

    # we hit the top or bottom of the screen so we reverse the Y component
    def bounce(self):
        self.dy *= -1
        self.y += self.dy

    # we hit a paddle - so we reverse the X component
    def hit(self):
        self.dx *= -1
        self.move()

# now we create an instance of the ball and reset it to the start position
ball = Ball()
ball.reset()

# the paddle is our controller for our player
class Paddle:
    
    def __init__(self, channel, xpos, top = 0, bottom = 0):
        
        # we have defaults for two values but not the ADC channel and the X-position on the screen
        self.channel = channel
        self.xpos = xpos
        self.top = top
        self.bottom = bottom

    def draw(self):
        
        # calculate the Y-position - scaled over the range we expect to see
        self.top = int(paddle_range / 32767 * self.readchannel(self.channel)) + 62
        self.bottom = self.top + PADDLE_SIZE
        pico.set_pen(255, 255, 255)
        pico.rectangle(self.xpos, self.top, 4, PADDLE_SIZE)

    # this reads the ADC value for the given channel, set when the paddle is first initialised
    def readchannel(self, channel):
        
        # read the paddle position as an unsigned 16 bit integer
        raw = machine.ADC(channel).read_u16()
        
        # we will only use the middle 50% of the potentiometer's 0-65535 range to make controls a little easier
        if raw > 49151:
            raw = 49151
        if raw < 16384:
            raw = 16384

        # return a range 0-32767
        return(raw - 16384)
    


# now we will initialise two paddles - left and right - defining their ADC channel and X positions
paddle = [Paddle(1, 46), Paddle(2, screen_width - 50)]

# it isn't a game if we don't have sound...
def bleep(frequency):
    pico.set_tone(frequency)
    tim.init (period = 150, mode = Timer.ONE_SHOT, callback = lambda t: pico.set_tone(-1))

# this shows the player scores
def show_scores():

    # show the player scores
    pico.set_pen(255, 255, 255)    
    pico.text("{:.0f}".format(player1), 60, 20, 40, 4)
    pico.text("{:.0f}".format(player2), screen_width - 80, 20, 40, 4)

# this will draw the court for us
def draw_court():
    
    # set a grass background
    pico.set_pen(0, 192, 0)
    pico.clear()
    
    # switch to light grey for the court
    pico.set_pen(224, 224, 224)
    pico.rectangle(10, 60, screen_width - 20, 2)
    pico.rectangle(10, screen_height - 12, screen_width - 20, 2)    
    pico.rectangle(10, 60, 2, screen_height - 70)
    pico.rectangle(screen_width - 12, 60, 2, screen_height - 70)

    # the net is a dashed line in the middle of the screen
    ypos = 80
    while (ypos < screen_height - 20):
        pico.rectangle(int(screen_width/2), ypos, 2, 10)
        ypos += 20

# this shows a text message inside a rectangle for when the game is paused or a player wins...
def show_text(text):
    
    pico.set_pen(64, 128, 64)
    pico.rectangle(30, 80, screen_width - 60, 60)
    pico.set_pen(224, 224, 224)
    pico.text (text, 60, 90, screen_width - 90,3)
    pico.update()


# we will run this forever
while True:

    draw_court()
    paddle[0].draw()
    paddle[1].draw()
    ball.move()


    
    # if the centre of the ball is colliding with either bat then reverse the ball's direction and move the ball back
    if (ball.x >= ball_xmax - 40) and (ball.x <= ball_xmax - 30) and (ball.y > paddle[1].top - 10) and (ball.y < paddle[1].bottom + 10) and (ball.dx > 0):
        ball.hit()
        bleep(880)

    elif (ball.x <= ball_xmin + 40) and (ball.x >= ball_xmin + 30) and (ball.y > paddle[0].top - 10) and (ball.y < paddle[0].bottom + 10) and (ball.dx < 0):
        ball.hit()
        bleep(880)

    # if we hit the top or bottom of the screen - we bounce the ball and bleep
    if ball.y < ball_ymin or ball.y > ball_ymax:
        ball.bounce()
        bleep(440)

    # oh dear, the ball ran off the edge - alter the score and set the ball up for a 'serve'
    elif ball.x > ball_xmax:
        ball.reset()
        player1 += 1
        bleep(220)

    elif ball.x < ball_xmin:
        ball.reset()
        player2 += 1
        bleep(220)
            
    show_scores()

    # check if a player wins
    if (player1 >= MAX_SCORE or player2 >= MAX_SCORE):
        if (player1 >= MAX_SCORE):
            show_text("Player one wins")
        else:
            show_text("Player two wins")
            
        # now wait until the X button is pressed to reset the game    
        while not pico.is_pressed(2):
            sleep(0.01)
        ball.reset()
        player1 = 0
        player2 = 0            
        sleep(0.25)

    ball.draw()
    pico.update()

    # reset the game on X
    if pico.is_pressed(2):
        ball.reset()
        player1 = 0
        player2 = 0

    # pause the game on Y
    if pico.is_pressed(3):
        sleep(0.25)
        show_text("Game paused")
        while not pico.is_pressed(3):
            sleep(0.01)
        sleep(0.25)

    # slight delay in the loop, although not much is really needed - this isn't super fast
    sleep(0.01)