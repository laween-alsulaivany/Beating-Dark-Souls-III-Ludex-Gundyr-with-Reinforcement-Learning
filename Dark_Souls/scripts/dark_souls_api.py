# dark_souls_api.py
import psutil
import math
import os
import time
import numpy as np
import pydirectinput
from colorama import Fore, Style
import gym_wrapper
import pointer_scanner as ps

"""
INFO
COLORS:
    # Fore.RED: ERROR.
    # Fore.GREEN: SUCCESS.
    # Fore.YELLOW: HEAL.
    # Fore.BLUE: WALK.
    # Fore.CYAN: DODGE.
    # Fore.MAGENTA: ATTACK.
    # Fore.WHITE: INFO.
    # Fore.RESET: Reset to default text color.

LOGS:
    # For state vector ordering:
    # [playerHealth: 0, playerStamina: 1, playerX: 2, playerY: 3, playerZ: 4, playerAngle: 5,
    #  bossHealth: 6, bossX: 7, bossY: 8, bossZ: 9, bossAngle: 10, bossAnim: 11]

"""


# Paths to logger output files
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(os.path.dirname(script_dir), "data")

GUNDYR_INFO_PATH = os.path.join(data_dir, "gundyr_info.txt")
TRIGGER_PATH = os.path.join(data_dir, "reset_trigger.txt")
LOCK_FILE_PATH = os.path.join(data_dir, "lock_on.txt")

current_movement = 0.0  # to track current movement state (0, 1)
attack_threshold = 5  # Only attack if within 4 units of boss
dodge_threshold = 4  # Only dodge if within 3 units of boss
counter = 0  # to track how many times the player has been waiting to enter the arena
current_step_global = 0  # to track the current step in the environment
reader = None  # Global reference
whiffed_attack = False  # Flag to track if the attack was a whiff
useless_dodge = False  # Flag to track if the dodge was useless

action_dict = {
    0: "light attack",
    1: "dodge",
    2: "heal"
}


def reset_environment():
    """
    Reset the game environment by triggering your Lua reset script.
    This should teleport the player to the proper position.
    """
    start = time.time()
    initialize_pointers()
    global reader, counter
    ready_for_training()
    while True:
        if get_player_in_boss_fight():
            heal_player()
            break
        wait_until_in_arena()
    print(Fore.WHITE + "🕹️   Getting ready for training...")
    print(Fore.WHITE + "🔁 Gym requested environment reset.")
    print(Fore.WHITE + f"🕒 Reset took: {time.time() - start:.2f} seconds")
    return get_state()


def send_in_game_actions(action):
    """
    Send in-game actions to DS3.
    """
    global current_movement, attack_threshold, dodge_threshold, reader, whiffed_attack, useless_dodge

    if get_player_in_boss_fight():
        if not ensure_lock_on_bruteforce():
            print("🛑 Could not lock on after multiple attempts.")
            return
    command = int(action['command'])
    movement = float(action['movement'])

    # Get current state once to decide on actions.
    state = get_state()
    playerHP = state[0]
    playerStamina = state[1]
    playerX = state[2]
    playerY = state[3]
    playerZ = state[4]
    playerAngle = state[5]
    bossHP = state[6]
    bossX = state[7]
    bossY = state[8]
    bossZ = state[9]
    bossAngle = state[10]

    # Extract player and boss positions for proximity checks.
    dist = abs(playerX - bossX)

    # ----- Command: Attack, Dodge, or Heal -----
    # if command == 0:
    #     # Light attack only if we're within 'attack_threshold'
    #     # if dist <= attack_threshold:
    #     pydirectinput.press('u')   # Press 'u' for attack
    # elif command == 1:
    #     # Dodge if close and the boss is in "Attack" animation
    #     # if dist < dodge_threshold and is_boss_anim(state, "A"):
    #     pydirectinput.press('space')
    if command == 0:  # Attack
        pydirectinput.press('u')
        # If far away, this is likely a whiff
        # let's define dist>6 as truly pointless, or you can keep your threshold
        if dist > attack_threshold:
            whiffed_attack = True

    elif command == 1:  # Dodge
        pydirectinput.press('space')
        # If you're not in danger, or boss isn't attacking, it's useless
        # We'll approximate "boss is not attacking" by bossHP>0 and dist>some_value,
        # or if you track boss animation
        if dist > dodge_threshold:
            useless_dodge = True
    elif command == 2:
        # Heal if player's HP is under ~250 and we have an Estus
        initial_health = playerHP
        estus_flasks = get_player_estus()
        if estus_flasks > 1 and initial_health <= 250:
            pydirectinput.press('r')

    # Process movement continuously:
    if abs(movement - current_movement) > 0.05:
        # Release any previously held movement keys.
        pydirectinput.keyUp('w')
        # Update movement based on new value.
        if movement > 0.1:
            try:
                with open(LOCK_FILE_PATH, 'r') as file:
                    status = file.read().strip()
                    if status == "locked":
                        print(
                            Fore.BLUE + "🚶‍♂️   Started holding 'w' for forward movement.")
                        pydirectinput.keyDown('w')
                    else:
                        print(
                            Fore.BLUE + "🫷   Stopped holding 'w' because not locked on to anything.")
                        pydirectinput.keyUp('w')
            except:
                pass

        else:
            # movement near 0: no key held.
            print(Fore.BLUE + "⏭️   No movement key held (movement ~0).")
        current_movement = movement
    else:
        # Movement value unchanged; keep holding the key.
        pass


def step_environment(action):
    """
    Apply the given action in the game environment.
    Returns the new state, reward, done flag, and info dictionary
    """
    # Handle any action format robustly
    try:
        # First, convert to numpy array to normalize the input
        action_array = np.array(action)
        
        # Flatten the array and take the first element
        flat_action = action_array.flatten()
        if len(flat_action) == 0:
            command = 0  # Default action
        else:
            command = int(flat_action[0])
            
        # Ensure command is within valid range (0, 1, 2 for Discrete(3))
        command = max(0, min(2, command))
        
    except Exception as e:
        print(Fore.YELLOW + f"⚠️  Action conversion error: {e}, using default action 0")
        command = 0
    
    if not is_ds3_running():
        print(Fore.RED + "❌ DS3 process not found. Exiting training...")
        raise RuntimeError("DS3 process not running.")
    # movement is binary: 1 means forward movement, 0 means no movement.
    movement = 1.0

    act = {"command": command, "movement": movement}
    send_in_game_actions(act)
    # Allow a brief delay for input effects
    time.sleep(0.02)
    state = get_state()
    reward = compute_reward(state, act)
    done = check_done(state)
    info = {}
    return state, reward, done, info


def one_hot_anim(anim_str):
    """
    Converts an animation string to a one-hot encoded vector.
    """
    anims = ["W", "E", "A", "T"]  # Define possible animations
    one_hot = [0, 0, 0, 0]  # Initialize one-hot vector with zeros
    if anim_str in anims:
        idx = anims.index(anim_str)  # Find the index of the animation
        one_hot[idx] = 1  # Set the corresponding index to 1
    return one_hot  # Return the numeric one-hot vector


def get_state():
    """
    Reads game state from your log files.
    """
    # FIXME: consider using estus as a state
    global reader
    player_state = [454.0, 95, 0.0, 0.0, 0.0, -2.78]
    boss_state = [1037.0, 150.0, 0.0, 0.0, 0.0]
    boss_anim_str = "idle"

    player_state[0] = float(get_playerHP() or 0.0)
    player_state[1] = float(get_player_stamina() or 0.0)
    player_state[2] = float(get_playerX() or 0.0)
    player_state[3] = float(get_playerY() or 0.0)
    player_state[4] = float(get_playerZ() or 0.0)
    player_state[5] = float(get_playerAngle() or 0.0)
    boss_state[0] = float(get_bossHP() or 0.0)

    gundyr_info = read_gundyr_info()

    if gundyr_info is not None:
        (
            boss_state[1],
            boss_state[2],
            boss_state[3],
            boss_state[4],
            boss_anim_str
        ) = gundyr_info

    else:
        print(Fore.YELLOW + "⚠ gundyr_info.txt not found or invalid. Using default boss state values.")
        boss_state[1], boss_state[2], boss_state[3], boss_state[4], boss_anim_str = 0.0, 0.0, 0.0, 0.0, "idle"

    anim_vector = one_hot_anim(boss_anim_str)
    state = np.array(player_state + boss_state + anim_vector, dtype=np.float32)
    return state


stale_counter = 0


def compute_reward(state, action):
    """
    Compute reward based on state and action.
    """
    global current_step_global, whiffed_attack, useless_dodge
    # Keep track of previous damage/reward values in a static dictionary
    # Initialize static storage on first call
    if not hasattr(compute_reward, "prev_values"):
        compute_reward.prev_values = {
            "player_damage": state[0],   # set to current player health
            "boss_damage": state[6],     # set to current boss health
            "reward": 0
        }

    # Extract previous values
    prev_player_health = compute_reward.prev_values["player_damage"]
    prev_boss_health = compute_reward.prev_values["boss_damage"]

    # Calculate damage
    # higher damage dealt = positive reward
    boss_damage = max(0, prev_boss_health - state[6])
    # damage taken = negative reward
    player_damage = max(0, prev_player_health - state[0])

    # positive reward for attacking - penalty for getting hit
    reward = (boss_damage*1) - (player_damage * 0.1)

    if whiffed_attack:
        reward -= 0.05  # small penalty for whiffing at long range
        whiffed_attack = False  # reset the flag
    if useless_dodge:
        reward -= 0.05
        whiffed_attack = False  # reset the flag
    # Detect changes (use a small tolerance to avoid floating-point noise)
    changed = (prev_player_health != state[0]) or (
        prev_boss_health != state[6])
    global stale_counter
    if compute_reward.prev_values["reward"] == reward:
        stale_counter += 1
        if stale_counter == 30:
            kill_player()
            print(Fore.RED + f"⚠️⚠️⚠️ Termined Episode due to staleness")
    else:
        stale_counter = 0

    compute_reward.prev_values["player_damage"] = state[0]
    compute_reward.prev_values["boss_damage"] = state[6]
    compute_reward.prev_values["reward"] = reward

    # Final reward calculations if boss or player is dead
    boss_dead = get_boss_flag()
    # boss_dead = (state[6] == 0)
    player_dead = (state[0] == 0)

    if boss_dead:
        # Bonus for defeating the boss
        reward += 500

    if player_dead:
        # Penalty for dying
        reward -= 75

    # Only print if damage/reward changed, OR the boss/player died
    if changed or boss_dead or player_dead:
        print(
            Fore.WHITE + f"\n 📍   Step: {time.strftime('%H:%M:%S')} {current_step_global}")
        print(
            Fore.WHITE + f"📊   Player damage: {player_damage:.2f}, Boss damage: {boss_damage:.2f}")
        print(Fore.WHITE + f"📊   Reward: {reward:.2f}")

        if boss_dead:
            print(
                Fore.WHITE + f"\n 📍   Step: {current_step_global}")
            print(Fore.WHITE +
                  f"📊   Final Reward (boss dead): {reward:.2f}")
        if player_dead:
            print(
                Fore.WHITE + f"\n 📍   Step: {current_step_global}")
            print(Fore.WHITE +
                  f"📊   Final Reward (player dead): {reward:.2f}")

    # Store new values for next comparison
    compute_reward.prev_values["player_damage"] = state[0]
    compute_reward.prev_values["boss_damage"] = state[6]
    compute_reward.prev_values["reward"] = reward
    return reward


def check_done(state):
    """
    The episode is done if the boss (index 6) or player (index 0) health is <= 0.
    """
    global current_movement

    if state[0] == 0:
        pydirectinput.keyUp('w')
        current_movement = 0.0
        print(Fore.GREEN + "✅   Episode done:  player health <= 0.")
        return True
    elif get_boss_flag():
        pydirectinput.keyUp('w')
        perform_gesture()
        current_movement = 0.0
        print(Fore.GREEN + "✅   Episode done:  boss health <= 0.")

        return True
    else:
        return False


# ------------------ #
#  HELPER FUNCTIONS  #
# ------------------ #
def perform_gesture():
    print(Fore.GREEN + "😊   Performing Gesture.")
    pydirectinput.press('g')
    time.sleep(0.1)
    pydirectinput.press('r')
    time.sleep(0.1)
    pydirectinput.press('g')


def kill_player(delay=7):
    ps.write_value(reader, [0x04543F60, 0x28, 0x3A0,
                   0x70, 0x90], 0, data_type="int", name="playerHP")
    print(Fore.WHITE + "🩸   Player killed manually.")
    time.sleep(delay)  # Wait for 7 seconds before checking the state again


def heal_player():
    ps.write_value(reader, [0x04543F60, 0x28, 0x3A0,
                            0x70, 0x90], 454, data_type="int", name="playerHP")
    print(Fore.WHITE + "❤️   Player healed manually.")


def change_player_angle(angle):
    PlayerX_PTR = [0x04543F60, 0x28, 0x80]
    x_address = reader.update_address(PlayerX_PTR, name="PlayerX")
    ps.write_float_using_address(
        reader, x_address - 0xC, angle, name="Player Angle Boss fight")  # Angle
    print(Fore.WHITE + f"🔄   Player angle changed to {angle}.")


def reset_boss_flag():
    ps.reset_boss_flag(reader)
    print(Fore.WHITE + "✅   Boss flag reset.")


def get_player_in_boss_fight():
    """
    Check if the player is currently in a boss fight.
    """
    if ps.get_player_in_boss_fight(reader):
        return True
    else:
        return False


def get_boss_flag():
    """
    Check if the boss is defeated.
    """
    return ps.get_boss_flag(reader)  # Returns True if boss is defeated, False otherwise


def teleport_to_boss():
    ps.teleport_to_boss(reader)
    print(Fore.WHITE + "✈️   Teleporting player to boss arena.")


def get_playerX():
    return ps.get_playerX(reader)


def get_playerY():
    return ps.get_playerY(reader)


def get_playerZ():
    return ps.get_playerZ(reader)


def get_playerAngle():
    return ps.get_playerAngle(reader)


def get_player_estus():
    return ps.get_player_estus(reader)


def get_player_stamina():
    return ps.get_player_stamina(reader)


def get_playerHP():
    return ps.get_player_HP(reader)


def get_bossHP():
    bosshp = ps.get_boss_HP(reader)
    if bosshp < 0 or bosshp > 1037:
        return -1
    return bosshp


def read_gundyr_info():
    """
    Reads the lines from gundyr_info.txt safely,
    returning (bossX, bossY, bossZ, bossAgle, bossAnim) or None if invalid.
    """
    filename = GUNDYR_INFO_PATH
    if not os.path.exists(filename):
        print(Fore.YELLOW + "⚠ gundyr_info.txt not found. Returning None.")
        return None

    try:
        with open(filename, "r") as f:
            line = f.readline().strip()
        parts = line.split(",")

        if len(parts) < 6:
            print(Fore.YELLOW + "⚠ Not enough data in gundyr_info.txt. Returning None.")
            return None

        gundyrX = float(parts[1])
        gundyrY = float(parts[2])
        gundyrZ = float(parts[3])
        gundyrAgle = float(parts[4])
        gundyrAnim = parts[5]
        return (gundyrX, gundyrY, gundyrZ, gundyrAgle, gundyrAnim)
    except Exception as e:
        print(Fore.RED + f"❌ Error reading boss info: {e}")
        return None


def env_trigger():
    """
    Write a trigger file to reset the game environment.
    """
    global TRIGGER_PATH
    with open(TRIGGER_PATH, "w") as f:
        f.write("reset")
    print(Fore.GREEN + "✅   Reset trigger file written.")


def ensure_lock_on_bruteforce():
    angles_to_try = [-2.5, 0.0, 2.5]

    for angle in angles_to_try:
        # Step 1: Check if already locked
        try:
            with open(LOCK_FILE_PATH, 'r') as file:
                status = file.read().strip()
                if status == "locked":
                    # print(Fore.GREEN + "🔒 Already locked on.")
                    return True
        except:
            pass

        # Step 2: Change angle and press Q
        change_player_angle(angle)
        time.sleep(0.05)
        pydirectinput.press('q')
        # print(Fore.WHITE + f"🎯 Trying to lock on at angle: {angle}")
        time.sleep(0.1)  # Give Lua time to detect

        # Step 3: Check again
        try:
            with open(LOCK_FILE_PATH, 'r') as file:
                status = file.read().strip()
                if status == "locked":
                    # print(Fore.GREEN +
                    #       f"✅ Lock-on successful at angle {angle}")
                    return True
        except:
            pass

    # print(Fore.RED + "❌ Failed to lock on after all angle attempts.")
    return False


# ------------------ #
#  Fight Setup        #
# ------------------ #

def wait_until_in_arena():
    """
    Waits until the player enters the boss arena. If the player is dead, triggers a reset instead of waiting.
    """
    global counter
    counter = 0  # reset each time
    while True:
        if get_player_in_boss_fight():
            heal_player()
            break
        time.sleep(2)
        start_fight()
        env_trigger()
        if counter == 1:
            print(Fore.RED + "🔃   Timeout: Trying again.")
        if counter >= 3:
            print(
                Fore.RED + "⏰   Timeout: Player did not enter boss arena." + Style.RESET_ALL)
            teleport_to_boss()
            print(Fore.WHITE + "🔁   Teleporting player to boss arena.")
            break
        counter += 1


def ready_for_training():
    """
    Prepare the environment for training.
    This function should be called once before starting the training loop.
    """
    if get_boss_flag():
        print(Fore.RED + "❌   Boss flag not reset. Resetting.")
        reset_boss_flag()
        time.sleep(0.5)
        kill_player(10)
    print("calling env_trigger()")
    env_trigger()
    print("calling teleport_to_boss()")
    teleport_to_boss()
    print("calling start_fight()")
    start_fight()
    print(Fore.GREEN + "🚀 Training can begin!")


def start_fight():
    time.sleep(0.5)  # Give some time for the game to load
    try:
        player_current_pos = get_state()[2]
    except Exception as e:
        print(Fore.RED + f"❌   Error getting player position: {e}")
        return

    if player_current_pos < 127 and player_current_pos > 122:
        print(Fore.WHITE + "⚔️   Starting fight...")
        pydirectinput.keyDown('w')  # Press and hold the 'w' key
        time.sleep(0.9)               # Hold it for 2 seconds
        pydirectinput.keyUp('w')    # Release the 'w' key
        print(Fore.WHITE + "🕹️   Holding 'w' for 2s for moving forward.")
        pydirectinput.press('e')
        print(Fore.WHITE + "🕹️   Executed 'e' press for interacting with fogwall.")
        time.sleep(1)
        pydirectinput.press('q')
        print(Fore.WHITE + "🕹️   Executed 'q' press for locking on to boss.")
        time.sleep(1)
    else:
        print(Fore.WHITE +
              f"Can't start fight, player_current_pos: {player_current_pos}")
        return


def is_boss_anim(state, tag):
    anims = {"W": 11, "E": 12, "A": 13, "T": 14}
    return state[anims[tag]] == 1


# ------------------ #
#  Pointers Setup     #
# ------------------ #

def initialize_pointers():
    """ Create a new PointerReader or re-attach to DS3. """
    global reader

    if reader is None:
        reader = ps.PointerReader("DarkSoulsIII.exe")
        print(Fore.WHITE + "✅ Reader attached once.")
    else:
        print(Fore.WHITE + "✅ Reusing existing reader.")


def is_ds3_running():
    """Returns True if DarkSoulsIII.exe is running."""
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == "DarkSoulsIII.exe":
            return True
    return False


class dark_souls_api:
    reset_environment = staticmethod(reset_environment)
    step_environment = staticmethod(step_environment)
    get_state = staticmethod(get_state)
    compute_reward = staticmethod(compute_reward)
    check_done = staticmethod(check_done)
