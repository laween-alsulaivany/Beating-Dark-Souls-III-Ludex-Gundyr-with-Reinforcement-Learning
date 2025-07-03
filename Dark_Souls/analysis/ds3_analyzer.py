#!/usr/bin/env python3
"""
Dark Souls III RL Training Data Analyzer
========================================

Comprehensive analysis tool for Dark Souls III reinforcement learning training data.
Consolidates log processing, data cleaning, visualization, and statistical analysis.

Author: Laween Al Sulaivany
Project: DS3 RL Agent for Iudex Gundyr
"""

import argparse
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


class DS3DataAnalyzer:
    """Main analysis class for Dark Souls III training data."""
    
    def __init__(self, data_dir="../data"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path("./output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Default reward function parameters
        self.baseline_boss_hp = 1037.0
        self.baseline_player_hp = 454.0
        
    def compute_final_reward(self, final_player_hp, final_boss_hp):
        """
        Computes final reward based on episode outcome.
        Mirrors the environment's reward logic.
        """
        boss_damage = self.baseline_boss_hp - final_boss_hp
        player_damage = self.baseline_player_hp - final_player_hp
        
        # Base reward calculation
        reward = boss_damage * 0.3 - player_damage * 0.1
        
        # Bonus for defeating boss
        if final_boss_hp <= 0:
            reward += boss_damage * 2
            
        # Penalty for dying
        if final_player_hp <= 0:
            reward -= player_damage * 0.5
            
        return reward
    
    def clean_run_logs(self, input_file, output_file=None, min_duration=5, max_boss_hp=1037):
        """
        Cleans raw log files by filtering out invalid runs.
        
        Args:
            input_file: Path to input log file
            output_file: Path to output cleaned file (optional)
            min_duration: Minimum episode duration in seconds
            max_boss_hp: Maximum acceptable final boss HP
        """
        if output_file is None:
            output_file = f"cleaned_{Path(input_file).stem}.txt"
            
        input_path = self.data_dir / input_file
        output_path = self.output_dir / output_file
        
        if not input_path.exists():
            print(f"❌ Error: Input file {input_path} not found!")
            return False
            
        filtered_lines = []
        stats = {"total": 0, "duration_filtered": 0, "boss_hp_filtered": 0, "kept": 0}
        
        print(f"🧹 Cleaning log file: {input_file}")
        print(f"   Filters: duration > {min_duration}s, boss HP < {max_boss_hp}")
        
        with open(input_path, "r") as file:
            for line in file:
                stats["total"] += 1
                try:
                    duration_match = re.search(r"Duration:\\s*(\\d+)", line)
                    boss_hp_match = re.search(r"Final BossHP:\\s*(\\d+)", line)
                    
                    if not duration_match or not boss_hp_match:
                        continue
                        
                    duration = int(duration_match.group(1))
                    boss_hp = int(boss_hp_match.group(1))
                    
                    if duration <= min_duration:
                        stats["duration_filtered"] += 1
                    elif boss_hp >= max_boss_hp:
                        stats["boss_hp_filtered"] += 1
                    else:
                        filtered_lines.append(line)
                        stats["kept"] += 1
                        
                except Exception as e:
                    print(f"⚠️  Skipping malformed line: {e}")
                    continue
        
        # Write cleaned data
        with open(output_path, "w") as file:
            file.writelines(filtered_lines)
            
        # Print statistics
        print(f"✅ Cleaning complete!")
        print(f"   📊 Total runs processed: {stats['total']}")
        print(f"   🗑️  Filtered (duration): {stats['duration_filtered']}")
        print(f"   🗑️  Filtered (boss HP): {stats['boss_hp_filtered']}")
        print(f"   ✅ Kept: {stats['kept']}")
        print(f"   💾 Output: {output_path}")
        
        return True
    
    def parse_logs_to_csv(self, input_file, output_file=None):
        """
        Parses cleaned log files and converts to structured CSV format.
        
        Args:
            input_file: Path to cleaned log file
            output_file: Path to output CSV file (optional)
        """
        if output_file is None:
            output_file = f"{Path(input_file).stem}_analysis.csv"
            
        input_path = self.data_dir / input_file if not (self.output_dir / input_file).exists() else self.output_dir / input_file
        output_path = self.output_dir / output_file
        
        if not input_path.exists():
            print(f"❌ Error: Input file {input_path} not found!")
            return False
            
        runs_data = []
        
        print(f"📊 Parsing logs to CSV: {input_file}")
        
        with open(input_path, "r") as file:
            for line in file:
                try:
                    # Extract data using regex
                    timestamp_match = re.search(r"(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})", line)
                    run_match = re.search(r"Run: (\\d+)", line)
                    outcome_match = re.search(r"Outcome: (\\w+)", line)
                    duration_match = re.search(r"Duration: (\\d+)", line)
                    player_hp_match = re.search(r"Final PlayerHP: (\\d+)", line)
                    boss_hp_match = re.search(r"Final BossHP: (\\d+)", line)
                    
                    if all([timestamp_match, run_match, outcome_match, duration_match, player_hp_match, boss_hp_match]):
                        timestamp = datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S")
                        run_num = int(run_match.group(1))
                        outcome = outcome_match.group(1)
                        duration = int(duration_match.group(1))
                        player_hp = int(player_hp_match.group(1))
                        boss_hp = int(boss_hp_match.group(1))
                        
                        # Calculate reward
                        reward = self.compute_final_reward(player_hp, boss_hp)
                        
                        runs_data.append({
                            "timestamp": timestamp,
                            "run": run_num,
                            "outcome": outcome,
                            "duration": duration,
                            "player_hp": player_hp,
                            "boss_hp": boss_hp,
                            "reward": reward,
                            "boss_damage": self.baseline_boss_hp - boss_hp,
                            "player_damage": self.baseline_player_hp - player_hp
                        })
                        
                except Exception as e:
                    print(f"⚠️  Error parsing line: {e}")
                    continue
        
        # Create DataFrame and save
        df = pd.DataFrame(runs_data)
        df.to_csv(output_path, index=False)
        
        print(f"✅ Parsing complete!")
        print(f"   📊 Total runs: {len(df)}")
        print(f"   🏆 Wins: {len(df[df['outcome'] == 'win'])}")
        print(f"   💀 Losses: {len(df[df['outcome'] == 'loss'])}")
        print(f"   💾 Output: {output_path}")
        
        return True
    
    def generate_training_analysis(self, csv_file):
        """
        Generates comprehensive training analysis and visualizations.
        
        Args:
            csv_file: Path to CSV file with training data
        """
        csv_path = self.output_dir / csv_file if not (self.data_dir / csv_file).exists() else self.data_dir / csv_file
        
        if not csv_path.exists():
            print(f"❌ Error: CSV file {csv_path} not found!")
            return False
            
        print(f"📈 Generating training analysis: {csv_file}")
        
        # Load data
        df = pd.read_csv(csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create comprehensive analysis plots
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Dark Souls III RL Training Analysis', fontsize=16, fontweight='bold')
        
        # 1. Win Rate Over Time
        df_sorted = df.sort_values('run')
        window = max(50, len(df) // 20)  # Adaptive window size
        win_rate = df_sorted['outcome'].eq('win').rolling(window=window).mean() * 100
        
        axes[0, 0].plot(df_sorted['run'], win_rate, color='green', linewidth=2)
        axes[0, 0].set_title(f'Win Rate Over Time (Rolling {window}-episode average)')
        axes[0, 0].set_xlabel('Episode')
        axes[0, 0].set_ylabel('Win Rate (%)')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Reward Distribution
        axes[0, 1].hist(df['reward'], bins=50, alpha=0.7, color='blue', edgecolor='black')
        axes[0, 1].set_title('Reward Distribution')
        axes[0, 1].set_xlabel('Reward')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].axvline(df['reward'].mean(), color='red', linestyle='--', 
                          label=f'Mean: {df["reward"].mean():.2f}')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Episode Duration vs Outcome
        win_durations = df[df['outcome'] == 'win']['duration']
        loss_durations = df[df['outcome'] == 'loss']['duration']
        
        axes[0, 2].hist([loss_durations, win_durations], bins=30, alpha=0.7, 
                       label=['Loss', 'Win'], color=['red', 'green'])
        axes[0, 2].set_title('Episode Duration by Outcome')
        axes[0, 2].set_xlabel('Duration (seconds)')
        axes[0, 2].set_ylabel('Frequency')
        axes[0, 2].legend()
        axes[0, 2].grid(True, alpha=0.3)
        
        # 4. Boss Damage vs Player Damage
        wins = df[df['outcome'] == 'win']
        losses = df[df['outcome'] == 'loss']
        
        axes[1, 0].scatter(losses['boss_damage'], losses['player_damage'], 
                          alpha=0.6, color='red', label='Loss', s=20)
        axes[1, 0].scatter(wins['boss_damage'], wins['player_damage'], 
                          alpha=0.6, color='green', label='Win', s=20)
        axes[1, 0].set_title('Boss Damage vs Player Damage')
        axes[1, 0].set_xlabel('Boss Damage Dealt')
        axes[1, 0].set_ylabel('Player Damage Taken')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # 5. Learning Progress (Cumulative Wins)
        df_sorted['cumulative_wins'] = df_sorted['outcome'].eq('win').cumsum()
        axes[1, 1].plot(df_sorted['run'], df_sorted['cumulative_wins'], 
                       color='purple', linewidth=2)
        axes[1, 1].set_title('Cumulative Wins Over Training')
        axes[1, 1].set_xlabel('Episode')
        axes[1, 1].set_ylabel('Total Wins')
        axes[1, 1].grid(True, alpha=0.3)
        
        # 6. Win Frequency Timeline
        df['hour'] = df['timestamp'].dt.floor('H')
        hourly_wins = df[df['outcome'] == 'win'].groupby('hour').size()
        
        if len(hourly_wins) > 0:
            axes[1, 2].plot(hourly_wins.index, hourly_wins.values, 
                           marker='o', color='orange', linewidth=2)
            axes[1, 2].set_title('Wins per Hour')
            axes[1, 2].set_xlabel('Time')
            axes[1, 2].set_ylabel('Wins per Hour')
            axes[1, 2].tick_params(axis='x', rotation=45)
            axes[1, 2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save the plot
        plot_path = self.output_dir / f"{Path(csv_file).stem}_analysis.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"💾 Analysis plot saved: {plot_path}")
        
        # Generate summary statistics
        self._generate_summary_stats(df, csv_file)
        
        plt.show()
        return True
    
    def _generate_summary_stats(self, df, csv_file):
        """Generate and save summary statistics."""
        stats_file = self.output_dir / f"{Path(csv_file).stem}_summary.txt"
        
        with open(stats_file, 'w') as f:
            f.write("=" * 60 + "\\n")
            f.write("DARK SOULS III RL TRAINING SUMMARY\\n")
            f.write("=" * 60 + "\\n\\n")
            
            # Basic stats
            total_episodes = len(df)
            total_wins = len(df[df['outcome'] == 'win'])
            total_losses = len(df[df['outcome'] == 'loss'])
            win_rate = (total_wins / total_episodes) * 100 if total_episodes > 0 else 0
            
            f.write(f"Total Episodes: {total_episodes}\\n")
            f.write(f"Wins: {total_wins} ({win_rate:.2f}%)\\n")
            f.write(f"Losses: {total_losses} ({100-win_rate:.2f}%)\\n\\n")
            
            # Duration stats
            f.write("EPISODE DURATION STATISTICS:\\n")
            f.write(f"Mean Duration: {df['duration'].mean():.2f} seconds\\n")
            f.write(f"Median Duration: {df['duration'].median():.2f} seconds\\n")
            f.write(f"Max Duration: {df['duration'].max()} seconds\\n")
            f.write(f"Min Duration: {df['duration'].min()} seconds\\n\\n")
            
            # Reward stats
            f.write("REWARD STATISTICS:\\n")
            f.write(f"Mean Reward: {df['reward'].mean():.2f}\\n")
            f.write(f"Median Reward: {df['reward'].median():.2f}\\n")
            f.write(f"Max Reward: {df['reward'].max():.2f}\\n")
            f.write(f"Min Reward: {df['reward'].min():.2f}\\n\\n")
            
            # Win vs Loss comparison
            if total_wins > 0 and total_losses > 0:
                wins = df[df['outcome'] == 'win']
                losses = df[df['outcome'] == 'loss']
                
                f.write("WIN vs LOSS COMPARISON:\\n")
                f.write(f"Average Win Duration: {wins['duration'].mean():.2f}s\\n")
                f.write(f"Average Loss Duration: {losses['duration'].mean():.2f}s\\n")
                f.write(f"Average Win Reward: {wins['reward'].mean():.2f}\\n")
                f.write(f"Average Loss Reward: {losses['reward'].mean():.2f}\\n")
                f.write(f"Average Boss Damage (Wins): {wins['boss_damage'].mean():.2f}\\n")
                f.write(f"Average Boss Damage (Losses): {losses['boss_damage'].mean():.2f}\\n")
        
        print(f"📄 Summary statistics saved: {stats_file}")
    
    def monitor_real_time_data(self, duration=60):
        """
        Monitor real-time game data from txt files.
        
        Args:
            duration: Monitoring duration in seconds
        """
        print(f"👁️  Monitoring real-time game data for {duration} seconds...")
        print("Press Ctrl+C to stop early\\n")
        
        player_file = self.data_dir / "player_info.txt"
        gundyr_file = self.data_dir / "gundyr_info.txt"
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                # Read player data
                if player_file.exists():
                    try:
                        with open(player_file, "r") as f:
                            data = f.read().strip()
                            if data:
                                parts = data.split(",")
                                if len(parts) >= 7:
                                    health, stamina, estus, x, y, z, angle = map(float, parts[:7])
                                    print(f"🎮 Player - HP: {health:.0f}, Stamina: {stamina:.0f}, "
                                          f"Pos: ({x:.1f}, {y:.1f}, {z:.1f}), Angle: {angle:.2f}")
                    except Exception as e:
                        print(f"⚠️  Error reading player data: {e}")
                
                # Read boss data
                if gundyr_file.exists():
                    try:
                        with open(gundyr_file, "r") as f:
                            data = f.read().strip()
                            if data:
                                parts = data.split(",")
                                if len(parts) >= 6:
                                    health, x, y, z, angle, anim = parts[:6]
                                    print(f"👹 Gundyr - HP: {health}, Pos: ({x}, {y}, {z}), "
                                          f"Angle: {angle}, Anim: {anim}")
                    except Exception as e:
                        print(f"⚠️  Error reading Gundyr data: {e}")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\\n⏹️  Monitoring stopped by user")
    
    def list_available_files(self):
        """List all available data files for analysis."""
        print("📁 Available data files:")
        print("=" * 40)
        
        # Check data directory
        if self.data_dir.exists():
            print(f"\\n📂 Data directory ({self.data_dir}):")
            for file in sorted(self.data_dir.glob("*.txt")):
                if file.name not in ["gundyr_info.txt", "player_info.txt", "lock_on.txt"]:
                    print(f"   📄 {file.name}")
            
            for file in sorted(self.data_dir.glob("*.csv")):
                print(f"   📊 {file.name}")
        
        # Check output directory
        if self.output_dir.exists() and any(self.output_dir.iterdir()):
            print(f"\\n📂 Output directory ({self.output_dir}):")
            for file in sorted(self.output_dir.glob("*")):
                if file.is_file():
                    icon = "📊" if file.suffix == ".csv" else "📄" if file.suffix == ".txt" else "🖼️" if file.suffix == ".png" else "📁"
                    print(f"   {icon} {file.name}")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Dark Souls III RL Training Data Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ds3_analyzer.py clean run_log.txt --min-duration 10
  python ds3_analyzer.py parse cleaned_run_log.txt
  python ds3_analyzer.py analyze training_data.csv
  python ds3_analyzer.py monitor --duration 120
  python ds3_analyzer.py list
        """
    )
    
    parser.add_argument('command', choices=['clean', 'parse', 'analyze', 'monitor', 'list'],
                       help='Analysis command to execute')
    parser.add_argument('file', nargs='?', help='Input file name')
    parser.add_argument('--output', '-o', help='Output file name')
    parser.add_argument('--min-duration', type=int, default=5,
                       help='Minimum episode duration for cleaning (default: 5)')
    parser.add_argument('--max-boss-hp', type=int, default=1037,
                       help='Maximum boss HP for valid episodes (default: 1037)')
    parser.add_argument('--duration', type=int, default=60,
                       help='Monitoring duration in seconds (default: 60)')
    parser.add_argument('--data-dir', default='../data',
                       help='Data directory path (default: ../data)')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = DS3DataAnalyzer(data_dir=args.data_dir)
    
    print("🎮 Dark Souls III RL Training Data Analyzer")
    print("=" * 50)
    
    # Execute commands
    if args.command == 'list':
        analyzer.list_available_files()
        
    elif args.command == 'clean':
        if not args.file:
            print("❌ Error: File argument required for clean command")
            return 1
        analyzer.clean_run_logs(args.file, args.output, args.min_duration, args.max_boss_hp)
        
    elif args.command == 'parse':
        if not args.file:
            print("❌ Error: File argument required for parse command")
            return 1
        analyzer.parse_logs_to_csv(args.file, args.output)
        
    elif args.command == 'analyze':
        if not args.file:
            print("❌ Error: File argument required for analyze command")
            return 1
        analyzer.generate_training_analysis(args.file)
        
    elif args.command == 'monitor':
        analyzer.monitor_real_time_data(args.duration)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
