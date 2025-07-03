# Dark Souls III - Reinforcement Learning Agent for Iudex Gundyr

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> A reinforcement learning project that trains an AI agent to defeat Iudex Gundyr, the first boss in Dark Souls III, using Proximal Policy Optimization (PPO) and real-time game state manipulation.

## 🎮 Overview

This project implements a reinforcement learning environment that interfaces directly with Dark Souls III to train an AI agent to defeat the tutorial boss, Iudex Gundyr. The agent learns through trial and error, receiving rewards for dealing damage to the boss and penalties for taking damage, ultimately developing strategies to overcome this challenging encounter.

> **Note**: This is an updated version of the original [FP-Machine-Learning project](https://github.com/Zach-A-Moore/FP-Machine-Learning) developed as a class collaboration. The original repository contains the initial proof-of-concept but is now outdated compared to this updated implementation.

### 🌟 Key Features

- **Real-time Game Integration**: Direct memory manipulation and input simulation with Dark Souls III
- **PPO-based Learning**: Uses Stable-Baselines3's PPO implementation for robust policy learning
- **Comprehensive State Space**: Tracks player and boss positions, health, stamina, and boss animations
- **Automated Environment Reset**: Seamless episode transitions with automatic player respawning and boss arena setup
- **Detailed Logging**: Comprehensive training metrics and progress tracking
- **Memory-Safe Operations**: Robust pointer scanning and memory management

## 🏗️ Architecture

### Environment Components

- **Game State Reader**: Extracts real-time game state using memory scanning
- **Action Executor**: Translates AI decisions into game inputs (attack, dodge, heal, movement)
- **Reward System**: Calculates rewards based on damage dealt/received and survival time
- **Episode Manager**: Handles automatic resets and boss fight initialization

### Action Space

The agent can perform three discrete actions:
- **0**: Light Attack (`u` key)
- **1**: Dodge Roll (`space` key)  
- **2**: Heal (`r` key - Estus Flask)

Movement is handled automatically with forward movement when locked onto the boss.

### Observation Space

16-dimensional state vector containing:
- Player: Health, Stamina, Position (X,Y,Z), Angle
- Boss: Health, Position (X,Y,Z), Angle
- Boss Animation: One-hot encoded (Wait, Evade, Attack, Transform)

## 🚀 Installation

### Prerequisites

- **Windows 10/11** (required for game integration)
- **Python 3.8+**
- **Dark Souls III** (Steam version recommended)
- **Cheat Engine 7.5** ([Download here](https://cheatengine.org/downloads.php))
- **CUDA-compatible GPU** (recommended for faster training)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/Beating-Dark-Souls-III-Ludex-Gundyr-with-Reinforcement-Learning.git
cd Beating-Dark-Souls-III-Ludex-Gundyr-with-Reinforcement-Learning/Dark_Souls
```

### Step 2: Create Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Setup Cheat Engine

1. Install Cheat Engine 7.5
2. **Update the enable_flags.lua script**:
   - Open `CheatEngine75/autorun/enable_flags.lua`
   - Change the first line to point to your `DS3_Table_V4.CT` file location:
     ```lua
     loadTable("C:\\Path\\To\\Your\\DS3_Table_V4.CT")
     ```
3. Copy the updated `enable_flags.lua` script to your Cheat Engine autorun folder:
   ```
   C:\Program Files\Cheat Engine 7.5\autorun\
   ```
4. **Manual Script Directory Setup** (Required):
   - Launch Cheat Engine and load Dark Souls III
   - Open the Custom Scripts group in the memory table
   - **For each script**, right-click and edit the directory paths to match your project location
   - This step is unfortunately necessary due to Cheat Engine's path handling

The script will automatically load the required memory table when Cheat Engine starts.

## 🎯 Usage

### Quick Start

1. **Launch Dark Souls III** and load a character
2. **Start Cheat Engine** (the autorun script will load automatically)
3. **Increase the game speed** to 5x (optional, but speeds up training)
   - Open Cheat Engine, select Dark Souls III process, and set speed to 5.0
4. **Navigate** to the first bonfire
5. **Run the training script**:

```bash
python scripts/train.py
```

6. **Switch back to Game Window**: switch to the game window to see the agent in action for input registration


### Training Configuration

The training can be customized by modifying parameters in `train.py`:

```python
# Training parameters
total_timesteps = 51_200        # Total training steps
n_steps = 2048                  # Steps per update
batch_size = 128                # Training batch size
learning_rate = 1e-3            # Learning rate
gamma = 0.99                    # Discount factor
```

### Monitoring Progress

- **Console Output**: Real-time training metrics and episode progress
- **TensorBoard**: Launch with `tensorboard --logdir=./logs/`
- **Model Checkpoints**: Automatically saved after training completion

## 📊 Training Process

### Episode Flow

1. **Reset**: Player respawns, boss resets, arena setup
2. **Action Loop**: Agent observes state → selects action → executes in game
3. **Reward Calculation**: Based on damage dealt/received
4. **Episode End**: Player death, boss defeat, or timeout
5. **Repeat**: Automatic reset for next episode

### Reward Function

```python
reward = (boss_damage * 1.0) - (player_damage * 0.1)

# Bonuses/Penalties
+ 500   # Boss defeated
- 75    # Player death
- 0.05  # Ineffective actions (whiffed attacks, unnecessary dodges)
```

## 🔧 Configuration

### Memory Addresses

The project uses dynamic pointer scanning to locate game values. If the game updates and breaks compatibility:

1. Update pointer chains in `pointer_scanner.py`
2. Verify memory addresses using Cheat Engine
3. Update the `DS3_Table_V4.CT` file if necessary

### Action Timing

Input timing can be adjusted in `dark_souls_api.py`:

```python
time.sleep(0.02)  # Delay between actions
```

## 📈 Results

Typical training progression:
- **Episodes 1-100**: Random exploration, learning basic controls
- **Episodes 100-500**: Developing combat awareness, reducing deaths
- **Episodes 500+**: Refining strategies, consistent boss defeats

Performance metrics are logged and can be analyzed using the included visualization tools.

## 🛠️ Development

### Project Structure

```
Dark_Souls/
├── scripts/                   # Core application code
│   ├── train.py              # Main training script
│   ├── gym_wrapper.py        # OpenAI Gym environment wrapper
│   ├── dark_souls_api.py     # Game API and reward logic
│   └── pointer_scanner.py    # Memory manipulation utilities
│
├── analysis/                  # Data analysis and visualization
│   ├── ds3_analyzer.py       # Comprehensive CLI analysis tool
│   ├── README.md            # Analysis tool documentation
│   └── output/              # Generated analysis outputs
│
├── data/                     # Runtime data and models
│   ├── *.txt                # Real-time game state files (Lua scripts)
│   └── *.pkl                # Model checkpoints and normalization stats
│
├── logs/                     # Training logs and monitoring
│   └── tensorboard/         # TensorBoard training metrics
│
└── lua_scripts/              # Cheat Engine automation scripts
    ├── gundyr_logger.lua    # Boss state logging
    ├── game_manager.lua     # Game state management
    ├── trigger.lua          # Environment reset triggers
    └── *.lua               # Additional automation scripts
```

### Adding New Actions

1. Define action in `action_dict` (dark_souls_api.py)
2. Update action space size in gym_wrapper.py
3. Implement action logic in `send_in_game_actions()`

### Debugging

- Enable debug output by uncommenting print statements
- Use Cheat Engine's memory viewer to verify pointer addresses
- Monitor `data/*.txt` files for real-time game state values

### Data Analysis

The project includes a comprehensive analysis tool for training data:

```bash
# Navigate to analysis directory
cd analysis

# Clean and analyze training logs
python ds3_analyzer.py clean run_log_model_4.txt
python ds3_analyzer.py parse cleaned_run_log_model_4.txt  
python ds3_analyzer.py analyze training_data.csv

# Monitor real-time training data
python ds3_analyzer.py monitor --duration 120
```

The analyzer provides:
- **Data cleaning** and filtering of invalid episodes
- **Statistical analysis** of training progress and performance
- **Comprehensive visualizations** including win rates, reward distributions, and learning curves
- **Real-time monitoring** of game state during training

See `analysis/README.md` for detailed usage instructions.

## ⚠️ Important Notes

- **Game Version**: Tested with Dark Souls III v1.15.2
- **Performance**: Training typically takes 2-6 hours depending on hardware
- **Safety**: The project only reads/writes specific memory addresses and sends keyboard inputs
- **Antivirus**: Some antivirus software may flag memory manipulation - add exceptions as needed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

### Original Team Contributors

This project builds upon the foundational work developed by our Machine Learning class team. Special thanks to the original contributors from the [FP-Machine-Learning repository](https://github.com/Zach-A-Moore/FP-Machine-Learning) (now outdated):

- **[Laween Al Sulaivany](https://github.com/laween-alsulaivany)** - Current maintainer and developer
- **[Ben Johnson](https://github.com/applesauce3535)** 
- **[Zach Moore](https://github.com/Zach-A-Moore)** 
- **[Shadrack Kumi](https://github.com/Shadrackkumi07)** 

### Technology Acknowledgments

- **FromSoftware** for creating Dark Souls III
- **Stable-Baselines3** team for the excellent RL library
- **Cheat Engine** community for memory manipulation tools
- **OpenAI Gym** for the environment interface standard

## 📞 Support

If you encounter issues:

1. Check the [Issues](https://github.com/yourusername/repo/issues) page
2. Verify your setup matches the requirements
3. Ensure Dark Souls III and Cheat Engine versions are compatible
4. Create a new issue with detailed error information

---

**Disclaimer**: This project is for educational purposes. Please respect the game's terms of service and use responsibly.