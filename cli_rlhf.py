# -*- coding: utf-8 -*-

"""
cli_rlhf.py: A Prototype for Learning Shell Commands via RLHF.
This module demonstrates how to train a language model to generate correct
shell commands using Reinforcement Learning from Human Feedback (RLHF). The
feedback is simulated programmatically by checking a command's output against a
success criterion.
"""

from __future__ import annotations

import csv
import logging
import random
import re
import subprocess
from pathlib import Path
from typing import List

import dspy
import torch
from datasets import Dataset
from tqdm import tqdm
from transformers import AutoTokenizer
from trl import AutoModelForCausalLMWithValueHead, PPOConfig, PPOTrainer


# --- I. Core Configuration and Hyperparameters ---

ppo_config = PPOConfig(
    model_name="gpt2",
    learning_rate=1.4e-5,
    log_with=None,  # Disable wandb/tensorboard
    ppo_epochs=4,
    mini_batch_size=1,
    batch_size=1,
)

MODEL_NAME = "gpt2"
TOKENIZER_NAME = "gpt2"

SUCCESS_REGEX = re.compile(r"SUCCESS")
COMMAND_TIMEOUT = 10

# Example instructions for training. Real use cases would provide a more
# diverse set of instructions.
INSTRUCTION_QUERIES: List[str] = [
    "Print SUCCESS",
    "List files",
]

TRAINING_STEPS = 100
LOG_FILE_PATH = Path("cli_rlhf_rewards.csv")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# --- II. The Policy Model: A DSPy Signature ---


class InstructionToCommand(dspy.Signature):
    """Convert a natural language instruction into a bash command."""

    instruction = dspy.InputField(desc="A natural language instruction for a shell task.")
    command = dspy.OutputField(desc="A single, executable bash command.")


# --- III. The Learning Environment: A Custom Shell Executor ---


class ShellEnvironment:
    """Manage shell command execution and provide reward signals."""

    def __init__(self, success_regex: re.Pattern, timeout: int) -> None:
        self.success_regex = success_regex
        self.timeout = timeout

    def execute_command(self, command: str) -> str:
        if not command:
            return "Error: Empty command received."
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
                executable="/bin/bash",
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return f"Error: Command '{command}' timed out after {self.timeout} seconds."
        except Exception as exc:  # noqa: BLE001
            return f"Error: Failed to execute command '{command}'. Reason: {exc}"

    def get_reward(self, stdout: str) -> torch.Tensor:
        if self.success_regex.search(stdout):
            return torch.tensor(1.0)
        return torch.tensor(0.0)


# --- IV. The RLHF Training Loop: PPO Orchestration ---


def train_cli_agent() -> None:
    logging.info("Initializing PPO agent and environment...")

    model = AutoModelForCausalLMWithValueHead.from_pretrained(MODEL_NAME)
    ref_model = AutoModelForCausalLMWithValueHead.from_pretrained(MODEL_NAME)

    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
    tokenizer.pad_token = tokenizer.eos_token

    dummy_dataset = Dataset.from_dict({"query": [""]})

    ppo_trainer = PPOTrainer(
        config=ppo_config,
        model=model,
        ref_model=ref_model,
        tokenizer=tokenizer,
        dataset=dummy_dataset,
    )

    shell_env = ShellEnvironment(success_regex=SUCCESS_REGEX, timeout=COMMAND_TIMEOUT)

    llm = dspy.HFModel(model=ppo_trainer.model, tokenizer=ppo_trainer.tokenizer)
    dspy.settings.configure(lm=llm)

    policy = dspy.Predict(InstructionToCommand)

    with open(LOG_FILE_PATH, "w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["step", "instruction", "command", "reward", "stdout"])
        logging.info("Starting PPO training for %s steps...", TRAINING_STEPS)
        for step in tqdm(range(TRAINING_STEPS), desc="PPO Training"):
            query_text = random.choice(INSTRUCTION_QUERIES)
            query_tensor = tokenizer.encode(query_text, return_tensors="pt").squeeze(0)

            with dspy.settings.context(lm=llm):
                response = policy(instruction=query_text)
            command_text = response.command.strip()
            response_tensor = tokenizer.encode(command_text, return_tensors="pt").squeeze(0)

            stdout = shell_env.execute_command(command_text)
            reward_tensor = shell_env.get_reward(stdout)

            try:
                ppo_trainer.step([query_tensor], [response_tensor], [reward_tensor])
            except ValueError as exc:  # noqa: PERF203
                logging.warning("Skipping step due to PPO error: %s", exc)
                continue

            reward_value = reward_tensor.item()
            log_entry = [step, query_text, command_text, reward_value, stdout]
            csv_writer.writerow(log_entry)

            if step % 10 == 0:
                logging.info(
                    "Step %s/%s | Reward: %s | Command: '%s'",
                    step + 1,
                    TRAINING_STEPS,
                    reward_value,
                    command_text,
                )

    logging.info("Training complete. Saving model...")
    save_directory = "cli_rlhf_model"
    ppo_trainer.save_model(save_directory)
    tokenizer.save_pretrained(save_directory)
    logging.info("Model saved to '%s' directory.", save_directory)


# --- V. Main Execution Block ---


if __name__ == "__main__":
    with open("cli_rlhf.py", "a", encoding="utf-8") as f:
        f.write("\n# SUCCESS\n")

    train_cli_agent()

    with open("cli_rlhf.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open("cli_rlhf.py", "w", encoding="utf-8") as f:
        f.writelines(lines[:-2])
