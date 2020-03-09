import os

import nltk
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

import numpy
import tflearn
import tensorflow
import random
import json
import pickle
from .models import UserInput

module_dir = os.path.dirname(__file__)
file_path = os.path.join(module_dir, 'intents.json')
with open(file_path) as file:
  data = json.load(file)

links_file_path = os.path.join(module_dir, 'intentsLinks.json')
with open(links_file_path) as file:
  linksData = json.load(file)

words = []
labels = []
docs_x = []
docs_y = []

for intent in data['intents']:
  for pattern in intent['patterns']:
    wrds = nltk.word_tokenize(pattern)
    words.extend(wrds)
    docs_x.append(wrds)
    docs_y.append(intent['tag'])

  if intent['tag'] not in labels:
    labels.append(intent['tag'])

words = [stemmer.stem(w.lower()) for w in words if w != "?"]
words = sorted(list(set(words)))

labels = sorted(labels)

training = []
output = []

out_empty = [0 for _ in range(len(labels))]

for x, doc in enumerate(docs_x):
  bag = []

  wrds = [stemmer.stem(w) for w in doc]

  for w in words:
    if w in wrds:
      bag.append(1)
    else:
      bag.append(0)

  output_row = out_empty[:]
  output_row[labels.index(docs_y[x])] = 1

  training.append(bag)
  output.append(output_row)

training = numpy.array(training)
output = numpy.array(output)

with open('data.pickle', 'wb') as f:
  pickle.dump((words, labels, training, output), f)
    
tensorflow.reset_default_graph()

net = tflearn.input_data(shape=[None, len(training[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(output[0]), activation='softmax')
net = tflearn.regression(net)

model = tflearn.DNN(net)

model.fit(training, output, n_epoch=1000, batch_size=9, show_metric=True)
model.save('model.tflearn')

def bag_of_wrds(s, words):
  bag = [0 for _ in range(len(words))]

  s_words = nltk.word_tokenize(s)
  s_words = [stemmer.stem(word.lower()) for word in s_words]

  for se in s_words:
    for i, w in enumerate(words):
      if w == se:
        bag[i] = 1

  return numpy.array(bag)

def chat(user_input):
  FINANCE_INTENTS = ["savings", "budgeting"]

  previous_user_input = list(UserInput.objects.all())[-2].text
  # two_prior_user_input = list(UserInput.objects.all())[-3].text
  # three_prior_user_input = list(UserInput.objects.all())[-4].text

  ERROR_THRESHOLD = 0.7
    
  results = model.predict([bag_of_wrds(user_input, words)])[0]
  results_index = numpy.argmax(results)
  tag = labels[results_index]



  # if user_input == 'yes':
  #   results = model.predict([bag_of_wrds(previous_user_input, words)])[0]
  #   results_index = numpy.argmax(results)
  #   tag = labels[results_index]
  #   for tg in linksData['intents']:
  #     if tg['tag'] == tag:
  #       responses = tg['responses']
  #   return random.choice(responses)

  if results[results_index] > ERROR_THRESHOLD:
    for tg in data['intents']:
      if tg['tag'] == 'yes':
        return showLinks(previous_user_input)
      elif tg['tag'] == tag:
        print('inside tag==tag')
        print(tg['tag'])
        responses = tg['responses']
        if tg['tag'] in FINANCE_INTENTS:
          return responses[0]
        else:
          return random.choice(responses)
  else:
    return "Sorry I don't undertand"

# def previousTag(previous_input):
#   results = model.predict([bag_of_wrds(previous_input, words)])[0]
#   results_index = numpy.argmax(results)
#   tag = labels[results_index]
#   return tag

def showLinks(prior_user_inputs):
  results = model.predict([bag_of_wrds(prior_user_inputs, words)])[0]
  results_index = numpy.argmax(results)
  tag = labels[results_index]

  for tg in linksData['intents']:
    if tg['tag'] == tag:
      responses = tg['responses']
      print(responses[0])
    return responses[0]

    # results = model.predict([bag_of_wrds(prior_user_inputs[0], words)])[0]
    # results_index = numpy.argmax(results)
    # tag = labels[results_index]

    # two_prior_results = model.predict([bag_of_wrds(prior_user_inputs[1], words)])[0]
    # two_prior_results_index = numpy.argmax(results)
    # two_prior_tag = labels[results_index]

    # three_prior_results = model.predict([bag_of_wrds(prior_user_inputs[2], words)])[0]
    # three_prior_results_index = numpy.argmax(results)
    # three_prior_tag = labels[results_index]

    # for tg in linksData['intents']:
    #   if tg['tag'] == tag:
    #     responses = tg['responses']
    #     if three_prior_tag == tag:
    #       return responses[2]
    #     elif three_prior_tag == tag:
    #       return responses[1]
    #     else: 
    #       return responses[0]