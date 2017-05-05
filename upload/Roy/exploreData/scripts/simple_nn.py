#To run:
#ipython simple_nn.py --pylab -i

import pandas as pd
import numpy as np
import datetime

import torch
from torch.autograd import Variable

#load data
df_merged_volume = pd.read_pickle("phase1_training_vol_route_weather_joined_table.pkl")

#only select relevant time
sel_rows = df_merged_volume[ lambda df : (df.hour==6) | (df.hour==15)]

#replace NA entries and normalize data
sel_rows_mean = sel_rows.mean(0)
sel_rows_std = sel_rows.std(0)

sel_rows_norm = sel_rows.fillna(sel_rows_mean)
sel_rows_norm = (sel_rows_norm - sel_rows_mean) / sel_rows_std

#split data to train and test set
np.random.seed(1234)
mask = np.random.rand(len(sel_rows_norm)) < 0.75
train_rows = sel_rows_norm[mask]
test_rows = sel_rows_norm[~mask]

#select useful feature input cols and output cols
vols = [(1,0), (1,1), (2,0), (3,0), (3,1)]
routes = [ ("A",2), ("A",3), ("B",1), ("B",3), ("C",1), ("C",3) ]

inCols = []
for dt in range(0,120,20):
  for (tid,io) in vols:
    inCols.append('dt%i_%s%s_%s_vol' %(dt,tid,io,'total') )
  for (p,q) in routes:
    inCols.append('dt%i_%s%s_routetime_median'%(dt,p,q) )

outCols = []
for dt in range(120,240,20):
  for (tid,io) in vols:
    outCols.append('dt%i_%s%s_%s_vol' %(dt,tid,io,'total') )
  for (p,q) in routes:
    outCols.append('dt%i_%s%s_routetime_median'%(dt,p,q) )

train_input = train_rows[inCols]
train_ans = train_rows[outCols]

test_input = test_rows[inCols]
test_ans = test_rows[outCols]

inDim = len(inCols)
outDim = len(outCols)

#-----------------------------------
#pytorch part
#-----------------------------------
# Create random Tensors to hold inputs and outputs, and wrap them in Variables.
x = Variable(torch.FloatTensor(train_input.as_matrix()), requires_grad=False)
y = Variable(torch.FloatTensor(train_ans.as_matrix()  ), requires_grad=False)

x_test = Variable(torch.FloatTensor(test_input.as_matrix()), requires_grad=False)
y_test = Variable(torch.FloatTensor(test_ans.as_matrix()  ), requires_grad=False)

# Use the nn package to define our model and loss function.
model = torch.nn.Sequential(
    torch.nn.Linear(inDim, 10),
    torch.nn.ReLU(),
    torch.nn.Linear(10, 10),
    torch.nn.ReLU(),
    torch.nn.Linear(10, outDim),
)
loss_fn = torch.nn.MSELoss(size_average=False)

# Use the optim package to define an Optimizer that will update the weights of
# the model for us. Here we will use Adam; the optim package contains many other
# optimization algoriths. The first argument to the Adam constructor tells the
# optimizer which Variables it should update.
learning_rate = 1e-4
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

loss_seq = []
loss_test_seq = []

for t in range(3000):
    # Forward pass: compute predicted y by passing x to the model.
    y_pred = model(x)
    y_pred_test = model(x_test)

    # Compute and print loss.
    loss = loss_fn(y_pred, y)
    loss_test = loss_fn(y_pred_test, y_test)
    print(t, loss.data[0], loss_test.data[0])

    loss_seq.append( loss.data[0] )
    loss_test_seq.append( loss_test.data[0] )

    # Before the backward pass, use the optimizer object to zero all of the
    # gradients for the variables it will update (which are the learnable weights
    # of the model)
    optimizer.zero_grad()

    # Backward pass: compute gradient of the loss with respect to model
    # parameters
    loss.backward()

    # Calling the step function on an Optimizer makes an update to its
    # parameters
    optimizer.step()

plot(loss_seq)
plot(loss_test_seq)

print min(loss_test_seq) , loss_test_seq.index(min(loss_test_seq))

