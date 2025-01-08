import pygame
from pygame.locals import *
import random
import math

pygame.init()

width, height = 1600, 900
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Flight Simulator")


# Font initialization
pygame.font.init()
font = pygame.font.Font(None, 36)  # You can adjust the font size and style
RED = (255, 0, 0)
ORANGE =  (255, 165, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)  # Green color for the speed bar
LIGHTGREEN = (124, 252,0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
WHITE_TRANS = (255, 255, 255, 150)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)

GREY = (128, 128, 128)
DEEP_SKY_BLUE = (0,191,255)
DEEP_PINK = (255,20,147)


pygame.joystick.init()

STICK_INPUT_SPEED = 20
THROTTLE_INPUT_SPEED = 0.2

# Check if a joystick is available
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(1)
    joystick.init()
    print(joystick.get_name())

    throttle = pygame.joystick.Joystick(0)
    throttle.init()
    print(throttle.get_name())


else:
    print("No joystick detected.")

# Initialize Pygame mixer for sound
pygame.mixer.init()
blaster_sound      = pygame.mixer.Sound("./fire.mp3")
kill_sound         = pygame.mixer.Sound("./kill.mp3")

grow_sound         = pygame.mixer.Sound("./Galaga - Demons of Death SFX (2).wav")
shield_sound       = pygame.mixer.Sound("./Galaga - Demons of Death SFX (3).wav")
pop_sound          = pygame.mixer.Sound("./Galaga - Demons of Death SFX (4).wav")
angry_sound        = pygame.mixer.Sound("./Galaga - Demons of Death SFX (5).wav")
extra_life_sound   = pygame.mixer.Sound("./Galaga - Demons of Death SFX (6).wav")
level_sound        = pygame.mixer.Sound("./Galaga - Demons of Death SFX (9).wav")
player_death_sound = pygame.mixer.Sound("./Galaga - Demons of Death SFX (10).wav")
bomb_sound         = pygame.mixer.Sound("./Galaga - Demons of Death SFX (11).wav")

fast_sound         = pygame.mixer.Sound("./Galaga - Demons of Death SFX (13).wav")


# Initialize the score
score = 0
score_at_wave_start = 0
high_score = 0
# Load the high score from the file
try:
    with open('high_score.txt', 'r') as file:
        high_score = int(file.read())
except FileNotFoundError:
    # If the file doesn't exist, initialize high score to 0
    high_score = 0
numKills = 0


class Aircraft(pygame.sprite.Sprite):
    def __init__(self):
        super(Aircraft, self).__init__()
        self.size = 50
        self.original_size = self.size
        self.size_ratio = 7/10
        self.scale = [self.size, self.size*(self.size_ratio)]
        self.color = BLUE 
        self.original_color = self.color
        self.image = pygame.Surface((self.size, self.size*self.size_ratio))  # Replace with your aircraft image
        self.image.fill(self.color)  # Set color (red in this case)
        self.rect = self.image.get_rect()
        self.rect.center = (width // 2, height - self.rect.height)

        if pygame.joystick.get_count() > 0:
            axis_y = throttle.get_axis(2)
            self.rect.y = int(axis_y * (height - self.rect.height))

        self.current_speed = (height - self.rect.y)/25
        self.max_speed = (height - self.rect.y)/25 -4

        self.lives = 5 + 1  # Initial number of lives

        self.blaster_dual = False
        self.blaster_tri = False
        self.blaster_quad = False

        self.engineBoost = 0

        self.num_bombs = 3  # Set the initial number of bombs

        # Cooldown variables
        self.bullet_cooldown = 0
        self.bullet_cooldown_time = 20  # Adjust the cooldown time as needed (in frames)

        self.angry = False
        self.flash_timer = 0 #10
        self.num_flashes = 0

        self.shield_up = True  # Initial state of the shield
        self.shieldStrength = 1
        self.shield_flash_timer = 0
        self.shield_flash_interval = 10  # Adjust the interval for shield flashing (in frames)


    def update(self):
        keys = pygame.key.get_pressed()



        # Throttle input, not the joystick! :|
        if pygame.joystick.get_count() > 0:

            if throttle.get_button(23): # EAC to ARM 
                axis_y = throttle.get_axis(2)

                # Scale the throttle to match the height of the screen
                new_ya = int((axis_y + 1) / 2 * (height - self.rect.height))


                # Calculate y-axis movement based on throttle and apply speed factor
                y_movement = new_ya - self.rect.y
                self.rect.y += int(y_movement * THROTTLE_INPUT_SPEED) + self.engineBoost  # Adjust the speed factor as needed

                # Limit the y-axis speed
                new_yb = min(height - self.rect.height, max(0, self.rect.y))

            

                # Check if the new y position is within bounds
                if 0 <= new_yb <= height - self.rect.height :
                    self.rect.y = new_yb

                # Limit the y-axis position
                self.rect.y = max((self.rect.height*2), min(height - (self.rect.height*2), new_yb))


        # Keyboard input
        if keys[K_LEFT] and self.rect.left > 0:
            self.rect.x -= STICK_INPUT_SPEED + self.engineBoost
        if keys[K_RIGHT] and self.rect.right < width:
            self.rect.x += STICK_INPUT_SPEED + self.engineBoost
        if keys[K_UP] and self.rect.top > 0:
            self.rect.y -= STICK_INPUT_SPEED + self.engineBoost
        if keys[K_DOWN] and self.rect.bottom < height:
            self.rect.y += STICK_INPUT_SPEED + self.engineBoost

        # Joystick input
        if pygame.joystick.get_count() > 0:
            axis_x = joystick.get_axis(0)
            axis_y = joystick.get_axis(1)
            if axis_x < 0 and self.rect.left > 0:
                self.rect.x += int(axis_x * STICK_INPUT_SPEED) + self.engineBoost
            elif axis_x > 0 and self.rect.right < width:
                self.rect.x += int(axis_x * STICK_INPUT_SPEED) + self.engineBoost

            if axis_y < 0 and self.rect.top > 0:
                self.rect.y += int(axis_y * STICK_INPUT_SPEED) + self.engineBoost
            elif axis_y > 0 and self.rect.bottom < height:
                self.rect.y += int(axis_y * STICK_INPUT_SPEED) + self.engineBoost

        # Limit the y-axis position
        self.rect.y = max((self.rect.height*2), min(height - (self.rect.height*2), self.rect.y))
        self.current_speed = (height - self.rect.y)/25


        joy_trigger_pulled = False
        joy_bomb_trigged = False

        # Joystick trigger input
        if pygame.joystick.get_count() > 0:
            if joystick.get_button(0): # trigger pulled
                joy_trigger_pulled = True

            if joystick.get_button(1): # trigger pulled
                bomb_trigged = True



        if joy_trigger_pulled or keys[K_SPACE]:
            # Create a new bullet when a joystick button is pressed
            # Check if the cooldown has expired before firing another bullet
            if self.bullet_cooldown == 0:
                if self.blaster_quad:
                    bullet = Bullet((self.rect.centerx-20, self.rect.top+30),(-5, -15))
                    player_bullets.add(bullet)
                    bullet = Bullet((self.rect.centerx+20, self.rect.top+30),(5, -15))
                    player_bullets.add(bullet)

                    bullet = Bullet((self.rect.centerx-15, self.rect.top+30))
                    player_bullets.add(bullet)
                    bullet = Bullet((self.rect.centerx+15, self.rect.top+30))
                    player_bullets.add(bullet)

                elif self.blaster_tri:
                    bullet = Bullet((self.rect.centerx-15, self.rect.top+30),(-2, -15))
                    player_bullets.add(bullet)
                    bullet = Bullet((self.rect.centerx+15, self.rect.top+30),(2, -15))
                    player_bullets.add(bullet)
                    bullet = Bullet((self.rect.centerx, self.rect.top+30))
                    player_bullets.add(bullet)

                elif self.blaster_dual:
                    bullet = Bullet((self.rect.centerx-15, self.rect.top+30))
                    player_bullets.add(bullet)
                    bullet = Bullet((self.rect.centerx+15, self.rect.top+30))
                    player_bullets.add(bullet)

                    

                else:
                    bullet = Bullet((self.rect.centerx, self.rect.top+30))
                    player_bullets.add(bullet)
                self.bullet_cooldown = self.bullet_cooldown_time
                blaster_sound.play()

        if joy_bomb_trigged or keys[K_TAB]:
            if self.bullet_cooldown == 0:
                if self.num_bombs > 0 and len(player_bombs.sprites()) == 0:
                    bomb = Bomb((self.rect.centerx, self.rect.top+30))
                    player_bombs.add(bomb)
                    self.num_bombs -= 1

                        

        # Reduce the cooldown time if it's greater than 0
        if self.bullet_cooldown > 0:
            self.bullet_cooldown -= 1

        #print(str(self.rect.x), " : ", str(self.rect.y))

        self.player_shieldEffect()


    def player_shieldEffect(self):
        # Flash the shield outline when the shield is up
        if self.shieldStrength > 0 or self.angry:
            # Scale the image
            self.size = self.original_size + (self.original_size * 0.10) + self.shieldStrength * 1
            

            if self.flash_timer <= 0:
                border_thickness = 2
                pygame.draw.rect(self.image, WHITE, (0, 0, self.rect.width, border_thickness))
                pygame.draw.rect(self.image, WHITE, (0, 0, border_thickness, self.rect.height))
                pygame.draw.rect(self.image, WHITE, (0, self.rect.height - border_thickness, self.rect.width, border_thickness))
                pygame.draw.rect(self.image, WHITE, (self.rect.width - border_thickness, 0, border_thickness, self.rect.height))

                self.num_flashes += 1
                self.flash_timer = self.shield_flash_interval

                self.image = pygame.transform.scale(self.image, get_scale(self))
                self.rect = self.image.get_rect(center=self.rect.center)

            else:
                self.flash_timer -= 1
                # Reset the image to its original state

                self.image = pygame.Surface((self.size, self.size*self.size_ratio))  # Replace with your aircraft image
                self.image.fill(self.color)  # Set color (red in this case)
                self.rect = self.image.get_rect(center=self.rect.center)
                self.color = self.original_color

            
            



        else:
            # Reset the image to its original state
            self.size = self.original_size
            self.image = pygame.Surface((self.size, self.size*self.size_ratio))  # Replace with your aircraft image
            self.image.fill(self.color)  # Set color (red in this case)
            self.rect = self.image.get_rect(center=self.rect.center)
            self.color = self.original_color










class EnemyAircraft(pygame.sprite.Sprite):
    def __init__(self, rectX, rectY):
        super(EnemyAircraft, self).__init__()
        self.original_size = 42
        self.size = self.original_size
        self.size_ratio = 2/3
        self.scale = [self.size, self.size*(self.size_ratio)]
        self.image = pygame.Surface(self.scale)
        self.color = RED
        self.original_color = self.color
        self.image.fill(self.color)  # Red color for enemy aircraft
        self.rect = self.image.get_rect()
        self.rect.x = rectX #random.randint(0, width - self.rect.width)
        self.rect.y = rectY #-self.rect.height  # Start above the top of the screen
        self.maxSpeed = 4
        self.speed = random.randint(2, self.maxSpeed)  # Varying speed
        self.downSpeed = 1

        # Randomly determine if the enemy moves left or right
        self.direction_x = random.choice([-1, 1])
        self.direction_y = 1  # Always start by moving downwards

        # Add variables to control movement pattern
        self.move_upwards = False
        self.move_downwards = True

        self.fire_probability = 0.01  # Adjust the probability as needed (e.g., 0.02 for 2% chance)
        # Cooldown variables
        self.bullet_cooldown = 0
        self.bullet_cooldown_time = 60  # Adjust the cooldown time as needed (in frames)

        self.point_value = 15

        self.angry = False
        self.flash_timer = 0 #10
        self.num_flashes = 0

        self.shield_up = True  # Initial state of the shield
        self.shieldStrength = 1
        self.shield_flash_timer = 0
        self.shield_flash_interval = 10  # Adjust the interval for shield flashing (in frames)



    def update(self):
        global score
        global numKills

        shieldEffect(self)

        enemy_movement(self)
        

        # Randomly change the left/right movement direction
        if random.randint(0, 100) < 5:
            self.direction_x *= -1

        # Check for the chance to shoot bullets downward
        if random.random() < self.fire_probability:
            self.shoot_downward()

        # Reduce the cooldown time if it's greater than 0
        if self.bullet_cooldown > 0:
            self.bullet_cooldown -= 1

        
        enemy_collide(self)



    def shoot_downward(self):
        if self.bullet_cooldown == 0:
            if len(enemy_bullets.sprites()) < 6:
                # Create a bullet and add it to the bullets group
                bullet = Bullet(self.rect.center, speed=(0, 5))  # Adjust the speed as needed
                enemy_bullets.add(bullet)
                self.bullet_cooldown = self.bullet_cooldown_time

class FormationEnemy(pygame.sprite.Sprite):
    def __init__(self, formation_offset, color, direction, speed, *groups):
        super(FormationEnemy, self).__init__(*groups)
        self.original_size = 40
        self.size = self.original_size
        self.size_ratio = 2/3
        self.scale = [self.size, self.size*(self.size_ratio)]
        self.image = pygame.Surface(self.scale)
        self.color = color
        self.original_color = self.color
        self.image.fill(self.color)  # Adjust color as needed
        self.rect = self.image.get_rect()

        # Set initial position based on formation offset

        self.rect.x = formation_offset[0]
        self.rect.y = formation_offset[1]

        # Randomly determine if the enemy moves left or right
        self.direction_x = direction
        self.direction_y = 1  # Always start by moving downwards

        # Add variables to control movement pattern
        self.move_upwards = False
        self.move_downwards = True

        self.maxSpeed = 2
        self.speed = speed  # Fixed speed for formation enemies
        self.downSpeed = 0.5
        self.point_value = 10  # Adjust point value as needed

        self.angry = False
        self.flash_timer = 0 #10
        self.num_flashes = 0

        self.shield_up = True  # Initial state of the shield
        self.shieldStrength = 1
        self.shield_flash_timer = 0
        self.shield_flash_interval = 10  # Adjust the interval for shield flashing (in frames)



    def update(self):
        global score
        global numKills
        global specialCount
        global level
        

 
        if self.angry:
            if self.flash_timer <= 0:
                if self.original_color == self.color:
                    
                    if not self.shield_up: self.num_flashes += 1
                    self.flash_timer = 2
                else:
                    ...
                if self.num_flashes >= 10:
                    self.kill()
                    enemy_aircraft = EnemyAircraft(self.rect.x, self.rect.y)
                    if not self.shield_up: enemy_aircraft.shield_up = False
                    enemy_aircrafts.add(enemy_aircraft)      

            else:
                self.flash_timer -= 1
            

        else:
            if (level >= 3) and (specialCount < 3):
            # Chance enemy will become angry!   ie change into regular enemy
                if self.rect.y > (1 * height / 5):        
                    if random.randint(0, 500) < 1:  # Adjust the frequency of enemy creation
                        self.num_flashes = 0
                        self.angry = True
                        angry_sound.play()
                        self.shield_flash_interval = 5

        shieldEffect(self)
        enemy_movement(self)
        enemy_collide(self)

class HoveringEnemy(pygame.sprite.Sprite):
    def __init__(self):
        super(HoveringEnemy, self).__init__()

        self.original_size = 35
        self.size = self.original_size
        self.size_ratio = 5/6
        self.scale = [self.size, self.size*(self.size_ratio)]
        self.image = pygame.Surface(self.scale)
        self.color = GREY
        self.original_color = self.color
        self.image.fill(self.color)  # Adjust color as needed
        self.rect = self.image.get_rect()

        self.original_image = self.image.copy()

        # Set the initial position randomly
        self.rect.x = random.randint(0, width - self.rect.width)
        self.rect.y = -self.rect.height  # Start above the top of the screen

        # Set the target position
        target_x = random.randint(40, width - 40)
        target_y = random.randint(40, height - 80)
        self.target_position = [target_x, target_y]

        # Set the speed
        self.speed = 5

        self.point_value = 100

        self.angry = False
        self.flash_timer = 0 #10
        self.num_flashes = 0

        self.shield_up = True  # Initial state of the shield
        self.shieldStrength = 6
        self.shield_flash_timer = 0
        self.shield_flash_interval = 10  # Adjust the interval for shield flashing (in frames)

        self.fire_probability = 0.01 # Adjust the probability as needed (e.g., 0.02 for 2% chance)
        # Cooldown variables
        self.bullet_cooldown = 0
        self.bullet_cooldown_time = 30  # Adjust the cooldown time as needed (in frames)

    def update(self):
        

        # Check if the HoveringEnemy has reached the target position
        if pygame.Rect(self.rect.inflate(10, 10)).colliderect(pygame.Rect(self.target_position[0], self.target_position[1], 1, 1)):
            # # If reached, hover around the target position
            # hover_distance = 60
            # hover_speed = 1

            # # Calculate new hover position
            # hover_x = self.target_position[0] + hover_distance * math.cos(pygame.time.get_ticks() / 1000 * hover_speed)
            # hover_y = self.target_position[1] + hover_distance * math.sin(pygame.time.get_ticks() / 1000 * hover_speed)

            # self.rect.x = hover_x
            # self.rect.y = hover_y
            ...

            # Shoot a missile towards the player's last location
            # Check for the chance to shoot bullets downward
            if (random.random() < self.fire_probability) and (self.bullet_cooldown == 0):
                player_last_position = player_aircraft.rect.center
                self.shoot_missile(player_last_position)
                self.bullet_cooldown = self.bullet_cooldown_time

                 # Set the new target position, move and shoot, repeat
                target_x = random.randint(40, width - 40)
                target_y = random.randint(40, height - 40)
                self.target_position = random.choice([[target_x, target_y], player_last_position])

            # Reduce the cooldown time if it's greater than 0
            if self.bullet_cooldown > 0:
                self.bullet_cooldown -= 1

        else:
            # Calculate the angle to the target position
            angle = math.atan2(self.target_position[1] - self.rect.centery, self.target_position[0] - self.rect.centerx)

            # Calculate the new position based on the angle and speed
            new_x = self.rect.x + self.speed * math.cos(angle)
            new_y = self.rect.y + self.speed * math.sin(angle)

            # Update the position
            self.rect.x = new_x
            self.rect.y = new_y

        enemy_collide(self)
        shieldEffect(self)

        

    def shoot_missile(self, target_position):
        if self.bullet_cooldown == 0:
            if len(enemy_bullets.sprites()) < 6:
                # Create a missile and add it to the missiles group
                missile = Missile(self.rect.center, target_position, ORANGE)

                enemy_bullets.add(missile)
                self.bullet_cooldown = self.bullet_cooldown_time



class FastEnemy(pygame.sprite.Sprite):
    def __init__(self, start_from_left=True):
        super(FastEnemy, self).__init__()
        self.original_size = 45
        self.size = self.original_size
        self.size_ratio = 1/4
        self.scale = [self.size, self.size*(self.size_ratio)]
        self.image = pygame.Surface(self.scale)
        self.color = LIGHTGREEN  # You can define the YELLOW color according to your requirements
        self.original_color = self.color
        self.image.fill(self.color)
        self.rect = self.image.get_rect()

        if start_from_left:
            self.rect.x = -self.rect.width
        else:
            self.rect.x = width  # Assuming 'width' is the screen width
        self.rect.y = random.randint(0, height*0.25 - self.rect.height)  # 'height' is the screen height

        self.speed = 12  # Adjust the speed as needed
        self.direction_x = 1 if start_from_left else -1  # 1 for left to right, -1 for right to left

        self.point_value = 500  # Adjust point value as needed


        self.fire_probability = 0.02  # Adjust the probability as needed (e.g., 0.02 for 2% chance)
        # Cooldown variables
        self.bullet_cooldown = 0
        self.bullet_cooldown_time = 30  # Adjust the cooldown time as needed (in frames)

        self.angry = False
        self.flash_timer = 0 #10
        self.num_flashes = 0

        #self.shield_up = True  # Initial state of the shield
        self.shieldStrength = 1
        self.shield_flash_timer = 0
        self.shield_flash_interval = 10  # Adjust the interval for shield flashing (in frames)
        fast_sound.play()

    def update(self):
        global level_enemies_remaining
        self.rect.x += self.speed * self.direction_x
        
            

        # Remove the enemy when it goes off the screen
        if self.rect.right < 0 or self.rect.left > width:
            self.kill()
            level_enemies_remaining += 1 # back to the pool 

        shieldEffect(self)
        enemy_collide(self)

        # Shoot a missile towards the player's last location
        # Check for the chance to shoot bullets downward
        if random.random() < self.fire_probability and self.bullet_cooldown == 0:
            player_last_position = player_aircraft.rect.center
            self.shoot_missile(player_last_position)
            self.bullet_cooldown = self.bullet_cooldown_time

        # Reduce the cooldown time if it's greater than 0
        if self.bullet_cooldown > 0:
            self.bullet_cooldown -= 1

    def shoot_missile(self, target_position):
        if self.bullet_cooldown == 0:
            if len(enemy_bullets.sprites()) < 6:
                # Create a missile and add it to the missiles group
                missile = Missile(self.rect.center, target_position, ORANGE)

                enemy_bullets.add(missile)
                self.bullet_cooldown = self.bullet_cooldown_time






class SpecialEnemy(pygame.sprite.Sprite):
    def __init__(self, original_size=45, color=ORANGE, shieldStrength=9):
        super(SpecialEnemy, self).__init__()
        self.original_size = original_size
        self.size = self.original_size
        self.size_ratio = 1/2
        self.scale = [self.size, self.size*(self.size_ratio)]
        self.image = pygame.Surface(self.scale)
        self.color = color 
        self.original_color = self.color
        self.image.fill(self.color)  # Red color for special enemies
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect()

        # Store the original rectangle for rotation
        self.original_rect = self.rect.copy()

        self.rect.x = random.randint(0, width - self.rect.width)
        self.rect.y = -self.rect.height  # Start above the top of the screen
        self.maxSpeed = 5
        self.speed = random.randint(2, self.maxSpeed)  # Varying speed
        self.downSpeed = 0.5
        # Randomly determine if the enemy moves left or right
        self.direction_x = random.choice([-1, 1])
        self.direction_y = 1  # Always start by moving downwards

        # Add variables to control movement pattern
        self.move_upwards = False
        self.move_downwards = True

        self.fire_probability = 0.01  # Adjust the probability as needed (e.g., 0.02 for 2% chance)
        # Cooldown variables
        self.bullet_cooldown = 0
        self.bullet_cooldown_time = 30  # Adjust the cooldown time as needed (in frames)

        self.point_value = 50

        self.angry = False
        self.flash_timer = 0 #10
        self.num_flashes = 0

        #self.shield_up = True  # Initial state of the shield
        self.shieldStrength = shieldStrength
        self.shield_flash_timer = 0
        self.shield_flash_interval = 10  # Adjust the interval for shield flashing (in frames)
        

        

    def update(self):
        global score
        global numKills

        # shieldEffect(self)

        enemy_movement(self)

        
        # Randomly change the left/right movement direction
        if random.randint(0, 100) < 1:
            self.direction_x *= -1

        # Shoot a missile towards the player's last location

        # Check for the chance to shoot bullets 
        if random.random() < self.fire_probability and self.bullet_cooldown == 0:

            # if self.spinning:
            #     # Set the target position
            #     target_x = random.randint(40, width - 40)
            #     target_y = random.randint(40, height - 40)
            #     target_position = [target_x, target_y]
            #     self.shoot_missile(target_position)

            player_last_position = player_aircraft.rect.center
            self.shoot_missile(player_last_position)


            self.bullet_cooldown = self.bullet_cooldown_time

        # Reduce the cooldown time if it's greater than 0
        if self.bullet_cooldown > 0:
            self.bullet_cooldown -= 1



        enemy_collide(self)
        shieldEffect(self)
 
    def shoot_missile(self, target_position):
        if self.bullet_cooldown == 0:
            if len(enemy_bullets.sprites()) < 6:
                # Create a missile and add it to the missiles group
                missile = Missile(self.rect.center, target_position)
                enemy_bullets.add(missile)
                self.bullet_cooldown = self.bullet_cooldown_time


class FallingEnemy(pygame.sprite.Sprite):
    def __init__(self):
        super(FallingEnemy, self).__init__()
        self.original_size = 8
        self.size = self.original_size
        self.size_ratio = 3 / 1
        self.scale = [self.size, self.size * (self.size_ratio)]
        self.image = pygame.Surface(self.scale)
        self.color = RED
        self.original_color = self.color
        self.image.fill(self.color)  # Adjust color as needed
        self.rect = self.image.get_rect()

        # Set initial position above the player
        self.rect.centerx = player_aircraft.rect.x #player_position[0]
        self.rect.y = -self.rect.height

        self.speed = random.randint(12,18)  # Speed at which the enemy falls

        self.point_value = 10  # Adjust point value as needed

        self.angry = False
        self.flash_timer = 0 #10
        self.num_flashes = 0

        self.shield_up = False  # Initial state of the shield
        self.shieldStrength = 0
        self.shield_flash_timer = 0
        self.shield_flash_interval = 10  # Adjust the interval for shield flashing (in frames)

        angry_sound.play()

    def update(self):
        global score
        global numKills
        global specialCount
        global level
        global level_enemies_remaining

        # Move downwards
        self.rect.y += self.speed

        # Check if the enemy has exited the bottom of the screen
        if self.rect.y > height:
            level_enemies_remaining += 1 # back to the pool 
            self.kill()  # Remove the enemy if it's below the screen

        enemy_collide(self)

        


class GrowableEnemy(pygame.sprite.Sprite):
    def __init__(self):
        super(GrowableEnemy, self).__init__()
        self.original_size = 60
        self.size = self.original_size
        self.size_ratio = 2/3
        self.scale = [self.size, self.size*(self.size_ratio)]
        self.image = pygame.Surface(self.scale)
        self.color = PURPLE
        self.original_color = self.color
        self.image.fill(self.color)  # Red color for growable enemies
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, width - self.rect.width)
        self.rect.y = -self.rect.height  # Start above the top of the screen
        self.maxSpeed = 2
        self.speed = random.randint(1, self.maxSpeed )  # Varying speed
        self.downSpeed = 0.5
        self.direction_x = random.choice([-1, 1])
        self.direction_y = 1  # Always start by moving downwards
        self.move_upwards = False
        self.move_downwards = True
        self.point_value = 500

        # Variables for growth
        self.growth_rate = 10  # Adjust the growth rate as needed
        self.max_size = 250  # Adjust the maximum size as needed
        self.growth_threshold = 1  # Number of hits needed for growth

        # Variables for explosion
        self.explosion_threshold = (self.max_size-self.original_size)/self.growth_rate  # Number of hits needed for explosion
        self.hit_count = 0

        self.fire_probability = 0.01  # Adjust the probability as needed (e.g., 0.02 for 2% chance)
        # Cooldown variables
        self.bullet_cooldown = 0
        self.bullet_cooldown_time = 30  # Adjust the cooldown time as needed (in frames)

        self.angry = False
        self.flash_timer = 0 #10
        self.num_flashes = 0

        self.shield_up = False  # Initial state of the shield
        self.shieldStrength = 0
        self.shield_flash_timer = 0
        self.shield_flash_interval = 10  # Adjust the interval for shield flashing (in frames)



    def update(self):
        global score
        global numKills

        #shieldEffect(self)

        enemy_movement(self)
        

        # Check for collisions with player bullets
        for collision in pygame.sprite.spritecollide(self, player_bullets, True):

            point_text = PointText(collision.rect.center, f"x",10)
            textShown.add(point_text)

            self.hit_count += 1
            if self.hit_count >= self.growth_threshold:
                self.grow()
                

        # Check for collisions with player explosions
        for collision in pygame.sprite.spritecollide(self, explosions, False):

            point_text = PointText(self.rect.center, f"x",10)
            textShown.add(point_text)

            self.hit_count += 1
            if self.hit_count >= self.growth_threshold:
                self.grow()
                

        # Check for self explosion
        if self.hit_count >= self.explosion_threshold:
            self.explode()

        if random.randint(0, 100) < 1:
            self.direction_x *= -1

        # Shoot a missile towards the player's last location
        # Check for the chance to shoot bullets downward
        if random.random() < self.fire_probability and self.bullet_cooldown == 0:
            player_last_position = player_aircraft.rect.center
            self.shoot_missile(player_last_position)
            self.bullet_cooldown = self.bullet_cooldown_time

        # Reduce the cooldown time if it's greater than 0
        if self.bullet_cooldown > 0:
            self.bullet_cooldown -= 1

    def grow(self):
        # Increase the size of the enemy up to a maximum size
        self.size += self.growth_rate
        self.size = min(self.size, self.max_size)
        self.image = pygame.transform.scale(self.image, (self.size, (self.size*(2/3))))
        self.rect = self.image.get_rect(center=self.rect.center)
        self.growth_threshold += 1
        grow_sound.play()

    def explode(self):
        global score
        global numKills
        # Perform explosion logic (e.g., spawn particles, play sound)
        # Then, remove the enemy

         # Handle the enemy being hit (destroy or respawn)

        # Create an explosion effect at the location of the enemy's death
        explosion = Explosion(self.rect.center,self.size*2.5,self.size,15)
        explosions.add(explosion)

        point_text = PointText(self.rect.center, f"+{self.point_value}")
        textShown.add(point_text)

        # Increase the score when an enemy is destroyed
        score += self.point_value
        numKills += 1
        kill_sound.play()
        pop_sound.play()
        self.kill()
        

    def shoot_missile(self, target_position):
        if self.bullet_cooldown == 0:
            if len(enemy_bullets.sprites()) < 6:
                # Create a missile and add it to the missiles group
                missile = Missile(self.rect.center, target_position, ORANGE)

                enemy_bullets.add(missile)
                self.bullet_cooldown = self.bullet_cooldown_time



class Star(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height, rel_speed):
        super(Star, self).__init__()
        self.image = pygame.Surface((2, 2))
        self.image.fill(WHITE)  # White color for stars
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, screen_width)
        self.rect.y = random.randint(0, screen_height)
        self.rel_speed = rel_speed

    def update(self, speed):
        if speed < 5: 
            speed = 5

        self.rect.y += speed*self.rel_speed
        if self.rect.y > height:
            self.rect.y = 0
            self.rect.x = random.randint(0, width)

class Explosion(pygame.sprite.Sprite):
    def __init__(self, position, max_size=100, start_size=1, growth_rate=5):
        super(Explosion, self).__init__()
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=position)
        self.growth_rate = growth_rate
        self.max_size = max_size
        self.current_size = start_size

    def update(self):
        # Expand the explosion
        self.current_size += self.growth_rate
        if self.current_size > self.max_size:
            self.kill()

        # Redraw the circle on the surface
        self.image = pygame.Surface((self.current_size, self.current_size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (WHITE_TRANS), (self.current_size // 2, self.current_size // 2), self.current_size // 2)
        self.rect = self.image.get_rect(center=self.rect.center)

class PointText(pygame.sprite.Sprite):
    def __init__(self, position, points, timeToLive=60, size=36, color=WHITE):
        super(PointText, self).__init__()
        self.font = pygame.font.Font(None, size)  # You can adjust the font size and style
        self.image = self.font.render(f"{points}", True, color)
        self.rect = self.image.get_rect(center=position)
        self.time_to_live = timeToLive  # Number of frames the text will be displayed
        self.current_frame = 0
        

    def update(self):
        self.current_frame += 1
        if self.current_frame >= self.time_to_live:
            self.kill()  # Remove the sprite when its time to live is up
        else:
            alpha = int(255 * (1 - self.current_frame / self.time_to_live))  # Calculate alpha for fading
            self.image.set_alpha(alpha)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, position, speed=(0, -15), color=RED):
        super(Bullet, self).__init__()
        self.image = pygame.Surface((5, 10))
        self.image.fill(color)  # Red color for bullets
        self.rect = self.image.get_rect(center=position)
        self.speed = speed
        self.rect.x += self.speed[0]*3
        self.rect.y += self.speed[1]*3


    def update(self):
        # Move the bullet
        self.rect.x += self.speed[0]
        self.rect.y += self.speed[1]

        # Remove the bullet if it goes off-screen
        if self.rect.bottom < 0 or self.rect.top > height:
            self.kill()

class Bomb(pygame.sprite.Sprite):
    def __init__(self, position, speed=(0, -10)):
        super(Bomb, self).__init__()
        self.image = pygame.Surface((10, 20))
        self.image.fill(ORANGE)  # Red color for bullets
        self.rect = self.image.get_rect(center=position)
        self.speed = speed
        self.rect.x += self.speed[0]*3
        self.rect.y += self.speed[1]*3


    def update(self):
        # Move the bullet
        self.rect.x += self.speed[0]
        self.rect.y += self.speed[1]


        # Remove the bullet if it goes off-screen
        if self.rect.bottom < height/3 or self.rect.top > height:
            explosion = Explosion(self.rect.center, max(height+self.rect.y, width+self.rect.x),1, 20)
            explosions.add(explosion)
            self.kill()

class Missile(pygame.sprite.Sprite):
    def __init__(self, position, target_position, color=ORANGE):
        super(Missile, self).__init__()
        self.image = pygame.Surface((5, 10))
        self.image.fill(color)  # Blue color for missiles
        self.rect = self.image.get_rect(center=position)
        self.speed = 10
        self.direction = pygame.math.Vector2(target_position[0] - position[0], target_position[1] - position[1]).normalize()

    def update(self):
        # Move the missile towards the target
        self.rect.x += self.speed * self.direction.x
        self.rect.y += self.speed * self.direction.y

        # Remove the missile if it goes off-screen
        if self.rect.bottom < 0 or self.rect.top > height or self.rect.right < 0 or self.rect.left > width:
            self.kill()



class PowerUp(pygame.sprite.Sprite):
    def __init__(self):
        super(PowerUp, self).__init__()
        self.size = 35
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.color = GREEN
        pygame.draw.circle(self.image, self.color, (self.size // 2, self.size // 2), self.size // 2)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, width - self.rect.width)
        self.rect.y = -self.rect.height
        self.speed = random.randint(1, 3)  # Varying speed

        # Randomly determine if the enemy moves left or right
        self.direction_x = random.choice([-1, 1])
        self.direction_y = 1  # Always start by moving downwards

        # Add variables to control movement pattern
        self.move_upwards = False
        self.move_downwards = True

        self.point_value = 100

        type_choices = []

        if player_aircraft.lives < 2:
            type_choices.append("L")

        if player_aircraft.bullet_cooldown > 4:
            type_choices.append("E")

        if player_aircraft.blaster_quad == False:
            type_choices.append("W")

        if player_aircraft.num_bombs < 5:
            type_choices.append("B")

        if player_aircraft.shieldStrength == 0:
            type_choices.append("S")

        type_choices.append("P")

        self.type = random.choice(type_choices)

        if self.type == "P":
            self.point_value = 100 + (50*random.randint(0,8))
            self.type = str(self.point_value)

    def update(self):
        if self.move_downwards:
            self.rect.y += self.speed * self.direction_y
            self.rect.x += self.speed * self.direction_x

            # If the enemy aircraft goes beyond 1/3 towards the bottom, switch movement direction
            if self.rect.y > 2 * height / 4:
                self.move_downwards = False
                self.move_upwards = True

        elif self.move_upwards:
            self.rect.y -= self.speed * self.direction_y
            self.rect.x += self.speed * self.direction_x

            # If the enemy aircraft goes above the top, switch movement direction
            if self.rect.y < -self.rect.height:
                self.kill()

        # Check and adjust direction to stay within the horizontal bounds
        if self.rect.x < 0:
            self.rect.x = 0
            self.direction_x = 1  # Move right
        elif self.rect.right > width:
            self.rect.right = width
            self.direction_x = -1  # Move left

        # Randomly change the left/right movement direction
        if random.randint(0, 100) < 2:
            self.direction_x *= -1

        # Make the power-up flash by changing color
        flash_speed = 500  # Adjust the speed of the flash (milliseconds)
        flash_intensity = abs(math.sin(pygame.time.get_ticks() / flash_speed))  # Varies between 0 and 1
        flash_color = (
            int(self.color[0] * flash_intensity),
            int(self.color[1] * flash_intensity),
            int(self.color[2] * flash_intensity),
        )

        # Create a copy of the original image to modify
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, flash_color, (self.size // 2, self.size // 2), self.size // 2)
        pygame.draw.circle(self.image, WHITE, (self.size // 2, self.size // 2), self.size // 2, 1)

        # Draw the type text
        self.draw_type_text()

        self.collideCheck()

    def collideCheck(self):
        global score
        # Check for collisions between player aircraft and power-ups
        for player in pygame.sprite.spritecollide(self, players, False):
            point_text = PointText(self.rect.center, "Power-Up")
            score += self.point_value
            # Player collected a power-up, add points and extra life
            
            if self.type == "L":
                player.lives += 1
                point_text = PointText(self.rect.center, "Extra Life")

            elif self.type == "E":
                if player.bullet_cooldown_time > 4:
                    player.bullet_cooldown_time -= 2
                    point_text = PointText(self.rect.center, "Upgrade")

            elif self.type == "W":
                    if player.blaster_tri == True:
                        player.blaster_quad = True
                        point_text = PointText(self.rect.center, "Quad Fire")            

                    elif player.blaster_dual:
                        player.blaster_tri = True
                        point_text = PointText(self.rect.center, "Tri Fire")

                    elif player.blaster_dual == False:
                        player.blaster_dual = True
                        point_text = PointText(self.rect.center, "Dual Fire")

                    

                        

            elif self.type == "B":
                player.num_bombs += 1
                point_text = PointText(self.rect.center, "Extra Bomb")

            elif self.type == "S":
                player.shieldStrength = 1
                point_text = PointText(self.rect.center, "Shield")

            else:
                point_text = PointText(self.rect.center, f"+{self.point_value}")
                

            extra_life_sound.play()
            textShown.add(point_text)
            self.kill()


    def draw_type_text(self):
        font = pygame.font.Font(None, 26)
        text = font.render(self.type, True, RED)
        text_rect = text.get_rect(center=(self.rect.centerx, self.rect.centery))
        screen.blit(text, text_rect)

def spawn_formation_grid(num_rows, num_columns):
    global level_enemies_remaining
    global level
    # Spawn formation enemies periodically

    # Calculate the maximum allowed spawn center
    max_spawn_center = width - (num_columns - 1) * 80

    # Ensure spawn_center stays within valid range
    spawn_center = random.randint(max(120, (num_columns // 2) * 80), min(max_spawn_center, width - (num_columns // 2) * 80))

    direction = random.choice([-1, 0, 1])
    maxSpeed = 2
    if level >= 5:
        maxSpeed = 4
    if level >= 10:
        maxSpeed = 5
    
    speed = random.randint(2,maxSpeed)
    color = random.choice([YELLOW, GREEN, DEEP_SKY_BLUE, DEEP_PINK])

    # Calculate the offsets based on the number of rows and columns
    formation_offsets = []
    for row in range(num_rows):
        color = random.choice([YELLOW, GREEN, DEEP_SKY_BLUE, DEEP_PINK])
        for col in range(num_columns):
            
            offset = (spawn_center + (col - num_columns // 2) * 80, (-40*num_rows) + row * 40),color
            formation_offsets.append(offset)

    formation_enemies = pygame.sprite.Group()

    for offset, color in formation_offsets:
        if level_enemies_remaining > 0:
            FormationEnemy(offset, color, direction, speed, formation_enemies, enemy_aircrafts)
            level_enemies_remaining -= 1
            if level_enemies_remaining <= 0:
                return

def spawn_formation_pyramid(num_levels, right_side_up=True):
    global level_enemies_remaining
    global level
    # Spawn pyramid formation enemies periodically

    # Calculate the maximum allowed spawn center
    max_spawn_center = width - (num_levels - 1) * 80

    # Ensure spawn_center stays within valid range
    spawn_center = random.randint(max(120, (num_levels // 2) * 80), min(max_spawn_center, width - (num_levels // 2) * 80))

    direction = random.choice([-1, 0, 1])
    maxSpeed = 2
    if level >= 5:
        maxSpeed = 4
    if level >= 10:
        maxSpeed = 5
    
    speed = random.randint(2,maxSpeed)
    color = random.choice([YELLOW, GREEN, DEEP_SKY_BLUE, DEEP_PINK])

    # Calculate the offsets based on the number of levels and orientation
    formation_offsets = []
    for this_level in range(num_levels):
        color = random.choice([YELLOW, GREEN, DEEP_SKY_BLUE, DEEP_PINK])
        row_width = num_levels - this_level
        offset_y = (-40 * num_levels) + this_level * 40 if right_side_up else (-40 * this_level)
        for offset_x in range(spawn_center - (row_width // 2) * 80, spawn_center + (row_width // 2) * 80, 80):
            offset = (offset_x, offset_y), color
            formation_offsets.append(offset)
            

    formation_enemies = pygame.sprite.Group()
    for offset, color in formation_offsets:
        if level_enemies_remaining > 0:
            FormationEnemy(offset, color, direction, speed, formation_enemies, enemy_aircrafts)
            level_enemies_remaining -= 1
            if level_enemies_remaining <= 0:
                return

def spawn_formation_flying_v(formation_height, right_side_up=True):
    global level_enemies_remaining
    global level

    direction = random.choice([-1, 0, 1])
    maxSpeed = 2
    if level >= 5:
        maxSpeed = 4
    if level >= 10:
        maxSpeed = 5
    
    speed = random.randint(2,maxSpeed)
    color = random.choice([YELLOW, GREEN, DEEP_SKY_BLUE, DEEP_PINK])

    # Calculate the total height of the formation
    total_height = formation_height * 40

    # Calculate the starting y-coordinate to ensure the entire formation is off-screen
    start_y = -total_height if right_side_up else 0

    # Calculate the offsets based on the V-shaped pattern
    formation_offsets = []
    for row in range(formation_height):
        color = random.choice([YELLOW, GREEN, DEEP_SKY_BLUE, DEEP_PINK])
        offset_y = start_y + row * 40 if right_side_up else start_y - row * 40

        if row == 0:
            # Tip of the V should have only one enemy in the top row
            offset = (max(0, width // 2), offset_y)
            formation_offsets.append(offset)
        else:
            offset_left = (max(0, width // 2 - row * 40), offset_y)
            offset_right = (min(width, width // 2 + row * 40), offset_y)
            formation_offsets.extend([offset_left, offset_right])

    formation_enemies = pygame.sprite.Group()
    for offset in formation_offsets:
        if level_enemies_remaining > 0:
            FormationEnemy(offset, color, direction, speed, formation_enemies, enemy_aircrafts)
            level_enemies_remaining -= 1
            if level_enemies_remaining <= 0:
                return




def enemy_collide(self):
    global score
    global numKills

    # Check for collisions between formation enemies and bullets
    for collision in pygame.sprite.spritecollide(self, player_bullets, True):

        point_text = PointText(collision.rect.center, f"x",10)
        textShown.add(point_text)

        if self.shieldStrength > 0: # self.shield_up:
            kill_sound.play()
            self.shieldStrength -= 1 # self.shield_up = False
            
        else:
            # Handle the enemy being hit (destroy or respawn)
            # Create an explosion effect at the location of the enemy's death
            explosion = Explosion(self.rect.center,self.size*.8)
            explosions.add(explosion)

            point_text = PointText(self.rect.center, f"+{self.point_value}")
            textShown.add(point_text)

            # Increase the score when an enemy is destroyed
            score += self.point_value
            numKills += 1
            self.kill()
            kill_sound.play()
            return

    # Check for collisions between enemy aircrafts and explosions
    for collision in pygame.sprite.spritecollide(self, explosions, False):

        point_text = PointText(self.rect.center, f"x",10)
        textShown.add(point_text)

        if self.shieldStrength > 0: # self.shield_up:
            kill_sound.play()
            self.shieldStrength -= 1 # self.shield_up = False
            
        else:
            # Handle the enemy being hit (destroy or respawn)

            # Create an explosion effect at the location of the enemy's death
            explosion = Explosion(self.rect.center,self.size*.8)
            explosions.add(explosion)

            point_text = PointText(self.rect.center, f"+{self.point_value}")
            textShown.add(point_text)


            # Increase the score when an enemy is destroyed
            score += self.point_value
            numKills += 1
            self.kill()
            kill_sound.play()
            return

def get_scale(self):
    self.scale = [self.size, self.size*(self.size_ratio)]
    return self.scale

def shieldEffect(self):
    # Flash the shield outline when the shield is up
    if self.shieldStrength > 0 or self.angry:
        if self.flash_timer <= 0:
            if self.original_color == self.color:
                if self.angry: self.color = RED
                else: self.color = WHITE
                self.num_flashes += 1
                self.flash_timer = 2
                self.size = self.original_size + (self.original_size*.25) + self.shieldStrength*2
                self.image = pygame.transform.scale(self.image, get_scale(self))
                self.rect = self.image.get_rect(center=self.rect.center)
            else:
                self.color = self.original_color
                self.flash_timer = self.shield_flash_interval
                self.size = self.original_size + (self.original_size*.10) + self.shieldStrength*2
                self.image = pygame.transform.scale(self.image, get_scale(self))
                self.rect = self.image.get_rect(center=self.rect.center)
                 
        else:
            self.flash_timer -= 1
        self.image.fill(self.color)

    else: 
        self.size = self.original_size
        self.image = pygame.transform.scale(self.image, get_scale(self))
        self.rect = self.image.get_rect(center=self.rect.center)
        self.color = self.original_color
        self.image.fill(self.color)

# Define the player_death_and_respawn function outside the game loop
def player_death_and_respawn():
    global score
    global running
    global respawnCoolDown
    global wave_end_counter
    global level_enemies_remaining

    if running:
        player_death_sound.play()

        lostPoints = score - score_at_wave_start
        point_text = PointText(player_aircraft.rect.center, f"-{lostPoints}",120, 50, RED)
        textShown.add(point_text)

    # Perform actions for player death
    # For example, stop player movement, reset score, or display a game over message

    player_aircraft.lives -= 1
    if player_aircraft.lives <= 0:
        # Game over logic (you can customize this based on your requirements)
        running = False
        
    else:
        # Respawn the player at a random position or starting position
        player_aircraft.rect.x = width // 2
        player_aircraft.rect.y = height - player_aircraft.rect.height  # Set the initial y position as needed
        score = score_at_wave_start
        player_aircraft.blaster_dual = False
        player_aircraft.blaster_tri = False
        player_aircraft.blaster_quad = False
        player_aircraft.bullet_cooldown_time = 10
        player_aircraft.engineBoost = 0

        player_bullets.empty()
        player_bombs.empty()
        enemy_bullets.empty()
        enemy_aircrafts.empty()
        power_ups.empty()
        respawnCoolDown = 120

        wave_end_counter = 0
        level_enemies_remaining = 10*level + 20
        point_text = PointText((width//2,height//2), f"Get Ready",120, 50)
        textShown.add(point_text)



def enemy_movement(self):
    self.speed = min(self.speed, self.maxSpeed)
    # Check for collisions between enemy aircrafts and enemy aircrafts
    for enemy in pygame.sprite.spritecollide(self, enemy_aircrafts, False):

        if enemy != self:
            if self.rect.x - enemy.rect.x <= 1:
                ...
            elif self.rect.x < enemy.rect.x:
                self.direction_x = -1
                enemy.direction_x = 1
            elif self.rect.x > enemy.rect.x:
                self.direction_x = 1
                enemy.direction_x = -1
            
            # if self.rect.y < enemy.rect.y:
            #     self.move_upwards = True
            #     self.move_downwards = False
            #     enemy.move_upwards = False
            #     enemy.move_downwards = True

            # elif self.rect.y > enemy.rect.y:
            #     self.move_upwards = True
            #     self.move_downwards = False
            #     enemy.move_upwards = False
            #     enemy.move_downwards = True

  
            self.speed = max(self.speed, enemy.speed)
            enemy.speed = max(self.speed, enemy.speed)




    if self.move_downwards:
        self.rect.y += (max(1,self.speed*self.downSpeed)) * self.direction_y
        self.rect.x += self.speed * self.direction_x


    elif self.move_upwards:
        self.rect.y -= (max(1,self.speed)) * self.direction_y
        self.rect.x += self.speed * self.direction_x

    # If the enemy aircraft goes beyond 2/3 towards the bottom, switch movement direction
    if self.rect.y > (2 * height / 3):
        self.move_downwards = False
        self.move_upwards = True

    # If the enemy aircraft goes above the top, switch movement direction
    if self.rect.top < 0:
        self.move_downwards = True
        self.move_upwards = False

    # Check and adjust direction to stay within the horizontal bounds
    if self.rect.left < 0:
        self.rect.left = 0
        self.direction_x *= -1  # Move right
        # self.kill()
    elif self.rect.right > width:
        self.rect.right = width
        self.direction_x *= -1  # Move left
        # self.kill()


player_aircraft = Aircraft()
players = pygame.sprite.Group(player_aircraft)

# Create stars
num_stars = 75
stars = pygame.sprite.Group()

for _ in range(num_stars):
    rel_speed = random.uniform(0.5,1.5)
    star = Star(width, height, rel_speed)
    stars.add(star)

# Create bullets group
player_bullets = pygame.sprite.Group()
player_bombs = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
textShown = pygame.sprite.Group()
power_ups = pygame.sprite.Group()

# Create enemy aircraft group
enemy_aircrafts = pygame.sprite.Group()

explosions = pygame.sprite.Group()



# # Cooldown variables
# bullet_cooldown = 0
# bullet_cooldown_time = 5  # Adjust the cooldown time as needed (in frames)

respawnCoolDown = 60
respawnCoolDown_time = 60
specialCount = 0

level = 1
level_enemies_remaining = 10*level + 20
wave_end_counter = 0
wave_end_counter_end = 10



running = False
clock = pygame.time.Clock()
player_death_and_respawn()
running = True
while running:

    if player_aircraft.lives <= 0:
        # Game over logic (you can customize this based on your requirements)
        running = False

    for event in pygame.event.get():
        if event.type == QUIT:
            running = False


    if len(explosions.sprites()) == 0:
        if respawnCoolDown == 0:

            # Spawn power-ups periodically
            if numKills >= 10:
                if len(power_ups.sprites()) < 2:
                    if random.randint(0, 100) < 1:  # Adjust the frequency of enemy creation
                        power_up = PowerUp()
                        power_ups.add(power_up)
                        respawnCoolDown = respawnCoolDown_time
                
            specialCount = 0
            notSpecialCount = 0
            for enemy in enemy_aircrafts.sprites():
                if not isinstance(enemy, FormationEnemy):
                    specialCount += 1
                else: notSpecialCount += 1

            # if numKills <= 5: specialCount = 10 #?? is this best

            # Create new enemy aircraft at random intervals
            if len(enemy_aircrafts.sprites()) < 30:

                if level_enemies_remaining > 0:
                
                    enemyChoices = []
                    enemyChoices.append("formation")
                    

                    
                    

                    if specialCount < 5 and notSpecialCount >= 5:

                        if level >= 1: #if numKills >= 100:
                            ...

                        if level >= 3: #if numKills >= 100:
                            enemyChoices.append("falling")

                            
                        if level >= 4:
                            enemyChoices.append("fast")
                            
                        if level >= 5: #if numKills >= 100:
                            #enemyChoices.append("normal")
                            enemyChoices.append("hover")
                            

                        if level >= 6: #if numKills >= 150:
                            enemyChoices.append("special")

                        if level >= 7: #if numKills >= 200:
                            enemyChoices.append("growable")
                    
                    # Spawn special enemies periodically          
                    if random.randint(0, 100) < 10:  # Adjust the frequency of enemy creation
                        choice = random.choice(enemyChoices)

                        if choice == "normal":
                            enemy_aircraft = EnemyAircraft(random.randint(0, width - 40),-40  )# Start above the top of the screen)
                            enemy_aircrafts.add(enemy_aircraft)
                            level_enemies_remaining -= 1

                        elif choice == "fast":
                            fast_enemy = FastEnemy(start_from_left=random.choice([True, False]))
                            enemy_aircrafts.add(fast_enemy)
                            level_enemies_remaining -= 1

                        elif choice == "hover":
                            
                            hover_enemy = HoveringEnemy()
                            enemy_aircrafts.add(hover_enemy)
                            level_enemies_remaining -= 1
            

                        elif choice == "special":
                                special_enemy = SpecialEnemy()
                                enemy_aircrafts.add(special_enemy)
                                level_enemies_remaining -= 1

                        elif choice == "growable":
                                growable_enemy = GrowableEnemy()
                                enemy_aircrafts.add(growable_enemy)
                                level_enemies_remaining -= 1

                        elif choice == "falling":
                            falling_enemy = FallingEnemy()
                            enemy_aircrafts.add(falling_enemy)
                            level_enemies_remaining -= 1

                        elif choice == "formation":
                            # Spawn formation enemies periodically

                            gridA = random.randint(1,6)
                            b2 = min(14, max(2,level+1))
                            print(b2)
                            gridB = random.randint(2,b2) # no bigger than 14

                            gridX = min(gridA, gridB)
                            gridY = max(gridA, gridB)

                            shape = random.choice(["grid","pyramid", "v"])

                            if shape == "grid":
                                spawn_formation_grid(gridX,gridY)
                            elif shape == "pyramid":
                                pyramid_height = round(math.sqrt((gridX*gridY)))
                                spawn_formation_pyramid(pyramid_height, random.choice([True, False]))
                            elif shape == "v":
                                v_height = round(math.sqrt((gridX*gridY)))
                                spawn_formation_flying_v(v_height, random.choice([True, False]))


                            
                    
                        respawnCoolDown = respawnCoolDown_time

                else:

                    if level_enemies_remaining == 0 and len(enemy_aircrafts.sprites()) == 0:
                        if wave_end_counter == 0:
                            # point_text = PointText((width//2,height//2), f"Wave " +str(level) +" Completed ! *",120)
                            # textShown.add(point_text)
                            ...
                        
                        wave_end_counter += 1

                        if wave_end_counter >= wave_end_counter_end: 
                            if len(textShown.sprites()) == 0: 
                                wave_end_counter = 0
                                level += 1
                                score_at_wave_start = score
                                level_enemies_remaining = 10*level + 20
                                point_text = PointText((width//2,height//2), f"Wave " +str(level),120, 50, RED)
                                textShown.add(point_text)
                                level_sound.play()
                        
            

        # Reduce the cooldown time if it's greater than 0
        if respawnCoolDown > 0:
            respawnCoolDown -= 1
            


    stars.update(player_aircraft.current_speed)  # Update stars based on aircraft's y-axis speed
    players.update()
    power_ups.update() # Update power-ups
    enemy_aircrafts.update()  # Update enemy aircraft
    player_bullets.update()  # Update bullets
    player_bombs.update()
    enemy_bullets.update()  # Update bullets
    explosions.update()
    textShown.update()
    




    # Check for collisions between enemy aircrafts and bombs
    for enemy in pygame.sprite.groupcollide(enemy_aircrafts, player_bombs, True, True):
        # Handle the enemy being hit (destroy or respawn)

        # Create an explosion effect at the location of the enemy's death
        explosion = Explosion(enemy.rect.center, max(height+enemy.rect.y, width+enemy.rect.x),1, 20)
        explosions.add(explosion)

        point_text = PointText(enemy.rect.center, f"+{enemy.point_value}")
        textShown.add(point_text)


        # # For now, we'll just respawn the enemy at a random position
        # enemy.rect.x = random.randint(0, width - enemy.rect.width)
        # enemy.rect.y = -enemy.rect.height

        # Increase the score when an enemy is destroyed
        score += enemy.point_value
        numKills += 1
        

    # Check for collisions between explosions and bullets
    for enemy in pygame.sprite.groupcollide(explosions, enemy_bullets, False, True):
        # Handle the enemy being hit (destroy or respawn)
        # Destroy enemy bullets
        ...

        
    # Check for collisions between enemy aircrafts and player
    for enemy in pygame.sprite.spritecollide(player_aircraft, enemy_aircrafts, True):
        # Handle the enemy being hit (destroy or respawn)

        # Create an explosion effect at the location of the enemy's death
        explosion = Explosion(enemy.rect.center)
        explosions.add(explosion)

        # # For now, we'll just respawn the enemy at a random position
        # enemy.rect.x = random.randint(0, width - enemy.rect.width)
        # enemy.rect.y = -enemy.rect.height



        # Create an explosion effect at the location of the player_aircraft's death
        explosion = Explosion(player_aircraft.rect.center, 200)
        explosions.add(explosion)


        

        # Player collided with an enemy, handle player death and respawn
        player_death_and_respawn()



    # Check for collisions between player_aircraft and bullets
    for enemy in pygame.sprite.spritecollide(player_aircraft, enemy_bullets, True):
        # Handle the enemy being hit (destroy or respawn)

        point_text = PointText(enemy.rect.center, f"x",10)
        textShown.add(point_text)

        if player_aircraft.shieldStrength > 0: # self.shield_up:
            shield_sound.play()
            player_aircraft.shieldStrength -= 1 # self.shield_up = False
            player_aircraft.blaster_dual = False
            player_aircraft.blaster_tri = False
            player_aircraft.blaster_quad = False
            player_aircraft.bullet_cooldown_time = 10
            
        else:

            # Create an explosion effect at the location of the player_aircraft's death
            explosion = Explosion(player_aircraft.rect.center)
            explosions.add(explosion)


            # # For now, we'll just respawn the enemy at a random position
            # enemy.rect.x = random.randint(0, width - enemy.rect.width)
            # enemy.rect.y = -enemy.rect.height

            # Player collided with an enemy, handle player death and respawn
            player_death_and_respawn()



    # Check for a new high score
    if score > high_score:
        high_score = score




    screen.fill(BLACK)  # Set background color (black in this case)

    # Draw stars
    stars.draw(screen)

    
    enemy_bullets.draw(screen)  # Draw bullets
    player_bullets.draw(screen)  # Draw bullets
    player_bombs.draw(screen)
    enemy_aircrafts.draw(screen)  # Draw enemy aircraft
    
    power_ups.draw(screen)# Draw power-ups
    for power_up in power_ups:
        power_up.draw_type_text()

    explosions.draw(screen)
    players.draw(screen)
    textShown.draw(screen)
   

    # Draw speed bar
    speed_percentage = int((player_aircraft.current_speed / player_aircraft.max_speed) * 100)
    speed_bar_height = int((player_aircraft.current_speed / player_aircraft.max_speed) * 200)  # Adjust the maximum height of the bar
    speed_bar_max = int((player_aircraft.max_speed / player_aircraft.max_speed) * 200)  # Adjust the maximum height of the bar
    speed_bar_rect = pygame.Rect(width - 30, height - 20 - speed_bar_height, 20, speed_bar_height)
    speed_bar_max_rect = pygame.Rect(width - 30, height - 20 - speed_bar_max, 20, speed_bar_max)
    pygame.draw.rect(screen, GREEN, speed_bar_rect)
    pygame.draw.rect(screen, GREEN, speed_bar_max_rect,1)

    
    # Draw score indicator in the top left part of the screen
    font = pygame.font.Font(None, 36)
    score_text = font.render(f"Score: {score}  High Score: {high_score}", True, WHITE)  # White color for text
    screen.blit(score_text, (10, 10))

    # Draw remaining lives in the top right corner
    font = pygame.font.Font(None, 36)
    lives_text = font.render(f"Lives: {player_aircraft.lives}", True, WHITE)
    screen.blit(lives_text, (width - lives_text.get_width() - 10, 10))

    # Draw numKills display in the top right corner
    font = pygame.font.Font(None, 36)
    num_kills_text = font.render(f"Wave: {level}  Kills: {numKills}", True, WHITE)  # White color for text
    screen.blit(num_kills_text, (width - num_kills_text.get_width() - 10, 50))


    # Draw bomb indicator
    font = pygame.font.Font(None, 36)
    bomb_text = font.render(f"Bombs: {player_aircraft.num_bombs}", True, WHITE)
    screen.blit(bomb_text, (width - bomb_text.get_width() - 10, height // 2 + 50))

    # Draw the weapon indicator
    font = pygame.font.Font(None, 36)
    blaster_text = "Standard "
    if player_aircraft.blaster_quad: blaster_text = "Quad Mode "
    elif player_aircraft.blaster_tri: blaster_text = "Tri Mode "
    elif player_aircraft.blaster_dual: blaster_text = "Dual Mode "

    if (10 - player_aircraft.bullet_cooldown_time) != 0:
        blaster_text += str((10 - player_aircraft.bullet_cooldown_time)//2)

    weapon_text = font.render("Blaster: " + (blaster_text), True, WHITE)
    screen.blit(weapon_text, (width - weapon_text.get_width() - 10, height // 2 - weapon_text.get_height() // 2))

    # Draw speed text
    speed_text = font.render(f"Speed: {speed_percentage}%", True, WHITE)  # White color for text
    screen.blit(speed_text, (width - 150, height - 50))


    pygame.display.flip()
    clock.tick(30)  # Adjust the frame rate as needed

# Write the high score to a file
with open('high_score.txt', 'w') as file:
    file.write(str(high_score))

print("Thank-You For Playing!")
pygame.quit()
