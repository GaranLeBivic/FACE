import pygame
import random
import math
import streamlit as st
import threading

# Configuration de la simulation
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Fonction pour lancer la simulation dans un thread séparé
def run_simulation(particule_count_precurseur, particule_count_catalyseur, particule_count_intermediaire, particule_count_polaire, particle_radius, interaction_radius, attraction_force, repulsion_force, polar_interaction_angle, vitesse, rotation_speed):
    # Couleurs pour les types de particules
    GREEN = (0, 255, 0)  # Précurseurs
    RED = (255, 0, 0)    # Catalyseurs
    PURPLE = (128, 0, 128)  # Intermédiaires
    YELLOW = (255, 255, 0)  # Polaires

    class Particle:
        def __init__(self, x, y, type, orientation=None):
            self.x = x
            self.y = y
            self.type = type
            self.vitesse = vitesse  # Facteur de vitesse
            self.dx = random.uniform(-1, 1) * self.vitesse  # Appliquer la vitesse au mouvement
            self.dy = random.uniform(-1, 1) * self.vitesse  # Appliquer la vitesse au mouvement
            self.orientation = orientation if orientation is not None else random.uniform(0, 2 * math.pi) if type == "polaire" else None
            self.rotation_speed = rotation_speed  # Vitesse de rotation des particules polaires
            self.interaction_radius = interaction_radius  # Rayon du cercle invisible autour des précurseurs

        def move(self):
            if not hasattr(self, "is_stuck") or not self.is_stuck:
                # Si la particule est polaire, applique la rotation à son orientation
                if self.type == "polaire":
                    self.orientation += self.rotation_speed

                    # Gérer l'orientation pour qu'elle reste dans les limites de [0, 2π]
                    if self.orientation >= 2 * math.pi:
                        self.orientation -= 2 * math.pi
                    elif self.orientation < 0:
                        self.orientation += 2 * math.pi
    
                # Déplace la particule avec la vitesse ajustée
                self.x += self.dx
                self.y += self.dy

                # Gérer les rebonds sur les bords
                if self.x < 0 or self.x > SCREEN_WIDTH:
                    self.dx *= -1
                    self.x = max(0, min(self.x, SCREEN_WIDTH))
                if self.y < 0 or self.y > SCREEN_HEIGHT:
                    self.dy *= -1
                    self.y = max(0, min(self.y, SCREEN_HEIGHT))

        def draw(self, screen):
            color = {
                "precurseur": GREEN,
                "catalyseur": RED,
                "intermediaire": PURPLE,
                "polaire": YELLOW
            }[self.type]
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), particle_radius)

            # Dessin de la queue pour les particules polaires
            if self.type == "polaire":
                tail_length = 10
                tail_x = self.x - tail_length * math.cos(self.orientation)
                tail_y = self.y - tail_length * math.sin(self.orientation)
                pygame.draw.line(screen, color, (self.x, self.y), (tail_x, tail_y), 2)


        def interact(self, other, polar_interaction_angle):
            # Distance entre les particules
            dx = self.x - other.x
            dy = self.y - other.y
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance > self.interaction_radius or self == other:
                return

            # Interaction Précurseur + Catalyseur : transformation immédiate
            if self.type == "precurseur" and other.type == "catalyseur":
                self.type = "intermediaire"

            # Interaction Précurseur + Intermédiaire : transformation double immédiate
            elif self.type == "precurseur" and other.type == "intermediaire":
                self.type = "polaire"
                self.orientation = random.uniform(0, 2 * math.pi)
                other.type = "catalyseur"

            # Interaction entre une particule précurseur et une particule catalyseur dans le cercle
            elif self.type == "precurseur" and other.type == "catalyseur" and distance <= self.interaction_radius:
                self.type = "intermediaire"

            # Interaction entre une particule intermédiaire et une particule précurseur dans le cercle
            elif self.type == "intermediaire" and other.type == "precurseur" and distance <= self.interaction_radius:
                self.type = "polaire"
                self.orientation = random.uniform(0, 2 * math.pi)
                other.type = "catalyseur"

            # Répulsion des Polaires avec Catalyseurs ou Intermédiaires
            elif self.type == "polaire" and other.type in ["catalyseur", "intermediaire"] and distance <= self.interaction_radius:
                other.repel(self)

            # Interaction entre deux particules polaires : ajuster leur orientation
            elif self.type == "polaire" and other.type == "polaire" and distance <= self.interaction_radius:
                self.align_with(other, polar_interaction_angle)

            # Attraction ou Répulsion entre Polaires
            elif self.type == "polaire" and other.type == "polaire":
                self.align_or_repel(other, distance, polar_interaction_angle, attraction_force, repulsion_force)               

        def align_with(self, other, polar_interaction_angle):
            # Ajuster l'orientation des particules polaires pour minimiser la différence d'angle
            angle_diff = abs(self.orientation - other.orientation) % (2 * math.pi)
            if angle_diff > polar_interaction_angle:
                self.orientation = other.orientation  # S'aligner avec l'autre particule

        def repel(self, other):
            # Force de répulsion simple
            dx = self.x - other.x
            dy = self.y - other.y
            distance = math.sqrt(dx ** 2 + dy ** 2)
            if distance > 0:
                force = repulsion_force / distance
                self.dx = max(min(self.dx + force * dx, 1), -1)
                self.dy = max(min(self.dy + force * dy, 1), -1)

        def align_or_repel(self, other, distance):
            attraction_threshold = 15  # Distance où elles doivent s’agglutiner
            strong_attraction_distance = 50  # Distance où elles commencent à s’attirer
            ideal_angle_shift = math.pi / 6  # Décalage d’angle pour former un cercle

            # SI ELLES SONT ASSEZ PROCHES, ELLES S’AGGLUTINENT EN CERCLE
            if distance < attraction_threshold:
                self.dx = self.dy = 0
                other.dx = other.dy = 0

                # Déterminer l’angle de connexion en cercle
                target_angle = math.atan2(other.y - self.y, other.x - self.x)
                self.orientation = (target_angle + ideal_angle_shift) % (2 * math.pi)
                other.orientation = (target_angle - ideal_angle_shift) % (2 * math.pi)

                # Ajustement des positions pour éviter le chevauchement
                mid_x = (self.x + other.x) / 2
                mid_y = (self.y + other.y) / 2
                offset_x = math.cos(target_angle) * attraction_threshold / 2
                offset_y = math.sin(target_angle) * attraction_threshold / 2

                self.x, self.y = mid_x + offset_x, mid_y + offset_y
                other.x, other.y = mid_x - offset_x, mid_y - offset_y

                # Marquer ces particules comme "collées"
                self.is_stuck = True
                other.is_stuck = True

            # SI ELLES SONT PROCHES MAIS PAS ENCORE ASSEZ, ELLES S’ATTIRENT
            elif distance < strong_attraction_distance:
                attraction_force = 1000  # Ajuste la force d’attraction
                target_angle = math.atan2(other.y - self.y, other.x - self.x)

                self.dx += attraction_force * math.cos(target_angle)
                self.dy += attraction_force * math.sin(target_angle)
                other.dx -= attraction_force * math.cos(target_angle)
                other.dy -= attraction_force * math.sin(target_angle)

                # Elles tournent progressivement vers la bonne orientation
                self.orientation = (self.orientation * 0.9 + (target_angle + ideal_angle_shift) * 0.1) % (2 * math.pi)
                other.orientation = (other.orientation * 0.9 + (target_angle - ideal_angle_shift) * 0.1) % (2 * math.pi)


    # Création des particules, selon les types et les quantités spécifiées
    particles = []

    # Ajouter les particules de chaque type
    for _ in range(particule_count_precurseur):
        particles.append(Particle(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), "precurseur"))
    for _ in range(particule_count_catalyseur):
        particles.append(Particle(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), "catalyseur"))
    for _ in range(particule_count_intermediaire):
        particles.append(Particle(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), "intermediaire"))
    for _ in range(particule_count_polaire):
        particles.append(Particle(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), "polaire", orientation=random.uniform(0, 2 * math.pi)))

    # Initialisation de Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Système de Particules")
    clock = pygame.time.Clock()

    # Boucle principale
    running = True
    while running:
        screen.fill((0, 0, 0))  # Nettoyage de l'écran
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Mise à jour et dessin des particules
        for particle in particles:
            particle.move()
            particle.draw(screen)

        # Gestion des interactions avec un système en deux étapes pour garantir des transformations immédiates
        interactions_to_process = []
        for i, particle in enumerate(particles):
            for other in particles[i + 1:]:
                interactions_to_process.append((particle, other))

        for particle, other in interactions_to_process:
            particle.interact(other, polar_interaction_angle)

        # Actualisation de l'écran
        pygame.display.flip()
        clock.tick(60)  # Limite à 60 images par seconde

    pygame.quit()


# Début de la description verbale

# Interface Streamlit pour les paramètres
st.title("Système à Particules avec Pygame et Streamlit")

# Introduction à la simulation
st.header("Contexte")
st.markdown("""
Cette application de simulation présente un modèle simplifié de celui conceptualisé dans <a href="https://arxiv.org/abs/2311.10761">"Emergence of autopoietic vesicles able to grow, repair and reproduce in a minimalist particle system."</a> de Cabaret, T. publié en 2024. 
Dans cette simulation, des particules de différents types interagissent entre elles dans un environnement virtuel.
Chaque particule a un comportement spécifique qui dépend de son type, et les interactions peuvent provoquer des transformations et des ajustements de leur position et orientation.
Le but de ce modèle est de simuler un environnement informatique dans lequel des particules forment des ensembles capables de réplication, stockage d'information et autopoïèse. 
""", unsafe_allow_html=True)

# Les types de particules
st.header("Les différents Types de Particules")

st.markdown("""
La simulation fonctionne grâce à quatre types de particules :

1. <span style="color:green">**Précurseurs**</span> : Ces particules, représentées par la couleur verte : 
    elles sont les éléments de départ. Elles interagissent avec d'autres particules pour initier des transformations.
   
2. <span style="color:red">**Catalyseur**</span> : Ces particules, affichées en rouge : 
   elles transforment des <span style="color:green">précurseurs</span> en des particules <span style="color:purple">intermédiaires</span>.
   
3. <span style="color:purple">**Intermédiaires**</span> : Les particules sont affichées en violet : 
    elles résultent de l'interaction entre <span style="color:green">précurseurs</span> et <span style="color:red">catalyseur</span>, et se changent en <span style="color:red">catalyseur</span> au contact d'un <span style="color:green">précurseur</span>, qui devient une particule <span style="color:yellow">polaire</span>.

4. <span style="color:yellow">**Polaires**</span> : Les particules <span style="color:yellow">polaires</span> sont affichées en jaune : 
   elles possèdent une orientation, illustrée par une queue, et peuvent interagir entre elles pour s'attirer mutuellement ou se séparer.
""", unsafe_allow_html=True)

# Chapitre 3: Interactions entre les particules
st.header("Interactions entre les Particules")

st.markdown("""
Les interactions entre particules sont au cœur de la dynamique du système. 

- <span style="color:green">**Précurseur**</span> + <span style="color:red">**Catalyseur**</span> : Lorsqu'un <span style="color:green">précurseur</span> entre en interaction avec un <span style="color:red">catalyseur</span>, il se transforme immédiatement en <span style="color:purple">intermédiaire</span>.
- <span style="color:green">**Précurseur**</span> + <span style="color:purple">**Intermédiaire**</span> : Lorsqu'un <span style="color:green">précurseur</span> entre en interaction avec un <span style="color:purple">intermédiaire</span>, le <span style="color:green">précurseur</span> devient <span style="color:yellow">polaire</span>, et l'<span style="color:purple">intermédiaire</span> se transforme en <span style="color:red">catalyseur</span>.
- <span style="color:yellow">**Polaires</span> entre elles** : Les particules <span style="color:yellow">polaires</span> interagissent en ajustant leur orientation. Lorsqu'elles se rapprochent, elles peuvent s'agglutiner avec un léger angle entre elles de sorte à former un cercle en se rapprochant pour former une structure stable.
""", unsafe_allow_html=True)

# Chapitre 4: Comportement des particules Polaires
st.header("Particules Polaires")

st.markdown("""
Les particules <span style="color:yellow">polaires</span> ont un comportement particulier. 

- **Répulsion** : Les particules <span style="color:yellow">polaires</span> repoussent les <span style="color:red">catalyseurs</span> et les <span style="color:purple">intermédiaires</span>. Elles se repoussent également enter elles lorsqu'elles sont dos à dos ou très proches. 
- **Attraction** : Les particules <span style="color:yellow">polaires</span> s'attirent entre elles dans les autres cas. Elles sont à l'équilibre avec leurs voisines lorsqu'elles ont un petit angle en comparaison avec le cas totalement parallèle. 
""", unsafe_allow_html=True)

st.header("Autrement")

st.markdown("""
En dehors de ces cas de figures, les particules s'ignorent entre elles et peuvent se croiser. 
""", unsafe_allow_html=True)

# Paramétrage
st.header("Réglage des paramètres du modèle")

particule_count_precurseur = st.slider("Nombre initial de précurseurs", min_value=0, max_value=300, value=50, step=5)
particule_count_catalyseur = st.slider("Nombre initial de catalyseurs", min_value=0, max_value=300, value=50, step=5)
particule_count_intermediaire = st.slider("Nombre initial d'intermédiaires", min_value=0, max_value=300, value=50, step=5)
particule_count_polaire = st.slider("Nombre initial de polaires", min_value=0, max_value=300, value=50, step=5)

particle_radius = st.slider("Rayon des particules", min_value=1, max_value=20, value=5, step=1)
interaction_radius = particle_radius*2

# Paramètres de force pour polaires
attraction_force = st.slider("Force d'attraction entre particules polaires", min_value=1.0, max_value=10.0, value=5.0, step=0.1)
repulsion_force = st.slider("Force de répulsion entre particules polaires", min_value=1.0, max_value=10.0, value=5.0, step=0.1)

# Angle d'interaction des polaires
polar_interaction_angle = st.slider("Angle de optimal d'attraction entre particules polaires (en radiants)", min_value=0.1, max_value=math.pi, value=math.pi / 4, step=0.01)

# Vitesse et rotation
vitesse = st.slider("Vitesse des particules", min_value=0.1, max_value=3.0, value=1.0, step=0.1)
rotation_speed = st.slider("Vitesse de rotation des particules", min_value=0.001, max_value=0.05, value=0.01, step=0.001)

# Lancer la simulation dans un thread séparé
if st.button("Lancer la simulation"):
    simulation_thread = threading.Thread(target=run_simulation, args=(particule_count_precurseur, particule_count_catalyseur, particule_count_intermediaire, particule_count_polaire, particle_radius, interaction_radius, attraction_force, repulsion_force, polar_interaction_angle, vitesse, rotation_speed))
    simulation_thread.start()
