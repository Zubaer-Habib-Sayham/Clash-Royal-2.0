from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import math
import time
import random

camera_mode = "OVERVIEW"  # OVERVIEW, FIRST_PERSON_PLAYER, FIRST_PERSON_ENEMY
camera_pos = [0, -1550, 1000]
camera_rotation = 0
camera_zoom = 1.0

paused = False
game_speed = 1.0
speed_display = 1.0
game_over = False
winner = None

fovY = 60
GRID_LENGTH = 800  
grid_size = 20       
tile_size = 100 

# Player elixir
player_elixir = 1.0
last_player_elixir_time = time.time()

# Enemy elixir
enemy_elixir = 1.0
last_enemy_elixir_time = time.time()
last_enemy_deploy_time = time.time()

# Tower positions
PLAYER_KING_TOWER_POS = [0, -700, 0]
PLAYER_LEFT_PRINCESS_POS = [-150, -650, 0]
PLAYER_RIGHT_PRINCESS_POS = [150, -650, 0]

ENEMY_KING_TOWER_POS = [0, 700, 0]
ENEMY_LEFT_PRINCESS_POS = [-150, 650, 0]
ENEMY_RIGHT_PRINCESS_POS = [150, 650, 0]

# Tower HP
player_king_hp = 1500
player_left_princess_hp = 800
player_right_princess_hp = 800

enemy_king_hp = 1500
enemy_left_princess_hp = 800
enemy_right_princess_hp = 800

# Troop Buttons
TROOP_BUTTONS = [
    [85, 50, 120, 70, "GOBLIN", 1],
    [255, 50, 120, 70, "ARCHER", 2],
    [425, 50, 120, 70, "KNIGHT", 3],
    [595, 50, 120, 70, "GIANT", 5]
]

deploy_position = "left"
enemy_deploy_position = "left"

TROOP_TYPES = {
    "GOBLIN": {"cost": 1, "hp": 120, "damage": 30, "speed": 1.5, "size": 40, "color": (0.0, 0.6, 0.0), "shoot_range": 280},
    "ARCHER": {"cost": 2, "hp": 200, "damage": 40, "speed": 1.0, "size": 60, "color": (1.0, 0.4, 0.7), "shoot_range": 400},
    "KNIGHT": {"cost": 3, "hp": 400, "damage": 50, "speed": 0.75, "size": 70, "color": (1.0, 1.0, 0.0), "shoot_range": 320},
    "GIANT": {"cost": 5, "hp": 800, "damage": 70, "speed": 0.5, "size": 80, "color": (0.5, 0.3, 0.8), "shoot_range": 240}
}

player_troops = []
enemy_troops = []
player_troops_count = 0
enemy_troops_count = 0

game_difficulty = "NEWBIE"
player_bullets = []
enemy_bullets = []
bullets_speed = 2

#Particles & Visuals

fire_particles = [] 

def create_explosion(x, y, z, color):
    cnt = random.randint(12, 18)
    for i in range(cnt):
        vx = random.uniform(-6, 6)
        vy = random.uniform(-6, 6)
        vz = random.uniform(3, 9) 
        
        p = {
            "x": x, "y": y, "z": z,
            "vx": vx, "vy": vy, "vz": vz,
            "life": 1.0, 
            "color": color,
            "s": random.uniform(4, 9)
        }
        fire_particles.append(p)

def manage_particles():
    global fire_particles
    alive_particles = []
    for p in fire_particles:
        p["x"] = p["x"] + p["vx"]
        p["y"] = p["y"] + p["vy"]
        p["z"] = p["z"] + p["vz"]
        
        
        p["vz"] = p["vz"] - 0.4
        
        
        p["life"] = p["life"] - 0.03
        
        
        if p["life"] > 0:
            if p["z"] > 0:
                alive_particles.append(p)
                
    fire_particles = alive_particles

def render_particles():
    for p in fire_particles:
        glPushMatrix()
        glTranslatef(p["x"], p["y"], p["z"])
        

        scale = max(0.0, p["life"]) 
        glScalef(scale, scale, scale)

        c = p["color"]
        glColor3f(c[0], c[1], c[2])
        
        glutSolidCube(p["s"])
        
        glPopMatrix()



def draw_troop_buttons():
    global player_elixir
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 800, 0, 600)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    for b in TROOP_BUTTONS:
        bx, by, bw, bh, name, cost = b
        if player_elixir < cost:
            glColor3f(0.4, 0.4, 0.4) 
        elif name == "GOBLIN":
            glColor3f(0.0, 0.6, 0.0) 
        elif name == "ARCHER":
            glColor3f(1.0, 0.4, 0.7) 
        elif name == "KNIGHT":
            glColor3f(1.0, 1.0, 0.0) 
        elif name == "GIANT":
            glColor3f(0.5, 0.3, 0.8) 
        glBegin(GL_QUADS)
        glVertex2f(bx, by)
        glVertex2f(bx + bw, by)
        glVertex2f(bx + bw, by + bh)
        glVertex2f(bx, by + bh)
        glEnd()
        glColor3f(1, 1, 1) 
        draw_text(bx + 10, by + 40, f"{name}")
        draw_text(bx + 10, by + 10, f"Cost: {cost}")
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def generate_troops(troop_type, team = "PLAYER"):
    global player_elixir, enemy_elixir, player_troops_count, enemy_troops_count, deploy_position, enemy_deploy_position
    
    troop_data = TROOP_TYPES[troop_type]
    
    if team == "PLAYER":
        if player_elixir < troop_data["cost"]:
            return 
        player_elixir -= troop_data["cost"]
        if deploy_position == "left":
            x = -150
        else:
            x = 150
        y = -550
        troops_list = player_troops
        player_troops_count += 1
    else:
        if enemy_elixir < troop_data["cost"]:
            return 
        enemy_elixir -= troop_data["cost"]
        if enemy_deploy_position == "left":
            x = -150
        else:
            x = 150
        y = 550
        troops_list = enemy_troops
        enemy_troops_count += 1
    
    troop = {"type": troop_type, "team": team, "pos": [x, y, 0], "hp": troop_data["hp"], "max_hp": troop_data["hp"], "damage": troop_data["damage"], "speed": troop_data["speed"],
        "size": troop_data["size"], "color": troop_data["color"], "shoot_range": troop_data["shoot_range"], "target": None, "dead": False, "attack_cooldown": 0}
    
    troops_list.append(troop)
    return True

def draw_troop(troop):
    """Draw a single troop with arms"""
    glPushMatrix()
    glTranslatef(troop["pos"][0], troop["pos"][1], troop["pos"][2])
    
    if troop["dead"]:
        glRotatef(90, 1, 0, 0)
        glColor3f(0.3, 0.3, 0.3)
    else:
        glColor3f(*troop["color"])
    
    # Body
    glPushMatrix()
    glTranslatef(0, 0, troop["size"] / 2)
    gluSphere(gluNewQuadric(), troop["size"], 20, 20) 
    glPopMatrix()
    
    # Head
    glPushMatrix()
    glTranslatef(0, 0, troop["size"] * 1.2)
    glColor3f(0, 0, 0)
    gluSphere(gluNewQuadric(), troop["size"]/3, 20, 20)
    glPopMatrix()
    
    # HP bar
    if not troop["dead"] and troop["hp"] > 0:
        glPushMatrix()
        glTranslatef(-troop["size"]/2, 0, troop["size"] * 1.5)
        glBegin(GL_QUADS)
        glColor3f(0.2, 0.2, 0.2)
        glVertex3f(0, 0, 0)
        glVertex3f(troop["size"], 0, 0)
        glVertex3f(troop["size"], 0, 3)
        glVertex3f(0, 0, 3)
        
        hp_ratio = troop["hp"] / troop["max_hp"]
        hp_width = troop["size"] * hp_ratio
        if hp_ratio > 0.5:
            glColor3f(0.2, 0.8, 0.2)
        elif hp_ratio > 0.25:
            glColor3f(0.8, 0.8, 0.2)
        else:
            glColor3f(0.8, 0.2, 0.2)
        glVertex3f(0, 0, 3)
        glVertex3f(hp_width, 0, 3)
        glVertex3f(hp_width, 0, 6)
        glVertex3f(0, 0, 6)
        glEnd()
        glPopMatrix()
    
    glPopMatrix()

def computer_troop_deploy():
    global enemy_deploy_position
    if game_difficulty == "NEWBIE":
        if player_troops_count > enemy_troops_count:
            enemy_deploy_position = random.choice(["left", "right"])
            generate_troops(random.choice(["GOBLIN","ARCHER"]),"ENEMY")
        else:
            return
    elif game_difficulty == "CHALLENGER":
        if player_troops_count + 1 > enemy_troops_count:
            enemy_deploy_position = random.choice(["left", "right"])
            generate_troops(random.choice(["GOBLIN","ARCHER","KNIGHT"]),"ENEMY")
        else:
            return
    else:
        if player_troops_count + 2 > enemy_troops_count:
            enemy_deploy_position = random.choice(["left", "right"])
            generate_troops(random.choice(["GOBLIN","ARCHER","KNIGHT","GIANT"]),"ENEMY")
        else:
            return

def move_troops():
    global player_king_hp, player_left_princess_hp, player_right_princess_hp
    global enemy_king_hp, enemy_left_princess_hp, enemy_right_princess_hp

    current_time = time.time()
    new_player_list = []
    for troop in player_troops:
        if not troop["dead"]:
            new_player_list.append(troop)
        else:
            death_age = current_time - troop.get("death_time", current_time)
            if death_age < 3.0:
                new_player_list.append(troop)
    player_troops[:] = new_player_list

    new_enemy_list = []
    for troop in enemy_troops:
        if not troop["dead"]:
            new_enemy_list.append(troop)
        else:
            death_age = current_time - troop.get("death_time", current_time)
            if death_age < 3.0:
                new_enemy_list.append(troop)
    enemy_troops[:] = new_enemy_list

    # Player troops logic
    for troop in player_troops:
        if troop["dead"]: continue
        troop["attack_cooldown"] = max(0, troop["attack_cooldown"] - 1)

        nearest_enemy = None
        min_troop_dist = float('inf')
        for enemy in enemy_troops:
            if not enemy["dead"]:
                dist = math.hypot(enemy["pos"][0] - troop["pos"][0], enemy["pos"][1] - troop["pos"][1])
                if dist < min_troop_dist:
                    min_troop_dist = dist
                    nearest_enemy = enemy

        if nearest_enemy and min_troop_dist < 400:
            troop["target"] = nearest_enemy["pos"]
            troop["target_hp"] = "TROOP"
            troop["target_ref"] = nearest_enemy
        else:
            tower_target_dead = False
            current_target_hp = troop.get("target_hp")
            if current_target_hp == "enemy_left_princess_hp" and enemy_left_princess_hp <= 0: tower_target_dead = True
            elif current_target_hp == "enemy_right_princess_hp" and enemy_right_princess_hp <= 0: tower_target_dead = True
            elif current_target_hp == "enemy_king_hp" and enemy_king_hp <= 0: tower_target_dead = True

            if troop.get("target") is None or current_target_hp == "TROOP" or tower_target_dead:
                if enemy_left_princess_hp > 0:
                    troop["target"] = ENEMY_LEFT_PRINCESS_POS
                    troop["target_hp"] = "enemy_left_princess_hp"
                elif enemy_right_princess_hp > 0:
                    troop["target"] = ENEMY_RIGHT_PRINCESS_POS
                    troop["target_hp"] = "enemy_right_princess_hp"
                elif enemy_king_hp > 0:
                    troop["target"] = ENEMY_KING_TOWER_POS
                    troop["target_hp"] = "enemy_king_hp"
                else:
                    troop["target"] = None

        if troop["target"]:
            tx, ty, _ = troop["target"]
            x, y, z = troop["pos"]
            dx, dy = tx - x, ty - y
            dist = math.hypot(dx, dy)
            if dist > troop["shoot_range"]:
                step = min(troop["speed"], dist - troop["shoot_range"])
                troop["pos"][0] += dx/dist * step
                troop["pos"][1] += dy/dist * step
            else:
                if troop["attack_cooldown"] <= 0:
                    angle_to_target = -math.degrees(math.atan2(dx, dy))
                    if troop["target_hp"] == "TROOP":
                        player_bullets.append([x, y, 130, angle_to_target, "TROOP", troop["damage"], troop["target_ref"]])
                    else:
                        player_bullets.append([x, y, 130, angle_to_target, troop["target_hp"], troop["damage"], None])
                    troop["attack_cooldown"] = 60

    # Enemy troops logic
    for troop in enemy_troops:
        if troop["dead"]: continue
        troop["attack_cooldown"] = max(0, troop["attack_cooldown"] - 1)

        nearest_player = None
        min_troop_dist = float('inf')
        for p_troop in player_troops:
            if not p_troop["dead"]:
                dist = math.hypot(p_troop["pos"][0] - troop["pos"][0], p_troop["pos"][1] - troop["pos"][1])
                if dist < min_troop_dist:
                    min_troop_dist = dist
                    nearest_player = p_troop

        if nearest_player and min_troop_dist < 400:
            troop["target"] = nearest_player["pos"]
            troop["target_hp"] = "TROOP"
            troop["target_ref"] = nearest_player
        else:
            tower_target_dead = False
            current_target_hp = troop.get("target_hp")
            if current_target_hp == "player_left_princess_hp" and player_left_princess_hp <= 0: tower_target_dead = True
            elif current_target_hp == "player_right_princess_hp" and player_right_princess_hp <= 0: tower_target_dead = True
            elif current_target_hp == "player_king_hp" and player_king_hp <= 0: tower_target_dead = True

            if troop.get("target") is None or current_target_hp == "TROOP" or tower_target_dead:
                if player_left_princess_hp > 0:
                    troop["target"] = PLAYER_LEFT_PRINCESS_POS
                    troop["target_hp"] = "player_left_princess_hp"
                elif player_right_princess_hp > 0:
                    troop["target"] = PLAYER_RIGHT_PRINCESS_POS
                    troop["target_hp"] = "player_right_princess_hp"
                elif player_king_hp > 0:
                    troop["target"] = PLAYER_KING_TOWER_POS
                    troop["target_hp"] = "player_king_hp"
                else:
                    troop["target"] = None

        if troop["target"]:
            tx, ty, _ = troop["target"]
            x, y, z = troop["pos"]
            dx, dy = tx - x, ty - y
            dist = math.hypot(dx, dy)
            if dist > troop["shoot_range"]:
                step = min(troop["speed"], dist)
                troop["pos"][0] += dx/dist * step
                troop["pos"][1] += dy/dist * step
            else:
                if troop["attack_cooldown"] <= 0:
                    angle_to_target = -math.degrees(math.atan2(dx, dy))
                    if troop["target_hp"] == "TROOP":
                        enemy_bullets.append([x, y, 130, angle_to_target, "TROOP", troop["damage"], troop["target_ref"]])
                    else:
                        enemy_bullets.append([x, y, 130, angle_to_target, troop["target_hp"], troop["damage"], None])
                    troop["attack_cooldown"] = 60



def draw_bullets():
    global bullets_speed, player_bullets, enemy_bullets
    global player_left_princess_hp, player_right_princess_hp, player_king_hp
    global enemy_left_princess_hp, enemy_right_princess_hp, enemy_king_hp
    all_bullets = [player_bullets, enemy_bullets]

    for bullet_list in all_bullets:
        active_bullets = []
        for b in bullet_list:
            x, y, z, angle, target_hp, damage, target_ref = b
            
            rad = -math.radians(angle)
            x = x + math.sin(rad) * bullets_speed
            y = y + math.cos(rad) * bullets_speed

            
            if x < -1000 or x > 1000 or y < -1000 or y > 1000:
                continue 
            
            
            if target_hp == "TROOP":
                if target_ref and target_ref["dead"] == True:
                    continue 

            glPushMatrix()
            glColor3f(1, 0, 0) 
            glTranslatef(x, y, z)
            glutSolidCube(20)
            glPopMatrix()

            hit_something = False
            if target_hp == "TROOP":
                if target_ref: 
                    if target_ref["dead"] == False:
                        dx = target_ref["pos"][0] - x
                        dy = target_ref["pos"][1] - y
                        d = math.hypot(dx, dy)
                        
                        if d < 40:
                            
                            target_ref["hp"] = target_ref["hp"] - damage
                            
                            
                            if target_ref["hp"] <= 0:
                                target_ref["dead"] = True
                                target_ref["death_time"] = time.time()
                                
                                
                                t_pos = target_ref["pos"]
                                create_explosion(t_pos[0], t_pos[1], t_pos[2], target_ref["color"])
                                
                            hit_something = True
                            
                            create_explosion(x, y, z, (1, 0.8, 0))
                else:
                    hit_something = True 

            else:
                t_pos = None
                if target_hp == "enemy_left_princess_hp":
                    t_pos = ENEMY_LEFT_PRINCESS_POS
                elif target_hp == "enemy_right_princess_hp": 
                    t_pos = ENEMY_RIGHT_PRINCESS_POS
                elif target_hp == "enemy_king_hp": 
                    t_pos = ENEMY_KING_TOWER_POS
                elif target_hp == "player_left_princess_hp": 
                    t_pos = PLAYER_LEFT_PRINCESS_POS
                elif target_hp == "player_right_princess_hp": 
                    t_pos = PLAYER_RIGHT_PRINCESS_POS
                elif target_hp == "player_king_hp": 
                    t_pos = PLAYER_KING_TOWER_POS

                if t_pos:
                    dist = math.hypot(t_pos[0] - x, t_pos[1] - y)
                    if dist < 20: 
                        if target_hp == "enemy_left_princess_hp": enemy_left_princess_hp -= damage
                        elif target_hp == "enemy_right_princess_hp": enemy_right_princess_hp -= damage
                        elif target_hp == "enemy_king_hp": enemy_king_hp -= damage
                        elif target_hp == "player_left_princess_hp": player_left_princess_hp -= damage
                        elif target_hp == "player_right_princess_hp": player_right_princess_hp -= damage
                        elif target_hp == "player_king_hp": player_king_hp -= damage
                        
                        hit_something = True
                        
                        create_explosion(x, y, z, (0.9, 0.5, 0.1))
            
            if hit_something == False:
                
                active_bullets.append([x, y, z, angle, target_hp, damage, target_ref])
                
       
        bullet_list[:] = active_bullets

def tower_self_defence():
    global player_bullets, enemy_bullets
    global player_king_hp, player_left_princess_hp, player_right_princess_hp
    global enemy_king_hp, enemy_left_princess_hp, enemy_right_princess_hp
    
    
    p_towers = []
    
    p_king_awake = False
    if player_king_hp < 1500:
        p_king_awake = True
    elif player_left_princess_hp <= 0:
        p_king_awake = True
    elif player_right_princess_hp <= 0:
        p_king_awake = True
        
    if player_king_hp > 0:
        if p_king_awake:
            p_towers.append({"pos": PLAYER_KING_TOWER_POS, "type": "player_king"})
    
    if player_left_princess_hp > 0:
        p_towers.append({"pos": PLAYER_LEFT_PRINCESS_POS, "type": "player_left"})
    if player_right_princess_hp > 0:
        p_towers.append({"pos": PLAYER_RIGHT_PRINCESS_POS, "type": "player_right"})
    
    # 2. Enemy Team Towers
    e_towers = []
    

    e_king_awake = False
    if enemy_king_hp < 1500:
        e_king_awake = True
    elif enemy_left_princess_hp <= 0:
        e_king_awake = True
    elif enemy_right_princess_hp <= 0:
        e_king_awake = True
        
    if enemy_king_hp > 0:
        if e_king_awake:
            e_towers.append({"pos": ENEMY_KING_TOWER_POS, "type": "enemy_king"})
    
    if enemy_left_princess_hp > 0:
        e_towers.append({"pos": ENEMY_LEFT_PRINCESS_POS, "type": "enemy_left"})
    if enemy_right_princess_hp > 0:
        e_towers.append({"pos": ENEMY_RIGHT_PRINCESS_POS, "type": "enemy_right"})
    

    for t in p_towers:
        my_x, my_y, _ = t["pos"]
        
        # find closest enemy
        closest = None
        min_d = 999999
        
        for e in enemy_troops:
            if e["dead"] == False:
                dist = math.hypot(e["pos"][0] - my_x, e["pos"][1] - my_y)
                
                if dist < 500:
                    if dist < min_d:
                        min_d = dist
                        closest = e
        
        if closest:
          
            if 'cooldown' not in t:
                t['cooldown'] = 0
            
            if t['cooldown'] <= 0:
               
                ex = closest["pos"][0]
                ey = closest["pos"][1]
                
               
                dx = ex - my_x
                dy = ey - my_y
                ang = -math.degrees(math.atan2(dx, dy))
                
               
                bullet = [my_x, my_y, 130, ang, "TROOP", 1, closest]
                player_bullets.append(bullet)
                
                t['cooldown'] = 1000
            else:
                t['cooldown'] -= 1
    
   
    for t in e_towers:
        my_x, my_y, _ = t["pos"]
        
        closest = None
        min_d = 999999
        
        for p in player_troops:
            if p["dead"] == False:
                dist = math.hypot(p["pos"][0] - my_x, p["pos"][1] - my_y)
                if dist < 500:
                    if dist < min_d:
                        min_d = dist
                        closest = p
        
        if closest:
            if 'cooldown' not in t:
                t['cooldown'] = 0
            
            if t['cooldown'] <= 0:
                px = closest["pos"][0]
                py = closest["pos"][1]
                dx = px - my_x
                dy = py - my_y
                ang = -math.degrees(math.atan2(dx, dy))
                
                
                bullet = [my_x, my_y, 130, ang, "TROOP", 0.05, closest]
                enemy_bullets.append(bullet)
                
                t['cooldown'] = 3000
            else:
                t['cooldown'] -= 1

def check_game_over():
    global game_over, winner, player_troops, enemy_troops
    
   
    if player_king_hp <= 0:
        if game_over == False:
            game_over = True
            winner = "ENEMY"
           
            for t in player_troops:
                if t["dead"] == False:
                    t["dead"] = True
                    t["death_time"] = time.time()
    
  
    elif enemy_king_hp <= 0:
        if game_over == False:
            game_over = True
            winner = "PLAYER"
          
            for t in enemy_troops:
                if t["dead"] == False:
                    t["dead"] = True
                    t["death_time"] = time.time()

def draw_tower(pos, hp, max_hp, is_player, tower_type):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    
    if hp <= 0:
        glColor3f(0.3, 0.3, 0.3)
        glPushMatrix()
        glTranslatef(0, 0, 10)
        glRotatef(45, 1, 0, 0)
        glutSolidCube(40 if tower_type == "KING" else 30)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(15, 10, 5)
        glRotatef(30, 0, 1, 0)
        glutSolidCube(25 if tower_type == "KING" else 20)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-15, -10, 5)
        glRotatef(-20, 0, 0, 1)
        glutSolidCube(20 if tower_type == "KING" else 15)
        glPopMatrix()
    else:
        if tower_type == "KING":
            base_size = 120
            top_size = 90
        else:
            base_size = 90
            top_size = 70
        
        if is_player:
            glColor3f(0.2, 0.4, 0.8)
        else:
            glColor3f(0.8, 0.2, 0.2)
        
        # Base
        glPushMatrix()
        glTranslatef(0, 0, base_size/2)
        glutSolidCube(base_size)
        glPopMatrix()
        
        # Top
        glPushMatrix()
        glTranslatef(0, 0, base_size)
        if is_player:
            glColor3f(0.3, 0.5, 0.9)
        else:
            glColor3f(0.9, 0.3, 0.3)
        glutSolidCube(top_size)
        glPopMatrix()
        
        # Cannon
        glPushMatrix()
        glTranslatef(0, 0, base_size + top_size/2)
        glScalef(2, 2, 2)
        glColor3f(0.4, 0.4, 0.4)
        if is_player:
            glRotatef(-90, 1, 0, 0)
        else:
            glRotatef(90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 8, 8, 30, 10, 10)
        glPopMatrix()
        
        # HP bar
        glPushMatrix()
        glTranslatef(-25, 0, base_size + top_size + 20)
        glBegin(GL_QUADS)
        glColor3f(0.2, 0.2, 0.2)
        glVertex3f(0, 0, 0)
        glVertex3f(75, 0, 0)
        glVertex3f(75, 0, 25)
        glVertex3f(0, 0, 25)
        
        hp_width = 75 * (hp / max_hp)
        if hp > max_hp * 0.5:
            glColor3f(0.2, 0.8, 0.2)
        elif hp > max_hp * 0.25:
            glColor3f(0.8, 0.8, 0.2)
        else:
            glColor3f(0.8, 0.2, 0.2)
        glVertex3f(0, 0, 25)
        glVertex3f(hp_width, 0, 25)
        glVertex3f(hp_width, 0, 10)
        glVertex3f(0, 0, 10)
        glEnd()
        glPopMatrix()
    
    glPopMatrix()

def draw_elixir_bar(x, y, width, height, elixir, is_enemy=False):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 800, 0, 600)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(0.15, 0.15, 0.15)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()
    filled_width = width * (elixir / 10)
    if is_enemy:
        glColor3f(0.8, 0.2, 0.2)   
    else:
        glColor3f(0.6, 0.2, 0.9)  
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + filled_width, y)
    glVertex2f(x + filled_width, y + height)
    glVertex2f(x, y + height)
    glEnd()
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def update_elixir():
    global player_elixir, enemy_elixir, last_player_elixir_time, last_enemy_elixir_time
    current_time = time.time()
    if current_time - last_player_elixir_time > 2.0:
        if player_elixir < 10: player_elixir = min(10, player_elixir + 1)
        last_player_elixir_time = current_time
    if current_time - last_enemy_elixir_time > 2.0:
        if enemy_elixir < 10: enemy_elixir = min(10, enemy_elixir + 1)
        last_enemy_elixir_time = current_time

def draw_difficulty_button():
    x, y = 310, 530
    w, h = 150, 30
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 800, 0, 600)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    if game_difficulty == "NEWBIE": 
        glColor3f(0, 1, 0)
    elif game_difficulty == "CHALLENGER": 
        glColor3f(1.0, 0.6, 0.1)
    else: 
        glColor3f(1, 0, 0)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()
    draw_text(330, 572, f"DIFFICULTY")
    draw_text(285, 571, f"___________________")
    draw_text(x + 10, y + 8, f"{game_difficulty}")
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def specialKeyListener(key, x, y):
    global camera_rotation, camera_zoom, camera_pos
    if key == GLUT_KEY_LEFT: camera_rotation -= 5
    if key == GLUT_KEY_RIGHT: camera_rotation += 5
    if key == GLUT_KEY_UP: camera_zoom = max(0.5, camera_zoom - 0.1)
    if key == GLUT_KEY_DOWN: camera_zoom = min(2.0, camera_zoom + 0.1)

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 800, 0, 600)  
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def keyboardListener(key, x, y):
    global camera_mode, deploy_position, paused, game_speed, speed_display
    global player_elixir, enemy_elixir, player_troops_count, enemy_troops_count
    global player_king_hp, player_left_princess_hp, player_right_princess_hp
    global enemy_king_hp, enemy_left_princess_hp, enemy_right_princess_hp
    global player_troops, enemy_troops, player_bullets, enemy_bullets
    global last_player_elixir_time, last_enemy_elixir_time, last_enemy_deploy_time
    global game_over, winner
    
    # Toggle pause
    if key == b'p' or key == b'P': 
        if paused == False:
            paused = True
        else:
            paused = False
            
    # Reset everything
    if key == b'r' or key == b'R':
        game_over = False
        winner = None
        paused = False
        
        # reset hp
        player_king_hp = 1500
        player_left_princess_hp = 800
        player_right_princess_hp = 800
        enemy_king_hp = 1500
        enemy_left_princess_hp = 800
        enemy_right_princess_hp = 800
        
        # clear lists
        player_troops[:] = []
        enemy_troops[:] = []
        player_bullets[:] = []
        enemy_bullets[:] = []
        
        # reset elixir
        player_elixir = 1.0
        enemy_elixir = 1.0
        
        game_speed = 1.0
        speed_display = 1.0
        
        last_player_elixir_time = time.time()
        last_enemy_elixir_time = time.time()
    
    # Speed up or down
    if key == b'+' or key == b'=':
        if game_speed < 3.0:
            game_speed = game_speed + 0.5
        speed_display = game_speed
        
    if key == b'-' or key == b'_':
        if game_speed > 0.5:
            game_speed = game_speed - 0.5
        speed_display = game_speed
        
    if key == b'a' or key == b'A': deploy_position = "left"
    elif key == b'd' or key == b'D': deploy_position = "right"
    if key == b'c' or key == b'C':
        if camera_mode == "OVERVIEW": camera_mode = "FIRST_PERSON_PLAYER"
        elif camera_mode == "FIRST_PERSON_PLAYER": camera_mode = "FIRST_PERSON_ENEMY"
        else: camera_mode = "OVERVIEW"

def mouseListener(button, state, x, y):
    global game_difficulty
    y = 600 - y
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        for b in TROOP_BUTTONS:
            bx, by, bw, bh, troop_name, cost = b
            if x >= bx and x <= (bx + bw) and y >= by and y <= (by + bh):
                if player_elixir >= cost:
                    if troop_name == "GOBLINS": generate_troops("GOBLIN", "PLAYER")
                    else: generate_troops(troop_name, "PLAYER")
                break 
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        bx, by = 310, 530
        bw, bh = 150, 40
        if bx <= x <= bx + bw and by <= y <= by + bh:
            if game_difficulty == "NEWBIE": game_difficulty = "CHALLENGER"
            elif game_difficulty == "CHALLENGER": game_difficulty = "DEATHMODE"
            else: game_difficulty = "NEWBIE"            

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.55, 0.1, 3000) 
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if camera_mode == "OVERVIEW":
        x = camera_pos[0] * camera_zoom
        y = camera_pos[1] * camera_zoom
        z = camera_pos[2] * camera_zoom
        rad = math.radians(camera_rotation)
        new_x = x * math.cos(rad) - y * math.sin(rad)
        new_y = x * math.sin(rad) + y * math.cos(rad)
        gluLookAt(new_x, new_y, z, 0, 0, 0, 0, 0, 1)
    elif camera_mode == "FIRST_PERSON_PLAYER":
        gluLookAt(PLAYER_KING_TOWER_POS[0], PLAYER_KING_TOWER_POS[1], 200,
                  ENEMY_KING_TOWER_POS[0], ENEMY_KING_TOWER_POS[1], 160,
                  0, 0, 1)
    else: 
        gluLookAt(ENEMY_KING_TOWER_POS[0], ENEMY_KING_TOWER_POS[1], 200,
                  PLAYER_KING_TOWER_POS[0], PLAYER_KING_TOWER_POS[1], 160,
                  0, 0, 1)

def idle():
    global last_enemy_deploy_time
    
    #Check for pause and loop for speed
    if paused == False:
        current_time = time.time()
        
        
        if current_time - last_enemy_deploy_time > (3.0 / game_speed):
            computer_troop_deploy()
            last_enemy_deploy_time = current_time
        
        
        loops = int(game_speed)
        for i in range(loops):
            move_troops()
            tower_self_defence()
            manage_particles() 
            
        check_game_over()
        
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity() 
    glViewport(0, 0, 800, 600)  
    setupCamera() 
    glBegin(GL_QUADS)
    for x in range(-GRID_LENGTH, GRID_LENGTH, tile_size):
        for y in range(-GRID_LENGTH, GRID_LENGTH, tile_size):
            if ((x // tile_size) + (y // tile_size)) % 2 == 0: glColor3f(0, 0, 0)
            else: glColor3f(1, 1, 1)
            glVertex3f(x, y, 0)
            glVertex3f(x+tile_size, y, 0)
            glVertex3f(x+tile_size, y+tile_size, 0)
            glVertex3f(x, y+tile_size, 0)
    glEnd()

    glBegin(GL_QUADS)
    glColor3f(0.7, 0, 0.3)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 60)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 60)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glColor3f(0.3, 0, 0.7)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 60)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 60)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glColor3f(0.7, 0, 0.3)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 60)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 60)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glColor3f(0.3, 0, 0.7)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 60)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 60)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glEnd()

    draw_tower(PLAYER_KING_TOWER_POS, player_king_hp, 1500, True, "KING")
    draw_tower(PLAYER_LEFT_PRINCESS_POS, player_left_princess_hp, 800, True, "PRINCESS")
    draw_tower(PLAYER_RIGHT_PRINCESS_POS, player_right_princess_hp, 800, True, "PRINCESS")
    
    draw_tower(ENEMY_KING_TOWER_POS, enemy_king_hp, 1500, False, "KING")
    draw_tower(ENEMY_LEFT_PRINCESS_POS, enemy_left_princess_hp, 800, False, "PRINCESS")
    draw_tower(ENEMY_RIGHT_PRINCESS_POS, enemy_right_princess_hp, 800, False, "PRINCESS")

    draw_elixir_bar(200, 20, 400, 25, elixir=player_elixir, is_enemy = False)
    draw_elixir_bar(200, 440, 400, 25, elixir=enemy_elixir, is_enemy = True)

    for troop in player_troops: draw_troop(troop)
    for troop in enemy_troops: draw_troop(troop)
    
    draw_bullets()
    render_particles() 
    
    draw_difficulty_button()
    draw_troop_buttons()


    draw_text(380, 27, f"{int(player_elixir)}/10")
    draw_text(90, 572, f"Player")
    draw_text(20, 571, f"___________________")
    draw_text(20, 550, f"King Tower: {max(0, int(player_king_hp))}/1500")
    draw_text(20, 530, f"Left Princess: {max(0, int(player_left_princess_hp))}/800")
    draw_text(20, 510, f"Right Princess: {max(0, int(player_right_princess_hp))}/800")
    
    draw_text(380, 447, f"{int(enemy_elixir)}/10")
    draw_text(620, 572, f"Enemy")
    draw_text(550, 571, f"___________________")
    draw_text(550, 550, f"King Tower: {max(0, int(enemy_king_hp))}/1500")
    draw_text(550, 530, f"Left Princess: {max(0, int(enemy_left_princess_hp))}/800")
    draw_text(550, 510, f"Right Princess: {max(0, int(enemy_right_princess_hp))}/800")

    if game_over:
        draw_text(275, 475, f"GAME OVER! Winner: {winner}")
        draw_text(310, 500, f"Press [R] to Restart")
    else:
        draw_text(130, 475, f"** Press [A] or [D] for LEFT and RIGHT side troops deployment **")
        draw_text(230, 500, f"Speed: {speed_display}x [+/-] | Paused: {paused} [P]")

    

    update_elixir()
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutInitWindowPosition(0, 0) 
    wind = glutCreateWindow(b"3D OpenGL Clash Royale") 

    glutDisplayFunc(showScreen) 
    glutKeyboardFunc(keyboardListener)  
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle) 

    glutMainLoop()  

if __name__ == "__main__":
    main()