import tensorflow as tf
import gym
import os
import random

import numpy as np
import scipy

import pandas as pd
import matplotlib.pyplot as plt
from collections import deque

from ReplayBuffer import ReplayBuffer
from Experience import Experience
from Utils import FileLogger, AverageRewardTracker, plot, backup_model
from DDQN import DDQN

env = gym.make("LunarLander-v2")

state_space = env.observation_space.shape[0] #states
action_space = env.action_space.n # actions
learning_rate = 0.001
gamma = 0.99
epsilon = 0.5
min_epsilon = 0.01
decay_rate = 0.995 # per episode
buffer_maxlen = 200000
reg_factor = 0.001

batch_size = 128
training_start = 256 # which step to start training
target_update_freq = 1000
max_episodes = 20
max_steps = 20
train_freq = 4
backup_freq = 100

agent = DDQN(state_space, action_space, learning_rate, 
  gamma, epsilon, min_epsilon, decay_rate, buffer_maxlen, reg_factor)

agent.load_from_weights('model_200.h5')

avg_reward_tracker = AverageRewardTracker(100) 
file_logger = FileLogger()

for episode in range(max_episodes): # training loop
  episode_reward = 0 
  state = env.reset() # vector of 8

  total_reward = 0 # reward tracker

  for step in range(1, max_steps + 1): # limit number of steps
    action = agent.select_action(state) # get action 
    next_state, reward, done, info = env.step(action) # next step
    total_reward += reward # increment reward

    if step == max_steps: # stop at max steps 
      print(f"Episode reached the maximum number of steps. {max_steps}")
      done = True

    experience = Experience(state, action, reward, next_state, done) # create new experience object
    agent.buffer.add(experience) # add experience to buffer

    state = next_state # update state

    if step % target_update_freq == 0: # update target weights every x steps 
      print("Updating target model")
      agent.update_target_weights()
    
    if (agent.buffer.length() >= training_start) & (step % train_freq == 0): # train agent every x steps
      batch = agent.buffer.sample(batch_size)
      inputs, targets = agent.calculate_inputs_and_targets(batch)
      agent.train(inputs, targets)

    if done: # stop if this action results in goal reached
      break
  
  avg_reward_tracker.add(total_reward)
  average = avg_reward_tracker.get_average()

  print(f"EPISODE {episode} finished in {step} steps, " )
  print(f"epsilon {agent.epsilon}, reward {total_reward}. ")
  print(f"Average reward over last 100: {average} \n")
  file_logger.log(episode, step, total_reward, average)
  if episode != 0 and episode % backup_freq == 0: # back up model every x steps 
    backup_model(agent.model, episode)
  
  agent.epsilon_decay()

plot(file_logger)
