import random

from grassland.config import DAY_LENGTH_HOURS
from grassland.config import GAME_HOURS_PER_SECOND
from grassland.config import WORLD_HEIGHT
from grassland.config import WORLD_WIDTH
from grassland.geometry import Vec2
from grassland.physics import PhysicsEngine


class Environment:
    def __init__(self):
        self.day = 1
        self.time = 6.0
        self.weather = "sunny"
        self.temperature = 28
        self.ended = False
        self.end_reason = ""

    def update(self, dt):
        previous_day = self.day
        game_hours = dt * GAME_HOURS_PER_SECOND
        self.change_time(game_hours)
        return self.day != previous_day

    def change_time(self, hours):
        self.time = self.time + hours

        while self.time >= DAY_LENGTH_HOURS:
            self.time = self.time - DAY_LENGTH_HOURS
            self.change_day()

    def change_day(self):
        self.day = self.day + 1
        self.change_weather()
        self.change_temperature()

    def change_weather(self):
        self.weather = random.choice(["sunny", "cloudy", "rain", "drought"])

    def change_temperature(self):
        if self.weather == "drought":
            self.temperature = random.randint(34, 42)
        elif self.weather == "rain":
            self.temperature = random.randint(20, 28)
        elif self.weather == "cloudy":
            self.temperature = random.randint(23, 31)
        else:
            self.temperature = random.randint(27, 36)

    def clock_text(self):
        hour = int(self.time)
        minute = int((self.time - hour) * 60)
        return str(hour).zfill(2) + ":" + str(minute).zfill(2)


class DroughtEvent:
    def __init__(self, drought_intensity):
        self.drought_intensity = drought_intensity

    def dry_up_map(self, world, dt):
        for resource in world.resources:
            if resource.kind == "resource" and resource.name == "Water_Puddle" and resource.alive:
                resource.consume(dt * self.drought_intensity * 3.0)


class MapObject:
    def __init__(self, name, kind, position, radius, color):
        self.name = name
        self.kind = kind
        self.position = position
        self.radius = radius
        self.color = color
        self.velocity = Vec2()
        self.alive = True
        self.solid = False
        self.action_text = ""

    def update(self, world, dt):
        return None

    def contains(self, entity):
        return self.position.distance_to(entity.position) <= self.radius


class BasicPlant(MapObject):
    def __init__(self, name, position, radius, color, health):
        MapObject.__init__(self, name, "plant", position, radius, color)
        self.health = health

    def consume(self, amount):
        eaten = min(self.health, amount)
        self.health = self.health - eaten
        if self.health <= 0:
            self.alive = False
        return eaten


class BasicResource(MapObject):
    def __init__(self, name, position, radius, color, amount):
        MapObject.__init__(self, name, "resource", position, radius, color)
        self.amount = amount
        self.max_amount = amount
        self.carried_by = None
        self.being_eaten_by = None

    def consume(self, amount):
        taken = min(self.amount, amount)
        self.amount = self.amount - taken
        if self.amount <= 0:
            self.alive = False
        return taken

    def regenerate(self, amount):
        self.amount = min(self.max_amount, self.amount + amount)
        self.alive = True

    def reduce_thirst(self, animal):
        taken = self.consume(18)
        animal.thirst = max(0.0, animal.thirst - taken)

    def fill_rain(self):
        self.regenerate(35)


class BasicTerrain(MapObject):
    def __init__(self, name, position, radius, color):
        MapObject.__init__(self, name, "terrain", position, radius, color)

    def enable_drinking(self, animal):
        animal.thirst = max(0.0, animal.thirst - 18.0)

    def hide_entity(self, entity):
        entity.is_hidden = True
        entity.action_text = "hidden"


class World:
    def __init__(self, width=WORLD_WIDTH, height=WORLD_HEIGHT):
        self.width = width
        self.height = height
        self.environment = Environment()
        self.physics = PhysicsEngine(width, height)
        self.elapsed = 0.0
        self.animals = []
        self.plants = []
        self.resources = []
        self.terrains = []
        self.drought_event = None

    @classmethod
    def seed_default(cls):
        world = cls()
        world.seed_terrain()
        world.seed_plants()
        world.seed_resources()
        return world

    def seed_terrain(self):
        self.terrains.append(BasicTerrain("Plain", Vec2(self.width / 2, self.height / 2), max(self.width, self.height), (126, 184, 92)))
        self.terrains.append(BasicTerrain("Lake_Side", Vec2(310, 260), 82, (79, 156, 201)))
        self.terrains.append(BasicTerrain("Cave", Vec2(1470, 890), 64, (82, 75, 67)))

    def seed_plants(self):
        self.plants.append(BasicPlant("Grass", Vec2(520, 300), 16, (83, 174, 80), 55))
        self.plants.append(BasicPlant("Grass", Vec2(780, 360), 16, (83, 174, 80), 55))
        self.plants.append(BasicPlant("Grass", Vec2(1080, 460), 16, (83, 174, 80), 55))
        self.plants.append(BasicPlant("Bush", Vec2(900, 260), 30, (47, 119, 67), 80))
        self.plants.append(BasicPlant("Acacia_Tree", Vec2(760, 660), 34, (97, 142, 63), 130))
        self.plants.append(BasicPlant("Baobab_Tree", Vec2(1010, 930), 42, (151, 120, 72), 180))

    def seed_resources(self):
        self.resources.append(BasicResource("Water_Puddle", Vec2(410, 360), 28, (65, 145, 208), 100))
        self.resources.append(BasicResource("Water_Puddle", Vec2(1330, 980), 28, (65, 145, 208), 100))
        self.resources.append(BasicResource("Carcass", Vec2(1120, 540), 20, (118, 72, 44), 85))

    def update(self, dt):
        if self.environment.ended:
            return

        self.elapsed = self.elapsed + dt
        new_day = self.environment.update(dt)

        if new_day:
            self.on_new_day()

        if self.environment.weather == "drought":
            if self.drought_event is None:
                self.drought_event = DroughtEvent(random.uniform(0.5, 1.0))
            self.drought_event.dry_up_map(self, dt)
        else:
            self.drought_event = None

        for plant in self.plants:
            plant.update(self, dt)

        for animal in self.animals:
            if hasattr(animal, "update"):
                animal.update(self, dt)

        self.physics.update(self.living_animals(), dt)

        for resource in self.resources:
            resource.update(self, dt)

        self.check_end_conditions()

    def on_new_day(self):
        if self.environment.weather == "rain":
            for water in self.water_puddles():
                water.fill_rain()

    def check_end_conditions(self):
        if self.environment.weather == "drought" and self.environment.day >= 3:
            water_left = 0
            for water in self.water_puddles():
                if water.alive:
                    water_left = water_left + water.amount

            if water_left <= 2:
                self.environment.ended = True
                self.environment.end_reason = "가뭄으로 물이 말라 생태계가 종료되었습니다."

    def spawn_carcass(self, animal):
        name = getattr(animal, "name", "animal")
        position = getattr(animal, "position", Vec2(self.width / 2, self.height / 2))
        self.resources.append(BasicResource("Carcass", position.copy(), 20, (118, 72, 44), 85))

    def living_animals(self):
        living = []
        for animal in self.animals:
            if getattr(animal, "alive", True):
                living.append(animal)
        return living

    def alive_plants(self):
        living = []
        for plant in self.plants:
            if plant.alive:
                living.append(plant)
        return living

    def water_puddles(self):
        result = []
        for resource in self.resources:
            if resource.name == "Water_Puddle" and resource.alive:
                result.append(resource)
        return result

    def carcasses(self):
        result = []
        for resource in self.resources:
            if resource.name == "Carcass" and resource.alive:
                result.append(resource)
        return result

    def nearest_alive(self, items, position, predicate=None, max_distance=None):
        nearest = None
        best_distance = float("inf")

        for item in items:
            if not getattr(item, "alive", True):
                continue

            if predicate is not None and not predicate(item):
                continue

            distance = position.distance_to(item.position)

            if max_distance is not None and distance > max_distance:
                continue

            if distance < best_distance:
                best_distance = distance
                nearest = item

        return nearest

    def nearest_plant(self, position):
        return self.nearest_alive(self.plants, position)

    def nearest_bush(self, position, max_distance):
        def is_bush(item):
            return item.name == "Bush"

        return self.nearest_alive(self.plants, position, is_bush, max_distance)

    def nearest_carcass(self, position):
        def is_free_carcass(item):
            return item.name == "Carcass" and item.carried_by is None

        return self.nearest_alive(self.resources, position, is_free_carcass)

    def nearest_water(self, position):
        water_items = []

        for water in self.water_puddles():
            water_items.append(water)

        for terrain in self.terrains:
            if terrain.name == "Lake_Side":
                water_items.append(terrain)

        return self.nearest_alive(water_items, position)

    def nearest_predator(self, animal, max_distance):
        def is_threat(item):
            role = getattr(item, "role", getattr(item, "diet_type", ""))
            return item is not animal and role == "carnivore" and getattr(item, "alive", True)

        return self.nearest_alive(self.animals, animal.position, is_threat, max_distance)

    def nearest_prey_for(self, predator, max_distance):
        def is_prey(item):
            role = getattr(item, "role", getattr(item, "diet_type", ""))
            return item is not predator and role in ["herbivore", "omnivore"]

        return self.nearest_alive(self.animals, predator.position, is_prey, max_distance)

    def nearest_named(self, name, position, max_distance):
        def has_name(item):
            return getattr(item, "name", "") == name

        return self.nearest_alive(self.animals, position, has_name, max_distance)

    def nearest_same_species(self, animal, radius):
        # 자기 자신을 제외하고 같은 이름(같은 종)의 가장 가까운 동물을 반환
        def is_same_species(item):
            return item is not animal and getattr(item, "name", "") == animal.name

        return self.nearest_alive(self.animals, animal.position, is_same_species, radius)

    def spawn_offspring(self, parent):
        # 부모와 같은 클래스의 자손을 부모 근처에 생성하고 animals 목록에 추가
        # 각 동물 서브클래스(Gazelle, Zebra 등)는 position 하나만 받는 생성자를 가짐
        offset = Vec2(random.uniform(-30, 30), random.uniform(-30, 30))
        new_position = Vec2(
            max(0.0, min(float(self.width), parent.position.x + offset.x)),
            max(0.0, min(float(self.height), parent.position.y + offset.y)),
        )
        try:
            offspring = type(parent)(new_position)
            self.animals.append(offspring)
        except Exception:
            pass

    def nearest_terrain_type(self, terrain_name, position):
        def has_terrain_name(item):
            return item.name == terrain_name

        return self.nearest_alive(self.terrains, position, has_terrain_name)

    def carcass_eaten_by_lion_near(self, position, max_distance):
        def matches(carcass):
            eater = carcass.being_eaten_by
            return eater is not None and getattr(eater, "name", "") == "Lion"

        return self.nearest_alive(self.carcasses(), position, matches, max_distance)

    def expel_meerkats_from_cave(self, cave):
        for animal in self.living_animals():
            if getattr(animal, "name", "") == "Meerkat" and cave.contains(animal):
                if hasattr(animal, "move_away_from"):
                    animal.move_away_from(cave.position, animal.speed * 1.3)
                animal.action_text = "expelled"
                animal.is_hidden = False

    def current_drought_intensity(self):
        if self.environment.weather != "drought" or self.drought_event is None:
            return 0.0
        return self.drought_event.drought_intensity

    def counts_by_name(self):
        counts = {}
        for animal in self.living_animals():
            name = getattr(animal, "name", "Animal")
            counts[name] = counts.get(name, 0) + 1
        return counts

