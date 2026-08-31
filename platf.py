import pygame
import sys


pygame.init()

clock = pygame.time.Clock()
fps = 60

#screen initialization
screen_width = 1280
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Platformer")

#graphics
sun_img = pygame.image.load("images/sun.png")
sky_img = pygame.image.load("images/sky.png")
dirt_img = pygame.image.load("images/dirt.png")
grass_img = pygame.image.load("images/grass.png")
player_img = pygame.image.load("images/player_standing.png")
player_crouch_img = pygame.image.load("images/player_crouching.png")
star_img = pygame.image.load("images/star.png")
enemy_img = pygame.image.load("images/enemy.png")
menu_img = pygame.transform.scale(pygame.image.load("images/menu_bg.png"), (1280, 720))


tile_size = 40
tile_img_dict = {
    1: dirt_img,
    2: grass_img,
    4: star_img
}
tile_size_dict = {
    0: (40, 40),
    1: (40, 20),
    2: (20, 20)
}

#map loader
def load_map(filename):
    with open(filename) as f:
        data = f.readlines()
    world_data = []
    for line in data:
        world_data.append([int(x) for x in line.strip().split()])
    return world_data

map1 = load_map("maps/map1.txt")
map2 = load_map("maps/map2.txt")
maps = [map1, map2]
current_map_index = 0

#draw text
def draw_text(text, size, color, surface, x, y):
    font = pygame.font.SysFont(None, size)
    textobj = font.render(text, 1, color)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

#game reset
def game_reset():
    player.rect.x , player.rect.y = 100, screen_height - 80
    player.dx, player.dy = 0, 0
    player.health = 100
    player.actions = ActionState()
    player.movement = MovementState()

class ActionState():
    def __init__(self):
        self.jumped = False
        self.dashed = [False, 0]
        self.double_jumped = [False, 0]
        self.hit = [False, 0]
        self.crouch_input = False
        self.crouching = False
    

class MovementState():
    def __init__(self):
        self.velocity_x = 0
        self.dashing_velocity = 0
        self.velocity_y = 0
        self.knockback = 0
        self.direction = {
            "walking_direction" : "",
            "facing_direction" : "right"
        }

#player class
class Player():
    def __init__(self, x, y):
        self.image = player_img
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.health = 100
        self.actions = ActionState()
        self.movement = MovementState()

    #update coordinates + check for collision
    def y_collision(self, level, dy):
            self.rect.y += dy
            for _, tile_rect in level.tile_list:
                if self.rect.colliderect(tile_rect):
                    if self.movement.velocity_y > 0:
                        self.rect.bottom = tile_rect.top
                        self.actions.jumped = False 
                        self.movement.velocity_y = 0
                    elif self.movement.velocity_y < 0:
                        self.rect.top = tile_rect.bottom 
                        self.movement.velocity_y = 0

    def x_collision(self, level, dx):
            self.rect.x += dx
            for _, tile_rect in level.tile_list:
                if self.rect.colliderect(tile_rect):
                    if dx > 0:
                        self.rect.right = tile_rect.left
                    elif dx < 0:
                        self.rect.left = tile_rect.right
    
    def crouch_resize_collision(self, level):
        temp_standing_rect  = player_img.get_rect()
        temp_standing_rect.midbottom = self.rect.midbottom
        for _, tile_rect in level.tile_list:
            if temp_standing_rect.colliderect(tile_rect):
                return True
        return False

    def border_collision(self, level):
        if self.rect.x <= 0:
            self.rect.x = 0
        if self.rect.right >= screen_width:
            self.rect.right = screen_width

        if self.rect.y <= 0:
            self.rect.y = 0
        if self.rect.bottom >= screen_height:
            self.rect.bottom = screen_height
        
    def dash(self, horizontal_direction):
        if horizontal_direction == "right":
            self.movement.dashing_velocity = 20
        elif horizontal_direction == "left":
            self.movement.dashing_velocity = -20
        self.actions.dashed = [True, pygame.time.get_ticks()]

    def deceleration(self, velocity):
        if velocity > 0:
            velocity -= 1
        elif velocity < 0:
            velocity += 1
        return velocity
    
    def get_keypress(self):
        key = pygame.key.get_pressed()
        self.movement.direction["walking_direction"] = []

        if key[pygame.K_SPACE] and self.actions.jumped == False and self.movement.velocity_y <= 0:
            self.movement.velocity_y = -15
            self.actions.jumped = True
        if key[pygame.K_a]:
            self.movement.velocity_x = -5
            self.movement.direction["walking_direction"] = "left"
            self.movement.direction["facing_direction"] = "left"
        if key[pygame.K_d]:
            self.movement.velocity_x = 5
            self.movement.direction["walking_direction"] = "right"
            self.movement.direction["facing_direction"] = "right"
        if key[pygame.K_q] and self.actions.dashed[0] == False and self.movement.direction["walking_direction"]:
            self.dash(self.movement.direction["walking_direction"])
        self.actions.crouch_input = key[pygame.K_LSHIFT]    

    
    #enemy collision
    def enemy_collision(self, enemy_group):
        for enemy in enemy_group:
            if self.rect.colliderect(enemy.rect) and self.actions.hit[0] == False:
                self.movement.dashing_velocity = 0
                print("hit")
                self.health -= 20
                self.actions.hit = [True, pygame.time.get_ticks()]
                if self.movement.direction["facing_direction"] == "right":
                    self.movement.knockback = -20
                else:
                    self.movement.knockback = 20
                if self.actions.jumped == True:
                    if self.movement.direction["facing_direction"] == "right":
                        self.movement.knockback = -20
                    else:
                        self.movement.knockback = 20

    #draw health bar
    def health_bar(self):
        pygame.draw.rect(screen, "red", (50, 50, 100, 10))
        pygame.draw.rect(screen, "green", (50, 50, self.health, 10))
        draw_text(f"Health = {self.health}", 20, "white", screen, 60, 60)       
    
    def update(self, level):

        self.health_bar()
            
        dx = 0
        dy = 0

        self.get_keypress()
        if self.actions.dashed[0] == True and pygame.time.get_ticks() - self.actions.dashed[1] >= 1000:
            self.actions.dashed[0] = False
        if self.actions.hit[0] == True and pygame.time.get_ticks() - self.actions.hit[1] >= 1000:
            self.actions.hit[0] = False

        if self.actions.crouch_input:
            self.actions.crouching = True
        else:
            if self.actions.crouching == True:
                if self.crouch_resize_collision(level) == False:
                    self.actions.crouching = False

        #gravity
        self.movement.velocity_y += 1
        dy = self.movement.velocity_y 

        #horizontal velocity
        self.movement.velocity_x = self.deceleration(self.movement.velocity_x)
        self.movement.dashing_velocity = self.deceleration(self.movement.dashing_velocity)
        self.movement.knockback = self.deceleration(self.movement.knockback)
        dx = self.movement.velocity_x + self.movement.dashing_velocity + self.movement.knockback

        #call collision
        self.y_collision(level, dy)
        self.x_collision(level, dx)
        self.border_collision(level)

        #interactions
        self.enemy_collision(enemy_group)

        #draw player 
        pos = self.rect.midbottom  
        if self.actions.crouching:
            self.image = player_crouch_img
        else:
            self.image = player_img
        self.rect = self.image.get_rect(midbottom = pos)
        screen.blit(self.image, self.rect)

#player loading
player = Player(100, screen_height - 80)

#enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = enemy_img
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 0.5
        if self.move_counter > 30:
            self.move_direction *= -1
            self.move_counter = 0

enemy_group = pygame.sprite.Group()

#world class
class World():
    def __init__(self, data):
        self.tile_list = []
        self.goal = 0

        #map file interpreter
        for line_index, line in enumerate(data):
            for cell_index, cell in enumerate(line):
                if cell == 30:
                    enemy = Enemy(cell_index * tile_size, line_index * tile_size)
                    enemy_group.add(enemy)

                elif cell != 0:
                    img_type = cell//10
                    size = cell%10
                    img = tile_img_dict[img_type]
                    img = pygame.transform.scale(img, tile_size_dict[size])
                    img_rect = img.get_rect()
                    img_rect.x = cell_index * tile_size
                    img_rect.y = line_index * tile_size
                    tile = (img, img_rect)
                    if cell == 40:
                        self.goal = tile
                    else:
                        self.tile_list.append(tile)

    def draw(self):
        for tile in self.tile_list:
            screen.blit(*tile)
        screen.blit(*self.goal)
    
    def next_level(self):
        if player.rect.colliderect(self.goal[1]):
            return True

def main_menu():
    click = False
    while True:

        clock.tick(fps)

        screen.blit(menu_img, (0, 0))
        draw_text("Main Menu", 60, "white", screen, 535, 240)

        mx, my = pygame.mouse.get_pos()

        game_button = pygame.Rect(545, 300, 200, 50)

        if game_button.collidepoint((mx, my)):
            if click:
                return "start"

        
        pygame.draw.rect(screen, "red", game_button)
        draw_text("Play game", 40, "white", screen, 580, 310)

        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True
        
        pygame.display.update()
    
def game_over_screen():
    click = False
    while True:
        clock.tick(fps)

        draw_text("Game Over", 60, "white", screen, 530, 240)
    
        mx, my = pygame.mouse.get_pos()

        try_again_button = pygame.Rect(545, 300, 200, 50)
        quit_to_menu_button = pygame.Rect(545, 400, 200, 50)

        if try_again_button.collidepoint((mx, my)):
            if click:
                return "try_again"

        if quit_to_menu_button.collidepoint((mx, my)):
            if click:
                return "menu"
        
        pygame.draw.rect(screen, "red", try_again_button)
        draw_text("Try again?", 40, "white", screen, 580, 310)

        pygame.draw.rect(screen, "red", quit_to_menu_button)
        draw_text("Quit to main menu?", 30, "white", screen, 548, 414)

        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True
        pygame.display.update()

def next_level_screen():
    click = False
    global current_map_index
    while True:
        clock.tick(fps)

        mx, my = pygame.mouse.get_pos()
        
        next_level_button = pygame.Rect(545, 300, 200, 50)
        quit_to_menu_button = pygame.Rect(545, 400, 200, 50)

        if current_map_index == 0:
            draw_text("Level complete", 60, "white", screen, 510, 240)


            pygame.draw.rect(screen, "red", next_level_button)
            draw_text("Next level?", 40, "white", screen, 570, 310)

            if next_level_button.collidepoint((mx, my)):
                if click:
                    return "next"
        else:
            draw_text("Final level completed", 60, "red", screen, 450, 240)

        pygame.draw.rect(screen, "red", quit_to_menu_button)
        draw_text("Quit to main menu?", 30, "white", screen, 548, 414)

        if quit_to_menu_button.collidepoint((mx, my)):
            if click:
                return "menu"
                
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True

        pygame.display.update()

def run_game():
    global current_map_index

    current_map_index = 0

    while True:
        enemy_group.empty()
        level = World(maps[current_map_index])
        game_reset()

        result = main_game_loop(level)

        if result == "game_over":
            action = game_over_screen()
            if action == "try_again":
                continue
            elif action == "quit":
                return
            elif action == "menu":
                return
        
        if result == "level_complete":
            action = next_level_screen()
            if action == "next":
                if current_map_index < 1:
                    current_map_index += 1
                continue
            elif action == "menu":
                return
            
        if result == "quit":
            return

def main_game_loop(level):
    running = True
    while running:

        clock.tick(fps)

        #background
        screen.blit(sky_img, (0, 0))
        screen.blit(sun_img, (100, 100))

        #map
        level.draw()

        #enemy
        enemy_group.update()
        enemy_group.draw(screen)

        #player
        player.update(level)

        if player.health <= 0:
            return "game_over"

        if level.next_level():
            return "level_complete"
    
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"
        
        pygame.display.update()

while True:
    menu_result = main_menu()
    
    if menu_result == "start":
        run_game()

    if menu_result == "quit":
        pygame.quit()
        sys.exit()
