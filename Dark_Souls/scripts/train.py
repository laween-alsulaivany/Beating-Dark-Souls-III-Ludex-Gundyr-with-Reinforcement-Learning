# train.py
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import VecMonitor, VecNormalize
import gym_wrapper
import os
from colorama import Fore


class StepLoggerCallback(BaseCallback):
    def _on_step(self) -> bool:
        if self.locals.get("dones") is not None:
            for i, done in enumerate(self.locals["dones"]):
                if done:
                    print(
                        f"✅ SB3: Env {i} episode {gym_wrapper.episode+1} ended at {self.num_timesteps} steps")
                    print(
                        f"🚧 SB3: Progress at {(self.num_timesteps/total_timesteps)*100:.2f}%")
        return True


if __name__ == "__main__":
    print(Fore.WHITE + "🗂️   Current working directory:", os.getcwd())

    def make_env():
        env = gym_wrapper.DarkSoulsGundyrEnv()
        wrapped_env = gym_wrapper.GymnasiumCompatEnv(env)
        return Monitor(wrapped_env, filename=f"./logs/monitor_{os.getpid()}.csv")

    env = make_vec_env(make_env, n_envs=1, seed=2)
    vec_normalize_env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)

    # Try to load existing normalization stats, or start fresh if not found
    try:
        vec_normalize_env = VecNormalize.load("./data/vecnormalize_stats_v2.pkl", vec_normalize_env)
        print(Fore.YELLOW + "🔄 Loaded existing normalization stats from v2")
    except FileNotFoundError:
        print(Fore.YELLOW + "⚠️  No existing normalization stats found, starting fresh")
    
    env = VecMonitor(vec_normalize_env)

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        tensorboard_log="./logs/",
        device="cuda",
        n_steps=2048,               # or 2048, if you want
        batch_size=128,            # was 128 by default
        learning_rate=1e-3,        # was 1e-4 by default
        gamma=0.99,                # 0.99 is typical; you could adjust
        policy_kwargs=dict(net_arch=[128, 128]),  # was [256, 256] by default
        ent_coef=0.05,  # makes the model explore more actions, recieves minor punishment for repeated actions

    )

    total_timesteps = 51_200  # Adjust timesteps as needed

    try:
        print(
            Fore.WHITE + f"🧪 train.py: Starting training for {total_timesteps} timesteps...")
        model.learn(total_timesteps=total_timesteps,
                    callback=StepLoggerCallback())
        print(Fore.GREEN + "✅ train.py: Training completed.")
    finally:
        model.save("ppo_dark_souls_gundyr_v5")
        print(Fore.GREEN + "✅ train.py: Model saved as 'ppo_dark_souls_gundyr_v5.zip'")
        vec_normalize_env.save("vecnormalize_stats_v5.pkl")
        print(
            Fore.GREEN + "✅ train.py: VecNormalize stats saved as 'vecnormalize_stats_v5.pkl'")
    
    # Try to load existing model for testing, or skip if not found
    try:
        model = PPO.load("./data/ppo_dark_souls_gundyr_v2", env=env)
        print(Fore.YELLOW + "🔄 Loaded existing model v2 for testing")
        
        obs = env.reset()
        done = False
        total_reward = 0

        print(Fore.GREEN + "✅ train.py: Test episode total reward:", total_reward)
    except FileNotFoundError:
        print(Fore.YELLOW + "⚠️  No existing model found for testing, skipping test episode")
    
    env.close()
