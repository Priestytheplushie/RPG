from colorama import Fore, Style
import random
import time
from tower.tower_data import tower_difficulty
from attack import calculate_attack
from tower.tower_data import bonus_ap, floor

class Enemy:
    def __init__(self, name, level, hp=None, strength=None, defense=None, speed=None, intelligence=None, weapon=None, loot_table_key="none"):
        self.name = name
        self.real_name = name
        self.weapon = weapon
        self.loot_table_key = loot_table_key
        self.level = max(1, level)  # Ensure a minimum level of 1
        self.status_effects = []

        # Use subclass-specific base stats if they are already set
        if not hasattr(self, 'base_hp'):
            self.base_hp = 10  # Default value, used if hp is not provided
        if not hasattr(self, 'base_strength'):
            self.base_strength = 2  # Default value, used if strength is not provided
        if not hasattr(self, 'base_defense'):
            self.base_defense = 1  # Default value, used if defense is not provided
        if not hasattr(self, 'base_speed'):
            self.base_speed = 5  # Default value, used if speed is not provided
        if not hasattr(self, 'base_intelligence'):
            self.base_intelligence = 3  # Default value, used if intelligence is not provided

        self.corrupted = False  # Default to False, can be set for corrupted enemies

        # If stats are not provided, use the base ones
        if hp is None:
            self.hp = max(self.base_hp * self.level, self.base_hp * 10)  # Ensure HP isn't too low
        else:
            self.hp = hp
        if strength is None:
            self.strength = self.base_strength * self.level
        else:
            self.strength = strength
        if defense is None:
            self.defense = self.base_defense * self.level
        else:
            self.defense = defense
        if speed is None:
            self.speed = self.base_speed + self.level
        else:
            self.speed = speed
        if intelligence is None:
            self.intelligence = self.base_intelligence + self.level
        else:
            self.intelligence = intelligence

        self.max_hp = self.hp  # Set max HP based on current HP

        self.adjust_for_difficulty()
        self.calculate_stats()

    def adjust_for_difficulty(self):
        global tower_difficulty

        # Use percentage values for easier scaling
        difficulty_settings = {
            "Easy": {"multiplier": 75, "rounding": "down"},
            "Normal": {"multiplier": 100, "rounding": "normal"},
            "Hard": {"multiplier": 125, "rounding": "up"},
            "Hardcore": {"multiplier": 150, "rounding": "up"}
        }

        setting = difficulty_settings.get(tower_difficulty.capitalize(), {"multiplier": 100, "rounding": "normal"})
        self.difficulty_multiplier = setting["multiplier"]
        self.rounding_method = setting["rounding"]


    def calculate_stats(self):
        global floor

        # Integer-only scaling
        floor_multiplier = 100 + (floor * 10)  # Represent as percentage

        def apply_scaling(base_stat):
            raw = (base_stat + self.level) * floor_multiplier * self.difficulty_multiplier
            scaled = raw // 10000  # Since both are percent-based (e.g., 125 * 110)
            if self.rounding_method == "up":
                return max(1, int(scaled) + (1 if raw % 10000 != 0 else 0))
            elif self.rounding_method == "down":
                return max(1, int(scaled))  # Floor division already rounds down
            else:
                return max(1, round(scaled))

        self.hp = apply_scaling(self.base_hp)
        self.strength = apply_scaling(self.base_strength)
        self.defense = apply_scaling(self.base_defense)
        self.speed = apply_scaling(self.base_speed)
        self.intelligence = apply_scaling(self.base_intelligence)

        self.max_hp = self.hp


    def apply_status(self, effect_name, duration):
        found = False
        for effect in self.status_effects:
            if effect['name'] == effect_name:
                effect['duration'] = duration
                found = True
        if not found:
            self.status_effects.append({'name': effect_name, 'duration': duration})

    def has_status(self, effect_name):
        for effect in self.status_effects:
            if effect['name'] == effect_name:
                return True
        return False

    def tick_status_effects(self):
        remaining = []
        for effect in self.status_effects:
            effect['duration'] -= 1
            if effect['duration'] > 0:
                remaining.append(effect)
            else:
                print(self.name + " is no longer affected by " + effect['name'] + ".")
                print("")
        self.status_effects = remaining

    def basic_attack(self, player):
        if random.random() < 0.10:
            print(Fore.YELLOW + self.name + " swings at " + player.name + " but misses!" + Fore.WHITE)
            print("")
            time.sleep(1)
            return
        raw_damage = calculate_attack(self.strength, 0)
        damage = max(1, raw_damage - player.defense)
        player.hp -= damage
        print(self.name + " attacks " + player.name + " for " + str(damage) + " damage!")
        print("")
        if player.defense > 0:
            print(Fore.LIGHTBLACK_EX + "(Reduced from " + str(raw_damage) + " by defense)" + Fore.WHITE)
            print("")

        print(player.name + " remaining HP: " + str(player.hp))
        print("")

    def choose_action(self, target):
        if self.has_status('stagger'):
            print(self.name + " is staggered and misses their turn!")
            print("")
            return
        self.basic_attack(target)

    def reveal_identity(self):
        self.name = self.real_name
        print("")
        print(Fore.YELLOW + "The veil lifts... it's a " + self.real_name + "!" + Fore.WHITE)
        print("")

        if self.corrupted:
            print(Fore.RED + "\nA dark aura surrounds it... This enemy is CORRUPTED!")
            print(Fore.MAGENTA + "The corruption has twisted its form and powers, making it far more dangerous than before!" + Fore.WHITE)
        else:
            print(Fore.GREEN + "This enemy appears to be normal, free of corruption." + Fore.WHITE)


class CorruptedHuman(Enemy):
    def __init__(self, level, weapon=None, loot_table_key="none"):
        self.base_hp = 50
        self.base_strength = 10
        self.base_defense = 5
        self.base_speed = 5
        self.base_intelligence = 100
        self.real_name = Fore.GREEN+"Corrupted Human"+Fore.WHITE

        super().__init__(name=Fore.MAGENTA+"???"+Fore.WHITE, level=level, weapon=weapon, loot_table_key=loot_table_key)
        self.corrupted = True
        self.max_hp = self.hp

    def use_item(self):
        items = [
            "Health Potion",
            "Strength Potion",
            "Defense Potion"
        ]

        used_item = random.choice(items)

        if used_item == "Health Potion":
            heal_amount = 25
            print(self.name, Fore.WHITE + "used Health Potion and restored", Fore.RED + str(heal_amount), Fore.WHITE + "HP!")
            time.sleep(1)

            # Prevent over-healing
            self.hp = min(self.hp + heal_amount, self.max_hp)  # Ensure HP doesn't exceed max HP

        elif used_item == "Strength Potion":
            print(self.name, Fore.WHITE + "used Strength Potion and increased strength by", Fore.RED + "5", Fore.WHITE)
            time.sleep(1)
            self.strength += 5

        elif used_item == "Defense Potion":
            print(self.name, Fore.WHITE + "used Defense Potion and increased Defense by", Fore.RED + "5", Fore.WHITE)
            time.sleep(1)
            self.defense += 5

    def choose_action(self, target):
        if self.has_status('stagger'):
            print(self.name + " is staggered and misses their turn!")
            print("")
            return
        if random.random() < 0.3:
            self.use_item()
        else:
            self.basic_attack(target)


class CorruptedWarrior(Enemy):
    def __init__(self, level, weapon=None, loot_table_key="none"):
        self.base_hp = 45
        self.base_strength = 20
        self.base_defense = 10
        self.base_speed = 0
        self.base_intelligence = 50
        self.real_name = Fore.GREEN+"Corrupted Warrior"+Fore.WHITE

        super().__init__(name=Fore.MAGENTA+"Warrior"+Fore.WHITE, level=level, weapon=weapon, loot_table_key=loot_table_key)
        self.corrupted = True
        self.max_hp = self.hp

    def battle_cry(self):
        print(Fore.WHITE+self.name+Fore.WHITE+" roars into the air, increasing their natural strength by +1")
        self.strength += 1

    def heavy_charge(self, player):
        if random.random() < 0.30:
            print(Fore.YELLOW + self.name +Fore.YELLOW+ " charges at " + player.name + " but misses!" + Fore.WHITE)
            print("")
            time.sleep(1)
            return
        raw_damage = calculate_attack(self.strength, 10)
        damage = max(1, raw_damage - player.defense)
        player.hp -= damage
        print(self.name + " charges at " + player.name + " dealing " + str(damage) + " damage!")
        print("")
        if player.defense > 0:
            print(Fore.LIGHTBLACK_EX + "(Reduced from " + str(raw_damage) + " by defense)" + Fore.WHITE)
            print("")

        print(player.name + " remaining HP: " + str(player.hp))
        print("")
        if random.random() < 0.2:
            time.sleep(1)
            player.apply_status('stagger', 1)

    def choose_action(self, target):
        if self.has_status('stagger'):
            print(self.name + " is staggered and misses their turn!")
            print("")
            return
        if random.random() < 0.3:
            self.battle_cry()
        else:
            if random.randint(0, 100) < 40:
                self.heavy_charge(target)
            else:
                self.basic_attack(target)

class CorruptedMage(Enemy):
    def __init__(self, level, weapon=None, loot_table_key="none"):
        self.base_hp = 25
        self.base_strength = 5
        self.base_defense = 2
        self.base_speed = 4
        self.base_intelligence = 20
        self.real_name = Fore.GREEN+"Corrupted Mage"+Fore.WHITE

        super().__init__(name=Fore.MAGENTA+"Mage"+Fore.WHITE, level=level, weapon=weapon, loot_table_key=loot_table_key)
        self.corrupted = True
        self.max_hp = self.hp

    def fireball(self, target):
        if random.random() < 0.2:
            print(Fore.YELLOW + self.name + " casts Fireball, but it misses!" + Fore.WHITE)
            print("")
            time.sleep(1)
            return
        damage = random.randint(10, 20)  # Fireball damage
        print(self.name + " casts Fireball at " + target.name + " for " + str(damage) + " damage!")
        target.hp -= damage
        print(target.name + " remaining HP: " + str(target.hp))
        print("")
        
        # 30% chance to burn an item (rendering it unusable)
        if random.random() < 0.30:
            burned_item = random.choice(target.inventory.items)
            print(Fore.RED + burned_item.name + " was burned and is now unusable!" + Fore.WHITE)
            target.inventory.items.remove(burned_item)

    def energy_ball(self, target):
        damage = random.randint(5, 15)  # Energy Ball damage
        print(self.name + " casts Energy Ball at " + target.name + " for " + str(damage) + " damage!")
        target.hp -= damage
        print(target.name + " remaining HP: " + str(target.hp))
        print("")

    def choose_action(self, target):
        if self.has_status('stagger'):
            print(self.name + " is staggered and misses their turn!")
            print("")
            return
        # 60% chance for Fireball, 40% for Energy Ball
        if random.random() < 0.6:
            self.fireball(target)
        else:
            self.energy_ball(target)
