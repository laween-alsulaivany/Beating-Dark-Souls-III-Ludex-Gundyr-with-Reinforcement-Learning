# gym_wrapper.py
import gymnasium as gymn
import gym
from gym import spaces
import numpy as np
import time
from colorama import Fore
import dark_souls_api
import pointer_scanner as ps

reader = ps.PointerReader("DarkSoulsIII.exe")
episode = 0


class DarkSoulsGundyrEnv(gym.Env):
    metadata = {"render.modes": ["human"]}

    def __init__(self, render_mode="human"):
        super(DarkSoulsGundyrEnv, self).__init__()
        self.render_mode = render_mode
        # Our state vector has 15 elements.
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(15,), dtype=np.float32)
        self.action_space = spaces.Discrete(3)
        self.current_state = None
        self.steps = 0
        self.max_steps = 1000  # Max steps per episode
        # For stale position check.
        self.last_player_position = None
        self.last_position_time = None
        self.position_threshold = 0.01  # Minimum change to count as movement.

    def seed(self, seed=None):
        np.random.seed(seed)
        return [seed]

    def reset(self, **kwargs):
        print(Fore.WHITE + "🔄   gym_wrapper.py: Resetting environment...")
        print(Fore.WHITE + "--------------------------------")
        print(Fore.WHITE + f"📘   Sleeping 8 seconds")
        print(Fore.WHITE + "--------------------------------")
        time.sleep(8)

        max_retries = 10
        for attempt in range(max_retries):
            self.current_state = dark_souls_api.reset_environment()

            # Check for valid state
            if self.current_state is None or np.any(np.isnan(self.current_state)):
                print(
                    Fore.YELLOW + f"⏳   Attempt {attempt+1}/{max_retries}: Invalid state, retrying...")
                time.sleep(1)
                continue

            # Try reading player HP
            try:
                hp = reader.resolve(
                    [0x04543F60, 0x28, 0x3A0, 0x70, 0x90], data_type="4byte")
                if hp and hp > 0:
                    print(Fore.GREEN +
                          f"✅   Reset successful. Player HP: {hp}")
                    break
                else:
                    print(
                        Fore.YELLOW + f"⏳   Attempt {attempt+1}/{max_retries}: HP = 0, retrying...")
            except:
                print(
                    Fore.RED + f"❌   Attempt {attempt+1}/{max_retries}: Error reading HP, retrying...")

            time.sleep(1)

        self.steps = 0
        self.last_player_position = None
        self.last_position_time = None
        return self.current_state, {}

    def step(self, action):
        self.steps += 1
        dark_souls_api.current_step_global = self.steps
        next_state, reward, done, info = dark_souls_api.step_environment(
            action)
        self.current_state = next_state

        terminated = False
        truncated = False
        if done:
            # Boss is dead
            if dark_souls_api.get_boss_flag():
                # if self.current_state[6] == 0:
                print(
                    Fore.WHITE + "🏆   Boss is dead. Waiting 5 seconds before ending episode...")
                time.sleep(5)
                dark_souls_api.reset_boss_flag()
                dark_souls_api.kill_player(0)
                terminated = True
            # Player is dead
            elif self.current_state[0] == 0:
                print(Fore.WHITE + "💀   Player is dead. Waiting to respawn in arena...")
                terminated = True

        # Timeout
        elif self.steps >= self.max_steps:
            truncated = True

        # Enrich info
        if terminated:
            info["death_reason"] = "boss dead" if self.current_state[6] == 0 else "player dead"
        elif truncated:
            info["death_reason"] = "timeout"
        else:
            info["death_reason"] = "alive"

        return self.current_state, reward, terminated, truncated, info

    def render(self):
        if self.render_mode == "human":
            print(Fore.WHITE + "ℹ️   gym_wrapper.py:  Current State:",
                  self.current_state)

    def close(self):
        pass


# --- Gymnasium Compatibility Wrapper ---

class GymnasiumCompatEnv(gymn.Env):
    def __init__(self, env):
        super().__init__()
        self.env = env
        self.observation_space = gymn.spaces.Box(
            low=env.observation_space.low,
            high=env.observation_space.high,
            shape=env.observation_space.shape,
            dtype=env.observation_space.dtype,
        )
        self.action_space = gymn.spaces.Discrete(env.action_space.n)
        self.metadata = env.metadata

    def reset(self, **kwargs):

        obs = self.env.reset(**kwargs)
        global episode
        episode += 1
        print(Fore.WHITE + "--------------------------------")
        print(Fore.WHITE + f"🎬 Episode: {episode} started.")
        print(Fore.WHITE + "--------------------------------")
        if isinstance(obs, tuple):
            return obs
        return obs, {}

    def step(self, action):

        obs, reward, terminated, truncated, info = self.env.step(action)
        if terminated:
            print(Fore.WHITE + "--------------------------------")
            print(Fore.WHITE + f"📘   Episode: {episode} terminated.")
            print(Fore.WHITE + "--------------------------------")
            info["death_reason"] = "boss dead" if self.env.current_state[6] == 0 else "player dead"

        elif truncated:
            print(Fore.WHITE + "--------------------------------")
            print(Fore.WHITE + f"📘   Episode: {episode} truncated.")
            print(Fore.WHITE + "--------------------------------")
            info["death_reason"] = "timeout"
        else:
            info["death_reason"] = "alive"
        return obs, reward, terminated, truncated, info

    def render(self, mode="human"):
        return self.env.render(mode)

    def close(self):
        return self.env.close()


# For local testing:
if __name__ == "__main__":
    env = DarkSoulsGundyrEnv()
    obs = env.reset()
    done = False
    total_reward = 0
    while not done:
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        total_reward += reward
        env.render()
        time.sleep(0.1)
    print(Fore.GREEN + "✅   gym_wrapper.py: Episode finished with total reward:", total_reward)
    env.close()
