import pygame
import math
import socket
import threading
import sys

WIDTH, HEIGHT = 800, 600
FPS = 60
DT = 1 / FPS
FRICTION = 2
MIN_SPEED = 0.1
BALL_RADIUS = 15
PLAYER_RADIUS = 35

TEAM1_COLOR = (255, 0, 0)
TEAM2_COLOR = (0, 0, 255)
BALL_COLOR = (255, 255, 255)

GOAL_AREA_WIDTH = 150
GOAL_AREA_HEIGHT = 200



# Placeholder functions for server interaction
def send_join_request(name, join_code):
    print(f"Sending join request for {name} with join code {join_code}...")
    return True  # Simulate successful join request

class Circle:
    def __init__(self, id, x, y, radius, mass, color, image_path, is_ball=False):
        self.initial_x = x
        self.initial_y = y
        self.x = x
        self.y = y
        self.radius = radius
        self.mass = mass
        self.color = color
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (2 * radius, 2 * radius))
        self.vx = 0
        self.vy = 0
        self.dragging = False
        self.is_ball = is_ball
        self.id = id

    def reset_position(self):
        self.x = self.initial_x
        self.y = self.initial_y
        self.vx = 0
        self.vy = 0

    def update_position(self):
        if not self.dragging or self.is_ball:
            self.x += self.vx * DT
            self.y += self.vy * DT

            speed = math.sqrt(self.vx**2 + self.vy**2)
            if speed != 0:
                friction_force = FRICTION * self.mass * DT / speed
                self.vx -= (friction_force * self.vx)
                self.vy -= (friction_force * self.vy)

            if math.sqrt(self.vx**2 + self.vy**2) < MIN_SPEED:
                self.vx = 0
                self.vy = 0

    def check_wall_collision(self):
        if self.is_ball:
            if ((self.x - self.radius < 50) and ((self.y - self.radius < 247 or self.y - self.radius > 408))) or ((self.x + self.radius > WIDTH - 50) and ((self.y - self.radius < 247 or self.y - self.radius > 408))):
                self.vx = -self.vx
            if self.y - self.radius < 54 or self.y + self.radius > HEIGHT - 10:
                self.vy = -self.vy
        else:
            if (self.x - self.radius < 50) or (self.x + self.radius > WIDTH - 50):
                self.vx = -self.vx
            if self.y - self.radius < 54 or self.y + self.radius > HEIGHT - 10:
                self.vy = -self.vy

    def check_circle_collision(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance < self.radius + other.radius:
            angle = math.atan2(dy, dx)
            total_mass = self.mass + other.mass

            v1_rot = [self.vx * math.cos(angle) + self.vy * math.sin(angle),
                      -self.vx * math.sin(angle) + self.vy * math.cos(angle)]
            v2_rot = [other.vx * math.cos(angle) + other.vy * math.sin(angle),
                      -other.vx * math.sin(angle) + other.vy * math.cos(angle)]

            v1_rot_prime = [(v1_rot[0] * (self.mass - other.mass) + 2 * other.mass * v2_rot[0]) / total_mass,
                            v1_rot[1]]
            v2_rot_prime = [(v2_rot[0] * (other.mass - self.mass) + 2 * self.mass * v1_rot[0]) / total_mass,
                            v2_rot[1]]

            self.vx = v1_rot_prime[0] * math.cos(angle) - v1_rot_prime[1] * math.sin(angle)
            self.vy = v1_rot_prime[0] * math.sin(angle) + v1_rot_prime[1] * math.cos(angle)
            other.vx = v2_rot_prime[0] * math.cos(angle) - v2_rot_prime[1] * math.sin(angle)
            other.vy = v2_rot_prime[0] * math.sin(angle) + v2_rot_prime[1] * math.cos(angle)

            overlap = 0.5 * (self.radius + other.radius - distance + 1)
            self.x -= overlap * math.cos(angle)
            self.y -= overlap * math.sin(angle)
            other.x += overlap * math.cos(angle)
            other.y += overlap * math.sin(angle)

    def draw(self, screen):
        screen.blit(self.image, (self.x - self.radius, self.y - self.radius))
        if self.dragging:
            pygame.draw.line(screen, (0, 0, 0), (self.x, self.y), pygame.mouse.get_pos(), 2)

class Goalkeeper(Circle):
    def __init__(self, id, x, y, radius, mass, color, goal_area, image_path):
        super().__init__(id, x, y, radius, mass, color, image_path)
        self.goal_area = goal_area
        self.initial_x = x
        self.initial_y = y

    def update_position(self):
        super().update_position()
        if not self.goal_area.collidepoint(self.x, self.y):
            speed = math.sqrt(self.vx**2 + self.vy**2)
            if speed <= 1:
                self.x = self.initial_x
                self.y = self.initial_y

class Defender(Circle):
    def __init__(self, id, x, y, color, image_path):
        super().__init__(id, x, y, PLAYER_RADIUS + 6, 60, color, image_path)

class Forward(Circle):
    def __init__(self, id, x, y, color, image_path):
        super().__init__(id, x, y, PLAYER_RADIUS, 40, color, image_path)
        self.strike_power = 1.5

class SoccerStarsGame:
    def __init__(self, playerNumber, username, joinCode, server_ip, server_port):
        self.init_screen()

        self.selected_circle = None
        self.start_pos = None
        self.turn = 0
        self.last_turn_time = pygame.time.get_ticks()

        self.team1_score = 0
        self.team2_score = 0
        self.goal_scored = False
        self.goal_scored_time = 0
        self.connected = False
        self.playerNumber = playerNumber
        self.turnPlayer = 0
        self.running = False

        self.socket = None
        self.server_ip = server_ip
        self.server_port = server_port
        self.username1 = ""
        self.username2 = ""
        self.elapsed_time = 0

        self.init_server_connection()
        if(playerNumber == 1):
            self.username1 = username
            self.send_command("START_GAME", [username])
        else:
            self.username2 = username
            self.send_command("JOIN_GAME", [username, joinCode])

    def init_screen(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Soccer Stars")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 55)
        self.small_font = pygame.font.SysFont(None, 40)

        self.field_image = pygame.image.load("field3.png").convert()

        self.team1_goal_area = pygame.Rect(0, (HEIGHT - GOAL_AREA_HEIGHT) // 2, GOAL_AREA_WIDTH, GOAL_AREA_HEIGHT)
        self.team2_goal_area = pygame.Rect(WIDTH - GOAL_AREA_WIDTH, (HEIGHT - GOAL_AREA_HEIGHT) // 2, GOAL_AREA_WIDTH, GOAL_AREA_HEIGHT)

        self.team1 = [
            Goalkeeper(11, 100, 328, PLAYER_RADIUS, 50, TEAM1_COLOR, self.team1_goal_area, "player1.png"),
            Defender(12, 150, 228, TEAM1_COLOR, "player1.png"),
            Defender(13, 150, 458, TEAM1_COLOR, "player1.png"),
            Forward(14, 320, 328, TEAM1_COLOR, "player1.png"),
            Forward(15, 200, 128, TEAM1_COLOR, "player1.png"),
            Forward(16, 200, 528, TEAM1_COLOR, "player1.png")
        ]

        self.team2 = [
            Goalkeeper(21, 700, 328, PLAYER_RADIUS, 50, TEAM2_COLOR, self.team2_goal_area, "player2.png"),
            Defender(22, 650, 228, TEAM2_COLOR, "player2.png"),
            Defender(23, 650, 428, TEAM2_COLOR, "player2.png"),
            Forward(24, 485, 328, TEAM2_COLOR, "player2.png"),
            Forward(25, 600, 128, TEAM2_COLOR, "player2.png"),
            Forward(26, 600, 528, TEAM2_COLOR, "player2.png")
        ]

        self.ball = Circle(0, WIDTH // 2, HEIGHT // 2 + 28, BALL_RADIUS, 20, BALL_COLOR, "ball.png", is_ball=True)
        self.circles = self.team1 + self.team2 + [self.ball]

    def init_server_connection(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))

            thread = threading.Thread(target=self.receive_data)
            thread.start()
        except socket.error as e:
            print(f"Socket error: {e}")
            self.connected = False

    def receive_data(self):
        while True:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                lines = message.split('\r\n')
                for line in lines:
                    if(len(line) > 0):
                        self.process_line(line)
            except socket.error as e:
                print(f"Socket error: {e}")
                self.connected = False  # Mark the client as disconnected
                break

    def process_line(self, line):
        print("Recieved: '" + line + "'")
        params = line.split(',')
        command = params[0]

        if(command == "WAITING_FOR_OTHER_PLAYER"):
            self.showOpponentPage(params[1])
        elif(command == "JOIN_NUMBER_IS_INCORRECT"):
            print("Join number is incorrect")
            self.running = False
            quit()
        elif(command == "GAME_STARTED"):
            self.username1 = params[1] + ("[me]" if self.playerNumber == 1 else "")
            self.username2 = params[2] + ("[me]" if self.playerNumber == 2 else "")
        elif(command == "TURN_PLAYER_1" or command == "TURN_PLAYER_2"):
            self.turnPlayer = int(command[12])
            self.turn = self.turnPlayer-1
            if(not self.running):
                self.closeOpponentPage()
                self.init_screen()
                thread = threading.Thread(target=self.run)
                thread.start()
        elif(command == "MOVE"):
            self.move(int(params[1]), int(params[2]), int(params[3]))
        elif(command == "ELAPSED_TIME"):
            self.elapsed_time = int(params[1])
        elif(command == "SCORES"):
            self.team1_score = int(params[1])
            self.team2_score = int(params[2])
      
    def onStoppedCircle(self, circleId):
        self.send_command("NOT_GOAL", [])

    def send_move_command(self, circleId, vx, vy):
        self.send_command("MOVE", [str(circleId), str(vx), str(vy)])
    
    def send_command(self, command, params):
        try:
            line = f"{command},{','.join(params)}"
            print("Sent: " + line)
            self.socket.sendall(line.encode('utf-8'))
        except socket.error as e:
            print(f"Socket error: {e}")

    def showOpponentPage(self, joinCode):
        # while not self.connected:
        self.screen.fill((30, 30, 30))
        waiting_text = self.font.render("Waiting for opponent... [Join Code: " + joinCode + "]", True, (255, 255, 255))
        self.screen.blit(waiting_text, (WIDTH // 2 - waiting_text.get_width() // 2, HEIGHT // 2 - waiting_text.get_height() // 2))
        pygame.display.flip()
        pygame.time.delay(100)

    def closeOpponentPage(self):
        pygame.quit()

    def run(self):
        self.running = True
        while self.running:
            self.running = self.handle_events()
            self.update_game_state()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif self.playerNumber == self.turnPlayer:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.select_circle(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.release_circle(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.drag_circle(event.pos)
        return True

    def select_circle(self, pos):
        for circle in (self.team1 if self.turn == 0 else self.team2):
            if math.sqrt((circle.x - pos[0]) ** 2 + (circle.y - pos[1]) ** 2) < circle.radius:
                self.selected_circle = circle
                self.selected_circle.dragging = True
                self.start_pos = pos
                break

    def move(self, circleId, vx, vy):
        circle = None
        for c in self.circles:
            if(c.id == circleId):
                circle = c
        if circle != None:
            circle.vx = vx
            circle.vy = vy
            circle.dragging = False

    def release_circle(self, pos):
        if self.selected_circle is not None:
            self.selected_circle.dragging = False
            dx = pos[0] - self.start_pos[0]
            dy = pos[1] - self.start_pos[1]
            power = 1.0
            if isinstance(self.selected_circle, Forward):
                power = self.selected_circle.strike_power
            # self.selected_circle.vx = -dx * power
            # self.selected_circle.vy = -dy * power
            self.send_move_command(self.selected_circle.id, -dx * power, -dy * power)
            self.selected_circle = None
            self.turn = 1 - self.turn
            self.last_turn_time = pygame.time.get_ticks()
        
    def drag_circle(self, pos):
        if self.selected_circle is not None:
            end_pos = pos

    def update_game_state(self):
        for circle in self.circles:
            circle.update_position()
            circle.check_wall_collision()
            for other in self.circles:
                if circle != other:
                    circle.check_circle_collision(other)
        self.check_goal()
        if self.goal_scored:
            self.handle_goal()

    def check_goal(self):
        if not self.goal_scored:
            if 250 < self.ball.y < 400 and self.ball.x - self.ball.radius <= 45:
                self.goal_scored = True
                self.send_command("GOAL", ["2"])
            elif 250 < self.ball.y < 400 and self.ball.x + self.ball.radius >= WIDTH - 45:
                self.goal_scored = True
                self.send_command("GOAL", ["1"])

    def handle_goal(self):
        if pygame.time.get_ticks() - self.goal_scored_time > 1000:
            for circle in self.team1 + self.team2:
                circle.reset_position()
            self.reset_ball()
            self.goal_scored = False

    def reset_ball(self):
        self.ball = Circle(0, WIDTH // 2, HEIGHT // 2 + 28, BALL_RADIUS, 20, BALL_COLOR, "ball.png", is_ball=True)
        self.circles = self.team1 + self.team2 + [self.ball]

    def draw(self):
        self.screen.blit(self.field_image, (0, 0))
        self.draw_score()
        turn_text = self.font.render(f"Turn: {self.username1 if self.turn == 0 else self.username2}", True, (255, 255, 255))
        self.screen.blit(turn_text, (WIDTH // 2 - turn_text.get_width() // 2, 60))
        for circle in self.circles:
            circle.draw(self.screen)
        
        # Display remaining time
        timer_text = self.small_font.render(f"Time left: {int(self.elapsed_time)}", True, (0, 0, 0))
        self.screen.blit(timer_text, (WIDTH // 2 - timer_text.get_width() // 2, 10))

        pygame.display.flip()

    def draw_score(self):
        score_text = self.font.render(f"{self.username1}: {self.team1_score}                            {self.username2}: {self.team2_score}", True, (255, 255, 255))
        self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 10))

        # End game if score reaches 3
        if self.team1_score == 3 or self.team2_score == 3:
            game_over_text = self.font.render("Game Over!", True, (255, 0, 0))
            self.screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
            pygame.time.delay(3000)
            pygame.quit()
            quit()

def get_username(screen, font, user_data):
    input_box = pygame.Rect(WIDTH // 4, HEIGHT // 2, WIDTH // 2, 50)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

        screen.fill((30, 30, 30))
        txt_surface = font.render(text, True, color)
        width = max(200, txt_surface.get_width() + 10)
        input_box.w = width
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(screen, color, input_box, 2)

        # Draw label
        label_surface = font.render("Enter your username:", True, (255, 255, 255))
        screen.blit(label_surface, (input_box.x, input_box.y - 30))

        pygame.display.flip()

    user_data['username'] = text
    return text

def get_join_info(screen, font):
    input_box1 = pygame.Rect(WIDTH // 4, HEIGHT // 2 - 60, WIDTH // 2, 50)
    input_box2 = pygame.Rect(WIDTH // 4, HEIGHT // 2 + 30, WIDTH // 2, 50)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active1 = False
    active2 = False
    text1 = ''
    text2 = ''
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box1.collidepoint(event.pos):
                    active1 = not active1
                else:
                    active1 = False
                if input_box2.collidepoint(event.pos):
                    active2 = not active2
                else:
                    active2 = False
                color = color_active if (active1 or active2) else color_inactive
            if event.type == pygame.KEYDOWN:
                if active1:
                    if event.key == pygame.K_RETURN:
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        text1 = text1[:-1]
                    else:
                        text1 += event.unicode
                if active2:
                    if event.key == pygame.K_RETURN:
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        text2 = text2[:-1]
                    else:
                        text2 += event.unicode

        screen.fill((30, 30, 30))
        txt_surface1 = font.render(text1, True, color)
        width1 = max(200, txt_surface1.get_width() + 10)
        input_box1.w = width1
        screen.blit(txt_surface1, (input_box1.x + 5, input_box1.y + 5))
        pygame.draw.rect(screen, color, input_box1, 2)

        txt_surface2 = font.render(text2, True, color)
        width2 = max(200, txt_surface2.get_width() + 10)
        input_box2.w = width2
        screen.blit(txt_surface2, (input_box2.x + 5, input_box2.y + 5))
        pygame.draw.rect(screen, color, input_box2, 2)

        # Draw labels
        label_surface1 = font.render("Enter your username:", True, (255, 255, 255))
        screen.blit(label_surface1, (input_box1.x, input_box1.y - 30))
        label_surface2 = font.render("Enter join code:", True, (255, 255, 255))
        screen.blit(label_surface2, (input_box2.x, input_box2.y - 30))

        pygame.display.flip()

    return text1, text2

def main_menu(screen, font):
    menu_text = font.render("Soccer Stars", True, (255, 255, 255))
    create_game_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50)
    join_game_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 50)

    menu = True
    while menu:
        screen.fill((30, 30, 30))
        screen.blit(menu_text, (WIDTH // 2 - menu_text.get_width() // 2, HEIGHT // 4))

        pygame.draw.rect(screen, (0, 128, 0), create_game_rect, border_radius=10)
        pygame.draw.rect(screen, (0, 128, 0), join_game_rect, border_radius=10)

        create_game_text = font.render("Create Game", True, (255, 255, 255))
        join_game_text = font.render("Join Game", True, (255, 255, 255))
        screen.blit(create_game_text, (create_game_rect.x + (create_game_rect.width - create_game_text.get_width()) // 2, create_game_rect.y + (create_game_rect.height - create_game_text.get_height()) // 2))
        screen.blit(join_game_text, (join_game_rect.x + (join_game_rect.width - join_game_text.get_width()) // 2, join_game_rect.y + (join_game_rect.height - join_game_text.get_height()) // 2))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if create_game_rect.collidepoint(event.pos):
                    return "create"
                elif join_game_rect.collidepoint(event.pos):
                    return "join"

def main():
    if(len(sys.argv) < 2):
        print("python3 ./game.py <port>")
        quit()
        return

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Soccer Stars")
    font = pygame.font.SysFont(None, 55)

    user_data = {}

    serverIp = "0.0.0.0"
    serverPort = int(sys.argv[1])

    option = main_menu(screen, font)
    if option == "create":
        username = get_username(screen, font, user_data)
        print(f"Username stored: {username}")
        game = SoccerStarsGame(1, username, 0, serverIp, serverPort)
    elif option == "join":
        username, join_code = get_join_info(screen, font)
        print(f"Username stored: {username}")
        game = SoccerStarsGame(2, username, join_code, serverIp, serverPort)

if __name__ == "__main__":
    main()